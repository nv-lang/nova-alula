# Журнал примеров: коды машин примеров языка

Данные хозяина «примеры» (24 кода пробных машин `caller`, `callee`, `fan`, `lenses`, `gate`, `variants`, `actions`, `calc`). Код примеров не повторяет код языка. Форма: `Машина | Код события | Русский шаблон | Параметры`.

| Машина | Код события | Русский шаблон | Параметры |
|---|---|---|---|
| вызывающая | `child_answered` | вложенная ответила: {answer}, оценка {score} | `answer`, `score` |
| вызывающая | `child_failed` | вложенная отказала: {code} | `code` |
| вызываемая | `callee_answered` | вызываемая ответила: {label} | `label` |
| вызываемая | `callee_failed` | вызываемая отказала: {reason} | `reason` |
| вызываемая | `callee_silent` | вызываемая молчит: {label} | `label` |
| веер, линзы | `lens_answered` | линза {party} ответила | `party`; необязательные `answer`, `text` |
| веер, линзы | `lens_lost` | линза {party} потеряна | `party`; необязательные `reason`, `code` |
| действия | `big` | большое значение | — |
| действия | `small` | малое значение | — |
| действия | `boom` | сбой действия: {why} | `why` |
| действия | `doubled` | удвоено: {value} | `value` |
| действия | `seen` | просмотрено: {item} | `item` |
| счёт | `started` | счёт начат: {label} | `label` |
| счёт | `stepped` | шаг счёта: {count} | `count` |
| счёт | `reached_limit` | предел счёта достигнут: {count} | `count` |
| ворота | `stop_discarded` | стоп отброшен: {author} | `author` |
| ворота | `work_done` | работа сделана | — |
| ворота | `work_failed` | работа не удалась: {reason} | `reason` |
| варианты | `failed` | сбой: {why} | `why` |
| варианты | `got` | получено: {text} | `text` |
| варианты | `other_failure` | другой сбой | — |
| варианты | `retrying` | повтор | — |
| варианты | `silent` | молчание | — |
| варианты | `transient` | временный сбой | — |
| эхо | `echoed` | эхо: {text} | `text` |
| эхо | `closed_by_user` | эхо закрыто пользователем | — |
| повтор | `got_reply` | ответ получен: {text} | `text` |
| повтор | `asked_again_silent` | агент молчит: запрос посылается заново | — |
| повтор | `gave_up` | отказ: {reason} | `reason` |
| повтор | `noted` | заметка: {text} | `text` |
| повтор | `review_again` | просмотр заново | — |
| повтор | `accepted` | принято | — |
| повтор | `rejected` | отклонено | — |
| вердикт | `verdict_accepted` | судья принял: {score} | `score` |
| вердикт | `verdict_rejected` | судья отклонил: {reason} | `reason` |
| вердикт | `verdict_unsure` | судья не уверен | — |
| вердикт | `verdict_lost` | судья потерян: {reason} | `reason` |
| маршрут | `measured` | размер измерен: {verdict} | `verdict` |
| пауза | `worked` | работа сделана: {text} | `text` |
| пауза | `work_lost` | работа потеряна: {reason} | `reason` |
| ворота | `signal_allowed` | сигнал «разрешить», всего {count} | `count` |
| ворота | `signal_denied` | сигнал «отказать» | — |
| пачка | `job_answered` | работа {party} ответила: {answer} | `party`, `answer` |
| пачка | `job_lost` | работа {party} потеряна | `party`, `code` |
