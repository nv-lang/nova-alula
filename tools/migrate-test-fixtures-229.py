#!/usr/bin/env python3
"""Перенос фикстур тестов `*.alula.test.json` с провода 0.28 на провод 0.29 (эпик 0.29, задача G
методики 120; пакет alula 0.29.0). Скрипт-спутник `migrate-alula-229.py` (машины) — фикстуры тот не
трогает: `migrate_tree` берёт только деревья с `alula_version == 0.28`.

Зачет переноса — ТИПИЗИРОВАННЫЙ: скрипт знает, какие поля необязательные, где записи/варианты, —
поэтому читает дерево машины (machine/2: `alula compile` через `--alula`, или готовый
`<имя>.alula.json` рядом) и её таблицы: данные, стороны (включая вложенные машины), вход, конец.
Чисто механическое «null → {"$some"}» неверно: null — это none, «присутствующий null» — {"$some": null}.

Две формы провода (канон — шапки `src/machine/value.nv` и `src/machine/decode.nv`, README «The move
to 0.29»):
  - ВНУТРЕННЯЯ (данные теста: expect.data, also.*.data, expect.outcome): различимое необязательное
    `{"$some": v}` (null остается none); записи/варианты уже несут `$record`/`$variant` — их поля
    обходятся по типам;
  - ВНЕШНЯЯ (ответ стороны `agent`: event.input событий kind=answer по запросу агентской стороны,
    включая вложенные машины): `{"case": <имя>, "fields": {…}}`, необязательное — ТОЛЬКО
    `{"none": true}` / `{"some": v}` (голой формы у внешнего кодека нет, AL-153).

Идемпотентен: повторный запуск ничего не меняет (обе формы 0.29 распознаются и сохраняются).
Что НЕ решает: значения, чей тип по дереву не найден (чужие ключи данных, неизвестные стороны) —
место в отчете (выход 1), значение не трогается.

Запуск: `python tools/migrate-test-fixtures-229.py [--dry-run] [--alula <программа alula>]`
        `        [--machines <папка машин>] <фикстура или папка>…` (папки — рекурсивно по
`*.alula.test.json`); код 0 — перенесено (или нечего), 1 — остались места, 2 — ошибка запуска.
Машина ищется `<имя>.alula.md` (компилируется) или `<имя>.alula.json` рядом с фикстурой и вверх до
`--machines`; реестр — `registry.md` рядом с машиной. `--selftest` — регрессионный тест без дерева.
"""
import json, os, re, subprocess, sys, tempfile

# ---- разбор спецификаций типов (строки machine/2: "?int", "[]text", '{int: Summary}', '"a" | "b"') ----

def parse_spec(s):
    s = s.strip()
    if s.startswith('??'):
        return ('opt', ('opt', parse_spec(s[2:])))
    if s.startswith('?'):
        return ('opt', parse_spec(s[1:]))
    if s.startswith('[]'):
        return ('list', parse_spec(s[2:]))
    if s.startswith('{') and s.endswith('}') and ':' in s:
        k, v = s[1:-1].split(':', 1)
        return ('dict', parse_spec(k), parse_spec(v))
    if '|' in s or s.startswith('"'):
        return ('set', s)
    if s == 'text':
        return ('text',)
    if s == 'bool':
        return ('bool',)
    if s == 'id':
        return ('id',)
    if s.startswith('int'):
        return ('int',)
    if s.startswith('float') or s.startswith('вещ'):
        return ('float',)
    return ('type', s)


def spec_of_field(fields, name):
    for f in fields:
        if f['name'] == name:
            return parse_spec(f['type'])
    return None


class Machine:
    """Таблицы одной машины: данные по JSON-именам, стороны по id, типы, вход, результат конца."""

    def __init__(self, tree):
        self.name = tree.get('machine') or tree.get('name') or ''
        self.data = {d['name']: parse_spec(d['type']) for d in tree.get('data', [])}
        self.records = {r['name']: r['fields'] for r in tree.get('types', {}).get('records', [])}
        self.variant_defs = {v['name']: v for v in tree.get('types', {}).get('variants', [])}
        self.variants = {v['name']: v['cases'] for v in tree.get('types', {}).get('variants', [])}
        self.parties = tree.get('parties', [])
        self.signals = {}
        for sig in tree.get('signals', []) or []:
            self.signals[sig['name']] = sig.get('fields', [])
        for p in self.parties:
            for sig in p.get('signals', []) or []:
                self.signals[sig['name']] = sig.get('fields', [])
        self.input_fields = (tree.get('input') or {}).get('fields', [])
        self.result = (tree.get('ends') or {}).get('result')

    def party_by_id(self, pid):
        for p in self.parties:
            if p.get('id') == pid:
                return p
        return None

    def agent_result_spec(self, pid):
        p = self.party_by_id(pid)
        if p and p.get('kind') == 'agent' and p.get('result'):
            return ('type', p['result'])
        return None

    # СЛОВО значения энума по имени случая (values таблицы), иначе само имя
    def enum_word(self, variant, case):
        d = self.variant_defs.get(variant) or {}
        for pair in d.get('values', []) or []:
            if pair[0] == case:
                return pair[1]
        return case

    # Энум ли тип: все случаи без полей
    def is_enum(self, variant):
        cases = self.variants.get(variant)
        if cases is None:
            return False
        for c in cases:
            if c.get('fields'):
                return False
        return True

    def nested_of_party(self, pid):
        p = self.party_by_id(pid)
        if p and p.get('kind') == 'machine':
            return p.get('nested')
        return None


def load_machines(fixture_path, machine_name, machines_dir, alula, cache):
    """Дерево машины по имени: готовый .alula.json рядом/выше, иначе компиляция .alula.md."""
    if machine_name in cache:
        return cache[machine_name]
    roots = [os.path.dirname(os.path.abspath(fixture_path))]
    if machines_dir:
        roots.append(os.path.abspath(machines_dir))
    md = js = rg = None
    for root in roots:
        for base, _dirs, files in os.walk(root):
            if os.path.basename(machine_name) + '.alula.md' in files:
                md = os.path.join(base, machine_name + '.alula.md')
                if 'registry.md' in files:
                    rg = os.path.join(base, 'registry.md')
                break
            if os.path.basename(machine_name) + '.alula.json' in files:
                js = os.path.join(base, machine_name + '.alula.json')
                break
        if md or js:
            break
    if js and not md:
        with open(js, encoding='utf-8', newline='') as f:
            m = Machine(json.load(f))
            cache[machine_name] = m
            return m
    if not md:
        raise LookupError('машина %s не найдена (ни .alula.md, ни .alula.json) около %s' % (machine_name, fixture_path))
    if not alula:
        raise LookupError('для компиляции %s нужен --alula <программа>' % md)
    cmd = [os.path.abspath(alula), 'compile', md, '-o', os.path.join(tempfile.gettempdir(), 'alula-fixture-mig.json'), '--force']
    if rg:
        cmd += ['--registry', rg]
    done = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if done.returncode != 0:
        first = [l for l in (done.stderr or done.stdout).splitlines() if l.strip()][:1]
        raise LookupError('alula compile не собрал %s: %s' % (md, first[0] if first else done.returncode))
    with open(cmd[4], encoding='utf-8', newline='') as f:
        m = Machine(json.load(f))
    cache[machine_name] = m
    return m


# ---- обход внутренней формы (данные теста) ----------------------------------------------------------------

def walk_internal(v, spec, path, places):
    if spec is None:
        return v
    kind = spec[0]
    if kind == 'opt':
        if v is None:
            return None
        if isinstance(v, dict) and '$some' in v:
            return {'$some': walk_internal(v['$some'], spec[1], path + '.$some', places)}
        return {'$some': walk_internal(v, spec[1], path + '.$some', places)}
    if kind == 'list':
        if isinstance(v, list):
            return [walk_internal(x, spec[1], '%s[%d]' % (path, i), places) for i, x in enumerate(v)]
        return v
    if kind == 'type':
        rec = spec[1] if isinstance(spec, tuple) else None
        if isinstance(v, dict) and '$record' in v:
            fields = rec_tables.records.get(rec)
            if fields is None:
                places.append('%s: запись %s не в таблицах машины — значение не тронуто' % (path, rec))
                return v
            out = {'$record': v['$record'], 'fields': {}}
            for k, x in v.get('fields', {}).items():
                fs = spec_of_field(fields, k)
                if fs is None:
                    out['fields'][k] = x
                else:
                    out['fields'][k] = walk_internal(x, fs, '%s.%s' % (path, k), places)
            return out
        if isinstance(v, dict) and '$variant' in v:
            cases = rec_tables.variants.get(rec)
            cf = None
            if cases:
                for c in cases:
                    if c['name'] == v['name']:
                        cf = c.get('fields', [])
            if cf is None:
                places.append('%s: вариант %s.%s не в таблицах машины — значение не тронуто' % (path, rec, v.get('name')))
                return v
            held = v.get('fields', {})
            walked = {}
            for k, x in held.items():
                fs = spec_of_field(cf, k)
                walked[k] = x if fs is None else walk_internal(x, fs, '%s.%s' % (path, k), places)
            # канон value.nv: «fields» опускается, когда полей нет — движок в ответах её не пишет
            if walked:
                return {'$variant': v['$variant'], 'name': v['name'], 'fields': walked}
            return {'$variant': v['$variant'], 'name': v['name']}
        return v
    return v


class _RecTables:
    """Таблицы текущей машины для обходов (рекурсия не замыкает машину параметром)."""
    def __init__(self):
        self.records = {}
        self.variants = {}
        self.machine = None


rec_tables = _RecTables()


def with_machine_tables(m, fn):
    saved = (rec_tables.records, rec_tables.variants, rec_tables.machine)
    rec_tables.records, rec_tables.variants, rec_tables.machine = m.records, m.variants, m
    try:
        return fn()
    finally:
        rec_tables.records, rec_tables.variants, rec_tables.machine = saved


# ---- обход внешней формы (ответ стороны agent) ------------------------------------------------------------

def walk_external(v, spec, path, places):
    if spec is None:
        return v
    kind = spec[0]
    if kind == 'opt':
        if v is None:
            return {'none': True}
        if isinstance(v, dict) and set(v.keys()) == {'none'}:
            return v
        if isinstance(v, dict) and set(v.keys()) == {'some'}:
            return {'some': walk_external(v['some'], spec[1], path + '.some', places)}
        return {'some': walk_external(v, spec[1], path + '.some', places)}
    if kind == 'list':
        if isinstance(v, list):
            return [walk_external(x, spec[1], '%s[%d]' % (path, i), places) for i, x in enumerate(v)]
        return v
    if kind == 'type':
        name = spec[1]
        if isinstance(v, dict) and ('$variant' in v or 'case' in v):
            cname = v.get('name') or v.get('case')
            if rec_tables.machine is not None and rec_tables.machine.is_enum(name):
                # ЭНУМ во внешнем кодеке — СТРОКА: слово из values (или имя случая), не объект
                return rec_tables.machine.enum_word(name, cname)
            cases = rec_tables.variants.get(name)
            cf = None
            if cases:
                for c in cases:
                    if c['name'] == cname:
                        cf = c.get('fields', [])
            if cf is None:
                places.append('%s: вариант %s.%s не в таблицах машины — значение не тронуто' % (path, name, cname))
                return v
            # внешняя форма варианта — РОВНО case+fields (decode_variant требует оба ключа),
            # поэтому fields остаётся даже пустым; подсеть обходится (вложенные enum-объекты и т.п.)
            walked = {}
            for k, x in (v.get('fields') or {}).items():
                fs = spec_of_field(cf, k)
                walked[k] = x if fs is None else walk_external(x, fs, '%s.%s' % (path, k), places)
            return {'case': cname, 'fields': walked}
        if isinstance(v, dict) and '$record' in v:
            fields = rec_tables.records.get(name)
            if fields is None:
                places.append('%s: запись %s не в таблицах машины — значение не тронуто' % (path, name))
                return v
            out = {}
            for k, x in v.get('fields', {}).items():
                fs = spec_of_field(fields, k)
                out[k] = x if fs is None else walk_external(x, fs, '%s.%s' % (path, k), places)
            return out
        if isinstance(v, dict):
            fields = rec_tables.records.get(name)
            if fields is None:
                return v
            out = {}
            for k, x in v.items():
                fs = spec_of_field(fields, k)
                out[k] = x if fs is None else walk_external(x, fs, '%s.%s' % (path, k), places)
            return out
        return v
    return v


# ---- перенос одной фикстуры ------------------------------------------------------------------------------

def migrate_fixture(path, doc, machines_dir, alula, cache):
    """Возвращает (новый текст или None, места). Машины берутся из cache (имя -> Machine)."""
    places = []
    mname = doc.get('machine') or ''
    try:
        root = load_machines(path, mname, machines_dir, alula, cache)
    except LookupError as e:
        return None, ['%s: машина: %s' % (path, e)]
    changed = [False]

    def data_block(block, machine, where):
        if not isinstance(block, dict):
            return
        for k, v in block.items():
            spec = machine.data.get(k)
            if spec is None:
                continue  # чужой ключ данных — не трогаем (журнал/движок)
            nv = with_machine_tables(machine, lambda: walk_internal(v, spec, '%s %s.%s' % (path, where, k), places))
            if nv != v:
                block[k] = nv
                changed[0] = True

    def outcome_block(text, machine):
        if not isinstance(text, str) or not text.startswith('answer:') or not machine.result:
            return text
        try:
            v = json.loads(text[len('answer:'):])
        except ValueError:
            places.append('%s: outcome не разобран как JSON — не тронуто' % path)
            return text
        spec = ('type', machine.result)
        nv = with_machine_tables(machine, lambda: walk_internal(v, spec, path + ' outcome', places))
        return 'answer:' + json.dumps(nv, ensure_ascii=False, separators=(',', ':')) if nv != v else text

    def machine_for_also_or_on(key):
        """Имя вложенной машины по ключу also/on («parent» — сама машина фикстуры)."""
        if key == 'parent':
            return root
        base = key.rsplit('-', 1)[0] if re.match(r'.*-\d+$', key) else key
        nested = root.nested_of_party(base)
        if nested:
            try:
                return load_machines(path, nested, machines_dir, alula, cache)
            except LookupError as e:
                places.append('%s: %s: %s' % (path, key, e))
        return None

    for i, step in enumerate(doc.get('steps', [])):
        at = '%s: шаг %d' % (path, i + 1)
        ev = step.get('event') or {}
        on = step.get('on') or ''
        # внешняя форма: ответ агентской стороне
        if ev.get('kind') == 'answer':
            target = machine_for_also_or_on(on) if on else root
            if target is not None:
                rid = ev.get('request') or ''
                pid = rid.rsplit('-', 1)[0] if re.match(r'.+-\d+$', rid) else ''
                # только ответ СТОРОНЕ agent идёт внешним кодеком; ответ машине-вложению —
                # внутренний провод (голое значение в optional читается как present, legacy), не трогаем
                spec = None
                party_kind = ''
                for holder in (target, root):
                    if holder is None:
                        continue
                    p = holder.party_by_id(pid)
                    if p is None and pid != '':
                        # элемент набора: запросы `<имя>-<элемент>-<попытка>` держит сторона набора (id "")
                        p = holder.party_by_id('')
                    if p is not None:
                        party_kind = p.get('kind') or ''
                        if party_kind == 'agent' and p.get('result'):
                            spec = ('type', p['result'])
                        break
                if spec is None and party_kind == '':
                    # запрос без стороны-префикса: единственная агентская сторона машины
                    for holder in (target, root):
                        if holder is None:
                            continue
                        agents = [q for q in holder.parties if q.get('kind') == 'agent']
                        if len(agents) == 1 and agents[0].get('result'):
                            spec = ('type', agents[0]['result'])
                            break
                if spec is not None and isinstance(ev.get('input'), (dict, str)):
                    v = ev['input']
                    nv = with_machine_tables(target, lambda: walk_external(v, spec, at + ' event.input', places))
                    if nv != v:
                        ev['input'] = nv
                        changed[0] = True
                elif spec is None and party_kind == '':
                    places.append('%s: ответ агенту: сторона по запросу %r не найдена — не тронуто' % (at, rid))
        # 0.28-сокращение сигнала с ОДНИМ полем: голое значение → объект по имени поля
        if ev.get('kind') == 'signal' and isinstance(ev.get('input'), (str, int, float, bool)):
            sig_fields = None
            for holder in (root,):
                if ev.get('name') in holder.signals:
                    sig_fields = holder.signals[ev.get('name')]
                    break
            if sig_fields is not None and on != '':
                target0 = machine_for_also_or_on(on)
                if target0 is not None and ev.get('name') in target0.signals:
                    sig_fields = target0.signals[ev.get('name')]
            if sig_fields is not None and len(sig_fields) == 1:
                ev['input'] = {sig_fields[0]['name']: ev['input']}
                changed[0] = True
        # внутренняя форма: expect.data / outcome
        exp = step.get('expect') or {}
        if isinstance(exp, dict):
            data_block(exp.get('data'), machine_for_also_or_on(on) if on else root, 'expect.data')
            if 'outcome' in exp and not on:
                nv = outcome_block(exp['outcome'], root)
                if nv != exp['outcome']:
                    exp['outcome'] = nv
                    changed[0] = True
        for key, also in (step.get('also') or {}).items():
            m = machine_for_also_or_on(key)
            if m is None:
                continue
            if isinstance(also, dict) and isinstance(also.get('data'), dict):
                data_block(also['data'], m, 'also.%s.data' % key)
    if not changed[0]:
        return None, places
    text = json.dumps(doc, ensure_ascii=False, indent=2) + '\n'
    return text, places


# ---- запуск (по образцу migrate-alula-229.py) --------------------------------------------------------------

def candidates(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for base, _dirs, files in os.walk(p):
                for f in files:
                    if f.endswith('.alula.test.json'):
                        out.append(os.path.join(base, f))
        else:
            out.append(p)
    return out


def selftest():
    tree = {
        'machine': 'm', 'data': [{'name': 'started', 'type': '?int'}, {'name': 'reply', 'type': '?text'}],
        'types': {'records': [{'name': 'Reply', 'fields': [{'name': 'text', 'type': '?text'}]}], 'variants': [
            {'name': 'TurnResult', 'cases': [
                {'name': 'Finished', 'fields': [{'name': 'text', 'type': '?text'}, {'name': 'artifact', 'type': '?text'}]},
                {'name': 'PermanentError', 'fields': []}]}]},
        'parties': [{'name': 'агент', 'id': 'agent', 'kind': 'agent', 'result': 'TurnResult'}],
        'ends': {'result': 'Reply'},
    }
    fixture = {'machine': 'm', 'steps': [
        {'do': 'feed', 'event': {'kind': 'answer', 'name': 'agent_done', 'request': 'agent-1',
                                 'input': {'$variant': 'TurnResult', 'name': 'Finished', 'fields': {'text': 'hello', 'artifact': None}}},
         'expect': {'data': {'started': 1000, 'reply': None},
                    'outcome': 'answer:{"$record":"Reply","fields":{"text":"hello"}}'}},
        {'do': 'feed', 'event': {'kind': 'answer', 'name': 'agent_done', 'request': 'agent-1',
                                 'input': {'case': 'PermanentError', 'fields': {}}}},
    ]}
    machine = Machine(tree)
    cache = {'m': machine}
    new, places = migrate_fixture('t.alula.test.json', fixture, None, None, cache)
    assert places == [], places
    s0 = fixture['steps'][0]
    assert s0['event']['input'] == {'case': 'Finished', 'fields': {'text': {'some': 'hello'}, 'artifact': {'none': True}}}, s0['event']['input']
    assert s0['expect']['data']['started'] == {'$some': 1000}
    assert s0['expect']['data']['reply'] is None
    assert s0['expect']['outcome'] == 'answer:{"$record":"Reply","fields":{"text":{"$some":"hello"}}}', s0['expect']['outcome']
    # уже перенесённый ответ и уже различимое данное не меняются (идемпотентность)
    new2, places2 = migrate_fixture('t.alula.test.json', fixture, None, None, cache)
    assert new2 is None and places2 == [], (new2, places2)
    print('selftest: ок (внешняя форма ответа, {"$some"} данных, идемпотентность)')
    return 0


def main(argv):
    dry = False
    alula = 'target/alula.exe'
    machines_dir = None
    paths = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--dry-run':
            dry = True
        elif a == '--selftest':
            return selftest()
        elif a == '--alula':
            i += 1
            alula = argv[i] if i < len(argv) else ''
        elif a == '--machines':
            i += 1
            machines_dir = argv[i] if i < len(argv) else ''
        elif a.startswith('--'):
            sys.stderr.write('неизвестный ключ %s\n' % a)
            return 2
        else:
            paths.append(a)
        i += 1
    if not paths:
        sys.stderr.write('запуск: python tools/migrate-test-fixtures-229.py [--dry-run] [--alula <программа alula>] [--machines <папка>] <фикстура или папка>...\n'
                         '        python tools/migrate-test-fixtures-229.py --selftest — регрессионный тест\n')
        return 2
    for p in paths:
        if not os.path.exists(p):
            sys.stderr.write('нет пути: %s\n' % p)
            return 2
    if alula and not os.path.exists(alula):
        sys.stderr.write('нет программы alula: %s\n' % alula)
        return 2
    cache = {}
    changed = []
    places = []
    for path in candidates(paths):
        try:
            with open(path, encoding='utf-8', newline='') as f:
                doc = json.load(f)
        except (ValueError, OSError) as e:
            sys.stderr.write('%s: не прочитан как JSON: %s\n' % (path, e))
            return 2
        try:
            new, pl = migrate_fixture(path, doc, machines_dir, alula, cache)
        except Exception as e:  # путь фикстуры в сообщении — стектрейс без имени не называет её
            sys.stderr.write('%s: неожиданная ошибка: %s: %s (значение не тронуто)\n' % (path, type(e).__name__, e))
            return 2
        places += pl
        if new is not None:
            changed.append(path)
            if not dry:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(new)
    verb = 'изменился бы' if dry else 'перенесён'
    for p in changed:
        print('%s: %s' % (verb, p))
    for p in places:
        print(p)
    print('итог: фикстур %d, мест %d' % (len(changed), len(places)))
    return 1 if places else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
