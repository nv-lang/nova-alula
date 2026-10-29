#!/usr/bin/env python3
"""Перенос файлов Алулы с 0.27 на 0.28 (задача 253, пакет alula 0.28.0; AL-148…AL-152).

Зачем: 0.28 — ломающая версия без переходного периода (журнал изменений): файл с `- alula_version: 0.27` пакет 0.28.0 не читает
(подсказки раздела 10 «Запись 0.28»), а правка таблиц сторон, ключей с `;`, столбца «заново» и кодовых слов руками — ошибки
и потерянное время. Скрипт делает механическую часть и называет места, которые механически не решаются.

Что переносит:
  - шапка: `- alula_version: 0.27` — `- alula_version: 0.28`;
  - стороны (AL-148): таблица `## Стороны` — столбцы `настройка` и `разбор` после `вид` (английские `setting`, `parse`);
    вид `human или agent по настройке <имя>(итог …)` — `gatekeeper` и имя настройки в столбец `настройка`; запись
    `machine <имя>; разбор: <ф> -> Тип` — `machine <имя>` и имя функции в столбец `разбор`; `human(итог …)` со `—`
    в `счётчик` — вид `свободный_ввод` (английский `free_input`);
  - ключи (AL-149): `- Сторона: линза; набор: порядок_линз` — два элемента (`- Сторона: …` и `- Набор: …`),
    `- Правит: …; проверка: f` — `- Правит: …` и `- Проверка: f`;
  - «Куда» (AL-150): `ИМЯ, запуск заново` и `то же, запуск заново` — цель без суффикса и столбец `заново` (`да` у такой
    строки, пусто у остальных; столбец добавляется всей таблице); слово `то же` — `то_же`;
  - лексика (AL-152): `полный словарь` — `полный_словарь` (английское `full map` — `full_map`); `; ` между действиями
    в ячейке «Действия» строк состояния и в ячейке «действия» таблицы «При приёме» — `<br>` (внутри блоков `{ … }`
    и строковых литералов `;` остаётся); `- Имя:` подключения — `- Экземпляр:` (английское `- Name:` — `- As:`);
    `Начальное состояние: ИМЯ` без маркера — элемент списка `- Начальное состояние: ИМЯ`; пустая строка между элементом
    списка и следующей за ним таблицей (4.1: таблица — на уровне блока, без строки — ошибка разбора);
  - дерево `*.alula.json`: `alula_version` — `0.28`; `parse` стороны без ключа `type` (тип результата — из объявления
    функции); сторона `human` без счётчика — `kind: free_input` без `result`; рядом файл машины и задан `--alula` —
    дерево пересобирается `alula compile`;
  - подключение библиотеки: `- Хеш:` — хеш файла библиотеки рядом (файлы библиотек 0.28 другие).
Что НЕ решает сам (выход 1, строка на место `файл:строка: вид: что сделать`): дерево с файлом машины рядом без `--alula`.
Запуск: `python tools/migrate-alula-228.py [--dry-run] [--alula <программа alula>] <файл или папка>…` (папки — рекурсивно);
код 0 — перенесено (или нечего), 1 — остались места, 2 — ошибка запуска. `--dry-run` ничего не пишет.
`--selftest` — регрессионный тест: папка «машина + библиотеки» переносится одним запуском (хеши подключений считаются
по новым текстам библиотек этого же запуска), повторный запуск ничего не меняет.
"""
import json, os, re, subprocess, sys

W = {
    'ru': {'name': 'имя', 'id': 'идентификатор', 'kind': 'вид', 'setting': 'настройка', 'parse': 'разбор',
           'profile': 'профиль', 'signals': 'сигналы', 'counter': 'счётчик', 'parts': 'части',
           'event': 'Событие', 'cond': 'Условие', 'actions': 'Действия', 'to': 'Куда', 'rerun_col': 'заново', 'yes': 'да',
           'ev': 'событие', 'acts': 'действия', 'same': 'то же', 'same_new': 'то_же', 'rerun': 'запуск заново',
           'full_map': 'полный словарь', 'full_map_new': 'полный_словарь', 'result': 'итог', 'free': 'свободный_ввод',
           'party': 'Сторона', 'edits': 'Правит', 'set': 'набор', 'set_new': 'Набор', 'check': 'проверка',
           'check_new': 'Проверка', 'inst': 'Имя', 'inst_new': 'Экземпляр', 'initial': 'Начальное состояние',
           'gate': 'human или agent по настройке'},
    'en': {'name': 'name', 'id': 'id', 'kind': 'kind', 'setting': 'setting', 'parse': 'parse',
           'profile': 'profile', 'signals': 'signals', 'counter': 'counter', 'parts': 'parts',
           'event': 'Event', 'cond': 'Condition', 'actions': 'Actions', 'to': 'To', 'rerun_col': 'rerun', 'yes': 'yes',
           'ev': 'event', 'acts': 'actions', 'same': 'same', 'same_new': 'same', 'rerun': 'rerun',
           'full_map': 'full map', 'full_map_new': 'full_map', 'result': 'result', 'free': 'free_input',
           'party': 'Party', 'edits': 'Edits', 'set': 'set', 'set_new': 'Set', 'check': 'check',
           'check_new': 'Check', 'inst': 'Name', 'inst_new': 'As', 'initial': 'Initial state',
           'gate': 'human or agent by setting'},
}


class Run:
    def __init__(self, dry):
        self.dry = dry
        self.changed = []
        self.places = []

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


def is_sep(cells):
    return cells and all(set(c) <= set('-: ') and c for c in cells)


def join_row(cells):
    return '| %s |' % ' | '.join(cells)


def split_actions(s):
    """Части ячейки действий по `; ` вне фигурных скобок и строковых литералов; None — разделителей нет."""
    parts, depth, cur, i, quote = [], 0, '', 0, ''
    while i < len(s):
        c = s[i]
        if quote:
            cur += c
            if c == '\\' and i + 1 < len(s):
                cur += s[i + 1]
                i += 2
                continue
            if c == quote:
                quote = ''
            i += 1
            continue
        if c in '"\'':
            quote = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        if depth == 0 and s.startswith('; ', i):
            parts.append(cur.strip())
            cur = ''
            i += 2
            continue
        cur += c
        i += 1
    parts.append(cur.strip())
    return parts if len(parts) > 1 else None


def br_actions(cell):
    parts = split_actions(cell)
    return '<br>'.join(parts) if parts else cell


def header_line(lines):
    """Шапка: `- alula_version: 0.27` — `0.28` (строка одна на файл; скан без остановки на первом `## ` — так файл
    со вложенным текстом машины, как фикстура теста, тоже переносится)."""
    n = 0
    for i, l in enumerate(lines):
        if re.match(r'^(-\s+)?alula_version:\s*0\.27\s*$', l):
            lines[i] = re.sub(r'0\.27\s*$', '0.28', l)
            n += 1
    return n


def party_kind_227(kind, counter, w):
    """Вид и значения новых столбцов по записи 0.27: (новый вид, настройка, разбор) или None — строка не тронута."""
    m = re.match(r'^%s (\S+)\(%s .+\)$' % (re.escape(w['gate']), re.escape(w['result'])), kind)
    if m:
        return 'gatekeeper', m.group(1), '—'
    m = re.match(r'^machine (\S+); (?:%s): (\S+) -> .+$' % re.escape(w['parse']), kind)
    if m:
        return 'machine ' + m.group(1), '—', m.group(2)
    if re.match(r'^human\(%s .+\)$' % re.escape(w['result']), kind) and counter == '—':
        return w['free'], '—', '—'
    return None


def parties(lines, w):
    """Таблица `## Стороны` (AL-148, AL-151): столбцы `настройка` и `разбор` после `вид`."""
    n = 0
    i = 0
    while i < len(lines):
        cells = row_cells(lines[i])
        if not cells or len(cells) < 6 or cells[0] != w['name'] or cells[1] != w['id'] or cells[2] != w['kind'] \
                or cells[-1] != w['counter'] or w['setting'] in cells:
            i += 1
            continue
        lines[i] = join_row(cells[:3] + [w['setting'], w['parse']] + cells[3:])
        n += 1
        i += 1
        if i < len(lines) and is_sep(row_cells(lines[i]) or []):
            lines[i] = '|' + '---|' * (len(cells) + 2)
            i += 1
        while i < len(lines):
            cells = row_cells(lines[i])
            if not cells:
                break
            moved = party_kind_227(cells[2], cells[-1], w)
            if moved:
                kind, setting, parse = moved
                lines[i] = join_row([cells[0], cells[1], kind, setting, parse] + cells[3:])
            else:
                lines[i] = join_row(cells[:3] + ['—', '—'] + cells[3:])
            n += 1
            i += 1
    return n


def key_split(lines, w):
    """Второй ключ после `;` в элементе списка (AL-149) — своим элементом."""
    n = 0
    pat = re.compile(r'^(-\s+.*?); (%s|%s): (.*\S)\s*$' % (re.escape(w['set']), re.escape(w['check'])))
    i = 0
    while i < len(lines):
        m = pat.match(lines[i])
        if m:
            key = w['set_new'] if m.group(2) == w['set'] else w['check_new']
            lines[i:i + 1] = [m.group(1), '- %s: %s' % (key, m.group(3))]
            n += 1
        i += 1
    return n


def key_words(lines, w):
    """`- Имя:` — `- Экземпляр:`; `Начальное состояние: ИМЯ` без маркера — элемент списка (AL-152)."""
    n = 0
    for i, l in enumerate(lines):
        m = re.match(r'^- %s: (.*\S)\s*$' % re.escape(w['inst']), l)
        if m:
            lines[i] = '- %s: %s' % (w['inst_new'], m.group(1))
            n += 1
            continue
        m = re.match(r'^%s: (.*\S)\s*$' % re.escape(w['initial']), l)
        if m:
            lines[i] = '- %s: %s' % (w['initial'], m.group(1))
            n += 1
    return n


def full_map(lines, w):
    """`полный словарь` / `full map` — кодовое слово без пробела (AL-152)."""
    n = 0
    for i, l in enumerate(lines):
        if w['full_map'] in l:
            lines[i] = l.replace(w['full_map'], w['full_map_new'])
            n += 1
    return n


def state_tables(lines, w):
    """Таблицы строк состояний (AL-150, AL-152): последний столбец `Куда` — `то_же` и суффикс `, запуск заново` в столбец
    `заново`; `<br>` в столбце «Действия» перед ним. Формы шапок: обращение и общие события, развилка, операция."""
    n = 0
    i = 0
    heads = [[w['event'], w['cond'], w['actions'], w['to']], [w['cond'], w['actions'], w['to']], [w['actions'], w['to']]]
    while i < len(lines):
        cells = row_cells(lines[i])
        if cells not in heads:
            i += 1
            continue
        head = i
        width = len(cells)
        act = width - 2
        i += 1
        if i < len(lines) and is_sep(row_cells(lines[i]) or []):
            i += 1
        rows = []
        rerun = False
        while i < len(lines):
            cells = row_cells(lines[i])
            if not cells:
                break
            cells = (cells + [''] * width)[:width]
            to = cells[-1]
            mark = False
            for suffix in (', ' + w['rerun'], ',' + w['rerun']):
                if to.endswith(suffix):
                    to = to[:-len(suffix)].strip()
                    mark = True
                    break
            if to == w['same']:
                to = w['same_new']
            if to != cells[-1] or mark:
                n += 1
            cells[-1] = to
            new_actions = br_actions(cells[act])
            if new_actions != cells[act]:
                cells[act] = new_actions
                n += 1
            rows.append((cells, mark))
            rerun = rerun or mark
            i += 1
        if rerun:
            lines[head] = join_row((row_cells(lines[head]) or []) + [w['rerun_col']])
            lines[head + 1] = '|' + '---|' * (width + 1)
            for k, (cells, mark) in enumerate(rows):
                lines[head + 2 + k] = join_row(cells + [w['yes'] if mark else ''])
            n += 1
        else:
            for k, (cells, mark) in enumerate(rows):
                lines[head + 2 + k] = join_row(cells)
    return n


def accept_tables(lines, w):
    """Таблица «При приёме» `| событие | действия |`: `<br>` между действиями (AL-152)."""
    n = 0
    i = 0
    while i < len(lines):
        cells = row_cells(lines[i])
        if cells != [w['ev'], w['acts']]:
            i += 1
            continue
        i += 1
        if i < len(lines) and is_sep(row_cells(lines[i]) or []):
            i += 1
        while i < len(lines):
            cells = row_cells(lines[i])
            if not cells:
                break
            if len(cells) >= 2:
                new = br_actions(cells[1])
                if new != cells[1]:
                    cells[1] = new
                    lines[i] = join_row(cells)
                    n += 1
            i += 1
    return n


def list_table_gap(lines):
    """Пустая строка между элементом списка и таблицей (4.1: таблица стоит на уровне блока; без строки — ошибка разбора)."""
    n = 0
    i = 0
    while i + 1 < len(lines):
        if lines[i].startswith('- ') and (row_cells(lines[i + 1]) is not None):
            lines.insert(i + 1, '')
            n += 1
            i += 1
        i += 1
    return n


HERE = os.path.dirname(os.path.abspath(__file__))


def lib_hash(text):
    """Хеш библиотеки (раздел 9): по правилу скрипта 2.26 (`lib_hash` в `tools/migrate-alula-226.py`)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('m226', os.path.join(HERE, 'migrate-alula-226.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.lib_hash(text)


def hashes(lines, path, run, texts=None):
    """`- Хеш:` подключения — хеш файла библиотеки рядом с машиной (файлы библиотек 0.28 другие: шапка `alula_version`, формы 0.28).

    `texts` — словарь «нормальный путь → текст после переноса» всех файлов запуска: библиотека, которая сама
    переносится этим же запуском, хешируется по её НОВОМУ тексту (иначе при переносе машины и библиотек одной
    папкой хеш считался бы по старому тексту и первая сборка дерева падала на несовпадении хеша — блокер приёмки
    253); библиотеки вне запуска читаются с диска."""
    n = 0
    for i, l in enumerate(lines):
        mf = re.match(r'^- (?:Файл|File): (\S+)\s*$', l)
        if not mf or i + 1 >= len(lines):
            continue
        mh = re.match(r'^- (Хеш|Hash): ([0-9a-f]{12})\s*$', lines[i + 1])
        lib = os.path.join(os.path.dirname(path) or '.', mf.group(1))
        if not mh:
            continue
        key = os.path.normcase(os.path.abspath(lib))
        if texts is not None and key in texts:
            text = texts[key]
        elif os.path.exists(lib):
            with open(lib, encoding='utf-8') as f:
                text = f.read()
        else:
            continue
        h = lib_hash(text)
        if h != mh.group(2):
            lines[i + 1] = '- %s: %s' % (mh.group(1), h)
            n += 1
    return n


def migrate_md(path, text, run, hash_texts=None):
    lines = text.replace('\r\n', '\n').split('\n')
    w = W.get(file_lang(lines), W['ru'])
    n = header_line(lines) + parties(lines, w) + key_split(lines, w) + key_words(lines, w) \
        + full_map(lines, w) + state_tables(lines, w) + accept_tables(lines, w) + list_table_gap(lines)
    # hash_texts=False — перенос без хешей (первый проход main: тексты библиотек ещё не готовы)
    if hash_texts is not False:
        n += hashes(lines, path, run, hash_texts)
    if not n:
        return None
    return '\n'.join(lines)


def migrate_tree(path, text, run):
    try:
        tree = json.loads(text)
    except ValueError:
        return None
    if not isinstance(tree, dict) or ('kind' not in tree and 'alula_version' not in tree):
        return None
    n = 0

    def fix(v):
        nonlocal n
        if isinstance(v, dict):
            for k in list(v.keys()):
                if k == 'alula_version' and v[k] == '0.27':
                    v[k] = '0.28'
                    n += 1
                elif k == 'parse' and isinstance(v[k], dict) and 'type' in v[k]:
                    del v[k]['type']
                    n += 1
                else:
                    fix(v[k])
        elif isinstance(v, list):
            for x in v:
                fix(x)

    fix(tree)
    for p in tree.get('parties') or []:
        if isinstance(p, dict) and p.get('kind') == 'human' and not p.get('counter'):
            p['kind'] = 'free_input'
            p.pop('result', None)
            n += 1
    if not n:
        return None
    return json.dumps(tree, ensure_ascii=False, separators=(',', ':')) + ('\n' if text.endswith('\n') else '')


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


def selftest(alula):
    """Регрессионный тест (блокер приёмки 253): папка «машина + библиотеки» 0.27 переносится ОДНИМ запуском
    (rc=0, мест 0, дерево пересобрано, хеш подключения — от новой библиотеки), повторный запуск ничего не
    меняет (идемпотентность: rc=0, файлов 0). Образец — examples/chat, опущенный до 0.27 строкой версии."""
    import contextlib, io as sio, shutil, tempfile
    if not alula:
        alula = os.path.normpath(os.path.join(HERE, '..', 'target', 'alula.exe'))
    if not os.path.exists(alula):
        sys.stderr.write('самотесту нужна программа alula (ключ --alula или переменная ALULA), нет: %s\n' % alula)
        return 2
    tmp = tempfile.mkdtemp(prefix='migrate228-selftest-')
    try:
        work = os.path.join(tmp, 'chat')
        shutil.copytree(os.path.join(HERE, '..', 'examples', 'chat'), work)

        def rw(path, fn):
            with open(path, encoding='utf-8', newline='') as f:
                t = fn(f.read())
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(t)

        lib = os.path.join(work, 'libs', 'call_cancel.alula.md')
        mac = os.path.join(work, 'chat.alula.md')
        for p in (lib, mac):
            rw(p, lambda t: t.replace('- alula_version: 0.28', '- alula_version: 0.27'))
        with open(lib, encoding='utf-8') as f:
            h = lib_hash(f.read())
        rw(mac, lambda t: re.sub(r'^- Хеш: [0-9a-f]{12}$', '- Хеш: ' + h, t, flags=re.M))

        out = sio.StringIO()
        with contextlib.redirect_stdout(out):
            rc1 = main(['--alula', alula, work])
        first = out.getvalue()
        with open(lib, encoding='utf-8') as f:
            want = '- Хеш: ' + lib_hash(f.read())
        with open(mac, encoding='utf-8') as f:
            body = f.read()
        out = sio.StringIO()
        with contextlib.redirect_stdout(out):
            rc2 = main(['--alula', alula, work])
        second = out.getvalue()
        ok = rc1 == 0 and rc2 == 0 and want in body and 'alula_version: 0.27' not in body \
            and 'мест 0' in first and 'файлов 0' in second
        if ok:
            print('самотест migrate-alula-228: ок (первый запуск — rc=0, мест 0; повторный — rc=0, файлов 0)')
            return 0
        sys.stderr.write('САМОТЕСТ КРАСНЫЙ: rc1=%d rc2=%d хеш_новый=%s\n--- первый запуск:\n%s--- второй:\n%s'
                         % (rc1, rc2, want in body, first, second))
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    paths, dry, alula, selftest_mode = [], False, os.environ.get('ALULA') or None, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--dry-run':
            dry = True
        elif a == '--selftest':
            selftest_mode = True
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
    if selftest_mode:
        if paths:
            sys.stderr.write('--selftest не берёт путей\n')
            return 2
        return selftest(alula)
    if not paths:
        sys.stderr.write('запуск: python tools/migrate-alula-228.py [--dry-run] [--alula <программа alula>] <файл или папка>...\n'
                         '        python tools/migrate-alula-228.py --selftest [--alula <программа alula>] — регрессионный тест\n')
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
    docs = []
    for path in candidates(paths):
        try:
            with open(path, encoding='utf-8', newline='') as f:
                text = f.read()
        except (UnicodeDecodeError, OSError) as e:
            sys.stderr.write('%s: не прочитан как UTF-8: %s\n' % (path, e))
            return 2
        if path.endswith('.alula.json'):
            trees.append((path, text))
        elif re.search(r'^# ', text[:2000], re.M):
            docs.append((path, text))
    # два прохода: сначала перенос всех файлов без хешей, затем хеши подключений — по НОВЫМ текстам библиотек
    # этого же запуска (папка «машина + библиотеки» переносится одним запуском, rc=0; блокер приёмки 253)
    planned = {}
    for path, text in docs:
        new = migrate_md(path, text, run, False)
        planned[os.path.normcase(os.path.abspath(path))] = text if new is None else new
    for path, text in docs:
        base = planned[os.path.normcase(os.path.abspath(path))]
        lines = base.split('\n')
        write(path, text, '\n'.join(lines) if hashes(lines, path, run, planned) else base, run)
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
