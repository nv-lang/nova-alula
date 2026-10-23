#!/usr/bin/env python3
"""Сверка структуры английской версии спецификации «Алулы» с русской.

Зачем: английский текст — перевод, нормативен русский; расхождение структуры (потерянный раздел, пропущенный блок
кода, строка каталога, метка правки) молчит, пока кто-то не прочтёт оба файла подряд.
Что проверяет, для пары `state-machine-alula-spec.md` и `state-machine-alula-spec.en.md`:
  1. одинаковые номера и порядок заголовков `## N.` и `### N.M` (номера разделов 1а и 1б — с кириллическими и латинскими буквами одинаковы);
  2. одинаковое число блоков кода (строк-ограждений из трёх обратных кавычек), и ограждения парные;
  3. одинаковое число строк-таблиц в разделе «Каталог функций» (раздел 12);
  4. одинаковый набор меток правок в тексте (AL-…, П-…, Т-…, И-…, Н-…, С-…, Р-…, А…, АМ…, ИС…, СГ…, СВ…, СЖ…, ША…, ШВ…, ШМ…, С…, E…, T…).
Чего не проверяет: смысл перевода, слова ключей в примерах (их проверяет `check-alula-keywords.py` по таблице слов), ссылки.
Самопроверка (`--selftest`): порча заголовка в копии английского файла даёт красный результат, исправный файл — зелёный;
так же проверяются порча ограждения, строки каталога и метки.
Запуск: из корня репозитория `python state-machines/check-alula-translation.py`; код возврата 1 при расхождениях.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RU = 'state-machine-alula-spec.md'
EN = 'state-machine-alula-spec.en.md'
LABEL = re.compile(r'(?<![\w`.])(?:E|T|А|АМ|ИС|СГ|СВ|СЖ|ША|ШВ|ШМ|С|AL-|[ИНПРСТ]-)\d+(?!\w)')
H2 = re.compile(r'^## (\d+[аaбb]?)\.')
H3 = re.compile(r'^### (\d+\.\d+)')


def read(name):
    return io.open(os.path.join(HERE, name), encoding='utf-8').read()


def headings(text):
    """Номера заголовков `## N.` и `### N.M` по порядку, вне блоков кода; «1а» и «1б» приведены к латинским «a» и «b»."""
    out, fenced = [], False
    for line in text.split('\n'):
        if line.startswith('```'):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = H2.match(line) or H3.match(line)
        if m:
            out.append(('##' if line.startswith('## ') else '###') + ' ' + m.group(1).replace('а', 'a').replace('б', 'b'))
    return out


def fences(text):
    return sum(1 for l in text.split('\n') if l.startswith('```'))


def catalog_rows(text):
    """Число строк-таблиц в разделе 12 «Каталог встроенных функций» (до следующего `## `)."""
    lines, n, inside, fenced = text.split('\n'), 0, False, False
    for line in lines:
        if line.startswith('```'):
            fenced = not fenced
        if fenced:
            continue
        if line.startswith('## '):
            inside = bool(H2.match(line)) and H2.match(line).group(1) == '12'
            continue
        if inside and line.startswith('|'):
            n += 1
    return n


def labels(text):
    return set(LABEL.findall(text))


def compare(ru, en):
    errs = []
    hr, he = headings(ru), headings(en)
    if hr != he:
        miss = [h for h in hr if h not in he]
        extra = [h for h in he if h not in hr]
        errs.append('заголовки: русский %d, английский %d; нет в английском: %s; лишние в английском: %s%s' % (
            len(hr), len(he), miss or '—', extra or '—', '' if (miss or extra) else '; порядок различается'))
    fr, fe = fences(ru), fences(en)
    if fr != fe:
        errs.append('блоков кода (ограждений): русский %d, английский %d' % (fr, fe))
    for name, t in ((RU, ru), (EN, en)):
        if fences(t) % 2:
            errs.append('%s: ограждения ``` непарные' % name)
    cr, ce = catalog_rows(ru), catalog_rows(en)
    if cr != ce:
        errs.append('строк-таблиц в разделе 12: русский %d, английский %d' % (cr, ce))
    lr, le = labels(ru), labels(en)
    if lr != le:
        errs.append('метки: нет в английском: %s; лишние в английском: %s' % (sorted(lr - le) or '—', sorted(le - lr) or '—'))
    return errs


def selftest(ru, en):
    bad = 0
    if compare(ru, en):
        print('самопроверка: исправный английский файл даёт расхождения — красный')
        bad += 1
    muts = []
    m = re.search(r'^## 5\. ', en, re.M)
    muts.append(('порча заголовка', en[:m.start()] + '## 6. ' + en[m.end():] if m else None))
    i = en.index('\n```')
    muts.append(('потеря ограждения', en[:i] + en[i + 4:]))
    j = en.index('| `has` |')
    k = en.index('\n', j)
    muts.append(('потеря строки каталога', en[:j] + en[k + 1:]))
    mm = LABEL.search(en)
    muts.append(('порча метки', en.replace(mm.group(0), 'Z-99') if mm else None))
    for name, text in muts:
        if text is None or not compare(ru, text):
            print('самопроверка: «%s» не замечена — красный' % name)
            bad += 1
    if bad == 0:
        print('самопроверка: исправный файл зелёный, порчи (%s) замечены' % ', '.join(n for n, _ in muts))
    return 1 if bad else 0


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ru, en = read(RU), read(EN)
    if '--selftest' in sys.argv:
        return selftest(ru, en)
    errs = compare(ru, en)
    for e in errs:
        print('ОШИБКА: ' + e)
    if not errs:
        print('структура английской версии совпадает с русской: заголовков %d, ограждений %d, строк каталога %d, меток %d' % (
            len(headings(ru)), fences(ru), catalog_rows(ru), len(labels(ru))))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
