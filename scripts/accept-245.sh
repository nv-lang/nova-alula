#!/bin/sh
# Зачем: одна команда-критерий задачи 245 «Алула 0.27, поток П2: пакет nova-alula 0.27.0» — образцы и examples скриптом миграции, наборы машин на копиях,
#     места владельцам, доводка check-alula-keywords.py (поверх потока П1, scripts/accept-244.sh).
# Проверяет: (1) версия 0.27.0 везде: `alula version` — `alula 0.27.0 (Алула 0.27)`, nova.toml и README — 0.27.0, номеров 0.10.0 и 0.27.0, шапок и деревьев 0.27 нет (кроме истории и журнала изменений);
#     (2) tools/check-alula-keywords.py — зелёный, `--selftest` — зелёный (порчи формы 0.27: шапка `revision`/`alula_version` и её порядок, ревизия — целое,
#         у библиотеки ревизии нет, единый `## Требует`, сторона `machine` со скобками — замечены; ALULA_GLOSSARY=<словарь методики> — ещё самопроверка образцов по словарю);
#     (3) examples и spec/samples 2.26 (вершина e69d729) с библиотеками методики 0.27 рядом переносятся tools/migrate-alula-227.py в файлы дерева: md — построчно
#         (проза-комментарий не сверяется), деревья и тесты — по JSON; повторный запуск ничего не меняет; `alula test` перенесённых examples — все;
#     (4) наборы машин ALULA_METHODOLOGY_MACHINES / ALULA_PRODUCT_MACHINES (копии во временной папке): скрипт переносит, его места — только перечисленные
#         в docs/owner-places-0.27.md, `alula test` — все (ALULA_METHODOLOGY_TESTS / ALULA_PRODUCT_TESTS=<число> — ещё и число тестов);
#     (5) docs/owner-places-0.27.md называет каждое место скрипта (файл, вид, тип) и место пакета `Vec.join`; (6) `nova test` всех папок пакета с тестами; стражи дерева.
# Не проверяет: публикацию (метка v0.27.0 — по слову владельца); правку наборов машин в их репозиториях; то, что проверяет scripts/accept-244.sh (тексты спецификации, хеши библиотек).
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git.
# Использование: sh scripts/accept-245.sh   (из корня дерева пакета; последняя строка «ПРИНЯТО 245: …» и код 0, иначе «НЕ ПРИНЯТО 245 …» и код 1)
#   ALULA=<путь>                       готовая программа alula вместо сборки в target/alula.exe
#   ALULA_GLOSSARY=<файл>              словарь методики state-machine-glossary.md (необязательно)
#   ALULA_METHODOLOGY_MACHINES=<папка> набор машин методики (alula-machines); ALULA_PRODUCT_MACHINES=<папка> набор машин продукта (machines/product); без них шаги пропускаются
#   ACCEPT_245_SKIP_NOVA_TEST=1        пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: слово владельца, 2026-10-28: «делай обновление-улучшение, супер быстро» (задание 245 интегратора); 21:28 — выпуск «Алула 0.27» вместо 0.27, программа 0.27.0.
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2
export PYTHONUTF8=1

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 245: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }
migrate="$PYTHON tools/migrate-alula-227.py"
places=docs/owner-places-0.27.md
base226=e69d729

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 245: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 245: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

tests_of() { "$alula" test "$1" 2>&1 | tail -1 | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1 \2/p'; }

# место скрипта миграции названо в docs/owner-places-0.27.md: имя файла, вид места и тип в обратных кавычках — в одной строке документа
named() {
  "$PYTHON" - "$places" "$1" <<'EOF'
import os, re, sys
doc = open(sys.argv[1], encoding='utf-8').read().split('\n') if os.path.exists(sys.argv[1]) else []
bad = 0
for l in open(sys.argv[2], encoding='utf-8'):
    m = re.match(r'^(.+?):(\d+): ([^:]+): (.*)$', l.rstrip('\n'))
    if not m or m.group(1).startswith('итог'):
        continue
    f = os.path.basename(m.group(1).replace('\\', '/'))
    ty = re.search(r'`([^`]+)`', m.group(4))
    keys = [f, m.group(3)] + ([ty.group(1)] if ty else [])
    if not any(all(k in d for k in keys) for d in doc):
        bad += 1
        print('место не названо в %s: %s (%s)' % (sys.argv[1], f, ', '.join(keys[1:])))
sys.exit(1 if bad else 0)
EOF
}

# ---- (1) версия -------------------------------------------------------------------------------------------------------------------------------------

echo "== версия 0.27.0"
want_version="alula 0.27.0 (Алула 0.27)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.27.0"' nova.toml || red "nova.toml: version не 0.27.0"
grep -q '2\.27\.0' README.md || red "README.md: нет версии 0.27.0"
old=$(git grep -n -I -E '0\.10\.0|2\.27\.0|Алула 2\.27|alula_version: 2\.27|"alula_version": ?"2\.27"' -- . ':(exclude)docs/history.md' ':(exclude)spec/alula-changelog*.md' ':(exclude)scripts/accept-245.sh' 2>/dev/null | head -5)
[ -z "$old" ] || { red "номер 0.10.0 или 0.27 (выпуск переименован в 0.27, слово владельца 2026-10-28 21:28) в дереве"; echo "$old"; }

# ---- (2) таблица слов и самопроверка ------------------------------------------------------------------------------------------------------------------

echo "== check-alula-keywords.py"
"$PYTHON" tools/check-alula-keywords.py >"$tmp/kw.out" 2>&1 || { red "check-alula-keywords.py"; tail -8 "$tmp/kw.out"; }
"$PYTHON" tools/check-alula-keywords.py --selftest >"$tmp/kw-self.out" 2>&1 || { red "check-alula-keywords.py --selftest"; grep -v '^таблица слов' "$tmp/kw-self.out" | head -20; }
if [ -n "${ALULA_GLOSSARY:-}" ]; then
  "$PYTHON" tools/check-alula-keywords.py --selftest --glossary "$ALULA_GLOSSARY" >"$tmp/kw-gloss.out" 2>&1 || { red "check-alula-keywords.py --selftest --glossary"; grep -v '^таблица слов' "$tmp/kw-gloss.out" | head -20; }
fi

# ---- (3) examples и образцы скриптом ----------------------------------------------------------------------------------------------------------------

echo "== examples и spec/samples 2.26 ($base226) скриптом миграции"
mkdir -p "$tmp/ex"
git archive "$base226" examples spec/samples | tar -x -C "$tmp/ex" || red "git archive $base226"
for f in "$tmp"/ex/examples/libs/*.alula.md "$tmp"/ex/spec/samples/libs/*.alula.md; do
  [ -f "$f" ] && cp "libs/$(basename "$f")" "$f"   # библиотеки 0.27 — файлы методики (libs/), а не перенос скриптом
done
$migrate --alula "$alula" "$tmp/ex/examples" "$tmp/ex/spec/samples" >"$tmp/ex.mig" 2>&1; ex_code=$?
grep -v '^перенесён' "$tmp/ex.mig" | sed "s|$tmp/||" | sed "s/^/  /"
[ "$ex_code" -le 1 ] || red "миграция examples: код $ex_code"
named "$tmp/ex.mig" || red "места examples и образцов не названы владельцам"
again=$($migrate --dry-run "$tmp/ex/examples" "$tmp/ex/spec/samples" 2>&1 | grep -c '^изменился бы')
[ "$again" = 0 ] || red "повторный запуск миграции examples меняет файлов: $again"
"$PYTHON" - "$tmp/ex" <<'EOF' >"$tmp/ex.cmp" 2>&1 || { red "перенесённые скриптом examples и образцы не равны дереву"; head -20 "$tmp/ex.cmp"; }
import glob, json, os, sys
src = sys.argv[1]
def code_lines(text):
    """Строки записи без прозы: заголовки, строки-ключи, таблицы, блоки кода (проза вне таблиц и блоков — комментарий, спецификация 1)."""
    out, fence = [], False
    for l in text.replace('\r\n', '\n').split('\n'):
        if l.startswith('```'):
            fence = not fence
            out.append(l)
        elif fence or l.startswith(('#', '- ', '|', '  ')) or not l.strip():
            out.append(l)
    return [l for i, l in enumerate(out) if l.strip() or (i and out[i - 1].strip())]
bad = 0
for base in ['examples', 'spec/samples']:
    mine = {p.replace(os.sep, '/') for p in glob.glob(base + '/**/*', recursive=True) if os.path.isfile(p)}
    moved = {os.path.relpath(p, src).replace(os.sep, '/') for p in glob.glob(os.path.join(src, base, '**', '*'), recursive=True) if os.path.isfile(p)}
    for p in sorted(mine ^ moved):
        bad += 1; print('%s: %s' % (p, 'только в дереве' if p in mine else 'только в переносе'))
    for p in sorted(mine & moved):
        a, b = open(os.path.join(src, p), 'rb').read(), open(p, 'rb').read()
        if p.endswith('.json'):
            same = json.loads(a) == json.loads(b)
        elif p.endswith('.md'):
            same = code_lines(a.decode('utf-8')) == code_lines(b.decode('utf-8'))
        else:
            same = a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n')
        if not same:
            bad += 1; print('%s: перенос скриптом не равен файлу дерева' % p)
sys.exit(1 if bad else 0)
EOF
set -- $(tests_of "$tmp/ex/examples")
if [ "${1:-0}" = "${2:-x}" ] && [ "${1:-0}" -gt 0 ]; then ex_line="examples скриптом $1 из $2"; else ex_line="examples скриптом ${1:-?} из ${2:-?}"; red "alula test перенесённых examples: $ex_line"; fi

# ---- (4), (5) наборы машин и места владельцам -------------------------------------------------------------------------------------------------------

echo "== места владельцам ($places)"
if [ -f "$places" ]; then
  grep -q 'Vec.join' "$places" || red "$places: нет места пакета Vec.join"
else
  red "нет $places"
fi

set_check() {
  if [ -z "$2" ]; then eval "set_$1=\"не задан\""; return; fi
  [ -d "$2" ] || { red "набор $1: нет папки $2"; return; }
  mkdir -p "$tmp/$1" && cp -r "$2/." "$tmp/$1/"
  $migrate --alula "$alula" "$tmp/$1" >"$tmp/$1.mig" 2>&1; mig_code=$?
  grep -v '^перенесён' "$tmp/$1.mig" | sed "s|$tmp/||" | sed "s/^/  $1: /"
  [ "$mig_code" -le 1 ] || red "набор $1: миграция код $mig_code"
  named "$tmp/$1.mig" || red "набор $1: места скрипта не названы владельцам"
  "$alula" test "$tmp/$1" >"$tmp/$1.test" 2>&1
  set -- "$1" "$3" $(tail -1 "$tmp/$1.test" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1 \2/p')
  eval "set_$1=\"${3:-?} из ${4:-?}\""
  if [ -z "${3:-}" ] || [ "${3:-0}" != "${4:-x}" ]; then
    red "набор $1: alula test ${3:-?} из ${4:-?}"; grep -a 'FAIL\|не прошёл\|error' "$tmp/$1.test" | head -8 | cut -c1-300
  elif [ -n "$2" ] && [ "$4" != "$2" ]; then
    red "набор $1: тестов $4, ждали $2"
  fi
}
set_methodology="?"; set_product="?"
echo "== наборы машин"
set_check methodology "${ALULA_METHODOLOGY_MACHINES:-}" "${ALULA_METHODOLOGY_TESTS:-}"
set_check product "${ALULA_PRODUCT_MACHINES:-}" "${ALULA_PRODUCT_TESTS:-}"

# ---- (6) nova test, стражи --------------------------------------------------------------------------------------------------------------------------

if [ "${ACCEPT_245_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_245_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 245: nova не в PATH"; exit 2; }
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

summary="$want_version; $ex_line; methodology $set_methodology; product $set_product; $test_line"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 245: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 245 ($fails красных): $summary"
exit 1
