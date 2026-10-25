#!/usr/bin/env python3
"""Сверка структуры английской версии спецификации «Алулы» с русской.

Зачем: английский текст — перевод, нормативен русский; расхождение структуры (потерянный раздел, пропущенный блок
кода, строка каталога, метка правки) молчит, пока кто-то не прочтёт оба файла подряд.
Спецификация разделена на два файла: правила языка (`spec/alula-spec.md`, `.en.md`) и журнал изменений
(`spec/alula-changelog.md`, `.en.md`: что изменилось, открытое, соответствие правилам методики). Метки правок
(`AL-NN` и прежние) живут только в журнале.
Что проверяет, для пары `spec/alula-spec.md` и `spec/alula-spec.en.md`:
  1. одинаковые номера и порядок заголовков `## N.` и `### N.M` (номера разделов 1а и 1б — с кириллическими и латинскими буквами одинаковы);
  2. одинаковое число блоков кода (строк-ограждений из трёх обратных кавычек), и ограждения парные;
  3. одинаковое число строк-таблиц в разделе «Каталог функций» (раздел 12);
  4. в спецификации нет меток правок (AL-…, П-…, Т-…, И-…, Н-…, С-…, Р-…, А…, АМ…, ИС…, СГ…, СВ…, СЖ…, ША…, ШВ…, ШМ…, С…, E…, T…;
     типовые переменные `T1`, `T2` метками не считаются) и нет ссылок на удалённые из неё разделы 0, 13, 14.
Для пары журналов `spec/alula-changelog.md` и `spec/alula-changelog.en.md` проверяет те же заголовки и ограждения
и одинаковый набор меток правок.
Чего не проверяет: смысл перевода, слова ключей в примерах (их проверяет `tools/check-alula-keywords.py` по таблице слов), ссылки.
Самопроверка (`--selftest`): порча заголовка в копии английского файла даёт красный результат, исправные файлы — зелёный;
так же проверяются порча ограждения, строки каталога, метка и ссылка на раздел 14, занесённые в спецификацию, порча метки
и заголовка в журнале.
Запуск: из корня репозитория `python tools/check-alula-translation.py` (`--selftest` — с самопроверкой); код возврата 1 при расхождениях.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # корень пакета: пути ниже считаются от него
RU = 'spec/alula-spec.md'
EN = 'spec/alula-spec.en.md'
RU_LOG = 'spec/alula-changelog.md'
EN_LOG = 'spec/alula-changelog.en.md'
LABEL = re.compile(r'(?<![\w`.])(?:E|T|А|АМ|ИС|СГ|СВ|СЖ|ША|ШВ|ШМ|С|AL-|[ИНПРСТ]-)\d+(?!\w)')
TYPE_VARS = {'T1', 'T2'}  # типовые переменные кортежа `(T1, T2)`, не метки
GONE = re.compile(r'(?:раздел\w*|[Ss]ections?)\s+(?:0|13|14)(?!\w|\.\d)')  # ссылки на разделы 0, 13, 14 (они теперь в журнале)
H2 = re.compile(r'^## (\d+[аaбb]?)\.')
H3 = re.compile(r'^### (\d+\.\d+)')


def read(name):
    return io.open(os.path.join(ROOT, name), encoding='utf-8').read()


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


def spec_labels(text):
    """Метки правок в основном тексте (типовые переменные T1, T2 не в счёт)."""
    return sorted(set(LABEL.findall(text)) - TYPE_VARS)


def gone_refs(text):
    """Ссылки вида «раздел 14» вне блоков кода (разделов 0, 13, 14 в спецификации нет)."""
    out, fenced = [], False
    for line in text.split('\n'):
        if line.startswith('```'):
            fenced = not fenced
            continue
        if not fenced:
            out += GONE.findall(line)
    return out


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
    for name, t in ((RU, ru), (EN, en)):
        sl = spec_labels(t)
        if sl:
            errs.append('%s: метки правок в спецификации (их место — журнал): %s' % (name, ', '.join(sl)))
        gr = gone_refs(t)
        if gr:
            errs.append('%s: ссылки на удалённые разделы 0, 13, 14: %s' % (name, ', '.join(sorted(set(gr)))))
    return errs


def compare_log(ru, en):
    """Журналы: заголовки `## N.`, ограждения и метки правок совпадают."""
    errs = []
    hr, he = headings(ru), headings(en)
    if hr != he:
        errs.append('журнал, заголовки: русский %s, английский %s' % (hr, he))
    fr, fe = fences(ru), fences(en)
    if fr != fe:
        errs.append('журнал, блоков кода (ограждений): русский %d, английский %d' % (fr, fe))
    for name, t in ((RU_LOG, ru), (EN_LOG, en)):
        if fences(t) % 2:
            errs.append('%s: ограждения ``` непарные' % name)
    lr, le = labels(ru), labels(en)
    if lr != le:
        errs.append('журнал, метки: нет в английском: %s; лишние в английском: %s' % (sorted(lr - le) or '—', sorted(le - lr) or '—'))
    return errs


def selftest(ru, en, lru, len_):
    bad = 0
    if compare(ru, en) or compare_log(lru, len_):
        print('самопроверка: исправные файлы дают расхождения — красный')
        bad += 1
    muts = []
    m = re.search(r'^## 5\. ', en, re.M)
    muts.append(('порча заголовка', en[:m.start()] + '## 6. ' + en[m.end():] if m else None))
    i = en.index('\n```')
    muts.append(('потеря ограждения', en[:i] + en[i + 4:]))
    j = en.index('| `has` |')
    k = en.index('\n', j)
    muts.append(('потеря строки каталога', en[:j] + en[k + 1:]))
    muts.append(('метка в спецификации', en + '\nText (AL-1).\n'))
    muts.append(('ссылка на раздел 14', en + '\nSee section 14.\n'))
    for name, text in muts:
        if text is None or not compare(ru, text):
            print('самопроверка: «%s» не замечена — красный' % name)
            bad += 1
    lmuts = []
    mm = LABEL.search(len_)
    lmuts.append(('порча метки в журнале', len_.replace(mm.group(0), 'Z-99') if mm else None))
    p = len_.index('\n## 14.')
    lmuts.append(('порча заголовка журнала', len_[:p] + '\n## 15.' + len_[p + 7:]))
    for name, text in lmuts:
        if text is None or not compare_log(lru, text):
            print('самопроверка: «%s» не замечена — красный' % name)
            bad += 1
    if bad == 0:
        print('самопроверка: исправные файлы зелёные, порчи (%s) замечены' % ', '.join(n for n, _ in muts + lmuts))
    return 1 if bad else 0


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ru, en = read(RU), read(EN)
    lru, len_ = read(RU_LOG), read(EN_LOG)
    if '--selftest' in sys.argv:
        return selftest(ru, en, lru, len_)
    errs = compare(ru, en) + compare_log(lru, len_)
    for e in errs:
        print('ОШИБКА: ' + e)
    if not errs:
        print('структура английской версии совпадает с русской: заголовков %d, ограждений %d, строк каталога %d, меток в спецификации 0; '
              'журнал: заголовков %d, ограждений %d, меток %d' % (
                  len(headings(ru)), fences(ru), catalog_rows(ru), len(headings(lru)), fences(lru), len(labels(lru))))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
