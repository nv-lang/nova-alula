# Зачем: найти рабочий интерпретатор Python 3.9+; на машине разработчика `python3` бывает заглушкой
#     магазина приложений, поэтому кандидат проверяется запуском, а не по имени.
# Проверяет: python, python3, py -3 по порядку; первый, что выполняет код и не старше 3.9, станет PYTHON.
# Не проверяет: пакеты (стражам нужна только стандартная библиотека).
# Правило: AGENTS.md п.15 и ADR-0006 держат стражи; интерпретатор для них — предпосылка (REQ-03).
#
# Использование: . scripts/guards/lib/find-python.sh; find_python || exit 1; $PYTHON скрипт.py
# Файл подключается точкой, сам ничего не запускает и не меняет окружение, кроме PYTHON и
# PYTHONDONTWRITEBYTECODE (иначе __pycache__ ломает проверку «git status пуст») и PYTHONIOENCODING (вывод
# в UTF-8 при любой кодовой странице консоли).
PYTHONDONTWRITEBYTECODE=1
PYTHONIOENCODING=utf-8
export PYTHONDONTWRITEBYTECODE PYTHONIOENCODING

find_python() {
  PYTHON=
  # GUARDS_PYTHON_CANDIDATES (через запятую) нужна только самотестам: подменить перечень кандидатов.
  fp_rest=${GUARDS_PYTHON_CANDIDATES:-python,python3,py -3}
  while [ -n "$fp_rest" ]; do
    fp_candidate=${fp_rest%%,*}
    case "$fp_rest" in *,*) fp_rest=${fp_rest#*,} ;; *) fp_rest= ;; esac
    # shellcheck disable=SC2086
    if $fp_candidate -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
      PYTHON=$fp_candidate
      return 0
    fi
  done
  echo "FAIL: предпосылка: не найден рабочий Python 3.9 или новее (пробовали: python, python3, py -3)." >&2
  echo "Поставьте Python 3.9+ и убедитесь, что команда python запускается." >&2
  return 1
}
