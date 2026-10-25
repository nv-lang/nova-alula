#!/bin/sh
# Зачем: одна команда-критерий задачи 225 «Алула 2.25, пакет alula 0.7.0» (спецификация: AL-133, AL-134).
# Проверяет: (1) `alula version` печатает `alula 0.7.0 (Alula 2.25, machine/2)`; пакет называет 0.7.0 (nova.toml);
#     (2) формат 2.24 не принимается: файл с `format: 2.24` и дерево с `alula_version` 2.24 — ошибка, в сообщении названы обе версии; формат 2.25 в данных везде;
#     (3) AL-134: прежнее `время_сейчас()` / `time_now()` — ошибка с подсказкой `событие.момент` / `event.at` (в выражении и в действии, на обоих языках); поле сигнала с именем `момент` / `at` — ошибка;
#         `событие.момент` / `event.at` читается и равно штампу события (СТАРТ, сигналы, одно значение в шаге) — сценарий scripts/accept-225/stamp.scenario.test.json;
#     (4) AL-133: функции `время_в_текст` / `текст_во_время` (`time_to_text` / `text_to_time`): граничные 0001-01-01 и 9999-12-31, `Z`, миллисекунды, високосный день,
#         текст не той записи — пусто; вне диапазона — ошибка машины (проба); в таблице слов они есть, `время_сейчас` — нет;
#     (5) словарь методики версии 13 не изменился: хеш 35c571ccda17 (scripts/glossary-names.py и tools/check-alula-keywords.py);
#     (6) хеши образцов 2.24 (818a4aaeef4f, 431e7018e2bb, cf2a79073e96, bf27e54db232, d879c525be04, b3e2d6bd08f8) не живут ни в коде, ни в тестах, ни в образцах, ни в тексте спецификации;
#     (7) `alula test examples`; `nova test` всех папок пакета (по одной, последовательно);
#     (8) tools/check-alula-translation.py (и --selftest) и tools/check-alula-keywords.py --glossary зелёные;
#     (9) в пакете нет слов `время_сейчас` / `time_now` (кроме тестов отказа v225_test.nv, подсказки проверки, таблицы прежних форм, текста спецификации и журнала изменений, истории и записей задач);
#     (10) стражи дерева: scripts/guards/run-all.sh.
# Не проверяет: публикацию пакета (метка v0.7.0 — отдельный шаг по слову владельца).
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git. Тяжёлые шаги идут по одному.
# Использование: sh scripts/accept-225.sh        (из корня дерева пакета; результат — последняя строка «ПРИНЯТО 225: …» и код 0, иначе «НЕ ПРИНЯТО 225 …» и код 1)
#   ALULA=<путь>            готовая программа alula вместо сборки в target/alula.exe
#   ALULA_GLOSSARY=<файл>   state-machine-glossary.md Методики (версия 13) для tools/check-alula-keywords.py --glossary; без него шаг красный
#   ACCEPT_225_SKIP_NOVA_TEST=1  пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: эпик «Алула 2.25» (слово владельца, 2026-10-25: «одним эпиком из 3 задач, один исполнитель»).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 225: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }

# ---- сборка -----------------------------------------------------------------------------------------------------------------------------------

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 225: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 225: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

# ---- (1) версия -------------------------------------------------------------------------------------------------------------------------------

echo "== alula version"
want_version="alula 0.7.0 (Alula 2.25, machine/2)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.7.0"' nova.toml || red "nova.toml: version не 0.7.0"

# ---- (2) формат 2.24 не принимается, 2.25 везде -----------------------------------------------------------------------------------------------

echo "== формат 2.24 отклонён, 2.25 в данных"
src_md=examples/echo.alula.md
src_json=examples/echo.alula.json
sed 's/^- format: 2\.25$/- format: 2.24/' "$src_md" >"$tmp/old-format.alula.md"
if cmp -s "$src_md" "$tmp/old-format.alula.md"; then
  red "проба формата: в $src_md нет строки «- format: 2.25»"
else
  old_out=$("$alula" check "$tmp/old-format.alula.md" 2>&1); old_rc=$?
  if [ "$old_rc" -eq 0 ]; then red "формат 2.24 принят: $src_md с format: 2.24 проверен чисто"; else
    case "$old_out" in *"2.24"*"2.25"*|*"2.25"*"2.24"*) ;; *) red "сообщение о формате 2.24 не называет обе версии: $(echo "$old_out" | head -2)" ;; esac
  fi
fi
sed 's/"alula_version": *"2\.25"/"alula_version": "2.24"/' "$src_json" >"$tmp/old-tree.alula.json"
if cmp -s "$src_json" "$tmp/old-tree.alula.json"; then
  red "проба дерева: в $src_json нет alula_version 2.25"
else
  if "$alula" check "$tmp/old-tree.alula.json" >"$tmp/old-tree.out" 2>&1; then red "дерево с alula_version 2.24 принято"; else
    case "$(cat "$tmp/old-tree.out")" in *"2.25"*) ;; *) red "сообщение о дереве 2.24 не называет 2.25: $(head -2 "$tmp/old-tree.out")" ;; esac
  fi
fi
n_old_format=$(grep -rIn --exclude=accept-225.sh --exclude=accept-225.log.md "^- format: 2\.24$\|^format: 2\.24$\|\"alula_version\": *\"2\.24\"" examples spec/samples src scripts/accept-175 scripts/accept-225 2>/dev/null | grep -v "_test.nv" | wc -l | tr -d ' ')
[ "$n_old_format" = 0 ] || red "строки format 2.24 или alula_version 2.24 в данных: $n_old_format"

# ---- (3) AL-134: событие.момент / event.at ----------------------------------------------------------------------------------------------------

echo "== AL-134: event.at, время_сейчас убрана"
probe=scripts/accept-225/stamp.en.alula.md
scen=scripts/accept-225/stamp.scenario.test.json
run_out=$("$alula" run "$probe" "$scen" 2>&1); run_rc=$?
{ [ "$run_rc" -eq 0 ] && [ "$run_out" = "ok" ]; } || red "сценарий штампа события (stamp): $(echo "$run_out" | head -4)"

# прежний вызов: в выражении («let moment = time_now()») и в действии («time_now();»)
sed 's/let moment = event\.at/let moment = time_now()/' "$probe" >"$tmp/old-call-expr.alula.md"
cmp -s "$probe" "$tmp/old-call-expr.alula.md" && red "проба прежнего вызова: в $probe нет «let moment = event.at»"
old_call=$("$alula" check "$tmp/old-call-expr.alula.md" 2>&1); old_call_rc=$?
if [ "$old_call_rc" -eq 0 ]; then red "time_now() принят"; else
  case "$old_call" in *"event.at"*) ;; *) red "time_now(): ошибка без подсказки event.at: $(echo "$old_call" | head -2)" ;; esac
fi
sed 's/| journal("closed_by_user") |/| journal("closed_by_user"); time_now() |/' "$probe" >"$tmp/old-call-act.alula.md"
cmp -s "$probe" "$tmp/old-call-act.alula.md" && red "проба прежнего вызова-действия: в $probe нет «| journal(\"closed_by_user\") |»"
old_act=$("$alula" check "$tmp/old-call-act.alula.md" 2>&1); old_act_rc=$?
if [ "$old_act_rc" -eq 0 ]; then red "time_now(); как действие принят"; else
  case "$old_act" in *"event.at"*) ;; *) red "time_now(); как действие: ошибка без подсказки event.at: $(echo "$old_act" | head -2)" ;; esac
fi
# русская форма: перевод пробы en -> ru, затем прежнее слово и поле «момент»
"$alula" convert "$probe" --language ru -o "$tmp/stamp.ru.alula.md" >"$tmp/convert.out" 2>&1 || red "перевод пробы en -> ru: $(head -2 "$tmp/convert.out")"
if [ -f "$tmp/stamp.ru.alula.md" ]; then
  grep -q "событие.момент" "$tmp/stamp.ru.alula.md" || red "русская проба не пишет «событие.момент»"
  sed 's/пусть момент = событие\.момент/пусть момент = время_сейчас()/' "$tmp/stamp.ru.alula.md" >"$tmp/old-call-ru.alula.md"
  cmp -s "$tmp/stamp.ru.alula.md" "$tmp/old-call-ru.alula.md" && red "проба прежнего вызова (ru): нет «пусть момент = событие.момент»"
  old_ru=$("$alula" check "$tmp/old-call-ru.alula.md" 2>&1); old_ru_rc=$?
  if [ "$old_ru_rc" -eq 0 ]; then red "время_сейчас() принято"; else
    case "$old_ru" in *"событие.момент"*) ;; *) red "время_сейчас(): ошибка без подсказки событие.момент: $(echo "$old_ru" | head -2)" ;; esac
  fi
  sed 's/сообщение { содержимое строка }/сообщение { содержимое строка, момент число }/' "$tmp/stamp.ru.alula.md" >"$tmp/field-ru.alula.md"
  cmp -s "$tmp/stamp.ru.alula.md" "$tmp/field-ru.alula.md" && red "проба поля «момент»: нет «сообщение { содержимое строка }» в русской пробе"
  "$alula" check "$tmp/field-ru.alula.md" >"$tmp/field-ru.out" 2>&1 && red "поле сигнала «момент» принято"
fi
# поле сигнала с именем at — ошибка (английский файл)
sed 's/message { content str }/message { content str, at int }/' "$probe" >"$tmp/field-en.alula.md"
cmp -s "$probe" "$tmp/field-en.alula.md" && red "проба поля at: нет «message { content str }»"
"$alula" check "$tmp/field-en.alula.md" >"$tmp/field-en.out" 2>&1 && red "поле сигнала at принято"
grep -q "^readable	событие.момент	event.at$" src/machine_text/alula-keywords.tsv || red "src/machine_text/alula-keywords.tsv: нет строки readable событие.момент event.at"
cmp -s src/machine_text/alula-keywords.tsv spec/alula-keywords.tsv || red "две копии таблицы слов различаются"

# ---- (4) AL-133: функции времени ------------------------------------------------------------------------------------------------------------------

echo "== AL-133: время_в_текст, текст_во_время"
grep -q "^catalog	время_в_текст	time_to_text$" src/machine_text/alula-keywords.tsv || red "таблица слов: нет catalog время_в_текст time_to_text"
grep -q "^catalog	текст_во_время	text_to_time$" src/machine_text/alula-keywords.tsv || red "таблица слов: нет catalog текст_во_время text_to_time"
grep -q "время_сейчас" src/machine_text/alula-keywords.tsv && red "таблица слов: время_сейчас ещё есть"
# вне диапазона 0001…9999 — ошибка машины: проба на начальном значении данных
sed 's/time_to_text(253402300799999)/time_to_text(253402300800000)/' "$probe" >"$tmp/range-hi.alula.md"
cmp -s "$probe" "$tmp/range-hi.alula.md" && red "проба диапазона: нет time_to_text(253402300799999)"
if "$alula" run "$tmp/range-hi.alula.md" "$scen" >"$tmp/range-hi.out" 2>&1; then red "время после 9999-12-31 принято: $(head -2 "$tmp/range-hi.out")"; fi
sed 's/time_to_text(-62135596800000)/time_to_text(-62135596800001)/' "$probe" >"$tmp/range-lo.alula.md"
if "$alula" run "$tmp/range-lo.alula.md" "$scen" >"$tmp/range-lo.out" 2>&1; then red "время до 0001-01-01 принято: $(head -2 "$tmp/range-lo.out")"; fi

# ---- (5) словарь ------------------------------------------------------------------------------------------------------------------------------

echo "== словарь методики версии 13 (хеш не менялся)"
dict_hash=$("$PYTHON" scripts/glossary-names.py --hash 2>&1 | tail -1)
[ "$dict_hash" = "35c571ccda17" ] || red "scripts/glossary-names.py --hash: «$dict_hash», нужно 35c571ccda17"
n_pairs=$(grep -vc '^#' src/machine_text/glossary_names.tsv)
[ "$n_pairs" = 1270 ] || red "пар в glossary_names.tsv: $n_pairs, нужно 1270"
grep -q "DICT_HASH = '35c571ccda17'" tools/check-alula-keywords.py || red "tools/check-alula-keywords.py держит не 35c571ccda17"
grep -q '"2.25" { return "35c571ccda17" }' src/machine_text/jname.nv || red "jname.nv: glossary_pinned_hash для 2.25 не 35c571ccda17"
grep -q '"2.24"' src/machine_text/jname.nv && red "jname.nv: формат 2.24 всё ещё закреплён"
[ -n "${ALULA_GLOSSARY:-}" ] && { "$PYTHON" scripts/glossary-names.py "$ALULA_GLOSSARY" --check >"$tmp/glossary-check.out" 2>&1 || { red "scripts/glossary-names.py --check"; tail -3 "$tmp/glossary-check.out"; }; }

# ---- (6) хеши образцов ------------------------------------------------------------------------------------------------------------------------

echo "== хеши образцов 2.24 не живут"
n_old_hash=$(grep -rIn --include=*.nv --include=*.alula.md --include=*.alula.txt --include=*.alula.json --include=*.tsv --include=alula-spec.md --include=alula-spec.en.md "818a4aaeef4f\|431e7018e2bb\|cf2a79073e96\|bf27e54db232\|d879c525be04\|b3e2d6bd08f8" examples spec src scripts tools 2>/dev/null | wc -l | tr -d ' ')
[ "$n_old_hash" = 0 ] || red "прежние хеши образцов 2.24 вне истории: $n_old_hash"

# ---- (7) examples и nova test -----------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
ex_out=$("$alula" test examples 2>&1 | tail -1)
ex_n=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) scenarios passed$/\1/p')
ex_m=$(echo "$ex_out" | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) scenarios passed$/\2/p')
if [ -n "$ex_n" ] && [ "$ex_n" = "$ex_m" ] && [ "$ex_n" -gt 0 ]; then ex_line="examples $ex_n из $ex_m"; else ex_line="examples ${ex_out}"; red "alula test examples: $ex_out"; fi

n_test_ok=0; n_test=0
if [ "${ACCEPT_225_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_225_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 225: nova не в PATH"; exit 2; }
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

# ---- (8) перевод и слова ----------------------------------------------------------------------------------------------------------------------

echo "== tools/check-alula-translation.py"
"$PYTHON" tools/check-alula-translation.py >"$tmp/translation.out" 2>&1 || { red "check-alula-translation.py"; tail -5 "$tmp/translation.out"; }
"$PYTHON" tools/check-alula-translation.py --selftest >"$tmp/translation-self.out" 2>&1 || { red "check-alula-translation.py --selftest"; tail -5 "$tmp/translation-self.out"; }

echo "== tools/check-alula-keywords.py --glossary"
glossary=${ALULA_GLOSSARY:-}
if [ -z "$glossary" ] || [ ! -f "$glossary" ]; then
  red "ALULA_GLOSSARY должен называть state-machine-glossary.md (версия 13)"
else
  "$PYTHON" tools/check-alula-keywords.py --glossary "$glossary" >"$tmp/keywords.out" 2>&1; kw_rc=$?
  if [ "$kw_rc" -ne 0 ]; then red "check-alula-keywords.py --glossary: код $kw_rc"; head -5 "$tmp/keywords.out"; fi
  "$PYTHON" tools/check-alula-keywords.py --selftest --glossary "$glossary" >"$tmp/keywords-self.out" 2>&1 || { red "check-alula-keywords.py --selftest"; tail -5 "$tmp/keywords-self.out"; }
  grep -q 'словарь версии 13: [0-9]* имён, хеш 35c571ccda17' "$tmp/keywords.out" || red "check-alula-keywords.py: словарь версии 13 с хешем 35c571ccda17 не назван"
fi

# ---- (9) время_сейчас / time_now в пакете ------------------------------------------------------------------------------------------------------

echo "== время_сейчас, time_now: нет в пакете"
# допускаются: тесты отказа (v225_test.nv), подсказка проверки (check.nv), таблица прежних форм (former.tsv), текст спецификации и журнал изменений, история, записи задач и инструмент Методики
n_time_now=$(grep -rIn "время_сейчас\|time_now" . --exclude-dir=target --exclude-dir=.git --exclude-dir=tools \
  --exclude=v225_test.nv --exclude=former.tsv --exclude=alula-spec.md --exclude=alula-spec.en.md --exclude=alula-changelog.md --exclude=alula-changelog.en.md \
  --exclude=history.md --exclude='accept-1*' --exclude='accept-2*' --exclude=check.nv 2>/dev/null | wc -l | tr -d ' ')
[ "$n_time_now" = 0 ] || red "время_сейчас / time_now в пакете: $n_time_now"
grep -c "time_now" src/machine_table/check.nv | grep -qx 1 || red "src/machine_table/check.nv: ровно одно упоминание time_now (подсказка) ожидается"

# ---- (10) стражи -------------------------------------------------------------------------------------------------------------------------------

echo "== стражи дерева"
sh scripts/guards/run-all.sh >"$tmp/guards.out" 2>&1 || { red "scripts/guards/run-all.sh"; tail -8 "$tmp/guards.out"; }

# ---- итог -----------------------------------------------------------------------------------------------------------------------------------------

summary="alula 0.7.0 (Alula 2.25, machine/2); $ex_line; $test_line; перевод и слова зелёные; время_сейчас $n_time_now"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 225: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 225 ($fails красных): $summary"
exit 1
