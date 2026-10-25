#!/bin/sh
# Зачем: одна команда-критерий задачи 175 «Внешние функции» (Алула 2.24, пакет alula 0.6.0; спецификация: AL-123, AL-129, разделы 1, 1б, 3.1, 6, 7, 8, 10).
# Проверяет: (1) пробы старых форм: `вызвать(…)`, заголовок `## Примитивы` (оба языка), внешняя функция в файле функций — ошибка с подсказкой AL-123;
#     (2) хвост параметров: объявление с хвостом и вызов с парами чисто, хвост у функции автора и повтор ключа — ошибка (AL-129);
#     (3) `alula test examples` — 66 из 66; (4) `вызвать(` и `## Примитивы` в examples, образцах и cases — нет; (5) круг «текст → дерево → текст» на образцах и examples;
#     (6) каждое дерево образцов и examples валидно по схеме machine-2; (7) деревья после миграции равны деревьям до неё, кроме узла primitives и поля named;
#     (8) сверка объявления с реестром хозяина: семь видов расхождения (имя, число параметров, тип параметра, результат, класс, нет в реестре, лишнее в реестре);
#     (9) корпус: каждая таблица из папок ALULA_CORPUS с её registry.md загружается без расхождений; (10) nova test затронутых папок.
# Не проверяет: версию формата и хеши образцов (задача 181), три функции по роли (180), контракт хозяина (179).
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+ с пакетом jsonschema, git. Тяжёлые шаги идут по одному.
# Использование: sh scripts/accept-175.sh        (из корня дерева пакета; результат — последняя строка «ПРИНЯТО 175: …» и код 0, иначе «НЕ ПРИНЯТО 175: …» и код 1)
#   ALULA=<путь>         готовая программа alula вместо сборки в target/alula.exe
#   OLD_ALULA=<путь>     программа до задачи (база: коммит ACCEPT_175_BASE, по умолчанию cde532f) для сравнения деревьев; нет её — собирается из базы в временной папке
#   ALULA_CORPUS=<папки> папки с таблицами хозяев (каждая со своим registry.md), уже переведёнными на 2.24, через пробел; без них шаг (9) красный
#   ACCEPT_175_SKIP_NOVA_TEST=1  пропустить шаг (10) (только для разработки: приёмка идёт без пропуска)
# Правило: doc/tasks/175-external-functions (репозиторий продукта), AC-1…AC-3.
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2
tools="$here/accept-175/tools.py"
probes="$here/accept-175"
base=${ACCEPT_175_BASE:-cde532f}

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 175: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 175: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 175: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

# ---- (1)(2) пробы по разделам спецификации --------------------------------------------------------------------------------------------------

# Проба: файл, ожидаемое («ошибка» — код 1 и все подстроки в выводе; «чисто» — код 0 и вывод без «error»), подстроки.
probe_run() {
  p_name=$1; p_file=$2; p_want=$3; shift 3
  p_out=$("$alula" check "$p_file" --registry "$tmp/registry.md" --journal "$probes/journal.md" 2>&1); p_rc=$?
  if [ "$p_want" = "чисто" ]; then
    if [ "$p_rc" -ne 0 ]; then echo "  проба $p_name: ожидалась чистая проверка, код $p_rc"; echo "$p_out" | head -5; return 1; fi
    return 0
  fi
  if [ "$p_rc" -eq 0 ]; then echo "  проба $p_name: ожидалась ошибка, проверка чистая"; return 1; fi
  for p_s in "$@"; do
    case "$p_out" in
      *"$p_s"*) ;;
      *) echo "  проба $p_name: в сообщении нет «$p_s»"; echo "$p_out" | head -5; return 1 ;;
    esac
  done
  return 0
}

# Реестр хозяина для проб: одна внешняя функция record (параметры и пр. задаёт вызывающий).
write_registry() {
  {
    echo "# Реестр проб"
    echo
    echo "## Primitives"
    echo
    echo "| name | parameters | result | class | reads | writes |"
    echo "|---|---|---|---|---|---|"
    [ -n "$1" ] && echo "$1"
  } >"$tmp/registry.md"
}

EN_ONE='external function record(code int, label str) acting'
RU_ONE='внешняя функция record(code число, label строка) действующая'
EN_TAIL='external function record(code int, ...fields: str) acting'
RU_TAIL='внешняя функция record(code число, ...fields: строка) действующая'
REG_ONE='| record | code: int; label: text | — | acting | — | — |'
REG_TAIL='| record | code: int; ...fields: text | — | acting | — | — |'

mk_en() { "$PYTHON" "$tools" fill "$probes/probe.en.alula.md" "$1" "ACTION=$2" "EXTERNAL=$3" "FUNCTIONS=${4:-—}"; }
mk_ru() { "$PYTHON" "$tools" fill "$probes/probe.ru.alula.md" "$1" "ACTION=$2" "EXTERNAL=$3" "FUNCTIONS=${4:-—}"; }
ext_en() { printf '## External functions\n\n```\n%s\n```' "$1"; }
ext_ru() { printf '## Внешние функции\n\n```\n%s\n```' "$1"; }
code_block() { printf '```\n%s\n```' "$1"; }

echo "== пробы старых форм AL-123"
old_total=0; old_ok=0
old_probe() {
  old_total=$((old_total + 1))
  if probe_run "$@"; then old_ok=$((old_ok + 1)); else red "проба старой формы $1"; fi
}
write_registry "$REG_ONE"
mk_ru "$tmp/old-call.ru.alula.md" '; вызвать(record, 7, "a")' "$(ext_ru "$RU_ONE")"
old_probe "вызвать(record…)" "$tmp/old-call.ru.alula.md" ошибка "AL-123" "вызвать(…)" "имя(арг)" "переходного периода нет"
mk_en "$tmp/old-call.en.alula.md" '; call(record, 7, "a")' "$(ext_en "$EN_ONE")"
old_probe "call(record…)" "$tmp/old-call.en.alula.md" ошибка "AL-123" "call(…)" "имя(арг)"
mk_ru "$tmp/old-section.ru.alula.md" '; record(7, "a")' "$(printf '## Примитивы\n\n| имя | параметры | результат | класс | читает | пишет |\n|---|---|---|---|---|---|\n| record | code число; label строка | — | действующая | — | — |')"
old_probe "## Примитивы" "$tmp/old-section.ru.alula.md" ошибка "AL-123" "## Примитивы" "## Внешние функции"
mk_en "$tmp/old-section.en.alula.md" '; record(7, "a")' "$(printf '## Primitives\n\n| name | parameters | result | class | reads | writes |\n|---|---|---|---|---|---|\n| record | code int; label str | — | acting | — | — |')"
old_probe "## Primitives" "$tmp/old-section.en.alula.md" ошибка "AL-123" "## Primitives" "## External functions"
"$PYTHON" "$tools" fill "$probes/funcs.ru.alula.md" "$tmp/funcs.ru.alula.md" "FUNCTIONS=внешняя функция читать(x число) изменчивая -> число"
old_probe "внешняя функция в файле функций" "$tmp/funcs.ru.alula.md" ошибка "AL-123" "внешн"

echo "== пробы хвоста параметров AL-129"
tail_total=0; tail_ok=0
tail_probe() {
  tail_total=$((tail_total + 1))
  if probe_run "$@"; then tail_ok=$((tail_ok + 1)); else red "проба хвоста $1"; fi
}
write_registry "$REG_TAIL"
mk_en "$tmp/tail.en.alula.md" '; record(7, label: "a", note: "b")' "$(ext_en "$EN_TAIL")"
tail_probe "объявление с хвостом и вызов с парами (en)" "$tmp/tail.en.alula.md" чисто
mk_ru "$tmp/tail.ru.alula.md" '; record(7, label: "a", note: "b")' "$(ext_ru "$RU_TAIL")"
tail_probe "объявление с хвостом и вызов с парами (ru)" "$tmp/tail.ru.alula.md" чисто
mk_en "$tmp/tail-none.en.alula.md" '; record(7)' "$(ext_en "$EN_TAIL")"
tail_probe "вызов без пар" "$tmp/tail-none.en.alula.md" чисто
mk_en "$tmp/tail-author.en.alula.md" '' "$(ext_en "$EN_TAIL")" "$(code_block 'fn total(a int, ...rest: str) -> int => a')"
tail_probe "хвост у функции автора" "$tmp/tail-author.en.alula.md" ошибка "AL-129"
mk_en "$tmp/tail-twice.en.alula.md" '; record(7, label: "a", label: "b")' "$(ext_en "$EN_TAIL")"
tail_probe "повтор ключа в вызове" "$tmp/tail-twice.en.alula.md" ошибка "AL-129" "label"

echo "== сверка с реестром: семь видов расхождения"
rec_total=0; rec_ok=0
rec_probe() {
  rec_total=$((rec_total + 1))
  rec_name=$1; rec_row=$2; rec_want=$3; shift 3
  write_registry "$rec_row"
  if probe_run "сверка: $rec_name" "$tmp/rec.alula.md" "$rec_want" "$@"; then rec_ok=$((rec_ok + 1)); else red "сверка: $rec_name"; fi
}
mk_en "$tmp/rec.alula.md" '; record(7, "a")' "$(ext_en "$EN_ONE")"
write_registry "$REG_ONE"
probe_run "сверка: контрольная, точное совпадение" "$tmp/rec.alula.md" чисто || red "сверка: контрольная проба"
rec_probe "имя" '| record_all | code: int; label: text | — | acting | — | — |' ошибка "функция record:" "нет в реестре хозяина"
rec_probe "число параметров" '| record | code: int | — | acting | — | — |' ошибка "функция record:" "число параметров в файле 2, в реестре 1"
rec_probe "тип параметра" '| record | code: int; label: int | — | acting | — | — |' ошибка "функция record:" "параметр 2 в файле строка, в реестре число"
rec_probe "результат" '| record | code: int; label: text | int | acting | — | — |' ошибка "функция record:" "результат"
rec_probe "класс" '| record | code: int; label: text | — | volatile | — | — |' ошибка "функция record:" "класс в файле действующая, в реестре изменчивая"
rec_probe "нет в реестре" '' ошибка "функция record:" "нет в реестре хозяина"
rec_probe "лишнее в реестре (ожидается ок)" "$(printf '%s\n%s' "$REG_ONE" '| other | — | int | volatile | — | — |')" чисто

# ---- (3) examples -----------------------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
ex_out=$("$alula" test examples 2>&1 | tail -1)
case "$ex_out" in
  "66 of 66 scenarios passed") ex_line="examples 66 из 66" ;;
  *) ex_line="examples ${ex_out}"; red "alula test examples: $ex_out" ;;
esac

# ---- (4) старые формы в данных ----------------------------------------------------------------------------------------------------------------

echo "== вызвать( и ## Примитивы в данных"
n_call=$(grep -rnE "(^|[^[:alnum:]_])(вызвать|call)\(" examples spec/samples src/machine_agent/cases 2>/dev/null | wc -l | tr -d ' ')
n_prim=$(grep -rn "^## Примитивы\|^## Primitives" examples spec/samples src/machine_agent/cases 2>/dev/null | grep -v "registry.md" | wc -l | tr -d ' ')
[ "$n_call" = 0 ] || red "вызвать( в данных: $n_call"
[ "$n_prim" = 0 ] || red "## Примитивы в данных: $n_prim"

# ---- (5)(6)(7) круг, схема, деревья до и после -------------------------------------------------------------------------------------------------

echo "== круг текст → дерево → текст, схема, деревья до миграции"
machines=$(ls examples/*.alula.md spec/samples/agent-step.alula.md spec/samples/agent-step.en.alula.md src/machine_agent/cases/agent-step-methodology-222.alula.txt src/machine_agent/cases/agent-step-methodology-222.en.alula.txt \
  src/machine_text_eq/cases/agent-step.alula.md src/machine_text_eq/cases/format-examples.alula.md src/machine_nested/cases/meeting-examples.alula.md 2>/dev/null | sort -u)
# файлы определений (не машины) в круг не входят: у них нет дерева
n_circle=0; n_circle_ok=0; n_schema=0; n_schema_ok=0
i=0
trees=""
for f in $machines; do
  i=$((i + 1))
  n_circle=$((n_circle + 1)); n_schema=$((n_schema + 1))
  lang=ru; case "$(head -8 "$f")" in *"language: en"*) lang=en ;; esac
  t1=$tmp/c$i.1.json; m2=$tmp/c$i.2.alula.md; t2=$tmp/c$i.2.json; m3=$tmp/c$i.3.alula.md
  if "$alula" compile "$f" --no-check -o "$t1" >"$tmp/c$i.log" 2>&1 \
     && "$alula" render "$t1" --language "$lang" -o "$m2" >>"$tmp/c$i.log" 2>&1 \
     && cp "$m2" "$tmp/c$i.2.alula.md.keep" \
     && "$alula" compile "$m2" --no-check -o "$t2" >>"$tmp/c$i.log" 2>&1 \
     && "$alula" render "$t2" --language "$lang" -o "$m3" >>"$tmp/c$i.log" 2>&1 \
     && "$PYTHON" "$tools" treesame "$t1" "$t2" && cmp -s "$m2" "$m3" \
     && [ "$("$PYTHON" "$tools" decls "$f")" = "$("$PYTHON" "$tools" decls "$m2")" ]; then
    n_circle_ok=$((n_circle_ok + 1))
  else
    red "круг: $f"; head -3 "$tmp/c$i.log"
  fi
  if [ -f "$t1" ]; then trees="$trees $t1"; else red "нет дерева: $f"; fi
done
if [ -n "$trees" ]; then
  # shellcheck disable=SC2086
  if "$PYTHON" "$tools" schema src/machine/schema/machine-2.schema.json $trees; then n_schema_ok=$n_schema; else red "схема machine-2"; fi
else
  red "нет деревьев для схемы"
fi
# деревья, которые лежат готовыми рядом с машинами (examples/*.alula.json), тоже по схеме
for j in examples/*.alula.json; do
  n_schema=$((n_schema + 1))
  if "$PYTHON" "$tools" schema src/machine/schema/machine-2.schema.json "$j"; then n_schema_ok=$((n_schema_ok + 1)); else red "схема: $j"; fi
done

# деревья до миграции: из базового коммита, программой базового коммита
old_exe=${OLD_ALULA:-}
if [ -z "$old_exe" ]; then
  echo "== сборка программы базового коммита $base"
  mkdir -p "$tmp/base"
  git archive "$base" | tar -x -C "$tmp/base"
  ( cd "$tmp/base" && nova build src/alula.nv -o "$tmp/base/alula.exe" >"$tmp/base-build.log" 2>&1 ) || { tail -10 "$tmp/base-build.log"; red "сборка базы"; }
  old_exe=$tmp/base/alula.exe
fi
n_eq=0; n_eq_ok=0
i=0
for f in $machines; do
  i=$((i + 1))
  n_eq=$((n_eq + 1))
  old_file=$tmp/old$i.$(basename "$f")
  if ! git show "$base:$f" >"$old_file" 2>/dev/null; then n_eq=$((n_eq - 1)); continue; fi
  if "$old_exe" compile "$old_file" --no-check -o "$tmp/old$i.json" >/dev/null 2>"$tmp/old$i.err" \
     && "$PYTHON" "$tools" treeeq "$tmp/old$i.json" "$tmp/c$i.1.json" \
     && "$PYTHON" "$tools" primnames "$tmp/old$i.json" "$tmp/c$i.1.json"; then
    n_eq_ok=$((n_eq_ok + 1))
  else
    red "дерево до и после миграции: $f"; head -2 "$tmp/old$i.err"
  fi
done

# ---- (9) корпус ----------------------------------------------------------------------------------------------------------------------------

echo "== корпус: таблицы хозяев с их registry.md"
n_tables=0; n_diverge=0
if [ -z "${ALULA_CORPUS:-}" ]; then
  red "не задан ALULA_CORPUS (папки с таблицами хозяев, переведёнными на 2.24, каждая со своим registry.md)"
else
  for d in $ALULA_CORPUS; do
    if [ ! -f "$d/registry.md" ]; then red "корпус: в $d нет registry.md"; continue; fi
    for t in "$d"/*.alula.md; do
      [ -f "$t" ] || continue
      n_tables=$((n_tables + 1))
      c_out=$("$alula" check "$t" --registry "$d/registry.md" 2>&1); c_rc=$?
      if [ "$c_rc" -ne 0 ]; then n_diverge=$((n_diverge + 1)); echo "  $t"; echo "$c_out" | head -4; fi
    done
  done
  [ "$n_tables" -gt 0 ] || red "корпус пуст"
  [ "$n_diverge" -eq 0 ] || red "корпус: расхождений $n_diverge"
fi

# ---- (10) nova test ------------------------------------------------------------------------------------------------------------------------

n_test_ok=0; n_test=0
if [ "${ACCEPT_175_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_175_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  for dir in machine machine_table machine_text machine_text_unicode machine_run engine machine_nested_run machine_text_lang machine_nested machine_agent machine_agent_en machine_text_render machine_text_eq machine_text_fmt alula_scenarios alula_eq alula_cli; do
    echo "== nova test src/$dir"
    t_out=$(nova test "src/$dir" --jobs 2 2>&1 | tail -3)
    t_pass=$(echo "$t_out" | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\1/p' | tail -1)
    t_fail=$(echo "$t_out" | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\2/p' | tail -1)
    t_pass=${t_pass:-0}; t_fail=${t_fail:-1}
    n_test=$((n_test + t_pass + t_fail)); n_test_ok=$((n_test_ok + t_pass))
    [ "$t_fail" = 0 ] || red "nova test src/$dir: $t_fail красных"
    sleep 5
  done
  test_line="nova test $n_test_ok из $n_test"
fi

# ---- итог -----------------------------------------------------------------------------------------------------------------------------------------

[ "$old_ok" = "$old_total" ] || red "пробы старых форм: $old_ok из $old_total"
[ "$tail_ok" = "$tail_total" ] || red "пробы хвоста: $tail_ok из $tail_total"
[ "$rec_ok" = "$rec_total" ] && [ "$rec_total" = 7 ] || red "виды сверки: $rec_ok из $rec_total"

summary="пробы старых форм AL-123: $old_ok из $old_total; хвост: $tail_ok проб из $tail_total; $ex_line; вызвать( $n_call; Примитивы $n_prim; круг $n_circle_ok из $n_circle; схема $n_schema_ok из $n_schema; деревьев равных $n_eq_ok из $n_eq; сверка: видов $rec_ok из $rec_total, таблиц $n_tables, расхождений $n_diverge; $test_line"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 175: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 175 ($fails красных): $summary"
exit 1
