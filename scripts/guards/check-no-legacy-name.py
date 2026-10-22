# -*- coding: utf-8 -*-
"""Страж прежнего имени: в отслеживаемых файлах и в их путях нет слова «portolan» и «Портолан».

Зачем: язык записи машин называется Алула (Alula), прежнее имя убрано одной волной и без переходного периода
    (задача 148 продукта); одно забытое имя в файле, модуле или ключе дерева возвращает путаницу двух названий,
    а читатель не поймёт, какое из них действует.
Проверяет: в каждом отслеживаемом текстовом файле (кроме двоичных по расширению) нет слова «portolan» (латиница,
    без учёта регистра, вместе с любым окончанием: `portolan_cli`, `*.portolan.md`, `portolan_version`) и слова
    «портолан» (кириллица, без учёта регистра, любое склонение); и в пути файла нет «portolan».
    Исключение одно: строка или файл с пометкой `guard-allow(legacy-name): <причина>` в строке (на этой строке) или
    `guard-fixture(legacy-name): <причина>` в любом месте файла (весь файл); пометка без причины — красный. Такие места
    есть там, где прежнее имя названо нарочно: отказ переводчика («`*.portolan.md` не читается»), тесты этого отказа,
    пометка об истории имени в README, сам страж.
Не проверяет: смысл остальных слов; файлы вне git; содержимое двоичных файлов.
Правило: задача 148 продукта (критерий AC-1), список изменений Алулы 2.14.
"""
import sys

sys.dont_write_bytecode = True

import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import guardlib  # noqa: E402

# guard-fixture(legacy-name): the guard names the two spellings it hunts for
LATIN = re.compile(r"portolan", re.IGNORECASE)
CYRILLIC = re.compile("портолан", re.IGNORECASE)


def judge(source, args, rep):
    views, counted = guardlib.judged_files(source)
    for view in views:
        if LATIN.search(view.path):
            view.report(rep, "legacy-name", None, "прежнее имя в пути файла")
        for number, line in enumerate(view.lines, 1):
            if LATIN.search(line) or CYRILLIC.search(line):
                view.report(rep, "legacy-name", number, "прежнее имя языка (Алула) в тексте")
    return guardlib.Outcome(count=counted)


if __name__ == "__main__":
    sys.exit(guardlib.run("check-no-legacy-name", "файлов на прежнее имя", judge,
                          lost="нет ни одного файла для проверки"))
