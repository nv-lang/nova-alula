#!/usr/bin/env python3
"""Перенос файлов Алулы с формата 2.25 на 2.26 (задача 239, поток 4 выпуска 2.26; AL-137…AL-143).

Зачем: 2.26 — ломающая версия без переходного периода (журнал изменений, раздел 0): файл `- format: 2.25` пакет `alula` 0.9.0
не читает как 2.26, а руками переносить сотни строк таблиц — ошибки и потерянное время. Скрипт делает механическую часть и
называет места, которые механически не решаются.

Что переносит (файлы `*.alula.md`, в том числе образцы с другим именем, если в шапке `- format: 2.25`):
  - шапка: `- format: 2.26`; строки шапки без маркера получают `- `; `# Функции:`/`# Functions:` с `functions_version` — библиотека
    (`# Библиотека:`, `- library: <латинское имя>`);
  - строки-ключи состояния и «Выхода» без маркера получают `- ` (AL-137); строка `- Читает:` убирается (AL-138);
  - таблицы строк: столбец `№` убран (переходы, развилки, общие события, `## Выход`); у операции событие `сразу` и условие убраны —
    таблица `Действия | Куда`; `—` в ячейках условия, действий и «Куда» — пустая ячейка; событие `deadline` английского файла — `timeout`;
  - «Запрос»: столбец `читает` убран, строки, которые читал только движок (`исполнитель`), убраны (стороне они не уходили; чтения
    2.26 выводит проверка), без строк — нет и строки `- Запрос:`; выражение `—` и выражение, равное имени поля, — пустая ячейка;
  - `## Данные`: столбец `пишет` убран; строки счётчиков сторон (столбец `счётчик`) и данных движка `запрос_вызова`,
    `открытые_запросы` убраны (их заводят загрузчик и библиотека `контракт`, AL-139, AL-141); данное «пишет механика», которое
    файл больше нигде не называет (счётчик стороны без счётчика), убрано вместе со строкой `## Имена`; другое данное механики
    (`возврат_подготовки`, правило 24) остаётся строкой данных — кто его пишет, 2.26 не записывает;
  - `## Концы` — `## Выход`; `## Обязывает` — `## Требует`; пустой раздел (`—`) не пишется;
  - `## Внешние функции`: слова `внешняя функция`/`external fn` перед объявлением убраны (AL-142);
  - `## Подключения`: `функции: <имя> версия N хеш H` и `Пауза(…)` — подзаголовок `### Имя` с `- Файл:`, `- Хеш:` и таблицей
    значений параметров (AL-140); файл библиотеки берётся из папки `libs/` пакета и кладётся рядом с машиной в `libs/`, если его
    там нет (русский — `libs/pause.alula.md`, английский — `libs/pause.en.alula.md`); хеш — по файлу рядом с машиной;
    параметр-примечание `право_записи` становится комментарием `//`;
  - тип `КодСбоя`/`FailCode`, объявленный машиной с кодами контракта, убран (тип даёт библиотека `контракт`, AL-141);
  - `## Части ответа` (слой продукта 2.25): тип части объявлен в `## Типы`, сторона называет его в столбце `части`, событие
    `часть(имя { … })` — `часть { … }`; `## Сигналы` убран (AL-141).
Деревья `*.alula.json` с `"alula_version": "2.25"`: версия — 2.26, у данных убрано поле `writes`, строки счётчиков сторон убраны;
дерево с фрагментами или подключениями скрипт не переносит (место «дерево»: пересобрать из файла `alula compile`).
Тесты `*.alula.test.json` формат 2.26 не меняет (`test/0`, спецификация, раздел 11): скрипт их читает и не правит.

Что НЕ решает сам (выход 1, строка на место `файл:строка: вид: что сделать`):
  - фрагмент 2.25 (`# Фрагмент:`) — библиотека пишется по разделу 9 (`## Требует`, параметры обычных типов); образец — `libs/pause.alula.md`;
  - строка операции с условием или не с событием `сразу`; вторая строка операции;
  - сигнал машины из `## Сигналы` (слой продукта 2.25) в строке обращения к стороне, у которой такого сигнала нет: в 2.26 сигнал
    машины вне контракта — только в общих событиях и ПАУЗЕ библиотеки (4.3, 9);
  - подключение незнакомой библиотеки функций (нет файла в `libs/` пакета) и проза в `## Подключения`;
  - `КодСбоя`, объявленный машиной с кодами, которых нет в контракте (продукт добавляет коды своей библиотекой);
  - дерево с фрагментами/подключениями; файл другого формата, кроме 2.25 и 2.26.
Запуск: `python tools/migrate-alula-226.py [--dry-run] [--alula <программа alula>] <файл или папка>…` (папки — рекурсивно);
с `--alula` (или переменной среды `ALULA`) дерево, рядом с которым лежит файл машины, пересобирается из перенесённого файла
`alula compile` пакета 0.9.0 (реестр и журнал хозяина — рядом с файлом), без неё такое дерево — место «дерево». Код возврата: 0 — перенесено
(или переносить нечего), 1 — перенесено, но остались места из перечня (печатаются на stdout), 2 — ошибка запуска (нет пути,
неизвестный ключ, файл не UTF-8). `--dry-run` ничего не пишет: печатает, какие файлы изменились бы, и те же места.
Повторный запуск на перенесённых файлах ничего не меняет (файл 2.26 не трогается).
"""
import hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIBS = os.path.join(ROOT, 'libs')

# ---- слова 2.25 и 2.26 по языку файла -------------------------------------------------------------------------------------------------------------

W = {
    'ru': {
        'ends': 'Концы', 'output': 'Выход', 'obliges': 'Обязывает', 'requires': 'Требует', 'states': 'Состояния', 'data': 'Данные',
        'parties': 'Стороны', 'types': 'Типы', 'includes': 'Подключения', 'external': 'Внешние функции', 'common': 'Общие события',
        'parts': 'Части ответа', 'signals_sec': 'Сигналы', 'num': '№', 'event': 'Событие', 'cond': 'Условие', 'actions': 'Действия',
        'to': 'Куда', 'field': 'поле запроса', 'expr': 'выражение', 'reads_col': 'читает', 'executor': 'исполнитель', 'json_name': 'JSON-имя', 'signal_ev': 'сигнал', 'writes': 'пишет', 'name': 'имя',
        'counter': 'счётчик', 'signals': 'сигналы', 'parts_col': 'части', 'immediate': 'сразу', 'reads_key': 'Читает',
        'operation': 'операция', 'party_col': 'сторона', 'fields_col': 'поля', 'part_ev': 'часть', 'deadline': None, 'timeout': None,
        'keys': ['Сторона', 'Срок тишины', 'Правит', 'Возвратов формы', 'Запрос', 'При входе', 'При приёме', 'Кроме', 'Результат',
                 'Предел запросов', 'Инвариант'],
        'ext_prefix': 'внешняя функция ', 'functions_hdr': 'Функции', 'fragment_hdr': 'Фрагмент', 'library_hdr': 'Библиотека',
        'engine': ['запрос_вызова', 'открытые_запросы'], 'mechanics': 'механика', 'failcode': 'КодСбоя', 'type_kw': 'тип',
        'file': 'Файл', 'hash': 'Хеш', 'param': 'параметр', 'value': 'значение', 'pause': 'Пауза',
        'pause_params': {'сигнал_остановки': 'сигнал_остановки', 'код_остановки': 'код_остановки', 'вложенные': 'вложенные',
                         'отмена_запросов': 'отмена_запросов', 'вход_заново': 'вход_заново'},
        'pause_note': ('право_записи', 'право записи'), 'pause_file': 'libs/pause.alula.md', 'functions_kw': 'функции',
    },
    'en': {
        'ends': 'Ends', 'output': 'Output', 'obliges': None, 'requires': 'Requires', 'states': 'States', 'data': 'Data',
        'parties': 'Parties', 'types': 'Types', 'includes': 'Includes', 'external': 'External functions', 'common': 'Common events',
        'parts': 'Response parts', 'signals_sec': 'Signals', 'num': '№', 'event': 'Event', 'cond': 'Condition', 'actions': 'Actions',
        'to': 'To', 'field': 'request_field', 'expr': 'expression', 'reads_col': 'reads', 'executor': 'executor', 'json_name': 'json_name', 'signal_ev': 'signal', 'writes': 'writes', 'name': 'name',
        'counter': 'counter', 'signals': 'signals', 'parts_col': 'parts', 'immediate': 'immediate', 'reads_key': 'Reads',
        'operation': 'operation', 'party_col': 'party', 'fields_col': 'fields', 'part_ev': 'part', 'deadline': 'deadline',
        'timeout': 'timeout',
        'keys': ['Party', 'Idle term', 'Edits', 'Form returns', 'Request', 'On entry', 'On accept', 'Except', 'Result', 'Request limit',
                 'Invariant'],
        'ext_prefix': 'external fn ', 'functions_hdr': 'Functions', 'fragment_hdr': 'Fragment', 'library_hdr': 'Library',
        'engine': ['call_request_id', 'open_requests'], 'mechanics': 'mechanics', 'failcode': 'FailCode', 'type_kw': 'type',
        'file': 'File', 'hash': 'Hash', 'param': 'parameter', 'value': 'value', 'pause': 'Pause',
        'pause_params': {'halt_signal': 'halt_signal', 'halt_code': 'halt_code', 'nested': 'nested', 'cancel_requests': 'request_cancel',
                         'reenter': 'reentry'},
        'pause_note': ('write_right', 'write right'), 'pause_file': 'libs/pause.en.alula.md', 'functions_kw': 'functions',
    },
}
HEADER_KEYS = ['machine', 'machine_version', 'format', 'language', 'library', 'fragment', 'functions_version']
# коды библиотеки `контракт` (7а): JSON-значения перечисления КодСбоя
CONTRACT_CODES = {'no_result', 'model_refused', 'connection_lost', 'form_not_fixed', 'timeout', 'stopped_by_human', 'ceiling_reached',
                  'cancelled', 'max_tokens', 'max_turn_requests'}
# библиотеки функций 2.25, которые шли с переводчиком: имя подключения -> латинское имя файла в libs/ пакета
KNOWN_FUNCTIONS = {'арифметика_цикла': 'cycle_arithmetic', 'cycle_arithmetic': 'cycle_arithmetic'}
# слова параметров «Паузы» 2.25, которые в 2.26 — строки набора литералов
PAUSE_QUOTED = {'сигнал_остановки', 'отмена_запросов', 'вход_заново', 'halt_signal', 'cancel_requests', 'reenter'}


class Run:
    def __init__(self):
        self.places = []
        self.changed = []

    def place(self, path, line, kind, todo):
        self.places.append('%s:%d: %s: %s' % (path, line, kind, todo))


def lib_hash(text):
    """Хеш библиотеки (раздел 9): 12 знаков SHA-256 после нормализации (BOM, LF, пробелы в конце строк, один LF в конце)."""
    if text.startswith('\ufeff'):
        text = text[1:]
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [l.rstrip(' \t') for l in text.split('\n')]
    while lines and lines[-1] == '':
        lines.pop()
    return hashlib.sha256(('\n'.join(lines) + '\n').encode('utf-8')).hexdigest()[:12]


# ---- таблицы -----------------------------------------------------------------------------------------------------------------------------------

def split_row(line):
    """Ячейки строки таблицы `| a | b |`; `\\|` внутри ячейки — знак, а не граница."""
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|') and not s.endswith('\\|'):
        s = s[:-1]
    cells, cur, i = [], '', 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s) and s[i + 1] == '|':
            cur += '\\|'
            i += 2
            continue
        if s[i] == '|':
            cells.append(cur.strip())
            cur = ''
        else:
            cur += s[i]
        i += 1
    cells.append(cur.strip())
    return cells


def join_row(cells):
    return '| ' + ' | '.join(cells) + ' |' if all(cells) else '|' + '|'.join((' %s ' % c) if c else '  ' for c in cells) + '|'


def is_sep(line):
    return re.match(r'^\s*\|(\s*:?-+:?\s*\|)+\s*$', line) is not None


def sep_row(n):
    return '|' + '---|' * n


def strip_comment(s):
    """Заголовок без комментария `//`."""
    i = s.find('//')
    return (s[:i] if i >= 0 else s).strip()


def dash(c):
    return c.strip() in ('—', '-')


# ---- файл машины, библиотеки функций -----------------------------------------------------------------------------------------------------------

def file_lang(lines):
    for l in lines[:40]:
        m = re.match(r'^\s*(?:-\s+)?language:\s*(\w+)', l)
        if m:
            return m.group(1)
    return 'ru'


def file_format(lines):
    for l in lines[:40]:
        m = re.match(r'^\s*(?:-\s+)?format:\s*([0-9.]+)', l)
        if m:
            return m.group(1)
    return None


def sections_of(lines):
    """Разделы `##`: [(начало, конец, ключ без комментария)]; до первого — шапка."""
    out, start, title = [], None, None
    fence = False
    for i, l in enumerate(lines):
        if l.strip().startswith('```'):
            fence = not fence
        if not fence and l.startswith('## '):
            if start is not None:
                out.append((start, i, title))
            start, title = i, strip_comment(l[3:])
    if start is not None:
        out.append((start, len(lines), title))
    return out


def tables_in(lines, a, b):
    """Таблицы между строками a и b: [(начало, конец)], начало — строка заголовка."""
    out, i = [], a
    while i < b:
        if lines[i].lstrip().startswith('|') and i + 1 < b and is_sep(lines[i + 1]):
            j = i + 2
            while j < b and lines[j].lstrip().startswith('|'):
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def party_signals(cell):
    """Имена сигналов ячейки `сигналы`: `a { поле тип }, b` -> {a, b}."""
    return {re.split(r'[\s{(]', x.strip(), maxsplit=1)[0] for x in split_top(cell) if x.strip() and not dash(x)}


def collect_parties(lines, w, psignals=None):
    """Счётчики сторон (имена из столбца `счётчик`); в psignals — сигналы каждой стороны."""
    counters = set()
    for a, b, title in sections_of(lines):
        if title != w['parties']:
            continue
        for ta, tb in tables_in(lines, a, b):
            head = split_row(lines[ta])
            if w['counter'] not in head:
                continue
            k = head.index(w['counter'])
            sk = head.index(w['signals']) if w['signals'] in head else None
            for r in range(ta + 2, tb):
                cells = split_row(lines[r])
                if k < len(cells) and not dash(cells[k]):
                    counters.add(cells[k])
                if psignals is not None and sk is not None and sk < len(cells):
                    psignals[cells[0]] = party_signals(cells[sk])
    return counters


def unused_mechanics(lines, w, counters):
    """Данные «пишет механика», которые не счётчики и не данные движка и которых файл больше нигде не называет (кроме `## Имена`)."""
    out = set()
    for a, b, title in sections_of(lines):
        if title != w['data']:
            continue
        for ta, tb in tables_in(lines, a, b):
            head = split_row(lines[ta])
            if w['writes'] not in head:
                continue
            wc, nc = head.index(w['writes']), head.index(w['name'])
            for r in range(ta + 2, tb):
                cells = split_row(lines[r])
                if wc >= len(cells) or cells[wc] != w['mechanics'] or cells[nc] in counters or cells[nc] in w['engine']:
                    continue
                name = cells[nc]
                pat = re.compile(r'(?<![\w])%s(?![\w])' % re.escape(name))
                names_row = re.compile(r'^\|\s*%s\s*\|\s*[A-Za-z_][A-Za-z0-9_]*\s*\|\s*$' % re.escape(name))
                uses = [i for i, l in enumerate(lines) if i != r and pat.search(l) and not names_row.match(l)]
                if not uses:
                    out.add(name)
    return out


def balanced_call(lines, i, name):
    """Вызов `Имя(…)` с начала строки i, возможно на нескольких строках: (текст аргументов, номер последней строки)."""
    text = lines[i].strip()[len(name):].lstrip()
    j = i
    depth = 0
    buf = ''
    while True:
        for ch in text:
            buf += ch
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
        if depth <= 0 or j + 1 >= len(lines):
            break
        j += 1
        text = ' ' + lines[j].strip()
    inner = buf.strip()
    if inner.startswith('(') and inner.endswith(')'):
        inner = inner[1:-1]
    return inner, j


def split_top(s, sep=','):
    out, depth, cur, q = [], 0, '', False
    for ch in s:
        if ch == '"':
            q = not q
        if not q:
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
            elif ch == sep and depth == 0:
                out.append(cur.strip())
                cur = ''
                continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def quote(v):
    v = v.strip()
    return v if v.startswith('"') else '"%s"' % v


def lib_beside(machine_path, rel, src_name, run, line):
    """Файл библиотеки рядом с машиной: если его нет, кладётся копия из libs/ пакета. Хеш — по файлу рядом с машиной."""
    dest = os.path.normpath(os.path.join(os.path.dirname(machine_path), rel))
    if not os.path.exists(dest):
        src = os.path.join(LIBS, src_name)
        if not os.path.exists(src):
            run.place(machine_path, line, 'подключение', 'нет файла библиотеки %s в libs/ пакета: положите файл `%s` и впишите его хеш' % (src_name, rel))
            return None
        if not run.dry:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(src, encoding='utf-8') as f:
                text = f.read()
            with open(dest, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
        run.changed.append(dest)
        with open(src, encoding='utf-8') as f:
            return lib_hash(f.read())
    with open(dest, encoding='utf-8') as f:
        return lib_hash(f.read())


def includes_block(path, lines, a, b, w, lang, run):
    """Новое тело `## Подключения`: подзаголовки библиотек."""
    out = []
    i = a + 1
    while i < b:
        s = lines[i].strip()
        if s == '' or s.startswith('```') or s.startswith('//'):
            i += 1
            continue
        m = re.match(r'^%s:\s*(\S+)\s+\S+\s+\d+\s+\S+\s+([0-9a-f]{12})\s*$' % w['functions_kw'], s)
        if m:
            name = m.group(1)
            latin = KNOWN_FUNCTIONS.get(name)
            if latin is None:
                run.place(path, i + 1, 'подключение', 'библиотека функций `%s` не из пакета: перепишите файл функций библиотекой (раздел 9) и подключите подзаголовком `### %s`' % (name, name))
                i += 1
                continue
            src = latin + ('.en' if lang == 'en' else '') + '.alula.md'
            rel = 'libs/' + src
            h = lib_beside(path, rel, src, run, i + 1)
            out += ['', '### %s' % name, '- %s: %s' % (w['file'], rel), '- %s: %s' % (w['hash'], h or '<хеш>')]
            i += 1
            continue
        if s.startswith(w['pause'] + '('):
            inner, j = balanced_call(lines, i, w['pause'])
            rows, notes = [], []
            for arg in split_top(inner):
                if ':' not in arg:
                    run.place(path, i + 1, 'подключение', 'аргумент `%s` «Паузы» без имени: назовите параметр' % arg)
                    continue
                k, v = arg.split(':', 1)
                k, v = k.strip(), v.strip()
                if k == w['pause_note'][0]:
                    notes.append('// %s: %s' % (w['pause_note'][1], v.strip('"')))
                    continue
                if k not in w['pause_params']:
                    run.place(path, i + 1, 'подключение', 'параметр `%s` «Паузы» неизвестен: сверьте с libs/pause.alula.md' % k)
                    continue
                if k in PAUSE_QUOTED:
                    v = quote(v)
                elif v.startswith('['):
                    items = [x.strip() for x in v[1:-1].split(',') if x.strip()]
                    v = '[' + ', '.join(quote(x) for x in items) + ']'
                rows.append((w['pause_params'][k], v))
            h = lib_beside(path, w['pause_file'], os.path.basename(w['pause_file']), run, i + 1)
            out += ['', '### %s' % w['pause'], '- %s: %s' % (w['file'], w['pause_file']), '- %s: %s' % (w['hash'], h or '<хеш>'), '',
                    '| %s | %s |' % (w['param'], w['value']), sep_row(2)]
            out += [join_row([k, v]) for k, v in rows]
            out += notes
            i = j + 1
            continue
        run.place(path, i + 1, 'подключение', 'в `## %s` 2.26 — только подзаголовки библиотек: перенесите строку `%s` в прозу раздела машины' % (w['includes'], s[:60]))
        i += 1
    return out


def remove_failcode(path, lines, a, b, w, run):
    """Убрать объявление `тип КодСбоя перечисление …` с кодами контракта из блока `## Типы`; номера убираемых строк."""
    drop = set()
    i = a
    while i < b:
        if re.match(r'^\s*%s\s+%s\b' % (w['type_kw'], w['failcode']), lines[i]):
            j = i + 1
            while j < b and re.match(r'^\s*\|', lines[j]):
                j += 1
            codes = set(re.findall(r'"([a-z_0-9]+)"', ' '.join(lines[i:j])))
            if codes and codes <= CONTRACT_CODES:
                drop.update(range(i, j))
                while j < b and lines[j].strip() == '' and (j + 1 >= b or not lines[j + 1].strip().startswith('```')):
                    drop.add(j)
                    j += 1
            else:
                run.place(path, i + 1, 'тип', '`%s` объявлен машиной с кодами вне контракта (%s): тип даёт библиотека `контракт`, свои коды — своей библиотекой (7а)' % (w['failcode'], ', '.join(sorted(codes - CONTRACT_CODES))))
            i = j
        else:
            i += 1
    return drop


def migrate_md(path, text, run):
    lines = text.replace('\r\n', '\n').split('\n')
    fmt = file_format(lines)
    if fmt == '2.26':
        return None
    if fmt != '2.25':
        run.place(path, 1, 'формат', 'формат %s: скрипт переносит только 2.25 -> 2.26' % fmt)
        return None
    lang = file_lang(lines)
    w = W[lang]
    title = lines[0] if lines else ''
    if title.startswith('# %s:' % w['fragment_hdr']):
        run.place(path, 1, 'фрагмент', 'фрагмент 2.25 — библиотека 2.26 (раздел 9): параметры обычных типов, `## Требует`, без `<…>`; образец — libs/pause.alula.md пакета')
        return None
    psignals = {}
    counters = collect_parties(lines, w, psignals)
    secs = sections_of(lines)
    ctx = {'party': None, 'state': None, 'dropped': unused_mechanics(lines, w, counters), 'msignals': set(), 'psignals': psignals}
    for a, b, t in secs:
        if t == w['signals_sec']:
            for ta, tb in tables_in(lines, a, b):
                for r in range(ta + 2, tb):
                    ctx['msignals'].add(split_row(lines[r])[0])
    # части ответа (слой продукта 2.25): сторона -> имя части; объявления типов
    parts, part_types = {}, []
    for a, b, t in secs:
        if t == w['parts']:
            for ta, tb in tables_in(lines, a, b):
                head = split_row(lines[ta])
                for r in range(ta + 2, tb):
                    c = split_row(lines[r])
                    row = dict(zip(head, c))
                    party, name, fields = row.get(w['party_col'], ''), row.get(w['name'], ''), row.get(w['fields_col'], '')
                    parts[party] = name
                    part_types.append('%s %s { %s }' % (w['type_kw'], name, fields if not dash(fields) else ''))
    out = []
    drop = set()
    # шапка
    first_sec = secs[0][0] if secs else len(lines)
    is_functions = title.startswith('# %s:' % w['functions_hdr'])
    for i in range(first_sec):
        l = lines[i]
        m = re.match(r'^(\s*)(-\s+)?(%s):\s*(.*)$' % '|'.join(HEADER_KEYS), l)
        if i == 0 and is_functions:
            name = title.split(':', 1)[1].strip()
            out.append('# %s: %s' % (w['library_hdr'], name))
            continue
        if m:
            key, val = m.group(3), m.group(4)
            if key == 'format':
                val = '2.26'
            if key == 'functions_version':
                name = title.split(':', 1)[1].strip()
                latin = KNOWN_FUNCTIONS.get(name, name if re.match(r'^[a-z][a-z0-9_]*$', name) else None)
                if latin is None:
                    run.place(path, i + 1, 'библиотека', 'латинское имя библиотеки `%s`: впишите `- library: <имя>`' % name)
                    latin = name
                key, val = 'library', latin
            out.append('- %s: %s' % (key, val))
        else:
            out.append(l)
    kind = None
    has_types = any(t == w['types'] and [x for x in lines[a + 1:b] if x.strip() not in ('', '—', '-')] for a, b, t in secs)
    for a, b, t in secs:
        if part_types and not has_types:
            # раздела типов не было: он первый после шапки, тип части — в нём
            out += ['## ' + w['types'], '', '```'] + part_types + ['```', '']
            part_types = []
        body = [x.strip() for x in lines[a + 1:b] if x.strip()]
        if body == ['—'] or body == ['-']:
            continue
        if t in (w['parts'], w['signals_sec']):
            continue
        head_line = lines[a]
        if t == w['ends']:
            head_line = '## ' + w['output']
        elif w['obliges'] and t == w['obliges']:
            head_line = '## ' + w['requires']
        out.append(head_line)
        if t == w['includes']:
            out += includes_block(path, lines, a, b, w, lang, run)
            out.append('')
            continue
        tables = {ta: tb for ta, tb in tables_in(lines, a + 1, b)}
        sdrop = set()
        if t == w['types']:
            sdrop = remove_failcode(path, lines, a + 1, b, w, run)
        fence_close = None
        if t == w['types'] and part_types:
            for k in range(b - 1, a, -1):
                if lines[k].strip().startswith('```'):
                    fence_close = k
                    break
            if fence_close is None:
                run.place(path, a + 1, 'части', 'тип части объявите в блоке кода `## %s`: %s' % (w['types'], '; '.join(part_types)))
        i = a + 1
        while i < b:
            l = lines[i]
            if i in sdrop:
                i += 1
                continue
            if i == fence_close:
                out += part_types
                part_types = []
            if l.startswith('### '):
                m = re.match(r'^###\s+(.+?)\s+—\s+(\S+)', l)
                kind = m.group(2) if m else None
                ctx['state'], ctx['party'] = (m.group(1) if m else None), None
            pm = re.match(r'^\s*(?:-\s+)?%s:\s*([^;]+)' % re.escape(w['keys'][0]), l)
            if pm and t == w['states']:
                ctx['party'] = pm.group(1).strip()
            if i in tables:
                tb = tables[i]
                rows = table(path, lines, i, tb, t, kind, w, counters, parts, run, ctx)
                if not rows:
                    # «Запрос» только из строк, которые читал движок (2.25 `читает: исполнитель`): стороне ничего не уходит, строки `Запрос` нет
                    while out and out[-1].strip() == '':
                        out.pop()
                    if out and re.match(r'^-\s+%s:\s*$' % re.escape(w['keys'][4]), out[-1]):
                        out.pop()
                    if tb < b and lines[tb].strip() == '':
                        tb += 1
                out += rows
                i = tb
                continue
            s = l.strip()
            # строки-ключи
            km = re.match(r'^(\s*)(-\s+)?(%s):(.*)$' % re.escape(w['reads_key']), l)
            if km and t in (w['states'], w['common'], w['ends'], w['output']):
                i += 1
                continue
            km = re.match(r'^(\s*)(-\s+)?(%s):(.*)$' % '|'.join(re.escape(k) for k in w['keys']), l)
            if km and not km.group(1) and t in (w['states'], w['ends'], w['parties'], w['output'], w['data']):
                out.append('- %s:%s' % (km.group(3), km.group(4)))
                i += 1
                continue
            if t == w['external'] and s.startswith(w['ext_prefix']):
                out.append(l.replace(w['ext_prefix'], '', 1))
                i += 1
                continue
            out.append(l)
            i += 1
    text2 = '\n'.join(out)
    if part_types:
        run.place(path, 1, 'части', 'нет раздела `## %s`: объявите тип части: %s' % (w['types'], '; '.join(part_types)))
    return text2


def table(path, lines, ta, tb, section, kind, w, counters, parts, run, ctx):
    head = split_row(lines[ta])
    rows = [split_row(lines[r]) for r in range(ta + 2, tb)]
    keep = list(range(len(head)))
    out_rows = []

    def drop_col(name):
        if name in head and head.index(name) in keep:
            keep.remove(head.index(name))

    def col(name):
        return head.index(name) if name in head else None

    if w['to'] in head:
        drop_col(w['num'])
        ev, cd, ac, to = col(w['event']), col(w['cond']), col(w['actions']), col(w['to'])
        operation = kind == w['operation'] and ev is not None
        if operation:
            if len(rows) != 1:
                run.place(path, ta + 1, 'операция', 'у операции %d строк: в 2.26 одна строка `Действия | Куда`' % len(rows))
            ok = all(r[ev] == w['immediate'] and dash(r[cd]) for r in rows) if cd is not None else all(r[ev] == w['immediate'] for r in rows)
            if ok:
                drop_col(w['event'])
                if cd is not None:
                    drop_col(w['cond'])
            else:
                run.place(path, ta + 1, 'операция', 'строка операции не `сразу` без условия: перепишите развилкой или операцией `Действия | Куда`')
        for r in rows:
            r = list(r) + [''] * (len(head) - len(r))
            for k in (cd, ac, to):
                if k is not None and dash(r[k]):
                    r[k] = ''
            if ev is not None:
                e = r[ev]
                sm = re.match(r'^%s\(\s*([^\s({)]+)' % re.escape(w['signal_ev']), e)
                if sm and sm.group(1) in ctx['msignals'] and section == w['states'] and ctx['party'] and sm.group(1) not in ctx['psignals'].get(ctx['party'], set()):
                    run.place(path, ta + 3 + len(out_rows), 'сигнал машины', 'сигнал `%s` из `## %s` в строке обращения %s к стороне `%s`: в 2.26 сигнал машины вне контракта — только в общих событиях и ПАУЗЕ библиотеки (4.3, 9), раздела `## %s` нет; перенесите строку в общие события библиотеки или дайте сигнал стороне' % (sm.group(1), w['signals_sec'], ctx['state'], ctx['party'], w['signals_sec']))
                m = re.match(r'^%s\(\s*([^\s({]+)\s*(\{.*\})?\s*\)$' % re.escape(w['part_ev']), e)
                if m:
                    r[ev] = w['part_ev'] + (' ' + m.group(2) if m.group(2) else '')
                if w['deadline'] and e == w['deadline']:
                    r[ev] = w['timeout']
            out_rows.append(r)
    elif w['field'] in head:
        rc = col(w['reads_col'])
        drop_col(w['reads_col'])
        f, x = col(w['field']), col(w['expr'])
        for r in rows:
            r = list(r) + [''] * (len(head) - len(r))
            if rc is not None and r[rc] == w['executor']:
                continue
            if x is not None and (dash(r[x]) or r[x] == r[f]):
                r[x] = ''
            out_rows.append(r)
    elif section in (w['ends'], w['output']) and w['num'] in head:
        drop_col(w['num'])
        out_rows = [list(r) for r in rows]
    elif section == w['data'] and w['writes'] in head:
        wc, nc = col(w['writes']), col(w['name'])
        drop_col(w['writes'])
        for n, r in enumerate(rows):
            r = list(r) + [''] * (len(head) - len(r))
            name = r[nc]
            if name in counters or name in w['engine'] or name in ctx['dropped']:
                continue
            out_rows.append(r)
    elif w['json_name'] in head and ctx['dropped']:
        out_rows = [list(r) for r in rows if r[0] not in ctx['dropped']]
    elif section == w['parties'] and parts and w['signals'] in head and w['parts_col'] not in head:
        k = head.index(w['signals']) + 1
        head = head[:k] + [w['parts_col']] + head[k:]
        keep = list(range(len(head)))
        nc = col(w['name'])
        for r in rows:
            r = list(r)
            r = r[:k] + [parts.get(r[nc], '—')] + r[k:]
            out_rows.append(r)
    else:
        return lines[ta:tb]
    if not out_rows and w['field'] in head:
        return []
    res = [join_row([head[k] for k in keep]), sep_row(len(keep))]
    for r in out_rows:
        r = list(r) + [''] * (len(head) - len(r))
        res.append(join_row([r[k] for k in keep]))
    return res


# ---- деревья -----------------------------------------------------------------------------------------------------------------------------------

def migrate_tree(path, text, run):
    try:
        tree = json.loads(text)
    except ValueError as e:
        run.place(path, 1, 'дерево', 'не JSON: %s' % e)
        return None
    if not isinstance(tree, dict) or tree.get('format') != 'machine/2':
        return None
    v = tree.get('alula_version')
    if v == '2.26':
        return None
    if v != '2.25':
        run.place(path, 1, 'дерево', 'alula_version %s: скрипт переносит только 2.25 -> 2.26' % v)
        return None
    if tree.get('fragments') or tree.get('includes'):
        run.place(path, 1, 'дерево', 'дерево с фрагментами или подключениями: перенесите файл машины и пересоберите дерево `alula compile`')
        return None
    counters = {p.get('counter') for p in tree.get('parties', []) if isinstance(p, dict)}
    data = []
    for d in tree.get('data', []):
        if d.get('name') in counters:
            continue
        d = {k: x for k, x in d.items() if k != 'writes'}
        data.append(d)
    out = {}
    for k, x in tree.items():
        if k == 'alula_version':
            x = '2.26'
        elif k == 'data':
            x = data
        out[k] = x
    compact = '\n' not in text.strip()
    if compact:
        return json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ('\n' if text.endswith('\n') else '')
    return json.dumps(out, ensure_ascii=False, indent=2) + ('\n' if text.endswith('\n') else '')


# ---- обход -------------------------------------------------------------------------------------------------------------------------------------

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


def compile_tree(path, md, alula, run):
    """Дерево из перенесённого файла машины: `alula compile <md> -o <json> --force` (рядом лежат реестр и журнал хозяина)."""
    import subprocess
    if run.dry:
        run.changed.append(path)
        return
    with open(path, encoding='utf-8', newline='') as f:
        before = f.read()
    try:
        done = subprocess.run([alula, 'compile', md, '-o', path, '--force'], capture_output=True, text=True, encoding='utf-8')
    except OSError as e:
        sys.stderr.write('alula не запускается: %s\n' % e)
        sys.exit(2)
    if done.returncode != 0:
        first = [l for l in (done.stderr or done.stdout).splitlines() if l.strip()][:1]
        run.place(path, 1, 'дерево', 'alula compile не собрал дерево из %s: %s' % (os.path.basename(md), first[0] if first else 'код %d' % done.returncode))
        return
    with open(path, encoding='utf-8', newline='') as f:
        if f.read() != before:
            run.changed.append(path)


def data_order(tree):
    """Порядок `все_данные` машины 2.26: данные дерева по порядку (данные движка, данные библиотек, данные машины), затем счётчики сторон."""
    order = [d.get('name') for d in tree.get('data', []) if isinstance(d, dict)]
    order += [p.get('counter') for p in tree.get('parties', []) if isinstance(p, dict) and p.get('counter')]
    return order


def tree_of(machine_md, alula):
    """Дерево 2.26 перенесённой машины: файл `.alula.json` рядом (2.26) или `alula compile` в память; None — нет дерева."""
    import subprocess
    beside = machine_md[:-len('.alula.md')] + '.alula.json'
    if os.path.exists(beside):
        try:
            with open(beside, encoding='utf-8') as f:
                t = json.load(f)
            if t.get('alula_version') == '2.26':
                return t
        except ValueError:
            pass
    if not alula:
        return None
    done = subprocess.run([alula, 'compile', machine_md], capture_output=True, text=True, encoding='utf-8')
    if done.returncode != 0:
        return None
    try:
        return json.loads(done.stdout)
    except ValueError:
        return None


def migrate_tests(tests, machines, tree_paths, alula, run):
    """Тесты: формат `test/0` не меняется; в ожидании журнала `machine_data` (`журнал(все_данные)`) порядок данных — порядок 2.26
    (данные движка `контракт` и библиотек впереди, счётчики сторон, которые заводит загрузчик, — в конце)."""
    if not tests:
        return
    trees = None
    for path in tests:
        with open(path, encoding='utf-8', newline='') as f:
            text = f.read()
        if '"machine_data"' not in text:
            continue
        try:
            test = json.loads(text)
        except ValueError:
            run.place(path, 1, 'тест', 'не JSON')
            continue
        if trees is None:
            trees = {}
            for md in machines:
                t = tree_of(md, alula)
                if t:
                    trees[t.get('machine')] = t
            for tp in tree_paths:
                try:
                    with open(tp, encoding='utf-8') as f:
                        t = json.load(f)
                except ValueError:
                    continue
                if isinstance(t, dict) and t.get('alula_version') == '2.26' and t.get('machine') not in trees:
                    trees[t.get('machine')] = t
        tree = trees.get(test.get('machine'))
        if tree is None:
            run.place(path, 1, 'тест', 'нет дерева 2.26 машины `%s` для порядка `все_данные`: запустите скрипт с --alula и папкой машины' % test.get('machine'))
            continue
        order = data_order(tree)
        new = text
        for old in sorted(set(re.findall(r'"code":\s*"machine_data",\s*"params":\s*\{\s*"data":\s*"((?:[^"\\]|\\.)*)"', text))):
            value = json.loads('"%s"' % old)
            pairs = split_top(value, ';')
            rank = {n: k for k, n in enumerate(order)}
            keyed = [(rank.get(p.split('=', 1)[0].strip(), len(order) + k), p) for k, p in enumerate(pairs)]
            again = '; '.join(p for _, p in sorted(keyed, key=lambda x: x[0]))
            if again != value:
                new = new.replace('"%s"' % old, json.dumps(again, ensure_ascii=False))
        if new != text:
            run.changed.append(path)
            if not run.dry:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(new)


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
        sys.stderr.write('запуск: python tools/migrate-alula-226.py [--dry-run] [--alula <программа alula>] <файл или папка>...\n')
        return 2
    for p in paths:
        if not os.path.exists(p):
            sys.stderr.write('нет пути: %s\n' % p)
            return 2
    if alula and not os.path.exists(alula):
        sys.stderr.write('нет программы alula: %s\n' % alula)
        return 2
    if alula:
        alula = os.path.abspath(alula)
    run = Run()
    run.dry = dry
    trees, tests, machines = [], [], []
    for path in candidates(paths):
        try:
            with open(path, encoding='utf-8', newline='') as f:
                text = f.read()
        except (UnicodeDecodeError, OSError) as e:
            sys.stderr.write('%s: не прочитан как UTF-8: %s\n' % (path, e))
            return 2
        if path.endswith('.alula.test.json'):
            tests.append(path)
            continue
        if path.endswith('.alula.json'):
            trees.append((path, text))
            continue
        head = text[:4000]
        if not path.endswith('.alula.md') and not re.search(r'^(-\s+)?format:\s*2\.2[56]\s*$', head, re.M):
            continue
        if not re.search(r'^# ', head, re.M):
            continue
        if re.search(r'^# (Машина|Machine):', head, re.M):
            machines.append(path)
        new = migrate_md(path, text, run)
        if new is not None and '\r\n' in text:
            new = new.replace('\n', '\r\n')
        if new is not None and new != text:
            run.changed.append(path)
            if not dry:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(new)
    for path, text in trees:
        try:
            tree = json.loads(text)
        except ValueError:
            tree = None
        if isinstance(tree, dict) and tree.get('alula_version') == '2.26':
            continue
        md = path[:-len('.alula.json')] + '.alula.md'
        if isinstance(tree, dict) and tree.get('alula_version') == '2.25' and os.path.exists(md):
            if alula:
                compile_tree(path, md, alula, run)
            else:
                run.place(path, 1, 'дерево', 'рядом файл машины %s: пересоберите дерево `alula compile` (или запустите скрипт с --alula <программа>)' % os.path.basename(md))
            continue
        new = migrate_tree(path, text, run)
        if new is not None and new != text:
            run.changed.append(path)
            if not dry:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(new)
    migrate_tests(tests, machines, [p for p, _ in trees], alula, run)
    verb ='изменился бы' if dry else 'перенесён'
    for p in run.changed:
        print('%s: %s' % (verb, p))
    for p in run.places:
        print(p)
    print('итог: файлов %d, мест %d' % (len(run.changed), len(run.places)))
    return 1 if run.places else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
