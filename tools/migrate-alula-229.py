#!/usr/bin/env python3
"""Перенос файлов Алулы с 0.28 на 0.29 (эпик 0.29, результат B, пакет alula 0.29.0).

Зачем: 0.29 — ломающая версия без переходного периода (журнал изменений AL-153…AL-157): файл с
`- alula_version: 0.28` пакет 0.29.0 не читает (подсказки называют этот скрипт). Нормы записи 0.29
(внешний кодек ответа, различимое необязательное, `декодировать`, `?x`, цепочки «иначе если») уже
в пакете 0.28.0-плюс; механически нерешаемое место переноса одно: равенство необязательного с голым
значением (AL-154) — его находит проверка компилятора и называет строку, правится руками по подсказке.

Что переносит:
  - шапка: `- alula_version: 0.28` — `- alula_version: 0.29`;
  - подключение библиотеки: `- Хеш:` — хеш файла библиотеки рядом (файлы библиотек 0.29 другие: шапка
    `alula_version`); библиотека, переносимая этим же запуском, хешируется по её НОВОМУ тексту;
  - дерево `*.alula.json`: `alula_version` — `0.29`; рядом файл машины и задан `--alula` — дерево
    пересобирается `alula compile`.

Что НЕ решает сам (после переноса машина собирается проверкой компилятора; место называет подсказка
«равенство необязательного» — сначала `есть(x)`, затем `обязательно(x) == v`): таблица, где необязательное
сравнивается с голым значением. Дерево рядом с файлом машины без `--alula` — место (выход 1).

Запуск: `python tools/migrate-alula-229.py [--dry-run] [--alula <программа alula>] <файл или папка>…`
(папки — рекурсивно); код 0 — перенесено (или нечего), 1 — остались места, 2 — ошибка запуска.
`--dry-run` ничего не пишет. `--selftest` — регрессионный тест: папка «машина + библиотеки» переносится
одним запуском (хеши подключений — по новым текстам библиотек этого же запуска), повторный запуск
ничего не меняет.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


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
    """Шапка: `- alula_version: 0.28` — `0.29` (строка одна на файл; скан без остановки на первом `## ` —
    так файл со вложенным текстом машины, как фикстура теста, тоже переносится)."""
    n = 0
    for i, l in enumerate(lines):
        if re.match(r'^(-\s+)?alula_version:\s*0\.28\s*$', l):
            lines[i] = re.sub(r'0\.28\s*$', '0.29', l)
            n += 1
    return n


def hashes(lines, path, run, texts=None):
    """`- Хеш:` подключения — хеш файла библиотеки рядом с машиной.

    `texts` — словарь «нормализованный путь → текст после переноса» всех файлов запуска: библиотека,
    которая сама переносится этим же запуском, хешируется по её НОВОМУ тексту (иначе при переносе
    машины и библиотек одной папкой хеш считался бы по старому тексту и первая сборка дерева падала
    на несовпадении хеша); библиотеки вне запуска читаются с диска."""
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
    if tree.get('alula_version') != '0.28':
        return None
    tree['alula_version'] = '0.29'
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
    """Регрессионный тест: папка «машина + библиотеки» 0.28 переносится ОДНИМ запуском (rc=0, мест 0,
    дерево пересобрано, хеш подключения — от новой библиотеки), повторный запуск ничего не меняет
    (идемпотентность: rc=0, файлов 0). Образец — examples/chat, опущенный до 0.28 строкой версии."""
    import contextlib, io as sio, shutil, tempfile
    if not alula:
        alula = os.path.normpath(os.path.join(HERE, '..', 'target', 'alula.exe'))
    if not os.path.exists(alula):
        sys.stderr.write('самотесту нужна программа alula (ключ --alula или переменная ALULA), нет: %s\n' % alula)
        return 2
    tmp = tempfile.mkdtemp(prefix='migrate229-selftest-')
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
            rw(p, lambda t: t.replace('- alula_version: 0.29', '- alula_version: 0.28'))
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
        ok = rc1 == 0 and rc2 == 0 and want in body and 'alula_version: 0.28' not in body \
            and 'мест 0' in first and 'файлов 0' in second
        if ok:
            print('самотест migrate-alula-229: ок (первый запуск — rc=0, мест 0; повторный — rc=0, файлов 0)')
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
        sys.stderr.write('запуск: python tools/migrate-alula-229.py [--dry-run] [--alula <программа alula>] <файл или папка>...\n'
                         '        python tools/migrate-alula-229.py --selftest [--alula <программа alula>] — регрессионный тест\n')
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
    # два прохода: сначала перенос всех файлов без хешей, затем хеши подключений — по НОВЫМ текстам
    # библиотек этого же запуска (папка «машина + библиотеки» переносится одним запуском, rc=0)
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
