# -*- coding: utf-8 -*-
"""Страж меток обходов дефектов Oracle: метка в коде ведёт к пункту README, индекс не врёт.

Зачем: обход дефекта компилятора, который нигде не назван, остаётся в коде навсегда: когда Нова
    исправит пункт, никто не найдёт места, где можно упростить. Метка `ORACLE-WORKAROUND(N): ...` и
    индекс «пункт -> места» делают чистку делом одной команды, но только если метки правильные, ведут
    к настоящим пунктам и индекс не отстал от них.
Проверяет: (а) каждая метка имеет вид `ORACLE-WORKAROUND(N[, M]...): текст` с непустым текстом после
    двоеточия; (б) каждый N есть пунктом в spikes/env/README.md (строка `N. ...`); (в) индекс
    spikes/env/workarounds.md есть и равен тому, что пишет `python scripts/oracle-workarounds.py --index`;
    (г) метка стоит в комментарии (`//`, `#`, `<!--`), а не в строке данных; в .md меткой считается только
    строка с `<!--` перед ней, проза о метках в README модулей не метка; (д) предупреждение, не ошибка:
    пункт README с пометкой «worked round in the code» в тексте и без единой метки в коде. Метки ищутся в
    отслеживаемых файлах src/, scripts/ и spikes/ (кроме README пунктов, индекса, стражей и самого
    скрипта); README без единого пункта - красный (мишень потеряна).
Не проверяет: смысл текста метки и то, что обход правда есть в коде (это приёмка по diff); что каждый
    обход помечен (это делает задача, поставившая метки, и просмотр diff); метки вне src/, scripts/ и
    spikes/ (плагин, doc/).
Правило: spikes/env/README.md, раздел «Marks of the workarounds»; задача 118.

Пометок-исключений у этого стража нет.
"""
import sys

sys.dont_write_bytecode = True

import importlib.util
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import guardlib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "oracle-workarounds.py")


def load_script():
    spec = importlib.util.spec_from_file_location("oracle_workarounds", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def judge(source, args, rep):
    ow = load_script()
    by_path = dict((e.path, e) for e in source.entries())

    def read_text(path):
        entry = by_path.get(path)
        if entry is None:
            return None
        data = source.read(entry)
        return None if data is None else data.decode("utf-8", "replace").lstrip("﻿")

    readme = read_text(ow.README)
    items = ow.parse_items(readme) if readme is not None else {}
    marks = []
    for path in sorted(by_path):
        entry = by_path[path]
        if entry.mode == "160000" or not ow.is_scanned(path):
            continue
        text = read_text(path)
        if text is not None and ow.MARK in text:
            marks.extend(ow.scan_text(path, text))

    if readme is not None and not items:
        rep.add(ow.README, None, "no-items", "в README нет ни одного пункта вида `N. текст`: формат изменился или файл не тот")
    for mark in marks:
        where = (mark["path"], mark["line"])
        if mark["error"]:
            rep.add(where[0], where[1], mark["error"][0], mark["error"][1])
            continue
        for number in mark["items"]:
            if number not in items:
                rep.add(where[0], where[1], "unknown-item",
                        "пункта %d нет в %s: заведите пункт (с воспроизведением) или поправьте номер" % (number, ow.README))

    if marks or items:
        expected = ow.render_index(items, marks)
        actual = read_text(ow.INDEX)
        if actual is None:
            if items:
                rep.add(ow.INDEX, None, "index-missing",
                        "нет индекса: выполните `python scripts/oracle-workarounds.py --index`")
        elif actual.replace("\r\n", "\n") != expected:
            rep.add(ow.INDEX, None, "index-stale",
                    "индекс не совпадает с метками и пунктами: выполните `python scripts/oracle-workarounds.py --index`")

    by_item = ow.count_by_item(marks)
    for number in sorted(items):
        if ow.WORKED_ROUND in items[number]["block"].lower() and number not in by_item:
            rep.accept(ow.README, items[number]["line"], "no-mark",
                       "предупреждение: пункт %d назван «%s», а метки в коде нет" % (number, ow.WORKED_ROUND))

    if not marks and not items:
        return guardlib.Outcome(nothing="нет ни пунктов в README, ни меток в коде")
    return guardlib.Outcome(count=len(marks) + len(items))


if __name__ == "__main__":
    sys.exit(guardlib.run("check-oracle-workarounds", "меток и пунктов README", judge,
                          lost="нет ни меток, ни пунктов README"))
