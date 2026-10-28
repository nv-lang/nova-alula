#!/usr/bin/env python3
"""Перенос файлов Алулы с 2.26 на 2.27 (задача 244, пакет alula 2.27.0; AL-144…AL-147).

Зачем: 2.27 — ломающая версия без переходного периода (журнал изменений): файл с `- format: 2.26` пакет 2.27.0 не читает
(подсказка «с 2.27 — revision и alula_version»), а правка шапок, разделов «Требует», сторон `machine` и ключей JSON руками —
ошибки и потерянное время. Скрипт делает механическую часть и называет места, которые механически не решаются.

Что переносит:
  - шапка файла машины и библиотеки (AL-144): `- machine_version: <целое>` — `- revision: <целое>`, любое другое значение
    (`alula-2.26`, `pilot-2.5`) — `- revision: 1`; `- format: 2.26` — `- alula_version: 2.27`;
  - библиотека (AL-145): единый `## Требует` (`имя | тип`) — три раздела: `## Требует данные` (`имя | тип`), `## Требует стороны`
    (`имя | вид | сигналы`: строка «сторона <вид> с сигналами A и B» — вид и сигналы через запятую), `## Требует концы` (`имя`: строки
    с типом «конец»); пустой раздел не пишется;
  - сторона `machine имя(вход Тип, итог Тип)` (AL-146) — `machine имя` (разбор `; разбор: f -> Т` остаётся); копия типа итога, которую
    объявляет и вызываемая машина рядом (то же имя), и тип входа, который файл больше нигде не называет, убираются из `## Типы`
    вызывающей (объявление в одну строку);
  - дерево `*.alula.json` (AL-147): `"format": "machine/2"` — `"kind": "machine"`, `"version"` — `"revision"` (целое, иначе 1),
    `alula_version` — `2.27`; рядом файл машины и задан `--alula` — дерево пересобирается `alula compile`;
  - тест `*.alula.test.json`: `"format": "test/0"` — `"kind": "test"`;
  - подключение библиотеки: `- Хеш:` — хеш файла библиотеки рядом (файлы библиотек 2.27 другие).
Что НЕ решает сам (выход 1, строка на место `файл:строка: вид: что сделать`): копия типа итога, объявленная в несколько строк, или итог,
вызываемой которого рядом нет; дерево с файлом машины рядом без `--alula`. Тип входа, который файл называет ещё где-то, остаётся его
собственным типом.
Запуск: `python tools/migrate-alula-227.py [--dry-run] [--alula <программа alula>] <файл или папка>…` (папки — рекурсивно); код 0 —
перенесено (или нечего), 1 — остались места, 2 — ошибка запуска. `--dry-run` ничего не пишет. Повторный запуск ничего не меняет.
"""
import json, os, re, subprocess, sys

W = {
    'ru': {'requires': 'Требует', 'data': 'Требует данные', 'parties': 'Требует стороны', 'ends': 'Требует концы', 'name': 'имя',
           'type': 'тип', 'kind': 'вид', 'signals': 'сигналы', 'end': 'конец', 'party': 'сторона', 'with': ' с сигналами ', 'and': ' и ',
           'types': 'Типы', 'type_kw': 'тип', 'input': 'вход', 'result': 'итог'},
    'en': {'requires': 'Requires', 'data': 'Requires data', 'parties': 'Requires parties', 'ends': 'Requires ends', 'name': 'name',
           'type': 'type', 'kind': 'kind', 'signals': 'signals', 'end': 'end', 'party': 'party', 'with': ' with the signals ', 'and': ' and ',
           'types': 'Types', 'type_kw': 'type', 'input': 'input', 'result': 'result'},
}


class Run:
    def __init__(self, dry):
        self.dry = dry
        self.changed = []
        self.places = []
        self.recompile = []

    def place(self, path, line, kind, todo):
        one = '%s:%d: %s: %s' % (path, line, kind, todo)
        if one not in self.places:
            self.places.append(one)


def file_lang(lines):
    for l in lines:
        if l.startswith('## '):
            break
        m = re.match(r'^(?:-\s+)?language:\s*(\S+)\s*$', l)
        if m:
            return m.group(1)
    return 'ru'


def split_top(s, seps):
    """Части строки между разделителями `seps` вне фигурных скобок."""
    out, depth, cur, i = [], 0, '', 0
    while i < len(s):
        c = s[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        hit = None
        if depth == 0:
            for sep in seps:
                if s.startswith(sep, i):
                    hit = sep
                    break
        if hit:
            out.append(cur)
            cur = ''
            i += len(hit)
            continue
        cur += c
        i += 1
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def row_cells(line):
    t = line.strip()
    if not t.startswith('|'):
        return None
    t = t[1:-1] if t.endswith('|') else t[1:]
    cells, cur, i = [], '', 0
    while i < len(t):
        if t[i] == '\\' and i + 1 < len(t) and t[i + 1] == '|':
            cur += '\\|'
            i += 2
            continue
        if t[i] == '|':
            cells.append(cur.strip())
            cur = ''
        else:
            cur += t[i]
        i += 1
    cells.append(cur.strip())
    return cells


def header(lines, run, path):
    """Шапка: строки до первого `## `. Возвращает число изменённых строк."""
    n = 0
    for i, l in enumerate(lines):
        if l.startswith('## '):
            break
        m = re.match(r'^(-\s+)?machine_version:\s*(.*?)\s*$', l)
        if m:
            v = m.group(2)
            lines[i] = '- revision: %s' % (v if re.fullmatch(r'[0-9]+', v) else '1')
            n += 1
            continue
        m = re.match(r'^(-\s+)?format:\s*(2\.2[67])\s*$', l)
        if m:
            lines[i] = '- alula_version: 2.27'
            n += 1
    return n


def requires(lines, w, run, path):
    """Единый `## Требует` библиотеки — три раздела."""
    head = '## ' + w['requires']
    for i, l in enumerate(lines):
        if l.rstrip() != head:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].startswith('## '):
            j += 1
        data, parties, ends = [], [], []
        for k in range(i + 1, j):
            cells = row_cells(lines[k])
            if not cells or len(cells) < 2 or set(cells[0]) <= set('-: ') or cells[0] == w['name']:
                continue
            name, ty = cells[0], cells[1]
            if ty == w['end']:
                ends.append(name)
            elif ty.startswith(w['party'] + ' '):
                rest = ty[len(w['party']) + 1:]
                if w['with'] in rest:
                    kind, sig = rest.split(w['with'], 1)
                    signals = ', '.join(split_top(sig, [w['and'], ',']))
                else:
                    kind, signals = rest, '—'
                parties.append((name, kind.strip(), signals))
            else:
                data.append((name, ty))
        out = []
        if data:
            out += ['## ' + w['data'], '', '| %s | %s |' % (w['name'], w['type']), '|---|---|'] + ['| %s | %s |' % d for d in data] + ['']
        if parties:
            out += ['## ' + w['parties'], '', '| %s | %s | %s |' % (w['name'], w['kind'], w['signals']), '|---|---|---|'] + ['| %s | %s | %s |' % p for p in parties] + ['']
        if ends:
            out += ['## ' + w['ends'], '', '| %s |' % w['name'], '|---|'] + ['| %s |' % e for e in ends] + ['']
        lines[i:j] = out
        return 1
    return 0


HERE = os.path.dirname(os.path.abspath(__file__))


def host_machines():
    """Имена машин реестра хозяина (`src/machine_text/names_host.tsv` пакета): русское имя -> латинское."""
    out = {}
    try:
        for l in open(os.path.join(HERE, '..', 'src', 'machine_text', 'names_host.tsv'), encoding='utf-8'):
            cells = l.rstrip('\n').split('\t')
            if len(cells) >= 3 and cells[0] == 'machine':
                out[cells[1]] = cells[2]
    except OSError:
        pass
    return out


def callee_types_of(path, name):
    """Типы, которые объявляет машина `name` рядом с файлом (по строке шапки `machine:`; имя реестра хозяина — по его латинскому имени)."""
    name = host_machines().get(name, name)
    d = os.path.dirname(path) or '.'
    for f in sorted(os.listdir(d)):
        if not f.endswith('.alula.md'):
            continue
        try:
            text = open(os.path.join(d, f), encoding='utf-8').read()
        except (OSError, UnicodeDecodeError):
            continue
        if re.search(r'^(-\s+)?machine:\s*%s\s*$' % re.escape(name), text, re.M):
            return set(re.findall(r'^\s*(?:тип|type)\s+(\S+)', text, re.M))
    return None


def machine_parties(lines, w, run, path):
    """Сторона `machine имя(вход Т, итог Т)` — `machine имя`; копии типов убираются из `## Типы`."""
    n = 0
    drop = []
    pat = re.compile(r'machine (\S+?)\(%s (\S+?), %s (\S+?)\)' % (w['input'], w['result']))
    for i, l in enumerate(lines):
        # a party is a row of the table `## Стороны`; the prose that quotes the old form stays
        m = pat.search(l) if l.lstrip().startswith('|') else None
        while m:
            name, tin, tout = m.group(1), m.group(2), m.group(3)
            l = l[:m.start()] + 'machine ' + name + l[m.end():]
            drop.append((name, tin, tout, i))
            m = pat.search(l)
        if lines[i] != l:
            lines[i] = l
            n += 1
    if not drop:
        return n
    body = '\n'.join(lines)
    for name, tin, tout, at in drop:
        callee = callee_types_of(path, name)
        for ty, why in [(tin, 'input'), (tout, 'result')]:
            decl = [k for k, x in enumerate(lines) if re.match(r'^\s*%s\s+%s(\s|\{|$)' % (w['type_kw'], re.escape(ty)), x)]
            if not decl:
                continue
            k = decl[0]
            # the uses in the code of the file (the rows of the tables and the blocks of code), not in the prose
            code, fence = [], False
            for x in lines:
                if x.startswith('```'):
                    fence = not fence
                    continue
                if fence or x.lstrip().startswith('|'):
                    code.append(x)
            uses = len(re.findall(r'(?<![\w])%s(?![\w])' % re.escape(ty), '\n'.join(code)))
            one_line = '{' in lines[k] and '}' in lines[k] or ' enum ' in lines[k] or ' перечисление ' in lines[k]
            if why == 'result' and (callee is None or ty not in callee):
                run.place(path, k + 1, 'тип итога', 'тип `%s` — итог вызываемой `%s`; её файла с этим типом рядом нет: копию убрать руками, когда вызываемая лежит рядом' % (ty, name))
                continue
            if why == 'input' and uses > 1:
                # the file needs the type elsewhere (a datum, a constructor): it is its own type now
                continue
            if not one_line:
                run.place(path, k + 1, 'копия типа', 'тип `%s` объявлен в несколько строк: копию убрать руками (с 2.27 типы берутся от вызываемой)' % ty)
                continue
            del lines[k]
            n += 1
    return n


def lib_hash(text):
    """Хеш библиотеки (раздел 9): по правилу скрипта 2.26 (`lib_hash` в `tools/migrate-alula-226.py`)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('m226', os.path.join(HERE, 'migrate-alula-226.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.lib_hash(text)


def hashes(lines, path, run):
    """`- Хеш:` подключения — хеш файла библиотеки рядом с машиной (файлы библиотек 2.27 другие: шапка `alula_version`, разделы требований)."""
    n = 0
    for i, l in enumerate(lines):
        mf = re.match(r'^- (?:Файл|File): (\S+)\s*$', l)
        if not mf or i + 1 >= len(lines):
            continue
        mh = re.match(r'^- (Хеш|Hash): ([0-9a-f]{12})\s*$', lines[i + 1])
        lib = os.path.join(os.path.dirname(path) or '.', mf.group(1))
        if not mh or not os.path.exists(lib):
            continue
        h = lib_hash(open(lib, encoding='utf-8').read())
        if h != mh.group(2):
            lines[i + 1] = '- %s: %s' % (mh.group(1), h)
            n += 1
    return n


def migrate_md(path, text, run):
    lines = text.replace('\r\n', '\n').split('\n')
    w = W.get(file_lang(lines), W['ru'])
    n = header(lines, run, path) + requires(lines, w, run, path) + machine_parties(lines, w, run, path) + hashes(lines, path, run)
    if not n:
        return None
    return '\n'.join(lines)


def migrate_tree(path, text, run):
    try:
        tree = json.loads(text)
    except ValueError:
        return None
    if not isinstance(tree, dict) or ('format' not in tree and 'version' not in tree):
        return None
    out = {}
    for k, v in tree.items():
        if k == 'format':
            out['kind'] = 'machine'
        elif k == 'version':
            out['revision'] = int(v) if isinstance(v, str) and re.fullmatch(r'[0-9]+', v) else (v if isinstance(v, int) else 1)
        elif k == 'alula_version':
            out[k] = '2.27'
        else:
            out[k] = v
    if 'kind' not in out:
        out = dict([('kind', 'machine')] + list(out.items()))
    return json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ('\n' if text.endswith('\n') else '')


def migrate_test(path, text, run):
    if not re.search(r'"format"\s*:\s*"test/0"', text):
        return None
    return re.sub(r'"format"(\s*):(\s*)"test/0"', r'"kind"\1:\2"test"', text, count=1)


def candidates(paths):
    for p in paths:
        if os.path.isdir(p):
            for d, dirs, files in os.walk(p):
                dirs[:] = sorted(x for x in dirs if x not in ('.git', 'target', 'node_modules'))
                for f in sorted(files):
                    if f.endswith('.md') or f.endswith('.alula.json') or f.endswith('.alula.test.json'):
                        yield os.path.join(d, f)
        else:
            yield p


def write(path, old, new, run):
    if new is None or new == old:
        return False
    if '\r\n' in old and '\r\n' not in new:
        new = new.replace('\n', '\r\n')
    run.changed.append(path)
    if not run.dry:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(new)
    return True


def main(argv):
    paths, dry, alula = [], False, os.environ.get('ALULA') or None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--dry-run':
            dry = True
        elif a == '--alula':
            if i + 1 >= len(argv):
                sys.stderr.write('--alula: нужен путь к программе alula\n')
                return 2
            alula = argv[i + 1]
            i += 1
        elif a.startswith('--'):
            sys.stderr.write('неизвестный ключ %s\n' % a)
            return 2
        else:
            paths.append(a)
        i += 1
    if not paths:
        sys.stderr.write('запуск: python tools/migrate-alula-227.py [--dry-run] [--alula <программа alula>] <файл или папка>...\n')
        return 2
    for p in paths:
        if not os.path.exists(p):
            sys.stderr.write('нет пути: %s\n' % p)
            return 2
    if alula and not os.path.exists(alula):
        sys.stderr.write('нет программы alula: %s\n' % alula)
        return 2
    run = Run(dry)
    trees = []
    # the libraries first: a connection takes the hash of the moved file of its library
    def library_first(path):
        try:
            head = open(path, encoding='utf-8').read(400)
        except (UnicodeDecodeError, OSError):
            return 1
        return 0 if re.match(r'^\s*# (Библиотека|Library):', head) else 1
    ordered = sorted(candidates(paths), key=library_first)
    for path in ordered:
        try:
            with open(path, encoding='utf-8', newline='') as f:
                text = f.read()
        except (UnicodeDecodeError, OSError) as e:
            sys.stderr.write('%s: не прочитан как UTF-8: %s\n' % (path, e))
            return 2
        if path.endswith('.alula.test.json'):
            write(path, text, migrate_test(path, text, run), run)
        elif path.endswith('.alula.json'):
            trees.append((path, text))
        elif re.search(r'^# ', text[:2000], re.M):
            write(path, text, migrate_md(path, text, run), run)
    for path, text in trees:
        md = path[:-len('.alula.json')] + '.alula.md'
        new = migrate_tree(path, text, run)
        # a tree whose machine file this run moved is built again from it
        if new is None and md not in run.changed:
            continue
        if new is None:
            new = text
        if os.path.exists(md) and alula:
            if dry:
                run.changed.append(path)
                continue
            done = subprocess.run([os.path.abspath(alula), 'compile', md, '-o', path, '--force'], capture_output=True, text=True, encoding='utf-8')
            if done.returncode != 0:
                first = [l for l in (done.stderr or done.stdout).splitlines() if l.strip()][:1]
                run.place(path, 1, 'дерево', 'alula compile не собрал дерево из %s: %s' % (os.path.basename(md), first[0] if first else 'код %d' % done.returncode))
                # the tree stays moved by its keys: the engine reads it until the file is built
                write(path, text, new, run)
            else:
                run.changed.append(path)
        else:
            write(path, text, new, run)
            if os.path.exists(md):
                run.place(path, 1, 'дерево', 'рядом файл машины %s: пересоберите дерево `alula compile` (или запустите скрипт с --alula <программа>)' % os.path.basename(md))
    verb = 'изменился бы' if dry else 'перенесён'
    for p in run.changed:
        print('%s: %s' % (verb, p))
    for p in run.places:
        print(p)
    print('итог: файлов %d, мест %d' % (len(run.changed), len(run.places)))
    return 1 if run.places else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
