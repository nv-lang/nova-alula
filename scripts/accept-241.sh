#!/bin/sh
# Зачем: одна команда-критерий задачи 241 «Алула 0.9.1: библиотека не пишет в данные машины» (пакет alula 0.9.1, язык 2.26).
# Проверяет: (1) `alula version` печатает `alula 0.9.1 (Alula 2.26, machine/2)`, nova.toml — 0.9.1;
#     (2) библиотека «Пауза»: libs/pause.alula.md и libs/pause.en.alula.md — блоки Методики (хеши e7d85aa43589 и d254e6297f61), своё перечисление
#         ПричинаПаузы/PauseReason и своё данное причина/reason, нет параметра код_остановки/halt_code и строки остановка/stop_reason в `## Требует`;
#         копии в examples/libs/ и spec/samples/libs/ равны libs/; ни один образец пакета не называет код_остановки/halt_code; хеш каждого подключения
#         в образцах равен хешу файла рядом; `tools/migrate-alula-226.py --dry-run` на образцах — «файлов 0, мест 0»;
#     (3) спецификация: alula-spec.md и alula-spec.en.md — CRLF, по 70 строк ограждений; блок «Пауза» раздела 9 по нормализованному тексту — те же хеши;
#         ALULA_SPEC_SOURCE=<папка> (необязательно) — файлы спецификации равны файлам Методики побайтно;
#     (4) встроенного фрагмента нет: нет src/machine_text/fragments/, нет embed_str фрагмента, pause_param_keys, pause_arg_names, pause_behavior_words;
#         слова fragment/фрагмент — только в журнале изменений и в истории (spec/alula-changelog*.md, docs/history.md, scripts/accept-1*/accept-2[0-3]*), в текстах Методики
#         (spec/alula-spec*.md, spec/samples/) и их охраняемых копиях 2.25 (src/machine_agent/cases/), в скрипте миграции 2.25 и в именах отвергаемых старых форм
#         (заголовок «Раскрытие фрагмента» 2.13, AL-44; ключ дерева `fragments`);
#     (5) скрипт миграции: examples 2.25 (вершина 35c2107) переносятся на новую Паузу без мест, `alula test` — все;
#     (6) наборы машин: копия набора методики (ALULA_METHODOLOGY_MACHINES, 508 тестов) переносится скриптом, все деревья — 2.26, `alula test` — все;
#         набор продукта (ALULA_PRODUCT_MACHINES, 81 тест) — то же;
#     (7) `alula test examples` — все; `nova test` всех папок пакета с тестами (по одной, `--jobs 2`); стражи дерева.
# Не проверяет: публикацию пакета (метка v0.9.1 — по слову владельца); правку наборов машин в их репозиториях (копии во временной папке).
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git.
# Использование: sh scripts/accept-241.sh   (из корня дерева пакета; последняя строка «ПРИНЯТО 241: …» и код 0, иначе «НЕ ПРИНЯТО 241 …» и код 1)
#   ALULA=<путь>                       готовая программа alula вместо сборки в target/alula.exe
#   ALULA_METHODOLOGY_MACHINES=<папка> набор машин методики (alula-machines); без него шаг красный
#   ALULA_PRODUCT_MACHINES=<папка>     набор машин продукта (machines/product); без него шаг красный
#   ALULA_SPEC_SOURCE=<папка>          файлы спецификации Методики (alula-spec.md, alula-spec.en.md) для сверки побайтно
#   ACCEPT_241_SKIP_NOVA_TEST=1        пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: слово владельца, 2026-10-27: «да, супер быстро» (чат Методики; задание 241 интегратора).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2
export PYTHONUTF8=1

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 241: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }
migrate="$PYTHON tools/migrate-alula-226.py"
base225=35c2107

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 241: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 241: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

tests_of() { "$alula" test "$1" 2>&1 | tail -1 | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1 \2/p'; }

# ---- (1) версия ---------------------------------------------------------------------------------------------------------------------------------

echo "== alula version"
want_version="alula 0.9.1 (Alula 2.26, machine/2)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"
grep -q '^version = "0.9.1"' nova.toml || red "nova.toml: version не 0.9.1"

# ---- (2) библиотека «Пауза», копии, хеши ------------------------------------------------------------------------------------------------------------

echo "== библиотека Пауза"
"$PYTHON" - <<'EOF' >"$tmp/pause.out" 2>&1 || { red "библиотека Пауза"; cat "$tmp/pause.out"; }
import glob, importlib.util, os, re, sys
spec = importlib.util.spec_from_file_location('m', 'tools/migrate-alula-226.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bad = 0
def no(why):
    global bad; bad += 1; print(why)
ru = open('libs/pause.alula.md', encoding='utf-8').read(); en = open('libs/pause.en.alula.md', encoding='utf-8').read()
if m.lib_hash(ru) != 'e7d85aa43589': no('libs/pause.alula.md: хеш %s, Методика ждёт e7d85aa43589' % m.lib_hash(ru))
if m.lib_hash(en) != 'd254e6297f61': no('libs/pause.en.alula.md: хеш %s, Методика ждёт d254e6297f61' % m.lib_hash(en))
for want in ['тип ПричинаПаузы перечисление', '| причина | ?ПричинаПаузы | пусто |']:
    if want not in ru: no('libs/pause.alula.md: нет «%s»' % want)
for want in ['type PauseReason enum', '| reason | ?PauseReason | none |']:
    if want not in en: no('libs/pause.en.alula.md: нет «%s»' % want)
for f in ['libs/pause.alula.md', 'libs/pause.en.alula.md']:
    for copy in ['examples/' + f, 'spec/samples/' + f]:
        if not os.path.exists(copy) or open(copy, encoding='utf-8').read() != open(f, encoding='utf-8').read(): no('%s не равен %s' % (copy, f))
old = re.compile(r'код_остановки|halt_code|\| остановка \| "cancel_request"|\| stop_reason \| "cancel_request"')
for f in glob.glob('libs/*.md') + glob.glob('examples/**/*.alula.md', recursive=True) + glob.glob('spec/samples/**/*.md', recursive=True):
    for i, l in enumerate(open(f, encoding='utf-8').read().split('\n')):
        if old.search(l): no('%s:%d: старая форма Паузы: %s' % (f, i + 1, l.strip()[:80]))
for f in glob.glob('examples/*.alula.md') + glob.glob('spec/samples/*.alula.md'):
    lines = open(f, encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines):
        mf = re.match(r'^- (?:Файл|File): (\S+)$', l)
        if mf and i + 1 < len(lines):
            mh = re.match(r'^- (?:Хеш|Hash): ([0-9a-f]{12})$', lines[i + 1])
            lib = os.path.join(os.path.dirname(f), mf.group(1))
            if not mh or not os.path.exists(lib) or m.lib_hash(open(lib, encoding='utf-8').read()) != mh.group(1):
                no('%s:%d: хеш подключения %s не равен хешу файла' % (f, i + 2, mf.group(1)))
sys.exit(1 if bad else 0)
EOF
dry=$($migrate --dry-run examples spec/samples libs 2>&1 | tail -1)
[ "$dry" = "итог: файлов 0, мест 0" ] || red "migrate --dry-run на образцах пакета: $dry"

# ---- (3) спецификация ---------------------------------------------------------------------------------------------------------------------------

echo "== спецификация"
"$PYTHON" - "${ALULA_SPEC_SOURCE:-}" <<'EOF' >"$tmp/spec.out" 2>&1 || { red "спецификация"; cat "$tmp/spec.out"; }
import importlib.util, os, re, sys
spec = importlib.util.spec_from_file_location('m', 'tools/migrate-alula-226.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bad = 0
want = {'spec/alula-spec.md': ('# Библиотека: Пауза', 'e7d85aa43589'), 'spec/alula-spec.en.md': ('# Library: Pause', 'd254e6297f61')}
for f, (head, h) in want.items():
    raw = open(f, 'rb').read()
    if raw.count(b'\n') != raw.count(b'\r\n'): print('%s: не CRLF' % f); bad += 1
    text = raw.decode('utf-8').replace('\r\n', '\n')
    fences = sum(1 for l in text.split('\n') if l.startswith('```'))
    if fences != 70: print('%s: строк ограждений %d, нужно 70' % (f, fences)); bad += 1
    blk = re.search(r'^````\n(' + re.escape(head) + r'\n.*?)^````$', text, re.S | re.M)
    if not blk: print('%s: нет блока «%s» в четырёхкавычном ограждении' % (f, head)); bad += 1
    elif m.lib_hash(blk.group(1)) != h: print('%s: хеш блока %s, Методика ждёт %s' % (f, m.lib_hash(blk.group(1)), h)); bad += 1
    src = sys.argv[1]
    if src:
        other = os.path.join(src, os.path.basename(f))
        if open(other, 'rb').read() != raw: print('%s не равен %s' % (f, other)); bad += 1
sys.exit(1 if bad else 0)
EOF

# ---- (4) встроенного фрагмента нет ------------------------------------------------------------------------------------------------------------------

echo "== фрагмент"
[ -d src/machine_text/fragments ] && red "src/machine_text/fragments/ есть"
grep -rnE 'embed_str\("fragments/|pause_param_keys|pause_arg_names|pause_behavior_words|behavior_words_' src >"$tmp/frag-code.out" && { red "код встроенной Паузы: $(wc -l <"$tmp/frag-code.out") строк"; head -5 "$tmp/frag-code.out"; }
grep -rniE 'fragment|фрагмент' . --exclude-dir=.git --exclude-dir=target --exclude-dir=__pycache__ \
  | grep -vE '^\./spec/alula-changelog(\.en)?\.md:|^\./docs/history\.md:|^\./scripts/accept-(1[0-9][0-9]|2[0-3][0-9])[^/]*:|^\./scripts/accept-(1[0-9][0-9]|2[0-3][0-9])/|^\./scripts/accept-241\.sh:'   | grep -vE '^\./spec/alula-spec(\.en)?\.md:|^\./spec/samples/|^\./src/machine_agent/cases/|^\./tools/migrate-alula-226\.py:'   | grep -viE 'Раскрытие фрагмента|раскрытие фрагмента|Fragment expansion|fragments' >"$tmp/frag-words.out"
[ -s "$tmp/frag-words.out" ] && { red "слова fragment/фрагмент вне журнала изменений: $(wc -l <"$tmp/frag-words.out") строк"; head -8 "$tmp/frag-words.out" | cut -c1-200; }

# ---- (5) скрипт миграции на образцах 2.25 ---------------------------------------------------------------------------------------------------------

echo "== скрипт миграции на examples 2.25 ($base225)"
mkdir -p "$tmp/ex225"
git archive "$base225" examples | tar -x -C "$tmp/ex225" || red "git archive $base225 examples"
$migrate --alula "$alula" "$tmp/ex225/examples" >"$tmp/mig1.out" 2>&1; code=$?
[ "$code" = 0 ] || { red "миграция examples 2.25: код $code"; tail -5 "$tmp/mig1.out"; }
grep -rl 'код_остановки' "$tmp/ex225/examples" >/dev/null 2>&1 && red "перенесённые examples называют код_остановки"
set -- $(tests_of "$tmp/ex225/examples")
[ "${1:-0}" = "${2:-x}" ] && [ "${1:-0}" -gt 0 ] || red "alula test на перенесённых examples: ${1:-?} из ${2:-?}"
again=$($migrate --alula "$alula" "$tmp/ex225/examples" 2>&1 | tail -1)
[ "$again" = "итог: файлов 0, мест 0" ] || red "повторный запуск миграции: $again"

# ---- (6) наборы машин ----------------------------------------------------------------------------------------------------------------------------

set_check() {
  if [ -z "$2" ] || [ ! -d "$2" ]; then red "набор $1: назовите папку (ALULA_METHODOLOGY_MACHINES / ALULA_PRODUCT_MACHINES)"; return; fi
  mkdir -p "$tmp/$1" && cp -r "$2/." "$tmp/$1/"
  $migrate --alula "$alula" "$tmp/$1" >"$tmp/$1.mig" 2>&1; mig_code=$?
  grep -v '^перенесён' "$tmp/$1.mig" | sed "s|$tmp/||" | sed "s/^/  $1: /"
  stale=$("$PYTHON" -c "import glob,json,os,sys; print(sum(1 for f in glob.glob(os.path.join(sys.argv[1],'**','*.alula.json'),recursive=True) if json.load(open(f,encoding='utf-8')).get('alula_version')!='2.26'))" "$tmp/$1")
  set -- "$1" "$2" "$3" $(tests_of "$tmp/$1")
  why=""
  [ "$mig_code" = 0 ] || why="миграция: код $mig_code"
  [ "$stale" = 0 ] || why="$why; деревьев не 2.26: $stale"
  [ "${4:-0}" = "$3" ] && [ "${5:-0}" = "$3" ] || why="$why; alula test ${4:-?} из ${5:-?} (нужно $3 из $3)"
  if [ -z "$why" ]; then eval "set_$1=\"${4} из ${5}\""; else red "набор $1: ${why#; }"; eval "set_$1=\"${4:-?} из ${5:-?}\""; fi
}
set_methodology="?"; set_product="?"
echo "== набор методики"
set_check methodology "${ALULA_METHODOLOGY_MACHINES:-}" 508
echo "== набор продукта"
set_check product "${ALULA_PRODUCT_MACHINES:-}" 81

# ---- (7) examples, nova test, стражи -------------------------------------------------------------------------------------------------------------

echo "== alula test examples"
set -- $(tests_of examples)
if [ "${1:-0}" = "${2:-x}" ] && [ "${1:-0}" -gt 0 ]; then ex_line="examples $1 из $2"; else ex_line="examples ${1:-?} из ${2:-?}"; red "alula test examples: $ex_line"; fi
"$PYTHON" tools/check-alula-samples.py >"$tmp/samples.out" 2>&1 || { red "check-alula-samples.py"; tail -5 "$tmp/samples.out"; }
"$PYTHON" tools/check-alula-translation.py >"$tmp/translation.out" 2>&1 || { red "check-alula-translation.py"; tail -5 "$tmp/translation.out"; }

if [ "${ACCEPT_241_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_241_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 241: nova не в PATH"; exit 2; }
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

summary="alula 0.9.1 (Alula 2.26, machine/2); $ex_line; methodology $set_methodology; product $set_product; $test_line; Пауза e7d85aa43589/d254e6297f61; фрагмента нет"
if [ "$fails" -eq 0 ]; then
  echo "ПРИНЯТО 241: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 241 ($fails красных): $summary"
exit 1
