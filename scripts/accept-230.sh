#!/bin/sh
# Зачем: одна команда-критерий задачи 230 «пакет alula 0.8.0: проверки называются test» (запись журнала изменений: AL-135).
# Проверяет: (1) `alula version` печатает `alula 0.8.0 (Alula 2.25, machine/2)`, nova.toml — 0.8.0;
#     (2) файлы проверок названы `*.alula.test.json`, ключ `"format"` в них `test/0`, схема `src/machine/schema/test-0.schema.json`; прежних `*.scenario.test.json`,
#         `examples/scenarios`, `scenario-0.schema.json` нет; проверка с `scenario/0` отклоняется, в сообщении названо `test/0`;
#     (3) слово `scenario` в пакете осталось только в истории (журнал изменений, docs/history.md, записи accept-*.log.md), в этом скрипте, в двух копиях образца методики (слово в них входит в хеш образца, `a154`) и в именах чужих файлов `gen_*_scenarios.py`;
#     (4) формат Алулы не менялся: хеш словаря 35c571ccda17 (scripts/glossary-names.py и tools/check-alula-keywords.py), образцы и перевод зелёные;
#     (5) `alula test examples` — все проверки; `nova test` всех папок пакета с тестами (по одной, `--jobs 2`); стражи дерева.
# Не проверяет: публикацию пакета (метка v0.8.0 — отдельный шаг по слову владельца); прогон набора методики (508 проверок): его делает методика на собранной программе.
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git.
# Использование: sh scripts/accept-230.sh   (из корня дерева пакета; последняя строка «ПРИНЯТО 230: …» и код 0, иначе «НЕ ПРИНЯТО 230 …» и код 1)
#   ALULA=<путь>            готовая программа alula вместо сборки в target/alula.exe
#   ALULA_GLOSSARY=<файл>   state-machine-glossary.md методики (версия 13) для tools/check-alula-keywords.py --glossary; без него шаг красный
#   ACCEPT_230_SKIP_NOVA_TEST=1  пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: слово владельца, 2026-10-26: «это механическое переименование, супер быстро» (малый маршрут; красная проба до правки не писалась: правка не меняет поведения языка).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 230: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 230: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 230: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

# ---- (1) версия ---------------------------------------------------------------------------------------------------------------------------------

echo "== alula version"
want_version="alula 0.8.0 (Alula 2.25, machine/2)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.8.0"' nova.toml || red "nova.toml: version не 0.8.0"

# ---- (2) имена и формат проверок ----------------------------------------------------------------------------------------------------------------

echo "== имена и формат проверок"
n_old_names=$(git ls-files | grep -c 'scenario')
[ "$n_old_names" = 0 ] || red "в именах отслеживаемых файлов осталось scenario: $n_old_names"
[ -f src/machine/schema/test-0.schema.json ] || red "нет src/machine/schema/test-0.schema.json"
n_tests=$(git ls-files | grep -c '\.alula\.test\.json$')
[ "$n_tests" -gt 0 ] || red "нет файлов *.alula.test.json"
n_fmt=$(git ls-files | grep '\.alula\.test\.json$' | while read -r f; do grep -c '"format": *"test/0"' "$f"; done | grep -c '^1$')
[ "$n_fmt" = "$n_tests" ] || red "ключ format: test/0 в $n_fmt файлах из $n_tests"
grep -q '"test/0"' src/machine/schema/test-0.schema.json || red "схема не называет test/0"

old_test=$(git ls-files 'examples/tests/*.alula.test.json' | head -1)
sed 's|"format": *"test/0"|"format": "scenario/0"|' "$old_test" >"$tmp/old.alula.test.json"
if "$alula" run examples/echo.alula.json "$tmp/old.alula.test.json" >"$tmp/old-run.out" 2>&1; then
  red "проверка с format scenario/0 принята"
else
  grep -q 'test/0' "$tmp/old-run.out" || red "сообщение об отказе не называет test/0: $(head -2 "$tmp/old-run.out")"
fi

# ---- (3) слово scenario только в истории --------------------------------------------------------------------------------------------------------

echo "== слово scenario только в истории"
n_scen=$(grep -rIn "scenario" . --exclude-dir=target --exclude-dir=.git \
  --exclude=alula-changelog.md --exclude=alula-changelog.en.md --exclude=history.md --exclude='accept-*.log.md' --exclude=accept-230.sh --exclude=agent-step.en.alula.md --exclude=agent-step-methodology-222.en.alula.txt 2>/dev/null \
  | grep -vc 'gen_[a-z_]*_scenarios\.py')
[ "$n_scen" = 0 ] || red "scenario вне истории: $n_scen строк"

# ---- (4) формат Алулы не менялся ----------------------------------------------------------------------------------------------------------------

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

# ---- (5) examples, nova test, стражи -------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
ex_out=$("$alula" test examples 2>&1 | tail -1)
ex_n=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1/p')
ex_m=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\2/p')
if [ -n "$ex_n" ] && [ "$ex_n" = "$ex_m" ] && [ "$ex_n" -gt 0 ]; then ex_line="examples $ex_n из $ex_m"; else ex_line="examples ${ex_out}"; red "alula test examples: $ex_out"; fi

if [ "${ACCEPT_230_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_230_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 230: nova не в PATH"; exit 2; }
  n_dirs=0; n_dirs_ok=0
  for d in src/*/; do
    dir=$(basename "$d")
    ls "$d"*_test.nv >/dev/null 2>&1 || continue
    echo "== nova test src/$dir"
    t_full=$(nova test "src/$dir" --jobs 2 --timeout 900 2>&1)
    t_out=$(echo "$t_full" | tail -3)
    t_fail=$(echo "$t_out" | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\2/p' | tail -1)
    t_fail=${t_fail:-1}
    n_dirs=$((n_dirs + 1))
    if [ "$t_fail" = 0 ]; then n_dirs_ok=$((n_dirs_ok + 1)); else red "nova test src/$dir: $t_fail красных"; echo "$t_full" | grep -a "FAIL\|TIMEOUT\|error" | head -4 | cut -c1-600; fi
    sleep 5
  done
  test_line="nova test $n_dirs_ok из $n_dirs"
fi

echo "== стражи дерева"
sh scripts/guards/run-all.sh >"$tmp/guards.out" 2>&1 || { red "scripts/guards/run-all.sh"; tail -8 "$tmp/guards.out"; }

summary="alula 0.8.0 (Alula 2.25, machine/2); $ex_line; $test_line; перевод и слова зелёные; scenario вне истории $n_scen"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 230: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 230 ($fails красных): $summary"
exit 1
