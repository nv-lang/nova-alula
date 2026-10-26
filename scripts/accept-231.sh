#!/bin/sh
# Зачем: одна команда-критерий задачи 231 «пакет alula 0.8.1: старое имя проверки отказывается явно» (запись журнала изменений: AL-136).
# Проверяет: (1) `alula version` печатает `alula 0.8.1 (Alula 2.25, machine/2)`, nova.toml — 0.8.1;
#     (2) на копии папки examples: смешанная папка (66 новых проверок и один файл со старым именем проверки) — `alula test` не 0 (код 2), на стандартной ошибке строка
#         `old file name, rename to *.alula.test.json: <путь>`, «N of M tests passed» не печатается; папка только со старым файлом — тот же отказ, не «no tests»;
#         `alula run <машина> <старое имя>` — код не 0 и то же сообщение; `alula run <машина> <*.alula.test.json>` и прочий путь — `ok`; чистая папка — 66 из 66;
#     (3) формат Алулы не менялся: хеш словаря 35c571ccda17, образцы, перевод и слова зелёные;
#     (4) `nova test` папок alula_cli, alula_tests, machine_run (по одной, `--jobs 2`); стражи дерева;
#     (5) слово из старого имени проверки в пакете есть только в истории и в тех файлах, что его называют, чтобы отказать (commands.nv, old_name_test.nv, этот скрипт, accept-230.sh).
# Не проверяет: публикацию пакета (метка v0.8.1 — отдельный шаг по слову владельца); полный `nova test` по всем папкам (правка сообщений CLI).
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git.
# Использование: sh scripts/accept-231.sh   (из корня дерева пакета; последняя строка «ПРИНЯТО 231: …» и код 0, иначе «НЕ ПРИНЯТО 231 …» и код 1)
#   ALULA=<путь>            готовая программа alula вместо сборки в target/alula.exe
#   ALULA_GLOSSARY=<файл>   state-machine-glossary.md методики (версия 13) для tools/check-alula-keywords.py --glossary; без него шаг красный
#   ACCEPT_231_SKIP_NOVA_TEST=1  пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: малый маршрут «супер быстро» (решение Методики AL-136 как следствие AL-135; вопрос владельцу не нужен).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 231: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 231: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 231: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

# ---- (1) версия ---------------------------------------------------------------------------------------------------------------------------------

echo "== alula version"
want_version="alula 0.8.1 (Alula 2.25, machine/2)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.8.1"' nova.toml || red "nova.toml: version не 0.8.1"

# ---- (2) отказ при старом имени -----------------------------------------------------------------------------------------------------------------

echo "== старое имя проверки"
old_word=scenario
old_suffix=".$old_word.test.json"
msg_head="old file name, rename to *.alula.test.json: "
good_test=examples/tests/echo-close.alula.test.json

mixed=$tmp/mixed
mkdir -p "$mixed"
cp -r examples/. "$mixed/"
cp "$good_test" "$mixed/tests/echo-old$old_suffix"
"$alula" test "$mixed" >"$tmp/mixed.out" 2>"$tmp/mixed.err"; code=$?
[ "$code" != 0 ] || red "смешанная папка: код 0"
grep -F "$msg_head" "$tmp/mixed.err" | grep -qF "/mixed/tests/echo-old${old_suffix}" || red "смешанная папка: нет строки отказа с путём: $(head -2 "$tmp/mixed.err")"
[ "$(wc -l <"$tmp/mixed.err" | tr -d ' ')" = 1 ] || red "смешанная папка: строк отказа не одна"
grep -q 'tests passed' "$tmp/mixed.out" && red "смешанная папка: напечатано «tests passed»"

only=$tmp/only
mkdir -p "$only"
cp examples/echo.alula.json examples/registry.md examples/journal.md "$only/"
cp "$good_test" "$only/echo-old$old_suffix"
"$alula" test "$only" >"$tmp/only.out" 2>"$tmp/only.err"; code=$?
[ "$code" != 0 ] || red "папка только со старым файлом: код 0"
grep -F "$msg_head" "$tmp/only.err" | grep -qF "/only/echo-old${old_suffix}" || red "папка только со старым файлом: нет строки отказа: $(head -2 "$tmp/only.err")"
grep -q 'no tests' "$tmp/only.err" && red "папка только со старым файлом: «no tests» вместо отказа"

"$alula" run "$mixed/echo.alula.json" "$mixed/tests/echo-old$old_suffix" >"$tmp/run-old.out" 2>"$tmp/run-old.err"; code=$?
[ "$code" != 0 ] || red "alula run со старым именем: код 0"
grep -F "$msg_head" "$tmp/run-old.err" | grep -qF "/mixed/tests/echo-old${old_suffix}" || red "alula run со старым именем: нет строки отказа: $(head -2 "$tmp/run-old.err")"

"$alula" run examples/echo.alula.json "$good_test" >"$tmp/run-new.out" 2>&1 || red "alula run с именем *.alula.test.json: код не 0"
[ "$(head -1 "$tmp/run-new.out")" = ok ] || red "alula run с именем *.alula.test.json: не ok"
cp "$good_test" "$tmp/other-name.json"
"$alula" run examples/echo.alula.json "$tmp/other-name.json" >"$tmp/run-other.out" 2>&1 || red "alula run с прочим путём: код не 0"
[ "$(head -1 "$tmp/run-other.out")" = ok ] || red "alula run с прочим путём: не ok"

# ---- (3) формат Алулы не менялся ----------------------------------------------------------------------------------------------------------------

echo "== словарь и хеши"
dict_hash=$("$PYTHON" scripts/glossary-names.py --hash 2>&1 | tail -1)
[ "$dict_hash" = "35c571ccda17" ] || red "scripts/glossary-names.py --hash: $dict_hash, нужно 35c571ccda17"
grep -q "DICT_HASH = '35c571ccda17'" tools/check-alula-keywords.py || red "tools/check-alula-keywords.py держит не 35c571ccda17"
[ -n "${ALULA_GLOSSARY:-}" ] && { "$PYTHON" scripts/glossary-names.py "$ALULA_GLOSSARY" --check >"$tmp/glossary-check.out" 2>&1 || { red "scripts/glossary-names.py --check"; tail -3 "$tmp/glossary-check.out"; }; }
"$PYTHON" tools/check-alula-samples.py >"$tmp/samples.out" 2>&1 || { red "check-alula-samples.py"; tail -5 "$tmp/samples.out"; }

echo "== tools/check-alula-translation.py"
"$PYTHON" tools/check-alula-translation.py >"$tmp/translation.out" 2>&1 || { red "check-alula-translation.py"; tail -5 "$tmp/translation.out"; }
"$PYTHON" tools/check-alula-translation.py --selftest >"$tmp/translation-self.out" 2>&1 || { red "check-alula-translation.py --selftest"; tail -5 "$tmp/translation-self.out"; }

echo "== tools/check-alula-keywords.py --glossary"
glossary=${ALULA_GLOSSARY:-}
if [ -z "$glossary" ] || [ ! -f "$glossary" ]; then
  red "ALULA_GLOSSARY должен называть state-machine-glossary.md (версия 13)"
else
  "$PYTHON" tools/check-alula-keywords.py --glossary "$glossary" >"$tmp/keywords.out" 2>&1 || { red "check-alula-keywords.py --glossary"; head -5 "$tmp/keywords.out"; }
  "$PYTHON" tools/check-alula-keywords.py --selftest --glossary "$glossary" >"$tmp/keywords-self.out" 2>&1 || { red "check-alula-keywords.py --selftest"; tail -5 "$tmp/keywords-self.out"; }
  grep -q 'словарь версии 13: [0-9]* имён, хеш 35c571ccda17' "$tmp/keywords.out" || red "check-alula-keywords.py: словарь версии 13 с хешем 35c571ccda17 не назван"
fi

# ---- (4) examples, nova test, стражи -------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
ex_out=$("$alula" test examples 2>&1 | tail -1)
ex_n=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1/p')
ex_m=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\2/p')
if [ -n "$ex_n" ] && [ "$ex_n" = "$ex_m" ] && [ "$ex_n" -gt 0 ]; then ex_line="examples $ex_n из $ex_m"; else ex_line="examples ${ex_out}"; red "alula test examples: $ex_out"; fi

if [ "${ACCEPT_231_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_231_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 231: nova не в PATH"; exit 2; }
  n_dirs=0; n_dirs_ok=0
  for dir in alula_cli alula_tests machine_run; do
    echo "== nova test src/$dir"
    t_full=$(nova test "src/$dir" --jobs 2 --timeout 900 2>&1)
    t_out=$(echo "$t_full" | tail -3)
    t_fail=$(echo "$t_out" | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\2/p' | tail -1)
    t_fail=${t_fail:-1}
    n_dirs=$((n_dirs + 1))
    if [ "$t_fail" = 0 ]; then n_dirs_ok=$((n_dirs_ok + 1)); else red "nova test src/$dir: $t_fail красных"; echo "$t_full" | grep -a "FAIL\|TIMEOUT\|error" | head -4 | cut -c1-600; fi
    sleep 5
  done
  test_line="nova test $n_dirs_ok из $n_dirs папок"
fi

echo "== стражи дерева"
sh scripts/guards/run-all.sh >"$tmp/guards.out" 2>&1 || { red "scripts/guards/run-all.sh"; tail -8 "$tmp/guards.out"; }

# ---- (5) старое слово только в истории и в файлах отказа ----------------------------------------------------------------------------------------

echo "== старое слово только в истории и в файлах отказа"
n_scen=$(grep -rIn "$old_word" . --exclude-dir=target --exclude-dir=.git \
  --exclude=alula-changelog.md --exclude=alula-changelog.en.md --exclude=history.md --exclude='accept-*.log.md' \
  --exclude=accept-230.sh --exclude=accept-231.sh --exclude=commands.nv --exclude=old_name_test.nv 2>/dev/null \
  | grep -vc 'gen_[a-z_]*_scenarios\.py')
[ "$n_scen" = 0 ] || red "старое слово вне истории: $n_scen строк"

summary="alula 0.8.1 (Alula 2.25, machine/2); $ex_line; $test_line; отказ при старом имени (test, run) и перевод и слова зелёные"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 231: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 231 ($fails красных): $summary"
exit 1
