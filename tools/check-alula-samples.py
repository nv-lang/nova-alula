#!/usr/bin/env python3
"""Сверка двух образцов машины «Шаг агента» на Алуле: русского и английского.

Зачем: образцы `state-machine-agent-step.alula.md` (русский) и `state-machine-agent-step.en.alula.md` (английский) — одна машина
в двух языках файла (спецификация, раздел 1а: дерево JSON `machine/2` одинаково при любом языке); расхождение поведения между ними
молчит до первой реализации разбора.
Что проверяет (структура, не смысл выражений):
  1. разделы `##` идут в одном порядке (раздел `## Имена` не сравнивается: он есть только там, где автоматическое имя неверно, AL-60),
     заголовки соответствуют по таблице слов `alula-keywords.tsv`; в каждой таблице раздела одинаковое
     число строк (типы — число объявлений и строк в блоке кода; функции — число и порядок объявлений `функция`/`fn`);
  2. состояния: одинаковые виды и порядок; JSON-имя состояния совпадает (строка `## Имена` или автоматическое имя, 1а); число строк переходов у каждого состояния,
     метки `№`, значения «куда» (русские имена состояний переведены в латинские по заголовкам, слова «куда» — по таблице слов),
     число действий (разделитель `;`) и коды журнала `журнал(код, …)`/`journal(code, …)` в каждой строке;
  3. строки «Концов»: число, конец (имя переведено), метка `№`, число конструкторов `Отказ(…)`/`Refusal(…)` и `Ответ(…)`/`Response(…)`
     в ответе (имена кодов отказа в двух языках разные — по глоссарию — и не сверяются);
  4. набор кодов журнала файла целиком (`журнал(код, …)`, кроме вызовов с выражением) одинаков;
  5. JSON-имена объявленных имён, которые выходят из машины (состояния, поля входа, данные, примитивы, имя настройки вратаря,
     сигналы сторон и их поля, типы, элементы перечислений, варианты, поля): у русского образца — строка `## Имена` или
     автоматическое (спецификация, 1а, AL-53, AL-60: словарь, затем транслитерация; функция `json_names` из `check-alula-keywords.py`),
     у английского — само имя; списки по порядку объявления равны (дерево `machine/2` одно).
Самопроверка (`--selftest`): порча английского образца (другое «куда», удалённая строка, другой код журнала, лишнее действие,
лишнее состояние, лишняя функция, лишняя строка концов, другая метка строки, другое имя поля) и русского (снятая строка
`## Имена` у поля и у настройки вратаря, строка с другим JSON-именем у состояния) даёт расхождение, неискажённая пара — нет.
Чего не проверяет: тела выражений и имена внутри выражений (структурные слова и таблицу `## Имена` проверяет `check-alula-keywords.py`); строки фрагмента «Пауза»
(образцы его не раскрывают, раздел 9 спецификации); значения-строки (тексты отказов, сообщения, текстовые литералы) — автор пишет их
на своём языке, и дерево JSON одинаково, если они совпадают (спецификация, 1а); поэтому перевод текста отказа и прозы допустим.
Запуск: из корня репозитория `python state-machines/check-alula-samples.py` (`--selftest` — с самопроверкой); код возврата 1 при расхождениях.
"""
import importlib.util, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('check_alula_keywords', os.path.join(HERE, 'check-alula-keywords.py'))
KW = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(KW)
RU = 'state-machine-agent-step.alula.md'
EN = 'state-machine-agent-step.en.alula.md'
TABLE = 'alula-keywords.tsv'
# состояние, которое приносит фрагмент «Пауза» (в разделе «Состояния» не объявлено)
FRAGMENT_STATE = ('ПАУЗА', 'Pause')
NOT_CODES = {'usage_event', 'transition_note', 'all_data'}  # журнал(выражение), а не код события


def read(name):
    return io.open(os.path.join(HERE, name), encoding='utf-8', newline='').read().replace('\r\n', '\n')


def load_words():
    """kind -> {ru: en}."""
    out = {}
    for line in read(TABLE).split('\n')[1:]:
        c = line.split('\t')
        if len(c) == 3:
            out.setdefault(c[0], {})[c[1]] = c[2]
    return out


def cells(line):
    return [c.strip() for c in re.split(r'(?<!\\)\|', line.strip())[1:-1]]


def split_sections(text):
    """Список (заголовок раздела, [строки]) по заголовкам `## `; блоки кода остаются в строках."""
    secs = []
    cur = None
    in_code = False
    for line in text.split('\n'):
        if line.startswith('```'):
            in_code = not in_code
        if not in_code and line.startswith('## '):
            cur = (line[3:].strip(), [])
            secs.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return secs


def tables(lines):
    """Таблицы раздела: список (заголовок, строки-ячейки), вне блоков кода."""
    out = []
    in_code = False
    cur = None
    for line in lines:
        if line.startswith('```'):
            in_code = not in_code
            cur = None
            continue
        if in_code:
            continue
        if line.startswith('|'):
            c = cells(line)
            if re.match(r'^[-:| ]+$', line.strip()):
                continue
            if cur is None:
                cur = (c, [])
                out.append(cur)
            else:
                cur[1].append(c)
        else:
            cur = None
    return out


def code_blocks(lines):
    out, cur, in_code = [], None, False
    for line in lines:
        if line.startswith('```'):
            if in_code:
                out.append(cur)
            cur = []
            in_code = not in_code
            continue
        if in_code:
            cur.append(line)
    return out


def states_in(lines, gloss, smap):
    """Состояния раздела: список (имя, вид, JSON-имя, [строки тела]); JSON-имя — из `## Имена` (`smap`) или автоматическое (1а, AL-60)."""
    out = []
    for line in lines:
        m = re.match(r'^### (\S+) — (\S+)(?:\s|$)', line)
        if m:
            out.append((m.group(1), m.group(2), smap.get(m.group(1)) or KW.auto_name(m.group(1), True, gloss), []))
        elif out:
            out[-1][3].append(line)
    return out


def journal_codes(s):
    return [c for c in re.findall(r'(?:журнал|journal)\(([a-z_]+)', s) if c not in NOT_CODES]


def summarize(text, lang, words, gloss):
    """Сводка образца: словарь признаков, одинаковый по смыслу для обоих языков."""
    dest = words['destination']
    ru_dest = dest if lang == 'ru' else {v: v for v in dest.values()}
    kinds = words['kind_state'] if lang == 'ru' else {v: v for v in words['kind_state'].values()}
    secs = split_sections(text)
    readable = set(words['readable'].keys()) if lang == 'ru' else set(words['readable'].values())
    names = KW.json_names(text, lang, gloss, readable)[0]
    smap = {nm: js for _, where, _, nm, _, js in names if where == 'состояния'}
    S = {}
    S['sections'] = []
    rename = {}  # имя состояния файла -> латинское
    for title, lines in secs:
        for n, k, lat, _ in states_in(lines, gloss, smap):
            rename[n] = lat
    rename[FRAGMENT_STATE[0]] = FRAGMENT_STATE[1]
    rename[FRAGMENT_STATE[1]] = FRAGMENT_STATE[1]

    def norm_to(v):
        v = v.strip()
        if v in rename:
            return rename[v]
        if lang == 'ru' and v in dest:
            return dest[v]
        return v

    def sec_key(title):
        if lang == 'ru':
            t = title.split('«')[0].strip()
            return words['section'].get(t, t)
        return title.split('"')[0].strip()

    secs = [s for s in secs if sec_key(s[0]) != 'Names']  # `## Имена` есть только у русского образца (AL-60)

    for title, lines in secs:
        key = sec_key(title)
        info = {'key': key, 'tables': [len(t[1]) for t in tables(lines)], 'code': [len(b) for b in code_blocks(lines)]}
        S['sections'].append(info)
        if key == 'Functions':
            info['defs'] = [m for b in code_blocks(lines) for m in re.findall(r'^(?:функция|fn) ', '\n'.join(b), re.M)]
            info['defs'] = len(info['defs'])
        if key == 'Types':
            blk = '\n'.join('\n'.join(b) for b in code_blocks(lines))
            info['decls'] = [m for m in re.findall(r'^(перечисление|тип|вариант|enum|type|variant) ', blk, re.M)]
            info['decls'] = [{'перечисление': 'enum', 'тип': 'type', 'вариант': 'variant'}.get(d, d) for d in info['decls']]
        if key == 'States':
            st = []
            for n, k, lat, body in states_in(lines, gloss, smap):
                rows = []
                for hdr, trs in tables(body):
                    if hdr and hdr[0] == '№':
                        for r in trs:
                            acts = r[-2]
                            rows.append((r[0], norm_to(r[-1]), len([a for a in acts.split(';') if a.strip() and a.strip() != '—']),
                                         tuple(journal_codes(acts)), 'machine_error' in acts or 'ошибка_машины' in acts))
                st.append((lat, kinds.get(k, k), rows))
            info['states'] = st
        if key == 'Ends':
            rows = []
            for hdr, trs in tables(lines):
                for r in trs:
                    resp = r[-1]
                    rows.append((rename.get(r[0], r[0]), r[1], len(re.findall(r'\b(?:Отказ|Refusal)\(', resp)),
                                 len(re.findall(r'\b(?:Ответ|Response)\(', resp))))
            info['ends'] = rows
    S['codes'] = sorted(journal_codes(text))
    S['names'] = [(where, js) for _, where, _, _, _, js in names]
    return S


def compare(ru, en):
    errs = []
    if len(ru['sections']) != len(en['sections']):
        errs.append('число разделов: ru %d, en %d' % (len(ru['sections']), len(en['sections'])))
    for a, b in zip(ru['sections'], en['sections']):
        k = a['key']
        if a['key'] != b['key']:
            errs.append('раздел: ru `%s`, en `%s`' % (a['key'], b['key']))
            continue
        for f in ('tables', 'code', 'defs', 'decls', 'ends'):
            if a.get(f) != b.get(f):
                if f in ('ends', 'tables'):
                    errs.append('раздел `%s`, %s: ru %s, en %s' % (k, f, _short(a.get(f)), _short(b.get(f))))
                else:
                    errs.append('раздел `%s`, %s: ru %s, en %s' % (k, f, a.get(f), b.get(f)))
        if 'states' in a:
            sa, sb = a['states'], b['states']
            if [x[:2] for x in sa] != [x[:2] for x in sb]:
                errs.append('состояния (имя, вид): ru %s, en %s' % ([x[:2] for x in sa], [x[:2] for x in sb]))
            for x, y in zip(sa, sb):
                if x[0] != y[0]:
                    continue
                if len(x[2]) != len(y[2]):
                    errs.append('состояние %s: строк переходов ru %d, en %d' % (x[0], len(x[2]), len(y[2])))
                    continue
                for r1, r2 in zip(x[2], y[2]):
                    if r1 != r2:
                        errs.append('состояние %s, строка № %s: ru %s, en %s' % (x[0], r1[0], r1[1:], r2[1:]))
            na = sum(len(x[2]) for x in sa)
            nb = sum(len(x[2]) for x in sb)
            if na != nb:
                errs.append('всего строк переходов: ru %d, en %d' % (na, nb))
    if ru['names'] != en['names']:
        diff = [(a, b) for a, b in zip(ru['names'], en['names']) if a != b]
        errs.append('JSON-имена объявлений: ru %d, en %d; первое расхождение: %s' % (
            len(ru['names']), len(en['names']), diff[0] if diff else 'в длине списка'))
    if ru['codes'] != en['codes']:
        only_ru = [c for c in ru['codes'] if c not in en['codes']]
        only_en = [c for c in en['codes'] if c not in ru['codes']]
        errs.append('коды журнала расходятся: только в ru %s, только в en %s (всего ru %d, en %d)' % (
            sorted(set(only_ru)), sorted(set(only_en)), len(ru['codes']), len(en['codes'])))
    return errs


def _short(v):
    s = str(v)
    return s if len(s) < 200 else s[:200] + '…'


def mutations(en_text):
    def sub(a, b):
        assert a in en_text, a
        return en_text.replace(a, b, 1)
    muts = [
        ('другое «куда»', sub('stop_reason = "no_result"; journal(agent_permanent_error) | Accounting |',
                              'stop_reason = "no_result"; journal(agent_permanent_error) | Halted |')),
        ('удалённая строка перехода', en_text.replace(
            [l for l in en_text.split('\n') if l.startswith('| 6 | response: TransientError')][0] + '\n', '', 1)),
        ('другой код журнала', sub('journal(model_refused)', 'journal(model_refusedd)')),
        ('лишнее действие', sub('turn_count += 1 | AgentTurn', 'turn_count += 1; turn_count += 1 | AgentTurn')),
        ('лишнее состояние', sub('### End — end', '### Extra — end\n- Reads: usage\n\n### End — end')),
        ('лишняя функция', sub('fn interactive(', 'fn extra(x int) -> int => x\n\nfn interactive(')),
        ('лишняя строка концов', sub('| Halted | 11 |', '| Halted | 12 | stop_reason == "x" | Refusal(FailCode.Cancelled, stop_reason) |\n| Halted | 11 |')),
        ('другая метка строки', sub('| 9 | failure(', '| 10 | failure(')),
        ('другое имя поля', sub('cache_write ?int', 'cache_writes ?int')),
    ]
    return muts


def ru_mutations(ru_text):
    def sub(a, b):
        assert a in ru_text, a
        return ru_text.replace(a, b, 1)
    return [
        ('снятая строка `## Имена` у данного и полей', sub('| расход | transport_usage |\n', '')),
        ('снятая строка `## Имена` у настройки вратаря', sub('| исполнитель_повышенного_внимания | elevated_attention_executor |\n', '')),
        ('строка `## Имена` с другим JSON-именем у состояния', sub('| расход | transport_usage |\n', '| расход | transport_usage |\n| ПОВТОР | Retrying |\n')),
    ]


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    words = load_words()
    ru_text, en_text = read(RU), read(EN)
    gloss = KW.load_glossary(KW.read(KW.GLOSSARY))[0]
    ru = summarize(ru_text, 'ru', words, gloss)
    en = summarize(en_text, 'en', words, gloss)
    errs = compare(ru, en)
    if '--selftest' in sys.argv:
        if errs:
            errs.append('самопроверка: исправная пара уже расходится')
        else:
            for what, mut in mutations(en_text):
                if not compare(ru, summarize(mut, 'en', words, gloss)):
                    errs.append('самопроверка: порча не замечена (%s)' % what)
            for what, mut in ru_mutations(ru_text):
                if not compare(summarize(mut, 'ru', words, gloss), en):
                    errs.append('самопроверка: порча не замечена (%s)' % what)
    for e in errs:
        print(e)
    st = [s for s in ru['sections'] if 'states' in s][0]['states']
    ends = [s for s in ru['sections'] if 'ends' in s][0]['ends']
    defs = [s for s in ru['sections'] if 'defs' in s][0]['defs']
    print('образцы: состояний %d, строк переходов %d, строк концов %d, функций %d, кодов журнала %d, JSON-имён %d; расхождений: %d' % (
        len(st), sum(len(x[2]) for x in st), len(ends), defs, len(ru['codes']), len(ru['names']), len(errs)))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
