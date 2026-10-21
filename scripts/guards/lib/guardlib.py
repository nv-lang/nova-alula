# -*- coding: utf-8 -*-
"""Общая библиотека стражей репозитория: источники содержимого, вердикты, пометки.

Зачем: у всех стражей один договор вызова и одни формы вердикта; разнесённый по стражам, он
    расходился бы (одна форма «ок», другая «OK», разный код возврата), и общий запуск не смог бы
    их сосчитать.
Проверяет: ничего сам не проверяет; даёт стражам Source (рабочая копия, индекс, коммит), охват
    текстовых файлов (judged_files, BINARY_EXT), четыре формы вердикта, пометки с причиной
    (guard-allow, guard-fixture), добавленные в индексе строки файла (Source.added_lines), разбор
    аргументов и запуск.
Не проверяет: содержимое файлов (это дело стражей) и ничего не читает из среды, кроме git.
Правило: AGENTS.md п.15 (приватные данные) и ADR-0006 (публичный репозиторий) держат стражи;
    сама библиотека правила не держит.

Договор стража: <страж> [--root <папка>] [--index | --commit <хеш>] [--ci]. Источник по умолчанию
рабочая копия и список git ls-files; --index — индекс (с --only git подставляет временный индекс
через GIT_INDEX_FILE, вызовы git его соблюдают); --commit — файлы, изменённые коммитом, и их
содержимое из дерева коммита. Вердикт — последняя строка вывода: «ок: осмотрено N <мишень>»,
«судить нечего: <причина>», «пропущено: <причина>» или «FAIL: ...» (код 1).
"""
import sys

sys.dont_write_bytecode = True

import argparse
import collections
import os
import re
import subprocess

# Расширения файлов, которые не читаются как текст. Определению git «бинарный по содержимому»
# не доверяем: файл вне списка с байтом NUL или BOM UTF-16 судит страж текста.
BINARY_EXT = frozenset((
    "png", "jpg", "jpeg", "gif", "webp", "ico", "bmp", "pdf", "zip", "gz", "tgz", "7z",
    "woff", "woff2", "ttf", "otf", "eot", "mp3", "mp4", "mov", "webm", "wasm",
))

Entry = collections.namedtuple("Entry", "path mode oid")

ALLOW_RE = re.compile(r"guard-allow\(([a-z0-9-]+)\):[ \t]*(.*)")
COMMENT_END = re.compile(r"\s*(-->|\*/)\s*$")
FIXTURE_RE = re.compile(r"guard-fixture\(([a-z0-9-]+)\):[ \t]*(.*)")
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


class Unavailable(Exception):
    """Предпосылка не выполнена (нет git, списка, интерпретатора): красный, а не пропуск."""


def setup_io():
    """stdout и stderr — UTF-8 с LF: вывод не зависит от локали и платформы."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass


def git(root, *args, **kw):
    """Запуск git в корне; возвращает байты stdout. check=False — не поднимать при коде != 0."""
    check = kw.get("check", True)
    try:
        proc = subprocess.run(("git",) + args, cwd=root, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    except OSError as exc:
        raise Unavailable("git не запускается (%s)" % exc.__class__.__name__)
    if check and proc.returncode != 0:
        msg = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        raise Unavailable("git %s: %s" % (args[0], msg[-1] if msg else "код %d" % proc.returncode))
    return proc.stdout


def _norm(path):
    return os.path.normcase(os.path.realpath(path))


def find_root(arg_root):
    """Корень репозитория: --root или git rev-parse --show-toplevel."""
    if arg_root:
        root = os.path.abspath(arg_root)
        if not os.path.isdir(root):
            raise Unavailable("нет папки %s" % os.path.basename(root))
        top = git(root, "rev-parse", "--show-toplevel", check=False)
        top = top.decode("utf-8", "replace").strip()
        if not top or _norm(top) != _norm(root):
            raise Unavailable("%s не корень репозитория git" % (os.path.basename(root) or "папка"))
        return root
    top = git(os.getcwd(), "rev-parse", "--show-toplevel").decode("utf-8", "replace").strip()
    if not top:
        raise Unavailable("не удалось найти корень репозитория git")
    return top


class _Batch(object):
    """Один процесс git cat-file --batch на все чтения блобов."""

    def __init__(self, root):
        try:
            self.proc = subprocess.Popen(("git", "cat-file", "--batch"), cwd=root,
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL)
        except OSError as exc:
            raise Unavailable("git не запускается (%s)" % exc.__class__.__name__)

    def get(self, oid):
        self.proc.stdin.write(oid.encode("ascii") + b"\n")
        self.proc.stdin.flush()
        head = self.proc.stdout.readline().split()
        if len(head) < 3 or head[1] == b"missing":
            return None
        size = int(head[2])
        data = self.proc.stdout.read(size)
        self.proc.stdout.read(1)
        return data

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


class Source(object):
    """Содержимое, которое судит страж: рабочая копия, индекс или коммит."""

    def __init__(self, root, mode="tree", commit=None):
        self.root = root
        self.mode = mode
        self.commit = commit
        self._batch = None
        self._entries = None
        self._changed = None

    # -- списки путей ------------------------------------------------------------------------
    def entries(self):
        """Все пути источника (для проверки существования цели ссылки)."""
        if self._entries is None:
            items = []
            if self.mode == "commit":
                raw = git(self.root, "ls-tree", "-r", "-z", "--full-tree", self.commit)
                for rec in raw.split(b"\0"):
                    if not rec:
                        continue
                    meta, _, path = rec.partition(b"\t")
                    parts = meta.split()
                    items.append(Entry(path.decode("utf-8", "replace"), parts[0].decode(),
                                       parts[2].decode()))
            else:
                raw = git(self.root, "ls-files", "-s", "-z")
                seen = set()
                for rec in raw.split(b"\0"):
                    if not rec:
                        continue
                    meta, _, path = rec.partition(b"\t")
                    parts = meta.split()
                    name = path.decode("utf-8", "replace")
                    if name in seen:
                        continue
                    seen.add(name)
                    items.append(Entry(name, parts[0].decode(), parts[1].decode()))
            self._entries = items
        return self._entries

    def paths(self):
        return set(e.path for e in self.entries())

    def changed(self):
        """Файлы, которые судят: для коммита — изменённые им (ACMR), иначе все пути."""
        if self.mode != "commit":
            return list(self.entries())
        if self._changed is None:
            raw = git(self.root, "diff-tree", "-r", "-z", "--root", "-m", "--no-commit-id",
                      "--diff-filter=ACMR", self.commit)
            toks = raw.split(b"\0")
            wanted = set()
            i = 0
            while i < len(toks):
                if toks[i].startswith(b":") and i + 1 < len(toks):
                    wanted.add(toks[i + 1].decode("utf-8", "replace"))
                    i += 2
                else:
                    i += 1
            by_path = dict((e.path, e) for e in self.entries())
            self._changed = [by_path[p] for p in sorted(wanted) if p in by_path]
        return self._changed

    # -- добавленные строки ------------------------------------------------------------------
    def added_lines(self, path):
        """Добавленные в индексе строки файла: список (номер строки в индексе, текст).

        Только в режиме индекса и только для файла, который уже есть в HEAD: первая версия файла
        целиком «добавлена» и этим понятием не судится. В режимах дерева и коммита, для файла не из
        HEAD и в репозитории без коммитов — None (не пустой список: «не определено» не то же, что
        «ничего не добавлено»). Строки берутся из `git diff --cached -U0 --no-renames`, поэтому
        временный индекс (GIT_INDEX_FILE) соблюдается; возврат каретки в конце строки сохраняется.
        """
        if self.mode != "index":
            return None
        known = git(self.root, "rev-parse", "--verify", "--quiet", "HEAD:" + path, check=False)
        if not known.strip():
            return None
        raw = git(self.root, "diff", "--cached", "-U0", "--no-renames", "--text", "--no-color",
                  "--", path).decode("utf-8", "replace")
        out = []
        number = None
        for line in raw.split("\n"):
            m = HUNK_RE.match(line)
            if m:
                number = int(m.group(1))
            elif number is not None and line.startswith("+"):
                out.append((number, line[1:]))
                number += 1
        return out

    # -- чтение ------------------------------------------------------------------------------
    def read(self, entry):
        """Байты файла или None, если файла нет (удалён из рабочей копии)."""
        if self.mode == "tree" and entry.mode != "120000":
            try:
                with open(os.path.join(self.root, entry.path), "rb") as handle:
                    return handle.read()
            except OSError:
                return None
        if self._batch is None:
            self._batch = _Batch(self.root)
        return self._batch.get(entry.oid)

    def close(self):
        if self._batch is not None:
            self._batch.close()
            self._batch = None


FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")


def strip_fenced(text):
    """Только огороженные блоки кода заменены пробелами (встроенный код в заголовках остаётся)."""
    out = []
    fence = None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if fence is None:
            if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
                fence = (m.group(2)[0], len(m.group(2)))
                out.append("")
            else:
                out.append(line)
        else:
            out.append("")
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= fence[1] and not m.group(3).strip():
                fence = None
    return "\n".join(out)


# -- пометки ----------------------------------------------------------------------------------
def _reason(text):
    """Причина пометки без закрывающих знаков комментария."""
    return COMMENT_END.sub("", text).strip()


class FileView(object):
    """Файл источника: байты, текст, строки и пометки с причиной."""

    def __init__(self, path, data):
        self.path = path
        self.data = data
        self.text = data.decode("utf-8", "replace")
        self.lines = self.text.split("\n")
        self._allow = {}
        self.fixture = {}
        for number, line in enumerate(self.lines, 1):
            for m in ALLOW_RE.finditer(line):
                self._allow.setdefault(number, {})[m.group(1)] = _reason(m.group(2))
            for m in FIXTURE_RE.finditer(line):
                self.fixture[m.group(1)] = _reason(m.group(2))

    def report(self, rep, rule, line, desc):
        """Нарушение правила; снимается пометкой с причиной, пометка без причины — красный."""
        reason = None
        if line is not None and rule in self._allow.get(line, {}):
            reason = self._allow[line][rule]
        elif rule in self.fixture:
            reason = self.fixture[rule]
        if reason is None:
            rep.add(self.path, line, rule, desc)
        elif reason == "":
            rep.add(self.path, line, rule, "пометка без причины: " + desc)
        else:
            rep.accept(self.path, line, rule, reason)


def judged_files(source):
    """Тексты, которые судят стражи приватности и текста; возвращает (файлы, число осмотренных).

    Все пути источника, кроме подмодулей (режим 160000: учитываются в числе, не читаются) и
    файлов с расширением из BINARY_EXT. Файл без расширения и с неизвестным расширением судится.
    """
    views = []
    counted = 0
    for entry in source.changed():
        if entry.mode == "160000":
            counted += 1
            continue
        name = entry.path.rsplit("/", 1)[-1]
        ext = name.rsplit(".", 1)[-1].lower() if "." in name.lstrip(".") else ""
        if ext in BINARY_EXT:
            continue
        data = source.read(entry)
        if data is None:
            continue
        views.append(FileView(entry.path, data))
        counted += 1
    return views, counted


# -- вердикты и отчёт --------------------------------------------------------------------------
class Report(object):
    def __init__(self):
        self.findings = []
        self.accepted = []

    def add(self, path, line, rule, desc):
        self.findings.append((path, line, rule, desc))

    def accept(self, path, line, rule, reason):
        self.accepted.append((path, line, rule, reason))

    def lines(self):
        out = []
        for path, line, rule, reason in self.accepted:
            out.append("принято %s: %s: %s" % (_where(path, line), rule, reason))
        for path, line, rule, desc in self.findings:
            out.append("FAIL %s: %s: %s" % (_where(path, line), rule, desc))
        return out


def _where(path, line):
    return "%s:%d" % (path, line) if line is not None else path


def ok(count, target):
    return "ок: осмотрено %d %s" % (count, target)


def nothing_to_judge(reason):
    return "судить нечего: " + reason


def skipped(reason):
    return "пропущено: " + reason


def fail(guard, count):
    return "FAIL: %s: %d нарушений" % (guard, count)


def no_target(what):
    """Пустота не бывает чистой: мишень стража исчезла."""
    return "FAIL: мишень потеряна: " + what


class Outcome(object):
    """Итог judge(): число осмотренного, либо «судить нечего» / «пропущено» с причиной."""

    def __init__(self, count=0, nothing=None, skip=None):
        self.count = count
        self.nothing = nothing
        self.skip = skip


def build_parser(extra=None, prog=None):
    parser = argparse.ArgumentParser(prog=prog, add_help=True)
    parser.add_argument("--root")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--index", action="store_true")
    group.add_argument("--commit")
    parser.add_argument("--ci", action="store_true")
    if extra:
        extra(parser)
    return parser


def open_source(args):
    root = find_root(args.root)
    if args.commit:
        git(root, "rev-parse", "--verify", "--quiet", args.commit + "^{commit}")
        return Source(root, "commit", args.commit)
    return Source(root, "index" if args.index else "tree")


def finish(lines, verdict, code):
    """Печать и код возврата: код решён до печати."""
    try:
        sys.stdout.write("\n".join(lines + [verdict]) + "\n")
        sys.stdout.flush()
    except Exception:
        pass
    return code


def run(guard, target, judge, argv=None, extra=None, lost="нет ни одного файла для проверки"):
    """Общий запуск стража дерева: judge(source, args, report) -> Outcome | число осмотренного."""
    setup_io()
    args = build_parser(extra, guard).parse_args(argv)
    rep = Report()
    try:
        source = open_source(args)
    except Unavailable as exc:
        return finish([], "FAIL: предпосылка: %s" % exc, 1)
    try:
        try:
            result = judge(source, args, rep)
        finally:
            source.close()
    except Unavailable as exc:
        return finish(rep.lines(), "FAIL: предпосылка: %s" % exc, 1)
    if not isinstance(result, Outcome):
        result = Outcome(count=result)
    lines = rep.lines()
    if rep.findings:
        return finish(lines, fail(guard, len(rep.findings)), 1)
    if result.skip:
        return finish(lines, skipped(result.skip), 0)
    if result.nothing:
        return finish(lines, nothing_to_judge(result.nothing), 0)
    if result.count <= 0 and source.mode == "commit":
        return finish(lines, nothing_to_judge("коммит не меняет файлов этой мишени"), 0)
    if result.count <= 0:
        return finish(lines, no_target(lost), 1)
    return finish(lines, ok(result.count, target), 0)
