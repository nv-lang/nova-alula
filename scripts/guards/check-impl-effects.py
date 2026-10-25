# -*- coding: utf-8 -*-
"""Страж реализаций внешних функций хозяина: модуль реализаций не импортирует эффектные модули и не берёт мир мимо среды.

Зачем: класс внешней функции (чистая, изменчивая, действующая) задан типом среды, но тип не мешает реализации
    прямо вызвать `println`, прочитать файл или поставить обработчик эффекта: чистая функция с тихим `Fs.read`
    остаётся «чистой» по подписи. Это дверь инварианта контракта хозяина (спецификация, раздел 7а, AL-130:
    «не доказано типами»); страж закрывает её для файлов реализаций.
Проверяет: в отслеживаемых файлах `.nv` папки реализаций (по умолчанию `src/host_impls/`, без `*_test.nv`)
    нет (а) импорта эффектного модуля `std` или его родителя/потомка; список эффектных модулей ВЫВОДИТСЯ из
    исходников `std` (файл объявляет `type X effect {` или подпись функции с рядом эффектов `) Io Fs -> T`), руками
    не пишется; модули `std.testing` и `std.ffi` запрещены явно; (б) токенов, которыми мир берут без импорта:
    `println`/`print`/`eprintln`/`eprint`, сырая операция эффекта `Io.f(`/`Fs.f(`/`Time.f(`/... (имена эффектов — из
    исходников `std` и стандартные), установка обработчика `with <Эффект>`, `extern`, `unsafe`, `spawn`,
    `detach`, `parallel for`. Комментарии вырезаются, строки остаются.
    Режимы: без аргументов — дерево (git ls-files); `--files <файл>...` — указанные файлы с диска (так страж
    запускают на образцах `scripts/guards/samples/impl-effects/`); `--impls <префикс>` (можно повторять) — другие
    папки реализаций; `--std <папка>` — исходники `std` (иначе `NOVA_STD_PATH`, иначе папка `std` рядом с `nova`);
    `--show-modules` — напечатать выведенный список.
Не проверяет: эффектные модули самого пакета транзитивно (`import alula.x`, где x сам читает файлы): это дело
    `nova check --strict-effects` и `nova info` (поверхность эффектов); чтение мира чистой функцией через захват
    (не меняет версию мира, виден только ревью); изменяемые глобальные состояния модуля, кроме токенов выше.
    Нет исходников `std` — «пропущено» (в CI пропуск красный).
Правило: задача 179, AL-130; спецификация, раздел 7а.

Пометок-исключений у этого стража нет.
"""
import sys

sys.dont_write_bytecode = True

import os
import re
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import guardlib  # noqa: E402

GUARD = "check-impl-effects"
DEFAULT_IMPLS = ("src/host_impls/",)

# Стандартные эффекты языка: имена, которые видны без объявления в `std` (к ним добавляются объявленные в исходниках).
STANDARD_EFFECTS = ["Io", "Fs", "Os", "Net", "Db", "Time", "Random", "Proc", "Log", "Trace", "Detach", "Blocking", "Supervisor", "Application"]
# Эффекты, что не выводят из программы в мир: `Fail[E]` - возврат ошибки (как `Result`), он есть в сигнатурах обычных модулей коллекций и текста.
NOT_WORLD_EFFECTS = ("Fail",)
# Модули `std`, запрещённые явно, хотя эффектом в сигнатурах они себя не объявляют.
BANNED_MODULES = ["std.testing", "std.ffi"]

EFFECT_DECL = re.compile(r"^(?:export\s+)?type\s+(\w+)(?:\[[^\]]*\])?\s+effect\b", re.M)
MODULE = re.compile(r"^module\s+([\w.]+)", re.M)
SKIP_DIRS = ("neg", "_experimental", "testing", "runtime")


def strip_comments(text):
    """Комментарии `//…` и `/*…*/` заменены пробелами (переводы строк сохранены); строки `"…"` и `` `…` `` остаются."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif c == "`":
            j = text.find("`", i + 1)
            j = n - 1 if j < 0 else j
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def std_sources(std_root):
    """Файлы `.nv` исходников `std` (без тестов и без папок, что не входят в публичный `std`)."""
    base = os.path.join(std_root, "src") if os.path.isdir(os.path.join(std_root, "src")) else std_root
    for d, dirs, files in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            if f.endswith(".nv") and not f.endswith("_test.nv"):
                yield os.path.join(d, f)


def derive(std_root):
    """(имена эффектов, {модуль: файл}) - выведено из исходников `std`."""
    texts = []
    for path in std_sources(std_root):
        with open(path, encoding="utf-8", errors="replace") as handle:
            texts.append((path, strip_comments(handle.read())))
    effects = set(STANDARD_EFFECTS)
    for _, text in texts:
        for m in EFFECT_DECL.finditer(text):
            if m.group(1) not in NOT_WORLD_EFFECTS:
                effects.add(m.group(1))
    row = re.compile(r"\)\s+((?:(?:%s)(?:\[[^\]]*\])?\s+)+)->" % "|".join(sorted(effects)))
    modules = {}
    for path, text in texts:
        m = MODULE.search(text)
        if not m:
            continue
        declares = [d for d in EFFECT_DECL.findall(text) if d not in NOT_WORLD_EFFECTS]
        if declares or row.search(text):
            name = m.group(1)
            if not name.startswith("std."):
                name = "std." + name
            modules.setdefault(name, os.path.basename(path))
    for name in BANNED_MODULES:
        modules.setdefault(name, "(запрещён явно)")
    return sorted(effects), modules


def find_std(arg):
    if arg:
        return arg
    env = os.environ.get("NOVA_STD_PATH")
    if env:
        return env
    nova = shutil.which("nova")
    if nova:
        cand = os.path.join(os.path.dirname(os.path.abspath(nova)), "std")
        if os.path.isdir(cand):
            return cand
    return None


def token_rules(effects):
    names = "|".join(effects)
    return [
        (re.compile(r"\b(println|print|eprintln|eprint)\s*\("), "вывод из prelude мимо среды"),
        (re.compile(r"\b(%s)\.[a-z_][a-z_0-9]*\s*\(" % names), "сырая операция эффекта"),
        (re.compile(r"\bwith\s+(%s)\b" % names), "установка обработчика эффекта"),
        (re.compile(r"\bextern\b"), "extern (FFI)"),
        (re.compile(r"\bunsafe\b"), "unsafe"),
        (re.compile(r"\b(spawn|detach|parallel\s+for)\b"), "параллельность мимо среды"),
    ]


IMPORT = re.compile(r"^\s*import\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)", re.M)


def judge_text(text, modules, rules):
    """Нарушения одного текста: список (строка, правило, описание)."""
    clean = strip_comments(text)
    found = []
    for m in IMPORT.finditer(clean):
        imp = m.group(1)
        line = clean.count("\n", 0, m.start(1)) + 1
        for mod in modules:
            # `import std.fs.{Fs, read}` даёт модуль `std.fs`; запрещены сам модуль, его родитель и потомок
            if mod == imp or mod.startswith(imp + ".") or imp.startswith(mod + "."):
                found.append((line, "effect-import", "импорт `%s` достаёт эффектный модуль `%s`" % (imp, mod)))
                break
    for rx, why in rules:
        for m in rx.finditer(clean):
            line = clean.count("\n", 0, m.start()) + 1
            found.append((line, "effect-token", "%s: `%s`" % (why, " ".join(m.group(0).split()))))
    return found


def extra(parser):
    parser.add_argument("--impls", action="append", default=[])
    parser.add_argument("--std")
    parser.add_argument("--files", nargs="+")
    parser.add_argument("--show-modules", action="store_true")


def load(args):
    std = find_std(args.std)
    if std is None or not os.path.isdir(std):
        return None
    effects, modules = derive(std)
    return effects, modules


def judge(source, args, rep):
    derived = load(args)
    if derived is None:
        return guardlib.Outcome(skip="нет исходников std (NOVA_STD_PATH или --std): список эффектных модулей вывести не из чего")
    effects, modules = derived
    if len(modules) <= len(BANNED_MODULES):
        raise guardlib.Unavailable("в исходниках std не найден ни один эффектный модуль: список вывести не удалось")
    rules = token_rules(effects)
    prefixes = tuple(args.impls) if args.impls else DEFAULT_IMPLS
    count = 0
    for entry in source.changed():
        name = entry.path.rsplit("/", 1)[-1]
        if not name.endswith(".nv") or name.endswith("_test.nv") or not entry.path.startswith(prefixes):
            continue
        data = source.read(entry)
        if data is None:
            continue
        count += 1
        for line, rule, desc in judge_text(data.decode("utf-8", "replace"), modules, rules):
            rep.add(entry.path, line, rule, desc)
    return guardlib.Outcome(count=count)


def run_files(args):
    """Режим образцов: указанные файлы с диска; код 1, если хоть одно нарушение."""
    guardlib.setup_io()
    derived = load(args)
    if derived is None:
        sys.stdout.write("FAIL: предпосылка: нет исходников std (NOVA_STD_PATH или --std)\n")
        return 1
    effects, modules = derived
    rules = token_rules(effects)
    total = 0
    lines = []
    for path in args.files:
        with open(path, "rb") as handle:
            text = handle.read().decode("utf-8", "replace")
        for line, rule, desc in judge_text(text, modules, rules):
            lines.append("FAIL %s:%d: %s: %s" % (path, line, rule, desc))
            total += 1
    if total:
        lines.append(guardlib.fail(GUARD, total))
        sys.stdout.write("\n".join(lines) + "\n")
        return 1
    sys.stdout.write("\n".join(lines + [guardlib.ok(len(args.files), "файлов реализаций")]) + "\n")
    return 0


def main(argv=None):
    probe = guardlib.build_parser(extra, GUARD).parse_args(argv)
    if probe.show_modules:
        guardlib.setup_io()
        derived = load(probe)
        if derived is None:
            sys.stdout.write("FAIL: предпосылка: нет исходников std\n")
            return 1
        effects, modules = derived
        sys.stdout.write("эффекты: %s\n" % ", ".join(effects))
        for name in sorted(modules):
            sys.stdout.write("%s\t%s\n" % (name, modules[name]))
        sys.stdout.write("ок: выведено %d эффектных модулей std\n" % len(modules))
        return 0
    if probe.files:
        return run_files(probe)
    return guardlib.run(GUARD, "файлов реализаций", judge, argv=argv, extra=extra,
                        lost="нет ни одного файла реализаций под %s" % ", ".join(DEFAULT_IMPLS))


if __name__ == "__main__":
    sys.exit(main())
