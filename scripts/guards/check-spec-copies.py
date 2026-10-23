# -*- coding: utf-8 -*-
"""Страж копий языка: то, что тесты встраивают в модули, равно первоисточнику в `spec/`.

Зачем: `embed_str` читает файл рядом с модулем, поэтому таблица слов и образцы лежат в `src/` копиями; первоисточник один — `spec/`
    (с версии 0.3.2 пакета). Копия, которая разошлась с ним молча, даёт тестам неверные слова или образец, а правда живёт в другом месте.
Проверяет: (а) `src/machine_text/alula-keywords.tsv` равна `spec/alula-keywords.tsv` (окончания строк не считаются);
    (б) три образца в `src/machine_agent/cases/` (`agent-step-methodology-222.alula.txt`, `.en.alula.txt`, `meeting-methodology-222.alula.txt`)
    равны образцам `spec/samples/` (`agent-step.alula.md`, `agent-step.en.alula.md`, `meeting-definitions.alula.md`) во всём, кроме ссылок
    вида `[текст](цель)`: копии для тестов остаются такими, какими образцы вышли из методики (их хеши закреплены тестами), а ссылки в `spec/samples/`
    переписаны под файлы пакета.
Не проверяет: смысл слов и образцов (это тесты и `tools/check-alula-*.py`); остальные файлы `cases/`.
Правило: задача 155 продукта (переезд первоисточника языка в пакет).

Пометок-исключений у этого стража нет.
"""
import sys

sys.dont_write_bytecode = True

import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import guardlib  # noqa: E402

LINK = re.compile(r'\[(?:[^\[\]]|\[[^\]]*\])*\]\([^)\s]*(?:\s+"[^"]*")?\)')

# (копия, первоисточник, сравнивать ли без ссылок)
PAIRS = [
    ("src/machine_text/alula-keywords.tsv", "spec/alula-keywords.tsv", False),
    ("src/machine_agent/cases/agent-step-methodology-222.alula.txt", "spec/samples/agent-step.alula.md", True),
    ("src/machine_agent/cases/agent-step-methodology-222.en.alula.txt", "spec/samples/agent-step.en.alula.md", True),
    ("src/machine_agent/cases/meeting-methodology-222.alula.txt", "spec/samples/meeting-definitions.alula.md", True),
]


def normal(data, without_links):
    text = data.decode("utf-8", "replace").replace("\r\n", "\n")
    return LINK.sub("[]()", text) if without_links else text


def judge(source, args, rep):
    by_path = dict((e.path, e) for e in source.entries())
    count = 0
    for copy, origin, without_links in PAIRS:
        missing = [p for p in (copy, origin) if p not in by_path]
        if missing:
            rep.add(missing[0], None, "no-file", "нет файла пары копия/первоисточник: %s и %s" % (copy, origin))
            continue
        a = source.read(by_path[copy])
        b = source.read(by_path[origin])
        count += 1
        if a is None or b is None:
            rep.add(copy, None, "no-file", "файл пары не прочитан")
            continue
        x, y = normal(a, without_links).split("\n"), normal(b, without_links).split("\n")
        if x == y:
            continue
        first = next((i for i in range(min(len(x), len(y))) if x[i] != y[i]), min(len(x), len(y)))
        rep.add(copy, first + 1, "copy-differs", "копия расходится с %s (первая разница на строке %d)%s" % (
            origin, first + 1, ", ссылки не считаются" if without_links else ""))
    return guardlib.Outcome(count=count)


if __name__ == "__main__":
    sys.exit(guardlib.run("check-spec-copies", "пар копия/первоисточник", judge,
                          lost="нет ни одной пары копия/первоисточник"))
