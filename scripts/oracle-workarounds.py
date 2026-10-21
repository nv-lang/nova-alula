# -*- coding: utf-8 -*-
"""Метки обходов дефектов Oracle в коде: список, индекс, сводка.

Метка - комментарий `ORACLE-WORKAROUND(N[, M]): что обойдено; как упростить, когда пункт N исправят`,
где N - номер пункта в spikes/env/README.md. Скрипт читает метки в отслеживаемых файлах src/,
scripts/ и spikes/ (кроме самого README пунктов, индекса и стражей) и пункты README.

Использование (из корня репозитория или с --root <папка>), только стандартная библиотека:
  python scripts/oracle-workarounds.py            сводка: число меток, пунктов с метками и без них
  python scripts/oracle-workarounds.py --list     пункт -> файл:строка -> текст метки, по пунктам
  python scripts/oracle-workarounds.py --index    пишет spikes/env/workarounds.md (таблица пунктов и мест)

Индекс не хранит номера строк: он устаревает, только когда метка появилась, исчезла или перешла в
другой файл. Страж scripts/guards/check-oracle-workarounds.py проверяет метки и сверяет индекс с тем,
что пишет `--index`; общий разбор лежит здесь, страж берёт его из этого файла.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import os
import re
import subprocess

README = "spikes/env/README.md"
INDEX = "spikes/env/workarounds.md"
MARK = "ORACLE-WORKAROUND"
WORKED_ROUND = "worked round in the code"

SCAN_PREFIXES = ("src/", "scripts/", "spikes/")
SKIP_PATHS = frozenset((README, INDEX, "scripts/oracle-workarounds.py"))
SKIP_PREFIXES = ("scripts/guards/",)
BINARY_EXT = frozenset((
    "png", "jpg", "jpeg", "gif", "webp", "ico", "bmp", "pdf", "zip", "gz", "tgz", "7z",
    "woff", "woff2", "ttf", "otf", "eot", "mp3", "mp4", "mov", "webm", "wasm", "exe", "dll", "lock",
))

ITEM_RE = re.compile(r"^(\d{1,3})\. \S")
ARGS_RE = re.compile(r"^\d+(?:\s*,\s*\d+)*$")
CLOSER_RE = re.compile(r"\s*(-->|\*/)\s*$")
TITLE_LIMIT = 130


def is_scanned(path):
    """Файл, в котором ищутся метки."""
    if path in SKIP_PATHS or not path.startswith(SCAN_PREFIXES) or path.startswith(SKIP_PREFIXES):
        return False
    name = path.rsplit("/", 1)[-1]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name.lstrip(".") else ""
    return ext not in BINARY_EXT


def parse_items(text):
    """Пункты README: {номер: {"line": номер строки, "title": первая строка, "block": весь текст пункта}}."""
    lines = text.replace("\r\n", "\n").split("\n")
    items = {}
    i = 0
    while i < len(lines):
        m = ITEM_RE.match(lines[i])
        if not m:
            i += 1
            continue
        number = int(m.group(1))
        block = [lines[i]]
        j = i + 1
        while j < len(lines) and lines[j].startswith("    "):
            block.append(lines[j])
            j += 1
        if number not in items:
            items[number] = {"line": i + 1, "title": title_of(lines[i]), "block": "\n".join(block)}
        i = j
    return items


def title_of(line):
    """Первая строка пункта без номера и жирного шрифта, обрезанная по слову."""
    body = re.sub(r"^\d+\.\s+", "", line.strip()).replace("**", "")
    if len(body) > TITLE_LIMIT:
        cut = body[:TITLE_LIMIT].rsplit(" ", 1)[0].rstrip(",;:( ")
        body = cut + "..."
    return body


def scan_text(path, text):
    """Метки одного файла: список словарей {path, line, items, text, error}.

    error - None или (правило, описание): bad-mark (формат), not-comment (метка не в комментарии).
    В .md меткой считается только та, что стоит после `<!--`: проза о метках в README модулей не метка.
    """
    is_md = path.lower().endswith(".md")
    found = []
    for number, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        start = raw.find(MARK + "(")
        pos = raw.find(MARK)
        if pos < 0:
            continue
        if start < 0:
            start = pos
        prefix = raw[:start]
        if is_md:
            if "<!--" not in prefix:
                continue
            in_comment = True
        else:
            in_comment = "//" in prefix or "#" in prefix or "<!--" in prefix
        rest = raw[start + len(MARK):]
        mark = {"path": path, "line": number, "items": [], "text": "", "error": None}
        m = re.match(r"^\(([^)]*)\)(.*)$", rest)
        if not in_comment:
            mark["error"] = ("not-comment", "метка стоит не в комментарии (`//`, `#`, `<!--`), а в строке данных")
        elif not m:
            mark["error"] = ("bad-mark", "нет скобок с номерами пунктов: нужно `%s(N[, M]): текст`" % MARK)
        else:
            args, tail = m.group(1), m.group(2)
            if not ARGS_RE.match(args.strip()):
                mark["error"] = ("bad-mark", "в скобках должны быть номера пунктов через запятую, а там «%s»" % args.strip())
            else:
                mark["items"] = [int(x) for x in re.split(r"\s*,\s*", args.strip())]
                body = CLOSER_RE.sub("", tail.rstrip())
                if not body.startswith(":"):
                    mark["error"] = ("bad-mark", "после скобок нет двоеточия: нужно `%s(N): текст`" % MARK)
                else:
                    mark["text"] = body[1:].strip()
                    if not mark["text"]:
                        mark["error"] = ("bad-mark", "после двоеточия нет текста: что обойдено и как упростить")
        found.append(mark)
    return found


def count_by_item(marks):
    """{номер пункта: [метки]} только по правильным меткам."""
    by_item = {}
    for mark in marks:
        if mark["error"]:
            continue
        for number in mark["items"]:
            by_item.setdefault(number, [])
            if mark not in by_item[number]:
                by_item[number].append(mark)
    return by_item


def render_index(items, marks):
    """Текст spikes/env/workarounds.md: он же эталон, с которым страж сверяет файл."""
    by_item = count_by_item(marks)
    good = [m for m in marks if not m["error"]]
    files = sorted(set(m["path"] for m in good))
    with_marks = sorted(n for n in items if n in by_item)
    without = sorted(n for n in items if n not in by_item)
    out = [
        "# Workarounds of Oracle 0.1.0 in the code",
        "",
        "<!-- generated by `python scripts/oracle-workarounds.py --index`; do not edit by hand: the guard "
        "`check-oracle-workarounds.py` fails when this file differs from what the command writes -->",
        "",
        "Every place of the package that goes round a defect or a limit of Oracle carries a comment "
        "`// ORACLE-WORKAROUND(N): what is gone round; how to simplify when item N is fixed`, where N is an item of "
        "[README.md](README.md) (\"Known problems\"). `git grep ORACLE-WORKAROUND` finds them, "
        "`python scripts/oracle-workarounds.py --list` prints them by item with the line. When Nova fixes an item, "
        "open its places below, simplify the code as the mark says and remove the mark; then rerun "
        "`python scripts/oracle-workarounds.py --index`.",
        "",
        "Marks: %d in %d files. Items with marks: %d. Items without marks: %d (no workaround in the code)."
        % (len(good), len(files), len(with_marks), len(without)),
        "",
        "| Item | What | Places (files; marks in a file if more than one) | Marks |",
        "|---|---|---|---|",
    ]
    for number in sorted(items):
        places = "no workaround in the code"
        count = 0
        if number in by_item:
            per_file = {}
            for mark in by_item[number]:
                per_file[mark["path"]] = per_file.get(mark["path"], 0) + 1
            count = len(by_item[number])
            places = ", ".join("`%s`%s" % (p, " (%d)" % c if c > 1 else "") for p, c in sorted(per_file.items()))
        title = items[number]["title"].replace("|", "\\|")
        out.append("| %d | %s | %s | %d |" % (number, title, places, count))
    out.append("")
    return "\n".join(out)


# -- работа с деревом (команда) ----------------------------------------------------------------
def git_files(root):
    proc = subprocess.run(("git", "ls-files", "-z"), cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise SystemExit("FAIL: git ls-files: %s" % proc.stderr.decode("utf-8", "replace").strip()[-200:])
    return [p.decode("utf-8", "replace") for p in proc.stdout.split(b"\0") if p]


def read_text(root, path):
    try:
        with open(os.path.join(root, path), "rb") as handle:
            return handle.read().decode("utf-8", "replace").lstrip("﻿")
    except OSError:
        return None


def load_tree(root):
    """(пункты README, метки всех отслеживаемых файлов дерева)."""
    readme = read_text(root, README)
    items = parse_items(readme) if readme is not None else {}
    marks = []
    for path in sorted(git_files(root)):
        if not is_scanned(path):
            continue
        text = read_text(root, path)
        if text is not None and MARK in text:
            marks.extend(scan_text(path, text))
    return items, marks


def command_list(items, marks):
    by_item = count_by_item(marks)
    for number in sorted(by_item):
        title = items[number]["title"] if number in items else "(no such item in README.md)"
        print("item %d: %s" % (number, title))
        for mark in sorted(by_item[number], key=lambda m: (m["path"], m["line"])):
            print("  %s:%d: %s" % (mark["path"], mark["line"], mark["text"]))
    broken = [m for m in marks if m["error"]]
    for mark in broken:
        print("broken mark %s:%d: %s" % (mark["path"], mark["line"], mark["error"][1]))
    return 0


def command_summary(items, marks):
    by_item = count_by_item(marks)
    good = [m for m in marks if not m["error"]]
    unknown = sorted(n for n in by_item if n not in items)
    print("marks: %d; items with marks: %d; items without marks: %d; broken marks: %d; marks of an unknown item: %d"
          % (len(good), len([n for n in items if n in by_item]), len([n for n in items if n not in by_item]),
             len(marks) - len(good), len(unknown)))
    return 0


def command_index(root, items, marks):
    if not items:
        print("FAIL: no items in %s" % README)
        return 1
    text = render_index(items, marks)
    target = os.path.join(root, *INDEX.split("/"))
    old = None
    try:
        with open(target, "rb") as handle:
            old = handle.read().decode("utf-8", "replace").replace("\r\n", "\n")
    except OSError:
        pass
    if old == text:
        print("%s is up to date" % INDEX)
        return 0
    with open(target, "wb") as handle:
        handle.write(text.encode("utf-8"))
    print("%s written" % INDEX)
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="Marks of the workarounds of Oracle in the code")
    parser.add_argument("--root", default=None, help="the root of the repository (default: the one of this script)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="item -> file:line -> text of the mark")
    group.add_argument("--index", action="store_true", help="write " + INDEX)
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root) if args.root else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    items, marks = load_tree(root)
    if args.list:
        return command_list(items, marks)
    if args.index:
        return command_index(root, items, marks)
    return command_summary(items, marks)


if __name__ == "__main__":
    sys.exit(main())
