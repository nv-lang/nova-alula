#!/bin/sh
# Зачем: одна команда-критерий задачи 239 «Алула 2.26, поток 4: скрипт миграции, образцы, хеши» (эпик 194, пакет alula 0.9.0; журнал изменений: AL-137…AL-143).
# Проверяет: (1) `alula version` печатает `alula 0.9.0 (Alula 2.26, machine/2)`, nova.toml — 0.9.0;
#     (2) образцы пакета на 2.26: у каждого `*.alula.md` в examples/, spec/samples/, libs/ — `format: 2.26`, у каждого дерева examples/ — `alula_version` 2.26;
#         библиотеки `libs/pause.alula.md` (с английским близнецом) и `libs/cycle_arithmetic.alula.md` есть; хеш каждого подключения `- Хеш:`/`- Hash:` в образцах
#         равен хешу файла библиотеки рядом (раздел 9); `tools/migrate-alula-226.py --dry-run` на образцах пакета — «файлов 0, мест 0»;
#     (3) скрипт миграции: на образцах 2.25 (examples/ вершины слитых потоков 35c2107) — код 0, мест 0, после переноса `alula test` — все; повторный запуск — «файлов 0»;
#         код 2 при ошибке запуска (нет пути, неизвестный ключ); код 1 и строка «файл:строка: вид: что сделать» на фрагменте 2.25;
#     (4) наборы машин: копия набора методики (ALULA_METHODOLOGY_MACHINES, 508 тестов) переносится скриптом без мест, все деревья копии — 2.26, `alula test` — все;
#         набор продукта (ALULA_PRODUCT_MACHINES, 81 тест) — то же, но его красное — место владельца продукта (сигнал машины `отмена` в обращении, в 2.26 его не объявить):
#         печатается строкой «МЕСТО ПРОДУКТА» и в итоговой строке, в счёт красного пакета не идёт (решение интегратора, 2026-10-27 09:01);
#     (5) шов 2.25 в инструментах снят: tools/check-alula-keywords.py не читает keywords_225.tsv; перевод, слова, образцы зелёные;
#     (6) `alula test examples` — все; `nova test` всех папок пакета с тестами (по одной, `--jobs 2`); стражи дерева.
# Не проверяет: публикацию пакета (метка v0.9.0 — по слову владельца); правку наборов машин в их репозиториях (копии во временной папке).
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git.
# Использование: sh scripts/accept-239.sh   (из корня дерева пакета; последняя строка «ПРИНЯТО 239: …» и код 0, иначе «НЕ ПРИНЯТО 239 …» и код 1)
#   ALULA=<путь>                       готовая программа alula вместо сборки в target/alula.exe
#   ALULA_GLOSSARY=<файл>              state-machine-glossary.md методики (версия 13); без него шаг слов красный
#   ALULA_METHODOLOGY_MACHINES=<папка> набор машин методики (alula-machines); без него шаг красный
#   ALULA_PRODUCT_MACHINES=<папка>     набор машин продукта (machines/product); без него шаг красный
#   ACCEPT_239_SKIP_NOVA_TEST=1        пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: слово владельца, 2026-10-27: «НАЧИНАТЬ Алулу 2.26 по целевой схеме», «Супер быстро» (чат методики; задание 239 интегратора).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 239: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }
migrate="$PYTHON tools/migrate-alula-226.py"
base225=35c2107

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 239: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 239: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

# all of M tests of a folder: «N из M» or the last line
tests_of() { "$alula" test "$1" 2>&1 | tail -1 | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1 \2/p'; }

# ---- (1) версия ---------------------------------------------------------------------------------------------------------------------------------

echo "== alula version"
want_version="alula 0.9.0 (Alula 2.26, machine/2)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.9.0"' nova.toml || red "nova.toml: version не 0.9.0"

# ---- (2) образцы пакета на 2.26, хеши -------------------------------------------------------------------------------------------------------------

echo "== образцы пакета на 2.26"
for f in examples/*.alula.md spec/samples/*.alula.md libs/*.alula.md; do
  grep -q '^- format: 2.26$' "$f" || red "$f: не format 2.26"
done
for f in examples/*.alula.json; do
  "$PYTHON" -c "import json,sys; sys.exit(0 if json.load(open(sys.argv[1],encoding='utf-8')).get('alula_version')=='2.26' else 1)" "$f" || red "$f: alula_version не 2.26"
done
for f in libs/pause.alula.md libs/pause.en.alula.md libs/cycle_arithmetic.alula.md libs/cycle_arithmetic.en.alula.md; do
  [ -f "$f" ] || red "нет $f"
done
"$PYTHON" - <<'EOF' >"$tmp/hashes.out" 2>&1 || { red "хеши подключений"; cat "$tmp/hashes.out"; }
import glob, importlib.util, os, re, sys
spec = importlib.util.spec_from_file_location('m', 'tools/migrate-alula-226.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bad = 0
for f in glob.glob('examples/*.alula.md') + glob.glob('spec/samples/*.alula.md'):
    lines = open(f, encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines):
        mf = re.match(r'^- (?:Файл|File): (\S+)$', l)
        if mf and i + 1 < len(lines):
            mh = re.match(r'^- (?:Хеш|Hash): ([0-9a-f]{12})$', lines[i + 1])
            lib = os.path.join(os.path.dirname(f), mf.group(1))
            if not mh or not os.path.exists(lib) or m.lib_hash(open(lib, encoding='utf-8').read()) != mh.group(1):
                print('%s:%d: хеш подключения %s не равен хешу файла' % (f, i + 2, mf.group(1))); bad += 1
sys.exit(1 if bad else 0)
EOF
dry=$($migrate --dry-run examples spec/samples libs 2>&1 | tail -1)
[ "$dry" = "итог: файлов 0, мест 0" ] || red "migrate --dry-run на образцах пакета: $dry"

# ---- (3) скрипт миграции на образцах 2.25 ---------------------------------------------------------------------------------------------------------

echo "== скрипт миграции на examples 2.25 ($base225)"
mkdir -p "$tmp/ex225"
git archive "$base225" examples | tar -x -C "$tmp/ex225" || red "git archive $base225 examples"
$migrate --alula "$alula" "$tmp/ex225/examples" >"$tmp/mig1.out" 2>&1; code=$?
[ "$code" = 0 ] || { red "миграция examples 2.25: код $code"; tail -5 "$tmp/mig1.out"; }
set -- $(tests_of "$tmp/ex225/examples")
[ "${1:-0}" = "${2:-x}" ] && [ "${1:-0}" -gt 0 ] || red "alula test на перенесённых examples: ${1:-?} из ${2:-?}"
again=$($migrate --alula "$alula" "$tmp/ex225/examples" 2>&1 | tail -1)
[ "$again" = "итог: файлов 0, мест 0" ] || red "повторный запуск миграции: $again"
$migrate "$tmp/нет-такой-папки" >/dev/null 2>&1; [ $? = 2 ] || red "нет пути: код не 2"
$migrate --no-such-key examples >/dev/null 2>&1; [ $? = 2 ] || red "неизвестный ключ: код не 2"
mkdir -p "$tmp/frag" && git show "$base225:src/machine_text/fragments/pause.fragment.md" >"$tmp/frag/pause.alula.md"
frag=$($migrate "$tmp/frag" 2>&1); code=$?
[ "$code" = 1 ] && echo "$frag" | grep -q 'pause.alula.md:1: фрагмент: ' || red "фрагмент 2.25: код $code, нет места «файл:строка: вид: что сделать»"

# ---- (4) наборы машин методики и продукта ---------------------------------------------------------------------------------------------------------

# set_check name folder expected verdict: verdict `red` — красное считается в итог; `place` — набор продукта: его красное — место владельца продукта (решение
# интегратора 2026-10-27 09:01: сигналы машины вне протокола 2.26 не объявить — нужен ответ методики или правка продукта), печатается строкой, в итог пакета не идёт
set_check() {
  if [ -z "$2" ] || [ ! -d "$2" ]; then red "набор $1: назовите папку (ALULA_METHODOLOGY_MACHINES / ALULA_PRODUCT_MACHINES)"; return; fi
  mkdir -p "$tmp/$1" && cp -r "$2/." "$tmp/$1/"
  $migrate --alula "$alula" "$tmp/$1" >"$tmp/$1.mig" 2>&1; mig_code=$?
  grep -v '^перенесён' "$tmp/$1.mig" | sed "s|$tmp/||" | sed "s/^/  $1: /"
  # дерево, которое скрипт не пересобрал, осталось 2.25, и декодер его читает (шов 2.25): тесты по нему ничего не доказывают
  stale=$("$PYTHON" -c "import glob,json,os,sys; print(sum(1 for f in glob.glob(os.path.join(sys.argv[1],'**','*.alula.json'),recursive=True) if json.load(open(f,encoding='utf-8')).get('alula_version')!='2.26'))" "$tmp/$1")
  set -- "$1" "$2" "$3" "$4" $(tests_of "$tmp/$1")
  why=""
  [ "$mig_code" = 0 ] || why="миграция: код $mig_code, мест $(grep -c ':[0-9][0-9]*: ' "$tmp/$1.mig")"
  [ "$stale" = 0 ] || why="$why; деревьев не 2.26: $stale"
  [ "${5:-0}" = "$3" ] && [ "${6:-0}" = "$3" ] || why="$why; alula test ${5:-?} из ${6:-?} (нужно $3 из $3)"
  if [ -z "$why" ]; then
    eval "set_$1=\"${5} из ${6}\""
  elif [ "$4" = place ]; then
    eval "set_$1=\"КРАСНО (место владельца продукта: сигнал машины в обращении; ${why#; })\""
    echo "МЕСТО ПРОДУКТА: $1: ${why#; }"
  else
    red "набор $1: ${why#; }"
    eval "set_$1=\"${5:-?} из ${6:-?}\""
  fi
}
set_methodology="?"; set_product="?"
echo "== набор методики"
set_check methodology "${ALULA_METHODOLOGY_MACHINES:-}" 508 red
echo "== набор продукта"
set_check product "${ALULA_PRODUCT_MACHINES:-}" 81 place

# ---- (5) шов 2.25 в инструментах, слова, перевод ----------------------------------------------------------------------------------------------------

echo "== шов 2.25 в инструментах"
grep -q 'keywords_225' tools/check-alula-keywords.py && red "tools/check-alula-keywords.py читает keywords_225.tsv"
"$PYTHON" tools/check-alula-samples.py >"$tmp/samples.out" 2>&1 || { red "check-alula-samples.py"; tail -5 "$tmp/samples.out"; }
"$PYTHON" tools/check-alula-translation.py >"$tmp/translation.out" 2>&1 || { red "check-alula-translation.py"; tail -5 "$tmp/translation.out"; }
glossary=${ALULA_GLOSSARY:-}
if [ -z "$glossary" ] || [ ! -f "$glossary" ]; then
  red "ALULA_GLOSSARY должен называть state-machine-glossary.md (версия 13)"
else
  "$PYTHON" tools/check-alula-keywords.py --glossary "$glossary" >"$tmp/keywords.out" 2>&1 || { red "check-alula-keywords.py --glossary"; head -5 "$tmp/keywords.out"; }
  "$PYTHON" tools/check-alula-keywords.py --selftest --glossary "$glossary" >"$tmp/keywords-self.out" 2>&1 || { red "check-alula-keywords.py --selftest"; tail -5 "$tmp/keywords-self.out"; }
fi

# ---- (6) examples, nova test, стражи -------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
set -- $(tests_of examples)
if [ "${1:-0}" = "${2:-x}" ] && [ "${1:-0}" -gt 0 ]; then ex_line="examples $1 из $2"; else ex_line="examples ${1:-?} из ${2:-?}"; red "alula test examples: $ex_line"; fi

if [ "${ACCEPT_239_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_239_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 239: nova не в PATH"; exit 2; }
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

summary="alula 0.9.0 (Alula 2.26, machine/2); $ex_line; methodology $set_methodology; product $set_product; $test_line; миграция examples 2.25 без мест; хеши подключений равны файлам"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 239: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 239 ($fails красных): $summary"
exit 1
