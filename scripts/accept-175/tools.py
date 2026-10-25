#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Помощник скрипта scripts/accept-175.sh (задача 175, Алула 2.24, внешние функции).

Зачем: то, что неудобно писать на sh, — подстановка в шаблоны проб, проверка деревьев по схеме, сравнение деревьев, круг «текст → дерево → текст».
Проверяет (подкоманды):
  fill ШАБЛОН ВЫХОД КЛЮЧ=ЗНАЧЕНИЕ…     подставляет @КЛЮЧ@ в шаблон (UTF-8, LF)
  schema СХЕМА ДЕРЕВО…                 каждое дерево валидно по схеме machine-2 (нужен пакет jsonschema)
  treeeq СТАРОЕ НОВОЕ                  деревья равны с точностью до `alula_version`, узла `primitives` и поля `named` вызова
  treesame ДЕРЕВО ДЕРЕВО               деревья равны с точностью до `title` (круг текст → дерево → текст теряет прозу, раздел 1б)
  primnames СТАРОЕ НОВОЕ               имена `primitives` нового дерева = имена старого, кроме стандартных (`time_now`, `new_id`)
  decls ТЕКСТ                          печатает объявления раздела внешних функций, по строке, пробелы сжаты
Код возврата 0 — всё в порядке; 1 — расхождения (печатаются); 2 — неверный вызов или нет предпосылки.
Не проверяет: смысл деревьев (это тесты пакета).
"""
import json
import re
import sys


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def cmd_fill(args):
    template, out = args[0], args[1]
    text = read(template)
    for pair in args[2:]:
        key, _, value = pair.partition("=")
        text = text.replace("@" + key + "@", value)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return 0


def cmd_schema(args):
    try:
        import jsonschema
    except ImportError:
        print("нет пакета jsonschema: поставьте его (pip install jsonschema)")
        return 2
    schema = json.loads(read(args[0]))
    validator = jsonschema.Draft202012Validator(schema)
    bad = 0
    for path in args[1:]:
        errors = sorted(validator.iter_errors(json.loads(read(path))), key=lambda e: list(e.absolute_path))
        if errors:
            bad += 1
            e = errors[0]
            print("%s: %s: %s" % (path, "/".join(str(p) for p in e.absolute_path), e.message[:200]))
    return 1 if bad else 0


def strip(node):
    if isinstance(node, dict):
        return {k: strip(v) for k, v in node.items() if k not in ("alula_version", "primitives", "named")}
    if isinstance(node, list):
        return [strip(x) for x in node]
    return node


def strip_title(node):
    if isinstance(node, dict):
        return {k: strip_title(v) for k, v in node.items() if k != "title"}
    if isinstance(node, list):
        return [strip_title(x) for x in node]
    return node


def first_diff(a, b, where="$"):
    if type(a) != type(b):
        return "%s: тип %s и %s" % (where, type(a).__name__, type(b).__name__)
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                return "%s.%s: есть только в новом" % (where, k)
            if k not in b:
                return "%s.%s: есть только в старом" % (where, k)
            d = first_diff(a[k], b[k], where + "." + k)
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return "%s: длина %d и %d" % (where, len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, "%s[%d]" % (where, i))
            if d:
                return d
        return None
    return None if a == b else "%s: %r и %r" % (where, a, b)


def cmd_treeeq(args):
    d = first_diff(strip(json.loads(read(args[0]))), strip(json.loads(read(args[1]))))
    if d:
        print("%s: %s" % (args[1], d))
        return 1
    return 0


def cmd_treesame(args):
    d = first_diff(strip_title(json.loads(read(args[0]))), strip_title(json.loads(read(args[1]))))
    if d:
        print("%s: %s" % (args[1], d))
        return 1
    return 0


STANDARD = ("time_now", "new_id")


def cmd_primnames(args):
    old = json.loads(read(args[0])).get("primitives", [])
    new = json.loads(read(args[1])).get("primitives", [])
    old_names = [p if isinstance(p, str) else p.get("name") for p in old if (p if isinstance(p, str) else p.get("name")) not in STANDARD]
    new_names = [p.get("name") if isinstance(p, dict) else p for p in new]
    if old_names != new_names:
        print("%s: primitives %r и %r" % (args[1], old_names, new_names))
        return 1
    return 0


def cmd_decls(args):
    lines = read(args[0]).split("\n")
    out = []
    in_section = False
    in_code = False
    for line in lines:
        if line.startswith("## "):
            in_section = line[3:].strip() in ("Внешние функции", "External functions")
            in_code = False
            continue
        if not in_section:
            continue
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code and line.strip():
            out.append(re.sub(r"\s+", " ", line.strip()))
    print("\n".join(out))
    return 0


COMMANDS = {"fill": cmd_fill, "schema": cmd_schema, "treeeq": cmd_treeeq, "treesame": cmd_treesame, "primnames": cmd_primnames, "decls": cmd_decls}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]))
