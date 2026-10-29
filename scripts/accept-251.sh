#!/bin/sh
# Зачем: одна команда-критерий задачи 251 «Пример chat переехать в пакет nova-alula как examples/chat/» (выпуск «Алула 0.28»): машина чата продукта CrewHarness —
#     демо-машина пакета, таблица формата 0.27 и её 39 проверок, без ссылок на продукт.
# Проверяет: (1) `alula version` — `alula 0.27.0 (Алула 0.27)` (пример читается программой 0.27.0, код пакета не меняется);
#     (2) состав examples/chat/: chat.alula.md (шапка alula_version 0.27), chat.alula.json, libs/call_cancel.alula.md, journal.md, README.md и ровно 39 проверок tests/chat-*.alula.test.json;
#     (3) в examples/chat/ нет ссылок на продукт: номеров задач, `src/`, слов «продукт»/«product», «CrewHarness», «на Нове»;
#     (4) README примера называет демо-машину: одна беседа с агентом, ожидание, ответ, отказ, отмена, таймаут;
#     (5) `alula compile` таблицы — код 0; `alula test examples/chat` — 39 из 39; `alula test examples` — все, 105 (66 прежних и 39 chat; коды чата есть в examples/journal.md);
#     (6) ALULA_PRODUCT_MACHINES=<machines/product продукта>: 39 проверок побайтно равны проверкам chat продукта; таблица и дерево равны продуктовым,
#         кроме прозы над «## Типы», заголовка `title` дерева и хеша библиотеки (её проза без ссылок на продукт); `alula test` набора продукта — 81 из 81;
#     (7) `nova test` папок пакета, что встраивают examples/journal.md и списки examples/; стражи дерева.
# Не проверяет: публикацию (0.28 — по слову владельца); код и миграцию 0.28; продукт (из него ничего не удаляется).
# Предпосылки: Nova Oracle 0.1.0 в окружении (nova в PATH, setup-env.ps1), Python 3.9+, git.
# Использование: sh scripts/accept-251.sh   (из корня дерева пакета; последняя строка «ПРИНЯТО 251: …» и код 0, иначе «НЕ ПРИНЯТО 251 …» и код 1)
#   ALULA=<путь>                       готовая программа alula вместо сборки в target/alula.exe
#   ALULA_PRODUCT_MACHINES=<папка>     набор машин продукта (machines/product); без него шаг (6) пропускается
#   ACCEPT_251_SKIP_NOVA_TEST=1        пропустить nova test (только для разработки: приёмка идёт без пропуска)
# Правило: слово владельца, 2026-10-29: «по рекомендации, chat в пакет nova-alula» (задание 251 интегратора CrewHarness); в выпуск 0.28, отдельно не публиковать.
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root" || exit 2
# shellcheck disable=SC1091
. "$here/guards/lib/find-python.sh"
find_python || exit 2
export PYTHONUTF8=1

tmp=$(mktemp -d 2>/dev/null) || { echo "НЕ ПРИНЯТО 251: нет временной папки"; exit 2; }
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fails=0
red() { fails=$((fails + 1)); echo "КРАСНО: $*"; }
chat=examples/chat

if [ -n "${ALULA:-}" ]; then
  alula=$ALULA
else
  echo "== сборка программы alula"
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 251: nova не в PATH (setup-env.ps1 Nova Oracle 0.1.0)"; exit 2; }
  mkdir -p target
  nova build src/alula.nv -o target/alula.exe >"$tmp/build.log" 2>&1 || { tail -20 "$tmp/build.log"; echo "НЕ ПРИНЯТО 251: сборка не прошла"; exit 1; }
  alula=$root/target/alula.exe
fi

tests_of() { "$alula" test "$1" 2>&1 | tail -1 | sed -n 's/^\([0-9][0-9]*\) of \([0-9][0-9]*\) tests passed$/\1 \2/p'; }

# ---- (1) версия -------------------------------------------------------------------------------------------------------------------------------------

echo "== версия 0.27.0"
want_version="alula 0.27.0 (Алула 0.27)"
got_version=$("$alula" version 2>&1 | head -1)
[ "$got_version" = "$want_version" ] || red "alula version: «$got_version», нужно «$want_version»"

# ---- (2) состав -------------------------------------------------------------------------------------------------------------------------------------

echo "== состав $chat"
for f in chat.alula.md chat.alula.json libs/call_cancel.alula.md journal.md README.md; do
  [ -f "$chat/$f" ] || red "$chat/$f: нет файла"
done
n_tests=$(ls "$chat"/tests/chat-*.alula.test.json 2>/dev/null | wc -l | tr -d ' ')
[ "$n_tests" = 39 ] || red "$chat/tests: проверок chat-*.alula.test.json $n_tests, нужно 39"
others=$(ls "$chat"/tests 2>/dev/null | grep -v '^chat-.*\.alula\.test\.json$' | head -3)
[ -z "$others" ] || red "$chat/tests: лишние файлы: $others"
if [ -f "$chat/chat.alula.md" ]; then
  grep -q '^- alula_version: 0\.27$' "$chat/chat.alula.md" || red "$chat/chat.alula.md: шапка не alula_version 0.27"
fi

# ---- (3) без ссылок на продукт ----------------------------------------------------------------------------------------------------------------------

echo "== ссылки на продукт"
if [ -d "$chat" ]; then
  refs=$(grep -rn -i -E '(задач[аиуе]?|task) ?[0-9]{3}|src/|продукт|product|crewharness|crew_harness|crew-harness|на нове' "$chat" | head -5)
  [ -z "$refs" ] || { red "$chat: ссылки на продукт"; echo "$refs" | cut -c1-200; }
fi

# ---- (4) README примера -----------------------------------------------------------------------------------------------------------------------------

echo "== README примера"
if [ -f "$chat/README.md" ]; then
  for w in 'демо-машина' 'одна беседа с агентом' 'ожидание' 'ответ' 'отказ' 'отмена' 'таймаут'; do
    grep -q -i -- "$w" "$chat/README.md" || red "$chat/README.md: нет слов «$w»"
  done
fi

# ---- (5) программа 0.27.0 читает пример ------------------------------------------------------------------------------------------------------------

echo "== alula compile, alula test"
if [ -f "$chat/chat.alula.md" ]; then
  "$alula" compile "$chat/chat.alula.md" -o "$tmp/chat.alula.json" --force >"$tmp/compile.out" 2>&1 || { red "alula compile $chat/chat.alula.md"; head -5 "$tmp/compile.out" | cut -c1-300; }
fi
got_chat=$(tests_of "$chat")
[ "$got_chat" = "39 39" ] || red "alula test $chat: «${got_chat:-не прочитано}», нужно 39 из 39"
got_all=$(tests_of examples)
[ "$got_all" = "105 105" ] || { red "alula test examples: «${got_all:-не прочитано}», нужно 105 из 105 (66 и 39 chat)"; "$alula" test examples 2>&1 | grep -a '^FAIL\|journal tables' | head -3 | cut -c1-300; }

# ---- (6) равенство с продуктом ---------------------------------------------------------------------------------------------------------------------

product_line="продукт: пропущено (ALULA_PRODUCT_MACHINES не задан)"
if [ -n "${ALULA_PRODUCT_MACHINES:-}" ]; then
  echo "== равенство с продуктом ($ALULA_PRODUCT_MACHINES)"
  "$PYTHON" - "$ALULA_PRODUCT_MACHINES" "$chat" <<'EOF' || red "examples/chat не равен chat продукта"
import glob, json, os, sys
prod, ex = sys.argv[1], sys.argv[2]
bad = 0
def say(m):
    global bad
    bad += 1
    print(m)
names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(prod, 'tests', 'chat-*.alula.test.json')))
if len(names) != 39:
    say('в продукте проверок chat %d, нужно 39' % len(names))
for n in names:
    e = os.path.join(ex, 'tests', n)
    if not os.path.exists(e):
        say('нет проверки %s' % n)
    elif open(os.path.join(prod, 'tests', n), 'rb').read() != open(e, 'rb').read():
        say('проверка %s не равна продуктовой' % n)
def body(path):
    if not os.path.exists(path):
        return None
    lines = open(path, encoding='utf-8').read().split('\n')
    at = next((i for i, l in enumerate(lines) if l.startswith('## Типы')), 0)
    return [l for l in lines[at:] if not l.startswith('- Хеш:')]
pb, eb = body(os.path.join(prod, 'chat.alula.md')), body(os.path.join(ex, 'chat.alula.md'))
if pb is None or eb is None or pb != eb:
    say('таблица chat от «## Типы» (кроме хеша библиотеки) не равна продуктовой')
def tree(path):
    if not os.path.exists(path):
        return None
    t = json.load(open(path, encoding='utf-8'))
    t.pop('title', None)
    for c in t.get('includes', []) or []:
        c.pop('hash', None)
    return t
pt, et = tree(os.path.join(prod, 'chat.alula.json')), tree(os.path.join(ex, 'chat.alula.json'))
if pt is None or et is None or pt != et:
    say('дерево chat (кроме title и хеша библиотеки) не равно продуктовому')
sys.exit(1 if bad else 0)
EOF
  got_prod=$(tests_of "$ALULA_PRODUCT_MACHINES")
  [ "$got_prod" = "81 81" ] || red "alula test $ALULA_PRODUCT_MACHINES: «${got_prod:-не прочитано}», нужно 81 из 81"
  product_line="продукт ${got_prod:-?}"
fi

# ---- (7) nova test, стражи --------------------------------------------------------------------------------------------------------------------------

if [ "${ACCEPT_251_SKIP_NOVA_TEST:-}" = 1 ]; then
  echo "== nova test пропущен (ACCEPT_251_SKIP_NOVA_TEST=1)"
  test_line="nova test пропущен"
else
  command -v nova >/dev/null 2>&1 || { echo "НЕ ПРИНЯТО 251: nova не в PATH"; exit 2; }
  n_dirs=0
  n_dirs_ok=0
  for dir in alula_cli alula_eq alula_tests machine_nested_run machine_run machine_table; do
    n_dirs=$((n_dirs + 1))
    echo "== nova test src/$dir"
    t_full=$(nova test "src/$dir" --jobs 2 --timeout 900 2>&1)
    t_fail=$(echo "$t_full" | tail -3 | sed -n 's/^PASS: \([0-9]*\)  FAIL: \([0-9]*\).*/\2/p' | tail -1)
    if [ "$t_fail" = 0 ]; then n_dirs_ok=$((n_dirs_ok + 1)); else red "nova test src/$dir: красных ${t_fail:-?}"; echo "$t_full" | grep -a "FAIL\|TIMEOUT\|error" | head -4 | cut -c1-600; fi
  done
  test_line="nova test $n_dirs_ok из $n_dirs"
fi

echo "== стражи"
sh scripts/guards/run-all.sh >"$tmp/guards.out" 2>&1 || { red "scripts/guards/run-all.sh"; tail -8 "$tmp/guards.out"; }

summary="$got_version; examples/chat ${got_chat:-?}; examples ${got_all:-?}; $product_line; $test_line"
if [ "$fails" = 0 ]; then
  echo "ПРИНЯТО 251: $summary"
  exit 0
fi
echo "НЕ ПРИНЯТО 251 ($fails красных): $summary"
exit 1
