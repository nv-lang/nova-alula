#!/bin/sh
# Зачем: запустить всех стражей дерева (scripts/guards/check-*) одним набором и сосчитать вердикты,
#     чтобы хук и CI не перечисляли их поимённо: новый check-* подключается построением (REQ-24).
# Проверяет: каждый check-* выполняется, печатает последней строкой вердикт одной из четырёх форм
#     («ок:», «судить нечего:», «пропущено:», «FAIL») и код возврата не противоречит вердикту.
# Не проверяет: сами правила стражей; стражей вне маски (guard-secrets, guard-commit-message): их
#     зовут свои хуки и CI явно.
# Правило: AGENTS.md п.8 (проверки до пуша), ADR-0006; контракт вердиктов — REQ-35.
#
# Использование: sh scripts/guards/run-all.sh [--root <папка>] [--index] [--ci] [--dir <папка стражей>]
# Код возврата решается до печати; в режиме --ci «пропущено» у обязательного стража — красный.
set -u

here=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$here/lib/find-python.sh"

guards_dir=$here
root=
index=0
ci=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dir) guards_dir=$2; shift 2 ;;
    --root) root=$2; shift 2 ;;
    --index) index=1; shift ;;
    --ci) ci=1; shift ;;
    *) echo "FAIL: предпосылка: неизвестный аргумент $1" >&2; exit 2 ;;
  esac
done

find_python || exit 1

tmp=$(mktemp -d 2>/dev/null) || { echo "FAIL: предпосылка: не создать временную папку" >&2; exit 1; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

n_ok=0
n_nothing=0
n_skipped=0
n_fail=0
count=0

# tally <вид>: счёт вердиктов по видам.
tally() {
  case "$1" in
    ok) n_ok=$((n_ok + 1)) ;;
    nothing) n_nothing=$((n_nothing + 1)) ;;
    skipped) n_skipped=$((n_skipped + 1)) ;;
    *) n_fail=$((n_fail + 1)) ;;
  esac
}

# run_one <скрипт>: запуск стража с общими аргументами.
run_one() {
  script=$1
  set -- "$script"
  [ -n "$root" ] && set -- "$@" --root "$root"
  [ "$index" = 1 ] && set -- "$@" --index
  [ "$ci" = 1 ] && set -- "$@" --ci
  script=$1
  shift
  case "$script" in
    *.py) $PYTHON "$script" "$@" ;;
    *.sh) sh "$script" "$@" ;;
    *) return 127 ;;
  esac
}

: > "$tmp/table"
# порядок стражей не зависит от локали (вывод двух прогонов под разными локалями совпадает построчно)
for guard in "$guards_dir"/check-*; do
  [ -f "$guard" ] && printf '%s\n' "$guard"
done | LC_ALL=C sort > "$tmp/list"
while IFS= read -r guard; do
  name=$(basename "$guard")
  count=$((count + 1))
  run_one "$guard" > "$tmp/out.$count" 2>"$tmp/err.$count" < /dev/null
  rc=$?
  last=$(tail -n 1 "$tmp/out.$count")
  case "$last" in
    "ок: "*) kind=ok ;;
    "судить нечего: "*) kind=nothing ;;
    "пропущено: "*) kind=skipped ;;
    "FAIL"*) kind=fail ;;
    *) kind=fail; last="FAIL: вердикта нет (код $rc)" ;;
  esac
  if [ "$kind" != fail ] && [ "$rc" -ne 0 ]; then
    kind=fail
    last="FAIL: код возврата $rc не совпал с вердиктом ($last)"
  fi
  if [ "$kind" = fail ] && [ "$rc" -eq 0 ]; then
    last="FAIL: код возврата 0 при вердикте FAIL ($last)"
  fi
  if [ "$kind" = skipped ] && [ "$ci" = 1 ]; then
    last="$last [в CI пропуск обязательного стража — красный]"
    echo "red" >> "$tmp/ci-red"
  fi
  tally "$kind"
  printf '%s\t%s\t%s\n' "$name" "$kind" "$last" >> "$tmp/table"
done < "$tmp/list"

if [ "$count" -eq 0 ]; then
  echo "FAIL: мишень потеряна: нет ни одного стража check-* в $(basename "$guards_dir")"
  exit 1
fi

rc=0
[ "$n_fail" -gt 0 ] && rc=1
[ -f "$tmp/ci-red" ] && rc=1

i=0
while [ "$i" -lt "$count" ]; do
  i=$((i + 1))
  lines=$(wc -l < "$tmp/out.$i")
  if [ "$lines" -gt 1 ]; then
    echo "== $(sed -n "${i}p" "$tmp/table" | cut -f1)"
    sed '$d' "$tmp/out.$i"
  fi
  if [ -s "$tmp/err.$i" ]; then
    echo "== stderr $(sed -n "${i}p" "$tmp/table" | cut -f1)"
    cat "$tmp/err.$i"
  fi
done

echo "страж -> вердикт"
tab=$(printf '	')
while IFS=$tab read -r name kind verdict; do
  printf '%s -> %s\n' "$name" "$verdict"
done < "$tmp/table"
echo "итого: ок $n_ok, судить нечего $n_nothing, пропущено $n_skipped, FAIL $n_fail"
exit "$rc"
