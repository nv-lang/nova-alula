#!/usr/bin/env python3
"""Перенос файлов Алулы с 0.30 на 0.31 (лямбда в форме Новы, решение владельца 2026-11-19).

Зачем: 0.31 — ломающая версия без переходного периода: лямбда пишется как в Нове — `|x| выр`,
двухместная — `|a, b| выр`; прежняя запись `x => выр` / `(a, b) => выр` в файле 0.31 — ошибка
(подсказка называет этот скрипт). Дерево не меняется: узел `lambda` {params, body} прежний,
меняется только синтаксис текста и значение `alula_version` в деревьях.

Что переносит:
  - шапка: `- alula_version: 0.30` — `- alula_version: 0.31`;
  - лямбды в аргументах вызовов: `x => выр` — `|x| выр`, `(a, b) => выр` — `|a, b| выр`;
    в ячейке таблицы бары пишутся `\\|x\\|` (строку таблицы режет `|`), в блоке кода — `|x|`;
    ветки `выбор`, тела функций (`-> Тип => …`), строки и комментарии не трогаются;
  - подключение библиотеки: `- Хеш:` — по новому тексту библиотеки (если в ней менялись лямбды);
  - дерево `*.alula.json`: `alula_version` — `0.31`; рядом файл машины и задан `--alula` — дерево
    пересобирается `alula compile`.

Запуск: `python tools/migrate-alula-231.py [--dry-run] [--alula <программа alula>] <файл или папка>…`
(папки — рекурсивно); код 0 — перенесено (или нечего), 1 — остались места, 2 — ошибка запуска.
`--dry-run` ничего не пишет. `--selftest` — регрессионный тест: лямбды в ячейке и в блоке кода
переносятся, тело функции и ветка `выбор` не трогаются, повторный запуск ничего не меняет.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

ID = r'[A-Za-zА-Яа-яЁё_][A-Za-zА-Яа-яЁё0-9_]*'
SINGLE = re.compile(r'(' + ID + r')\s*=>')
DOUBLE = re.compile(r'\(\s*(' + ID + r')\s*,\s*(' + ID + r')\s*\)\s*=>')


class Run:
    def __init__(self, dry):
        self.dry = dry
        self.changed = []
        self.places = []

    def place(self, path, line, kind, todo):
        one = '%s:%d: %s: %s' % (path, line, kind, todo)
        if one not in self.places:
            self.places.append(one)


def lib_hash(text):
    """Хеш библиотеки (раздел 9): по правилу скрипта 2.26 (`lib_hash` в `tools/migrate-alula-226.py`)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('m226', os.path.join(HERE, 'migrate-alula-226.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.lib_hash(text)


def header_line(lines):
    """Шапка: `- alula_version: 0.30` — `0.31` (скан без остановки на первом `## `)."""
    n = 0
    for i, l in enumerate(lines):
        if re.match(r'^(-\s+)?alula_version:\s*0\.30\s*$', l):
            lines[i] = re.sub(r'0\.30\s*$', '0.31', l)
            n += 1
    return n


def lambdas_in_line(line, cell):
    """Лямбды в аргументах вызовов одной строки: `x =>` — `|x|`, `(a, b) =>` — `|a, b|`.

    Верхняя незакрытая скобка должна быть `(` вызова (внутри `{ … }` — ветки `выбор` и тела
    функций — не трогаем); голова лямбды стоит сразу после `(` или `,`; строки и `//` не трогаем.
    В ячейке таблицы бары пишутся `\\|`; в блоке кода — `|`."""
    bar = '\\|' if cell else '|'
    out = []
    stack = []
    i = 0
    n = 0
    prev = ''
    while i < len(line):
        c = line[i]
        if c == '"':
            j = i + 1
            while j < len(line):
                if line[j] == '\\':
                    j += 2
                    continue
                if line[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(line[i:j])
            prev = '"'
            i = j
            continue
        if c == '/' and i + 1 < len(line) and line[i + 1] == '/':
            out.append(line[i:])
            break
        if c in '({':
            m = DOUBLE.match(line, i)
            if m and stack and stack[-1] == '(' and prev in ('(', ','):
                out.append('%s%s, %s%s' % (bar, m.group(1), m.group(2), bar))
                prev = ')'
                i = m.end()
                n += 1
                continue
            stack.append(c)
            out.append(c)
            prev = c
            i += 1
            continue
        if c in ')}':
            if stack:
                stack.pop()
            out.append(c)
            prev = c
            i += 1
            continue
        if stack and stack[-1] == '(' and prev in ('(', ','):
            m = SINGLE.match(line, i)
            if m:
                out.append('%s%s%s' % (bar, m.group(1), bar))
                prev = '|'
                i = m.end()
                n += 1
                continue
        if not c.isspace():
            prev = c
        out.append(c)
        i += 1
    return ''.join(out), n


def lambdas(lines):
    n = 0
    fence = False
    for k, l in enumerate(lines):
        if l.strip().startswith('```'):
            fence = not fence
            continue
        if fence:
            cell = False
        else:
            cell = l.strip().startswith('|')
        t, m = lambdas_in_line(l, cell)
        if m:
            lines[k] = t
            n += m
    return n


def hashes(lines, path, run, texts=None):
    """`- Хеш:` подключения — хеш файла библиотеки рядом с машиной; библиотека, переносимая этим же
    запуском, хешируется по её НОВОМУ тексту."""
    n = 0
    for i, l in enumerate(lines):
        mf = re.match(r'^- (?:Файл|File): (\S+)\s*$', l)
        if not mf or i + 1 >= len(lines):
            continue
        mh = re.match(r'^- (Хеш|Hash): ([0-9a-f]{12})\s*$', lines[i + 1])
        if not mh:
            continue
        lib = os.path.join(os.path.dirname(path) or '.', mf.group(1))
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
    n = header_line(lines)
    n += lambdas(lines)
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
    if tree.get('alula_version') != '0.30':
        return None
    tree['alula_version'] = '0.31'
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


SELFTEST_MD = '''# Машина: Пробa

- machine: Probe
- alula_version: 0.30

## Данные

| имя | тип | начальное |
|---|---|---|
| пары | словарь[строка, число] | ["a"].словарь(n => n, n => n) |

## Функции

функция ответ(x число) -> число => x + 1

## Состояния

### СТАРТ — начальное

#### Переходы

| когда | куда | действие |
|---|---|---|
| выбор x { 1 => да, иначе => нет } | КОНЕЦ | — |
'''


def selftest(alula):
    """Регрессионный тест: лямбды в ячейке и в блоке кода переносятся, тело функции (`-> Тип => …`)
    и ветка `выбор` не трогаются, дерево пересобирается, повторный запуск ничего не меняет."""
    import contextlib, io as sio, shutil, tempfile
    if not alula:
        alula = os.path.normpath(os.path.join(HERE, '..', 'target', 'alula.exe'))
    if not os.path.exists(alula):
        sys.stderr.write('самотесту нужна программа alula (ключ --alula или переменная ALULA), нет: %s\n' % alula)
        return 2
    tmp = tempfile.mkdtemp(prefix='migrate231-selftest-')
    try:
        md = os.path.join(tmp, 'probe.alula.md')
        with open(md, 'w', encoding='utf-8', newline='') as f:
            f.write(SELFTEST_MD)
        out = sio.StringIO()
        with contextlib.redirect_stdout(out):
            rc1 = main(['--alula', alula, md])
        first = out.getvalue()
        with open(md, encoding='utf-8') as f:
            body = f.read()
        out = sio.StringIO()
        with contextlib.redirect_stdout(out):
            rc2 = main(['--alula', alula, md])
        second = out.getvalue()
        ok = (rc1 == 0 and rc2 == 0
              and 'alula_version: 0.31' in body
              and 'словарь(\\|n\\| n, \\|n\\| n)' in body
              and '=> x + 1' in body
              and 'выбор x { 1 => да, иначе => нет }' in body
              and 'мест 0' in first and 'файлов 0' in second)
        if ok:
            print('самотест migrate-alula-231: ок (лямбды в ячейке — `\\|n\\|`, тело функции и ветка не тронуты; повтор — файлов 0)')
            return 0
        sys.stderr.write('САМОТЕСТ КРАСНЫЙ: rc1=%d rc2=%d\n--- текст:\n%s--- первый запуск:\n%s--- второй:\n%s'
                         % (rc1, rc2, body, first, second))
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
        sys.stderr.write('запуск: python tools/migrate-alula-231.py [--dry-run] [--alula <программа alula>] <файл или папка>...\n'
                         '        python tools/migrate-alula-231.py --selftest [--alula <программа alula>] — регрессионный тест\n')
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
    # два прохода: сначала все файлы без хешей, затем хеши подключений — по НОВЫМ текстам библиотек
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
