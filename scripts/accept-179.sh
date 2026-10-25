#!/bin/sh
# accept-179.sh - the criterion of task 179: the contract of the host `bind_pure` / `bind_volatile` / `bind_acting` (AL-130).
#
# Why: the class of an external function (pure, volatile, acting) must not be bypassed by its implementation: a volatile one does not write
#     the environment, a pure one does not read it. Types prove part of it (the type of the environment), the rest is proved by the guard
#     of the imports and by the test host, and the specification says so (section 7a, "not proven by types").
# Checks (one command, a red line names the step):
#   1. the text of the specification (ru, en): the three bindings and the honest record "not proven by types";
#   2. negative compilations: `nova check` of the files `scripts/negative-179/*.nv` must fail with the code written in the file line
#      `// expect: <CODE>` (one or more codes); the files go in three groups: write through ReadEnv, forged ActEnv, a wrong class in `bind_*`;
#   3. the test host: `nova test src/host` and `nova test src/host_impls` (the counters by class, the check of the version of the world,
#      a bypass through a closure is caught);
#   4. the guard of the imports of the implementations (`scripts/guards/check-impl-effects.py`) on its five samples
#      (one clean, four violating) and on the real module of the implementations;
#   5. `nova check --strict-effects` of the module of the implementations: no remarks; `nova info`: the effect surface is empty.
# Does not check: that every declared external function of a machine file is bound (the check against the file is made when a file is loaded,
#     task 181); the other folders of the package (the full `nova test src` is run by the acceptance of the epic).
# Rule: task 179, criterion AC-2; the epic 183.
#
# Usage: sh scripts/accept-179.sh        (the Nova Oracle environment is set: `nova` on PATH, NOVA_STD_PATH and the others; `NOVA=<path>` overrides)
# The last line is the verdict: `ПРИНЯТО 179: ...` (code 0) or `КРАСНОЕ 179: ...` (code 1).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
NOVA=${NOVA:-nova}
JOBS=${JOBS:-2}
. "$here/guards/lib/find-python.sh"
find_python || { echo "КРАСНОЕ 179: предпосылка: нет python"; exit 1; }

tmp=$(mktemp -d 2>/dev/null) || { echo "КРАСНОЕ 179: предпосылка: нет временной папки"; exit 1; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

reds=0
red() {
  echo "красное: $*"
  reds=$((reds + 1))
}

strip_ansi() { sed 's/\x1b\[[0-9;]*m//g'; }

# 1. The text of the specification.
echo "== 1. спецификация (раздел 7а, AL-130)"
for word in bind_pure bind_volatile bind_acting; do
  for f in spec/alula-spec.md spec/alula-spec.en.md; do
    grep -q "$word" "$f" || red "в $f нет $word"
  done
done
grep -q "Не доказано типами" spec/alula-spec.md || red "в spec/alula-spec.md нет записи «Не доказано типами»"
grep -q "Not proven by types" spec/alula-spec.en.md || red "в spec/alula-spec.en.md нет записи «Not proven by types»"
grep -q "AL-130" spec/alula-changelog.md || red "в spec/alula-changelog.md нет метки AL-130"

# 2. Negative compilations: three groups.
echo "== 2. отрицательные компиляции"
neg_dir=scripts/negative-179
neg_groups=0
neg_ok=0
neg_check() { # neg_check <group> <file>...
  group=$1
  shift
  group_ok=1
  for f in "$@"; do
    if [ ! -f "$neg_dir/$f" ]; then
      red "группа $group: нет файла $neg_dir/$f"
      group_ok=0
      continue
    fi
    out="$tmp/neg.out"
    "$NOVA" check "$neg_dir/$f" > "$out" 2>&1
    rc=$?
    strip_ansi < "$out" > "$out.txt"
    if [ "$rc" -eq 0 ]; then
      red "группа $group: $f компилируется, а должна не компилироваться"
      group_ok=0
      continue
    fi
    for code in $(sed -n 's|^// expect: *||p' "$neg_dir/$f"); do
      if ! grep -q "$code" "$out.txt"; then
        red "группа $group: $f не дал ожидаемого кода $code"
        group_ok=0
      fi
    done
  done
  neg_groups=$((neg_groups + 1))
  [ "$group_ok" = 1 ] && neg_ok=$((neg_ok + 1))
}
neg_check "запись через ReadEnv" write_through_readenv.nv read_private_field.nv
neg_check "подделка ActEnv" forge_actenv.nv
neg_check "не тот класс в bind_*" acting_in_volatile.nv volatile_in_acting.nv env_in_pure.nv
echo "отрицательных компиляций $neg_ok из $neg_groups"

# 3. The test host.
echo "== 3. тест-хост"
for dir in host host_impls; do
  if [ ! -d "src/$dir" ]; then
    red "нет папки src/$dir"
    continue
  fi
  "$NOVA" test "src/$dir" --jobs "$JOBS" > "$tmp/test.$dir" 2>&1
  rc=$?
  strip_ansi < "$tmp/test.$dir" | tail -n 3
  [ "$rc" -eq 0 ] || red "nova test src/$dir: код $rc"
done
closure_caught=нет
if grep -q 'test "[a-z ]*closure' src/host/*_test.nv 2>/dev/null; then closure_caught=да; fi
[ "$closure_caught" = да ] || red "нет теста обхода через замыкание в src/host"

# 4. The guard of the imports on five samples and on the real module.
echo "== 4. страж импортов эффектных модулей"
samples=scripts/guards/samples/impl-effects
guard=scripts/guards/check-impl-effects.py
clean_n=0
caught_n=0
if [ ! -f "$guard" ]; then
  red "нет стража $guard"
else
  for s in clean_impls.nv bad_import_fs.nv bad_println.nv bad_raw_effect.nv bad_with_handler.nv; do
    if [ ! -f "$samples/$s" ]; then
      red "нет образца $samples/$s"
      continue
    fi
    $PYTHON "$guard" --files "$samples/$s" > "$tmp/guard.out" 2>&1
    rc=$?
    case "$s" in
      clean_*) if [ "$rc" -eq 0 ]; then clean_n=$((clean_n + 1)); else red "страж ругает чистый образец $s"; fi ;;
      *) if [ "$rc" -eq 1 ]; then caught_n=$((caught_n + 1)); else red "страж не поймал $s (код $rc)"; fi ;;
    esac
  done
  $PYTHON "$guard" > "$tmp/guard.real" 2>&1 || { red "страж на модуле реализаций"; cat "$tmp/guard.real"; }
fi
echo "страж 5 проб ($clean_n чистая, $caught_n пойманы)"

# 5. strict-effects and the effect surface.
echo "== 5. --strict-effects и effect_surface"
surface=не-пуста
if [ -f src/host_impls/impls.nv ]; then
  "$NOVA" check --strict-effects src/host_impls/impls.nv src/host > "$tmp/strict.out" 2>&1
  rc=$?
  strip_ansi < "$tmp/strict.out" | grep -v "^ok:" | tail -n 8
  [ "$rc" -eq 0 ] || red "nova check --strict-effects: код $rc"
  if strip_ansi < "$tmp/strict.out" | grep -qi "warning"; then red "nova check --strict-effects: замечания"; fi
  "$NOVA" info src/host_impls > "$tmp/info.out" 2>&1
  strip_ansi < "$tmp/info.out"
  if strip_ansi < "$tmp/info.out" | grep -q "Effect-surface: *∅"; then surface=пуста; else red "effect_surface не пуста"; fi
else
  red "нет модуля реализаций src/host_impls/impls.nv"
fi

if [ "$reds" -gt 0 ]; then
  echo "КРАСНОЕ 179: красных проверок $reds; отрицательных компиляций $neg_ok из $neg_groups; страж 5 проб ($clean_n чистая, $caught_n пойманы); effect_surface $surface"
  exit 1
fi
echo "ПРИНЯТО 179: отрицательных компиляций $neg_ok из $neg_groups; обход замыканием пойман; страж 5 проб ($clean_n чистая, $caught_n пойманы); effect_surface $surface"
exit 0
