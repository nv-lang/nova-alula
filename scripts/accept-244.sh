#!/bin/sh
# Зачем: одна команда-критерий задачи 244 «Алула 0.27, поток П1: пакет nova-alula 0.27.0» (язык 0.27, AL-144…AL-147).
# Проверяет: (1) `alula version` печатает `alula 0.27.0 (Алула 0.27)` (ни machine/2, ни machine_version), nova.toml — 0.27.0;
#     (2) спецификация: spec/alula-spec*.md и spec/alula-changelog*.md — CRLF, alula-keywords.tsv — копия в src/machine_text/; ALULA_SPEC_SOURCE=<папка> (необязательно) —
#         тексты равны текстам методики (с точностью до концов строк); метки AL-144…AL-147 в журнале; блок «Пауза» раздела 9 — хеши файлов libs/;
#     (3) библиотеки: libs/ — файлы методики 0.27 (Пауза ru 87162f9feb8c, en 429adaba4cec; арифметика_цикла ru 34ef3ee7c00b, en 95c29f6d64ac), копии в examples/libs/ и
#         spec/samples/libs/ (какие там есть; Пауза — обязательно) равны libs/; ALULA_LIBS_SOURCE=<папка> (необязательно) — равны файлам методики побайтно;
#     (4) tools/check-alula-keywords.py — зелёный (таблица слов и образец синхронизированы);
#     (5) образцы пакета (examples, spec/samples, libs) — в форме 0.27: шапка `revision`/`alula_version`, ни `machine_version`, ни `format:`, ни единого `## Требует`,
#         сторона `machine` без скобок; деревья — `"kind": "machine"`, `alula_version` 0.27, `revision`; тесты — `"kind": "test"`;
#         `tools/migrate-alula-227.py --dry-run` на них — «файлов 0, мест 0»;
#     (6) `alula test examples` — все; наборы машин ALULA_METHODOLOGY_MACHINES / ALULA_PRODUCT_MACHINES (необязательно) — копия переносится скриптом, `alula test` — все;
#     (7) `nova test` всех папок пакета с тестами (по одной, `--jobs 2`); стражи дерева.
# Не проверяет: публикацию пакета (метка v0.27.0 — по слову владельца); таблицу «программа ↔ формат» в README (отложена владельцем); правку наборов машин в их репозиториях.
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git.
# Использование: sh scripts/accept-244.sh   (из корня дерева пакета; последняя строка «ПРИНЯТО 244: …» и код 0, иначе «НЕ ПРИНЯТО 244 …» и код 1)
#   ALULA=<путь>                       готовая программа alula вместо сборки в target/alula.exe
#   ALULA_SPEC_SOURCE=<папка>          тексты спецификации методики 0.27 (alula-spec.md, .en.md, alula-changelog.md, .en.md, alula-keywords.tsv)
#   ALULA_LIBS_SOURCE=<папка>          файлы библиотек методики 0.27 (pause*.alula.md, cycle_arithmetic*.alula.md)
#   ALULA_METHODOLOGY_MACHINES=<папка> набор машин методики; ALULA_PRODUCT_MACHINES=<папка> набор машин продукта (без них шаги пропускаются)
#   ACCEPT_244_SKIP_NOVA_TEST=1        пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: слово владельца, 2026-10-28: «делай обновление-улучшение, супер быстро» (чат методики; задание 244 интегратора).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2
export PYTHONUTF8=1

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 244: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }
migrate="$PYTHON tools/migrate-alula-227.py"

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 244: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 244: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

tests_of() { "$alula" test "$1" 2>&1 | tail -1 | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1 \2/p'; }

# ---- (1) версия ---------------------------------------------------------------------------------------------------------------------------------

echo "== alula version"
want_version="alula 0.27.0 (Алула 0.27)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.27.0"' nova.toml || red "nova.toml: version не 0.27.0"

# ---- (2), (3) спецификация и библиотеки -----------------------------------------------------------------------------------------------------------

echo "== спецификация и библиотеки"
"$PYTHON" - "${ALULA_SPEC_SOURCE:-}" "${ALULA_LIBS_SOURCE:-}" <<'EOF' >"$tmp/texts.out" 2>&1 || { red "спецификация и библиотеки"; cat "$tmp/texts.out"; }
import importlib.util, os, re, sys
spec = importlib.util.spec_from_file_location('m', 'tools/migrate-alula-226.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bad = 0
def no(why):
    global bad; bad += 1; print(why)
spec_src, libs_src = sys.argv[1], sys.argv[2]
for f in ['alula-spec.md', 'alula-spec.en.md', 'alula-changelog.md', 'alula-changelog.en.md']:
    raw = open('spec/' + f, 'rb').read()
    if raw.count(b'\n') != raw.count(b'\r\n'): no('spec/%s: не CRLF' % f)
    if spec_src and open(os.path.join(spec_src, f), 'rb').read().replace(b'\r\n', b'\n') != raw.replace(b'\r\n', b'\n'): no('spec/%s не равен тексту методики' % f)
kw = open('spec/alula-keywords.tsv', 'rb').read()
if spec_src and open(os.path.join(spec_src, 'alula-keywords.tsv'), 'rb').read() != kw: no('spec/alula-keywords.tsv не равен тексту методики')
if open('src/machine_text/alula-keywords.tsv', 'rb').read().replace(b'\r\n', b'\n') != kw.replace(b'\r\n', b'\n'): no('src/machine_text/alula-keywords.tsv не равен spec/alula-keywords.tsv')
log = open('spec/alula-changelog.md', encoding='utf-8').read()
for mark in ['AL-144', 'AL-145', 'AL-146', 'AL-147']:
    if mark not in log: no('spec/alula-changelog.md: нет метки %s' % mark)
want = {'pause.alula.md': '87162f9feb8c', 'pause.en.alula.md': '429adaba4cec', 'cycle_arithmetic.alula.md': '34ef3ee7c00b', 'cycle_arithmetic.en.alula.md': '95c29f6d64ac'}
for f, h in want.items():
    text = open('libs/' + f, encoding='utf-8').read()
    if m.lib_hash(text) != h: no('libs/%s: хеш %s, методика ждёт %s' % (f, m.lib_hash(text), h))
    if '- alula_version: 0.27' not in text: no('libs/%s: нет строки alula_version: 0.27' % f)
    for copy in ['examples/libs/' + f, 'spec/samples/libs/' + f]:
        if not os.path.exists(copy):
            if f.startswith('pause'): no('нет копии %s' % copy)
        elif open(copy, 'rb').read() != open('libs/' + f, 'rb').read(): no('%s не равен libs/%s' % (copy, f))
    if libs_src and open(os.path.join(libs_src, f), 'rb').read() != open('libs/' + f, 'rb').read(): no('libs/%s не равен файлу методики' % f)
for f, head, h in [('spec/alula-spec.md', '# Библиотека: Пауза', '87162f9feb8c'), ('spec/alula-spec.en.md', '# Library: Pause', '429adaba4cec')]:
    text = open(f, encoding='utf-8').read().replace('\r\n', '\n')
    blk = re.search(r'^````\n(' + re.escape(head) + r'\n.*?)^````$', text, re.S | re.M)
    if not blk: no('%s: нет блока «%s»' % (f, head))
    elif m.lib_hash(blk.group(1)) != h: no('%s: хеш блока %s, нужно %s' % (f, m.lib_hash(blk.group(1)), h))
sys.exit(1 if bad else 0)
EOF

# ---- (4) таблица слов ---------------------------------------------------------------------------------------------------------------------------

echo "== check-alula-keywords.py"
"$PYTHON" tools/check-alula-keywords.py >"$tmp/kw.out" 2>&1 || { red "check-alula-keywords.py"; tail -8 "$tmp/kw.out"; }
grep -q 'Требует данные' tools/check-alula-keywords.py && grep -q 'Requires parties' tools/check-alula-keywords.py && grep -q 'Требует концы' tools/check-alula-keywords.py \
  || red "check-alula-keywords.py: нет слов разделов AL-145"

# ---- (5) образцы пакета в форме 0.27 --------------------------------------------------------------------------------------------------------------

echo "== образцы 0.27"
"$PYTHON" - <<'EOF' >"$tmp/forms.out" 2>&1 || { red "образцы пакета не в форме 0.27"; head -20 "$tmp/forms.out"; }
import glob, json, re, sys
bad = 0
def no(why):
    global bad; bad += 1; print(why)
md = glob.glob('examples/**/*.alula.md', recursive=True) + glob.glob('spec/samples/**/*.alula.md', recursive=True) + glob.glob('libs/*.alula.md')
for f in md:
    head = []
    for l in open(f, encoding='utf-8').read().split('\n'):
        if l.startswith('## '): break
        head.append(l)
    h = '\n'.join(head)
    if re.search(r'^- (machine_version|format):', h, re.M): no('%s: старая шапка (machine_version/format)' % f)
    if not re.search(r'^- alula_version: 2\.27$', h, re.M): no('%s: нет alula_version: 0.27' % f)
    text = open(f, encoding='utf-8').read()
    if re.search(r'^## (Требует|Requires)\s*$', text, re.M): no('%s: единый раздел Требует' % f)
    if re.search(r'\| machine \S+\((вход|input) ', text): no('%s: сторона machine со скобками' % f)
for f in glob.glob('examples/**/*.alula.json', recursive=True):
    root = json.load(open(f, encoding='utf-8'))
    if root.get('kind') != 'machine' or root.get('alula_version') != '0.27' or 'format' in root or 'version' in root or not isinstance(root.get('revision'), int):
        no('%s: корень дерева не 0.27 (kind, alula_version, revision)' % f)
for f in glob.glob('examples/**/*.alula.test.json', recursive=True):
    root = json.load(open(f, encoding='utf-8'))
    if root.get('kind') != 'test' or 'format' in root: no('%s: корень теста не kind: test' % f)
sys.exit(1 if bad else 0)
EOF
dry=$($migrate --dry-run examples spec/samples libs 2>&1 | tail -1)
[ "$dry" = "итог: файлов 0, мест 0" ] || red "migrate-alula-227.py --dry-run на образцах пакета: $dry"

# ---- (6) examples и наборы машин --------------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
set -- $(tests_of examples)
if [ "${1:-0}" = "${2:-x}" ] && [ "${1:-0}" -gt 0 ]; then ex_line="examples $1 из $2"; else ex_line="examples ${1:-?} из ${2:-?}"; red "alula test examples: $ex_line"; fi
"$PYTHON" tools/check-alula-samples.py >"$tmp/samples.out" 2>&1 || { red "check-alula-samples.py"; tail -5 "$tmp/samples.out"; }
"$PYTHON" tools/check-alula-translation.py >"$tmp/translation.out" 2>&1 || { red "check-alula-translation.py"; tail -5 "$tmp/translation.out"; }

set_check() {
  if [ -z "$2" ]; then eval "set_$1=\"не задан\""; return; fi
  [ -d "$2" ] || { red "набор $1: нет папки $2"; return; }
  mkdir -p "$tmp/$1" && cp -r "$2/." "$tmp/$1/"
  $migrate --alula "$alula" "$tmp/$1" >"$tmp/$1.mig" 2>&1; mig_code=$?
  grep -v '^перенесён' "$tmp/$1.mig" | sed "s|$tmp/||" | sed "s/^/  $1: /"
  set -- "$1" $(tests_of "$tmp/$1")
  if [ "$mig_code" = 0 ] && [ -n "${2:-}" ] && [ "${2:-0}" = "${3:-x}" ]; then eval "set_$1=\"$2 из $3\""; else red "набор $1: миграция код $mig_code, alula test ${2:-?} из ${3:-?}"; eval "set_$1=\"${2:-?} из ${3:-?}\""; fi
}
set_methodology="?"; set_product="?"
echo "== наборы машин"
set_check methodology "${ALULA_METHODOLOGY_MACHINES:-}"
set_check product "${ALULA_PRODUCT_MACHINES:-}"

# ---- (7) nova test, стражи ------------------------------------------------------------------------------------------------------------------------

if [ "${ACCEPT_244_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_244_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 244: nova не в PATH"; exit 2; }
  n_dirs=0; n_dirs_ok=0
  for d in src/*/; do
    dir=$(basename "$d")
    ls "$d"*_test.nv >/dev/null 2>&1 || continue
    echo "== nova test src/$dir"
    t_full=$(nova test "src/$dir" --jobs 2 --timeout 900 2>&1)
    t_fail=$(echo "$t_full" | tail -3 | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\2/p' | tail -1)
    t_fail=${t_fail:-1}
    n_dirs=$((n_dirs + 1))
    if [ "$t_fail" = 0 ]; then n_dirs_ok=$((n_dirs_ok + 1)); else red "nova test src/$dir: $t_fail красных"; echo "$t_full" | grep -a "FAIL\|TIMEOUT\|error" | head -4 | cut -c1-600; fi
    sleep 5
  done
  test_line="nova test $n_dirs_ok из $n_dirs"
fi

echo "== стражи дерева"
sh scripts/guards/run-all.sh >"$tmp/guards.out" 2>&1 || { red "scripts/guards/run-all.sh"; tail -8 "$tmp/guards.out"; }

summary="$want_version; $ex_line; methodology $set_methodology; product $set_product; $test_line; Пауза 87162f9feb8c/429adaba4cec, арифметика_цикла 34ef3ee7c00b/95c29f6d64ac"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 244: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 244 ($fails красных): $summary"
exit 1
