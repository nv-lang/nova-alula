#!/bin/sh
# Зачем: одна команда-критерий задачи 181 «Формат 2.24, хеши образцов, пакет 0.6.0» (Алула 2.24, пакет alula 0.6.0; спецификация: AL-123, AL-128…AL-132).
# Проверяет: (1) `alula version` печатает `alula 0.6.0 (Alula 2.24, machine/2)`; пакет и справка называют 0.6.0 (nova.toml);
#     (2) формат 2.23 не принимается: файл с `format: 2.23` и дерево с `alula_version` 2.23 — ошибка, в сообщении названы обе версии; формат 2.24 в данных везде (строки `format:`, ключи `alula_version`);
#     (3) литерал роли в разборе стороны — ошибка с подсказкой AL-131 («литерал роли в разбор:»), три функции по роли записаны в образцах; таблицы «по роли» и механизма RoleRow/find_role/has_roles в коде нет;
#     (4) словарь методики версии 13: 1270 пар, хеш 35c571ccda17 (scripts/glossary-names.py и tools/check-alula-keywords.py держат один хеш), файла glossary_names_v11.tsv нет;
#     (5) хеши образцов файла функций пересчитаны под строку `format: 2.24`: прежние ru ebb7658048b2 и en a9af85407c2b не живут ни в коде, ни в тестах, ни в образцах, ни в тексте спецификации (остаются записи истории);
#     (6) `alula test examples` — все сценарии зелёные; `nova test` всех папок пакета зелёные (число — в итоговой строке);
#     (7) tools/check-alula-translation.py (и --selftest) и tools/check-alula-keywords.py --glossary зелёные (единственное исключение — ложное срабатывание проверки на объявлениях внешних функций, см. ниже);
#     (8) в пакете нет заглушек `AL-2` + `xx` (поиск по всему дереву, кроме этого скрипта);
#     (9) стражи дерева: scripts/guards/run-all.sh.
# Не проверяет: правила 182, 175, 179, 180 (их команды-критерии: accept-175.sh, accept-179.sh, accept-180.sh), публикацию пакета (метка v0.6.0 — отдельный шаг по слову владельца).
# Известное расхождение: tools/check-alula-keywords.py (инструмент Методики, здесь не правится) на объявлении внешней функции с результатом (`внешняя функция имя(…) изменчивая -> Тип`)
#     пишет «`->` — только перед типом результата»: он знает `->` лишь в заголовке определения, в `разбор:` и в каталоге. Такие строки (и только они) из вывода исключены, остальное — красное; число исключённых — в итоговой строке не печатается, а в журнале задачи.
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git. Тяжёлые шаги идут по одному.
# Использование: sh scripts/accept-181.sh        (из корня дерева пакета; результат — последняя строка «ПРИНЯТО 181: …» и код 0, иначе «НЕ ПРИНЯТО 181 …» и код 1)
#   ALULA=<путь>            готовая программа alula вместо сборки в target/alula.exe
#   ALULA_GLOSSARY=<файл>   state-machine-glossary.md Методики (версия 13) для tools/check-alula-keywords.py --glossary; без него шаг красный
#   ACCEPT_181_SKIP_NOVA_TEST=1  пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: doc/tasks/181-alula-2-24-format-0-6-0 (репозиторий продукта), AC-1…AC-3.
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 181: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }

# ---- сборка -----------------------------------------------------------------------------------------------------------------------------------

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 181: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 181: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

# ---- (1) версия -------------------------------------------------------------------------------------------------------------------------------

echo "== alula version"
want_version="alula 0.6.0 (Alula 2.24, machine/2)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.6.0"' nova.toml || red "nova.toml: version не 0.6.0"

# ---- (2) формат 2.23 не принимается, 2.24 везде -----------------------------------------------------------------------------------------------

echo "== формат 2.23 отклонён, 2.24 в данных"
src_md=examples/echo.alula.md
src_json=examples/echo.alula.json
sed 's/^- format: 2\.24$/- format: 2.23/' "$src_md" >"$tmp/old-format.alula.md"
if cmp -s "$src_md" "$tmp/old-format.alula.md"; then
  red "проба формата: в $src_md нет строки «- format: 2.24»"
else
  old_out=$("$alula" check "$tmp/old-format.alula.md" 2>&1); old_rc=$?
  if [ "$old_rc" -eq 0 ]; then red "формат 2.23 принят: $src_md с format: 2.23 проверен чисто"; else
    case "$old_out" in *"2.23"*"2.24"*|*"2.24"*"2.23"*) ;; *) red "сообщение о формате 2.23 не называет обе версии: $(echo "$old_out" | head -2)" ;; esac
  fi
fi
sed 's/"alula_version": *"2\.24"/"alula_version": "2.23"/' "$src_json" >"$tmp/old-tree.alula.json"
if cmp -s "$src_json" "$tmp/old-tree.alula.json"; then
  red "проба дерева: в $src_json нет alula_version 2.24"
else
  if "$alula" check "$tmp/old-tree.alula.json" >"$tmp/old-tree.out" 2>&1; then red "дерево с alula_version 2.23 принято"; else
    case "$(cat "$tmp/old-tree.out")" in *"2.24"*) ;; *) red "сообщение о дереве 2.23 не называет 2.24: $(head -2 "$tmp/old-tree.out")" ;; esac
  fi
fi
n_old_format=$(grep -rn --exclude=accept-181.sh --exclude=accept-181.log.md "^- format: 2\.23$\|^format: 2\.23$\|\"alula_version\": *\"2\.23\"" examples spec/samples src scripts 2>/dev/null | grep -v "_test.nv" | wc -l | tr -d ' ')
[ "$n_old_format" = 0 ] || red "строки format 2.23 или alula_version 2.23 в данных: $n_old_format"

# ---- (3) литерал роли, три функции, механизм «по роли» ---------------------------------------------------------------------------------------

echo "== литерал роли в разборе (AL-131)"
meet=src/machine_nested/cases/meeting-examples.alula.md
sed 's/разбор: разобрать_ответ_свидетеля /разбор: разобрать_ответ_свидетеля("witness") /' "$meet" >"$tmp/role-literal.alula.md"
if cmp -s "$meet" "$tmp/role-literal.alula.md"; then
  red "проба литерала роли: в $meet нет «разбор: разобрать_ответ_свидетеля»"
else
  role_out=$("$alula" check "$tmp/role-literal.alula.md" 2>&1); role_rc=$?
  if [ "$role_rc" -eq 0 ]; then red "литерал роли в разбор: принят"; else
    case "$role_out" in *"литерал роли в разбор:"*"отдельная функция на роль"*) ;; *) red "сообщение о литерале роли без подсказки AL-131: $(echo "$role_out" | head -2)" ;; esac
  fi
fi
n_agent=$(grep -rIn --include=*.alula.md --include=*.alula.txt --include=*.alula.json --include=*.fragment.md --include=*.fragment.en.md --include=*.tsv "разобрать_ответ_агента\|parse_agent_reply" examples spec/samples src/machine_agent/cases src/machine_nested/cases src/machine_text_eq/cases src/machine_text/defs src/machine_text/fragments 2>/dev/null | wc -l | tr -d ' ')
[ "$n_agent" = 0 ] || red "разобрать_ответ_агента / parse_agent_reply в образцах и данных: $n_agent"
n_samples_roles=$(grep -rIn -E 'разбор: [^ ]+\("' spec/samples/meeting-definitions.alula.md src/machine_agent/cases/meeting-methodology-222.alula.txt src/machine_nested/cases/meeting-examples.alula.md 2>/dev/null | wc -l | tr -d ' ')
[ "$n_samples_roles" = 0 ] || red "литерал роли в разбор: образцов: $n_samples_roles"
n_role_code=$(grep -rIn "RoleRow\|find_role\|has_roles\|add_role" src --include=*.nv 2>/dev/null | grep -v "_test.nv" | wc -l | tr -d ' ')
[ "$n_role_code" = 0 ] || red "механизм «по роли» в коде (RoleRow, find_role, has_roles, add_role): $n_role_code"
n_role_table=$(grep -rIn "по роли {\|by role {" examples spec/samples src --include=*.md --include=*.txt --include=*.tsv 2>/dev/null | wc -l | tr -d ' ')
[ "$n_role_table" = 0 ] || red "таблица «по роли» в данных: $n_role_table"
grep -q '"role"' src/machine/schema/machine-2.schema.json && red "схема machine-2: ключ role в разборе стороны"

# ---- (4) словарь ------------------------------------------------------------------------------------------------------------------------------

echo "== словарь методики версии 13"
dict_hash=$("$PYTHON" scripts/glossary-names.py --hash 2>&1 | tail -1)
[ "$dict_hash" = "35c571ccda17" ] || red "scripts/glossary-names.py --hash: «$dict_hash», нужно 35c571ccda17"
n_pairs=$(grep -vc '^#' src/machine_text/glossary_names.tsv)
[ "$n_pairs" = 1270 ] || red "пар в glossary_names.tsv: $n_pairs, нужно 1270"
grep -q "DICT_HASH = '35c571ccda17'" tools/check-alula-keywords.py || red "tools/check-alula-keywords.py держит не 35c571ccda17"
[ ! -e src/machine_text/glossary_names_v11.tsv ] || red "glossary_names_v11.tsv не удалён"
grep -q '"2.24" { return "35c571ccda17" }' src/machine_text/jname.nv || red "jname.nv: glossary_pinned_hash для 2.24 не 35c571ccda17"
grep -q '"2.23"' src/machine_text/jname.nv && red "jname.nv: формат 2.23 всё ещё закреплён"

# ---- (5) хеши образцов ------------------------------------------------------------------------------------------------------------------------

echo "== хеши образцов файла функций"
# живут только в записях истории (журналы изменений, справка к образцу, README, история): код, тесты, образцы и текст спецификации их не несут
n_old_hash=$(grep -rIn --include=*.nv --include=*.alula.md --include=*.alula.txt --include=*.alula.json --include=*.tsv --include=alula-spec.md --include=alula-spec.en.md "ebb7658048b2\|a9af85407c2b" examples spec src scripts tools 2>/dev/null | wc -l | tr -d ' ')
[ "$n_old_hash" = 0 ] || red "прежние хеши образцов (ebb7658048b2, a9af85407c2b) вне истории: $n_old_hash"

# ---- (6) examples и nova test -----------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
ex_out=$("$alula" test examples 2>&1 | tail -1)
ex_n=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) scenarios passed$/\1/p')
ex_m=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) scenarios passed$/\2/p')
if [ -n "$ex_n" ] && [ "$ex_n" = "$ex_m" ] && [ "$ex_n" -gt 0 ]; then ex_line="examples $ex_n из $ex_m"; else ex_line="examples ${ex_out}"; red "alula test examples: $ex_out"; fi

n_test_ok=0; n_test=0
if [ "${ACCEPT_181_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_181_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 181: nova не в PATH"; exit 2; }
  for d in src/*/; do
    dir=$(basename "$d")
    ls "$d"*_test.nv >/dev/null 2>&1 || continue
    echo "== nova test src/$dir"
    t_full=$(nova test "src/$dir" --jobs 2 --timeout 900 2>&1)
    t_out=$(echo "$t_full" | tail -3)
    t_pass=$(echo "$t_out" | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\1/p' | tail -1)
    t_fail=$(echo "$t_out" | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\2/p' | tail -1)
    t_pass=${t_pass:-0}; t_fail=${t_fail:-1}
    n_test=$((n_test + t_pass + t_fail)); n_test_ok=$((n_test_ok + t_pass))
    [ "$t_fail" = 0 ] || { red "nova test src/$dir: $t_fail красных"; echo "$t_full" | grep -a "FAIL\|TIMEOUT\|error" | head -4 | cut -c1-600; }
    sleep 5
  done
  test_line="nova test $n_test_ok из $n_test"
fi

# ---- (7) перевод и слова ----------------------------------------------------------------------------------------------------------------------

echo "== tools/check-alula-translation.py"
"$PYTHON" tools/check-alula-translation.py >"$tmp/translation.out" 2>&1 || { red "check-alula-translation.py"; tail -5 "$tmp/translation.out"; }
"$PYTHON" tools/check-alula-translation.py --selftest >"$tmp/translation-self.out" 2>&1 || { red "check-alula-translation.py --selftest"; tail -5 "$tmp/translation-self.out"; }

echo "== tools/check-alula-keywords.py --glossary"
glossary=${ALULA_GLOSSARY:-}
if [ -z "$glossary" ] || [ ! -f "$glossary" ]; then
  red "ALULA_GLOSSARY должен называть state-machine-glossary.md (версия 13)"
else
  "$PYTHON" tools/check-alula-keywords.py --glossary "$glossary" >"$tmp/keywords.out" 2>&1; kw_rc=$?
  # исключение: ложное срабатывание на объявлениях внешних функций (см. шапку): сообщение «`->` — только перед типом результата» на строке,
  # что сама начинается с `внешняя функция ` / `external fn `; любое другое замечание, и это сообщение на другой строке, остаются красными
  "$PYTHON" - "$tmp/keywords.out" "$tmp/keywords.rest" "$tmp/keywords.false" <<'PYEOF'
import io, re, sys
msg = '`->` — только перед типом результата'
rest, false = [], []
for line in io.open(sys.argv[1], encoding='utf-8').read().splitlines():
    m = re.match(r'^(.+?):(\d+): (.*)$', line)
    if m and msg in m.group(3):
        try:
            src = io.open(m.group(1), encoding='utf-8').read().splitlines()[int(m.group(2)) - 1]
        except (OSError, IndexError):
            src = ''
        if src.startswith(('внешняя функция ', 'external fn ')):
            false.append(line)
            continue
    rest.append(line)
io.open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write('\n'.join(rest) + '\n')
io.open(sys.argv[3], 'w', encoding='utf-8', newline='\n').write('\n'.join(false) + '\n')
PYEOF
  n_false=$(grep -c . "$tmp/keywords.false" | tr -d ' ')
  n_rest=$(grep -c '^[^ ]*:[0-9][0-9]*: ' "$tmp/keywords.rest" | tr -d ' ')
  if [ "$kw_rc" -ne 0 ] && [ "$n_rest" -gt 0 ]; then red "check-alula-keywords.py --glossary: $n_rest замечаний сверх известного расхождения"; head -5 "$tmp/keywords.rest"; fi
  if [ "$kw_rc" -ne 0 ] && [ "$n_rest" -eq 0 ] && [ "$n_false" -eq 0 ]; then red "check-alula-keywords.py --glossary: код $kw_rc без замечаний"; tail -3 "$tmp/keywords.out"; fi
  echo "   известное расхождение (->, объявления внешних функций): $n_false"
  grep -q 'словарь версии 13: [0-9]* имён, хеш 35c571ccda17' "$tmp/keywords.out" || red "check-alula-keywords.py: словарь версии 13 с хешем 35c571ccda17 не назван"
fi

# ---- (8) заглушки -----------------------------------------------------------------------------------------------------------------------------

echo "== заглушки"
stub="AL-2""xx"
n_stub=$(grep -rIn "$stub" . --exclude-dir=target --exclude-dir=.git --exclude=accept-181.sh --exclude=accept-181.log.md 2>/dev/null | wc -l | tr -d ' ')
[ "$n_stub" = 0 ] || red "заглушек $stub: $n_stub"

# ---- (9) стражи -------------------------------------------------------------------------------------------------------------------------------

echo "== стражи дерева"
sh scripts/guards/run-all.sh >"$tmp/guards.out" 2>&1 || { red "scripts/guards/run-all.sh"; tail -8 "$tmp/guards.out"; }

# ---- итог -----------------------------------------------------------------------------------------------------------------------------------------

summary="alula 0.6.0 (Alula 2.24, machine/2); $ex_line; $test_line; перевод и слова зелёные; AL-2xx $n_stub"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 181: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 181 ($fails красных): $summary"
exit 1
