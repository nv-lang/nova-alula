# -*- coding: utf-8 -*-
"""Словарь имён Алулы для переводчика: нормативная часть словаря методики (версия 11) в файл пакета.

Формат 2.16 (AL-61, AL-62) закрепляет словарь ХЕШЕМ нормативной части: пары «русское -> английское» таблиц разделов
2.1-2.9, 2.11, 2.12, 2.16 (первые два столбца, в обратных кавычках) и записей раздела 2.10 (`русское` -> `английское`)
в порядке файла; хеш - первые 12 знаков SHA-256 строк `русское -> английское`, соединённых LF (UTF-8, без LF в конце).
Переводчик читает файл `src/machine_text/glossary_names.tsv` (строки `русское<TAB>английское`, в том же порядке) и пересчитывает
хеш при каждом переводе; другой хеш - ошибка «словарь изменён без смены формата». Формат и хеш меняются только вместе.

Использование (из корня репозитория), только стандартная библиотека:
  python scripts/glossary-names.py <state-machine-glossary.md>            пишет src/machine_text/glossary_names.tsv и печатает хеш
  python scripts/glossary-names.py <state-machine-glossary.md> --check    сверяет файл пакета с глоссарием (код возврата 1 при расхождении)
  python scripts/glossary-names.py --hash                                 печатает хеш файла пакета и сверяет его с закреплённым форматом

Глоссарий методики - чужой репозиторий, он только читается; путь к нему передаёт запускающий.
"""
import hashlib
import io
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, '..', 'src', 'machine_text', 'glossary_names.tsv')
PINNED = '60383c370415'  # формат 2.17 закрепляет хеш словаря 2.16 (спецификация, 1а, AL-62)
NORMATIVE_TABLES = ['2.%d' % i for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 16)]  # разделы-таблицы; 2.10 - записи
HEADER = ('# Normative part of the dictionary of the names of the methodology (glossary version 11, sections 2.1-2.9, 2.11, 2.12, 2.16 and the records of 2.10), '
          'in the order of the glossary: "Russian<TAB>English". The hash of the pairs is pinned by the format (AL-62); change it only with the format. '
          'Made by scripts/glossary-names.py.')


def pairs_of(text):
    """Пары нормативной части в порядке файла."""
    pairs, sec = [], None
    for line in text.replace('\r\n', '\n').split('\n'):
        m = re.match(r'^#{2,4} (\d+(?:\.\d+)*)\.? ', line)
        if m:
            sec = m.group(1)
            continue
        if sec in NORMATIVE_TABLES:
            pairs += re.findall(r'^\| `([^`]+)` \| `([^`]+)` \|', line)
        elif sec == '2.10':
            pairs += re.findall(r'`([^`]+)` → `([^`]+)`', line)
    return pairs


def hash_of(pairs):
    body = '\n'.join('%s → %s' % p for p in pairs)
    return hashlib.sha256(body.encode('utf-8')).hexdigest()[:12]


def table_text(pairs):
    return HEADER + '\n' + ''.join('%s\t%s\n' % p for p in pairs)


def read_table():
    pairs = []
    with io.open(TARGET, encoding='utf-8') as f:
        for line in f.read().split('\n'):
            if line and not line.startswith('#'):
                a, b = line.split('\t')[:2]
                pairs.append((a, b))
    return pairs


def main(argv):
    if '--hash' in argv:
        h = hash_of(read_table())
        print(h)
        return 0 if h == PINNED else 1
    paths = [a for a in argv if not a.startswith('--')]
    if len(paths) != 1:
        print(__doc__)
        return 2
    with io.open(paths[0], encoding='utf-8') as f:
        pairs = pairs_of(f.read())
    h = hash_of(pairs)
    if '--check' in argv:
        same = read_table() == pairs
        print('пар %d, хеш %s, файл пакета %s' % (len(pairs), h, 'совпадает' if same else 'ОТЛИЧАЕТСЯ'))
        return 0 if same and h == PINNED else 1
    with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
        f.write(table_text(pairs))
    print('пар %d, хеш %s%s' % (len(pairs), h, '' if h == PINNED else ' (формат закрепил %s: словарь изменён без смены формата)' % PINNED))
    return 0 if h == PINNED else 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv[1:]))
