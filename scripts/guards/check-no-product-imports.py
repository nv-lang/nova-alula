# -*- coding: utf-8 -*-
"""Страж границы пакета: в ядре языка нет ни импорта продукта, ни его имени пакета.

Зачем: ядро (пакет `alula`) выносится из продукта CrewHarness и обязано собираться без него; один
    забытый `import crew_harness.*` возвращает зависимость, о которой узнают только при сборке в
    чужом репозитории.
Проверяет: в отслеживаемых файлах `.nv` и `nova.toml` нет слова `crew_harness` (имя пакета продукта:
    `module crew_harness.x`, `import crew_harness.x`, зависимость в `nova.toml`) и нет импорта модулей
    продукта по их прежним корням (`acp`, `chat`, `storage`, `server`, `pg*`, `web`) из пакета.
    `--prefix <путь>` (можно повторять) ограничивает проверку путями с этим началом: так страж
    запускают на дереве продукта, чтобы показать красное до выноса.
Не проверяет: тексты README и документы (они вправе называть продукт, откуда ядро вынесено); смысл
    зависимостей от других пакетов; приватные имена (это дело стража приватности продукта).
Правило: задача 144 продукта, критерий AC-3.

Пометок-исключений у этого стража нет.
"""
import sys

sys.dont_write_bytecode = True

import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import guardlib  # noqa: E402

PRODUCT_NAME = re.compile(r"\bcrew_harness\b")
PRODUCT_ROOTS = re.compile(r"^\s*import\s+(?:acp|acp_live|chat|storage|server|server_live|server_pg|pgconf|pgdb|pgstore|web)\b")


def extra(parser):
    parser.add_argument("--prefix", action="append", default=[])


def judge(source, args, rep):
    count = 0
    for entry in source.changed():
        name = entry.path.rsplit("/", 1)[-1]
        if entry.mode == "160000" or not (name.endswith(".nv") or name == "nova.toml"):
            continue
        if args.prefix and not any(entry.path.startswith(p) for p in args.prefix):
            continue
        data = source.read(entry)
        if data is None:
            continue
        count += 1
        for number, line in enumerate(data.decode("utf-8", "replace").split("\n"), 1):
            if PRODUCT_NAME.search(line):
                rep.add(entry.path, number, "product-name", "имя пакета продукта `crew_harness` в ядре")
            elif PRODUCT_ROOTS.match(line):
                rep.add(entry.path, number, "product-import", "импорт модуля продукта в ядре")
    return guardlib.Outcome(count=count)


if __name__ == "__main__":
    sys.exit(guardlib.run("check-no-product-imports", "файлов .nv и nova.toml", judge, extra=extra,
                          lost="нет ни одного .nv или nova.toml для проверки"))
