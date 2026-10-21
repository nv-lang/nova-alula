# Журнал: таблица шаблонов продукта

Коды журнала CrewHarness, которых нет в таблице методики (`journal_methodology.md`): записи механики движка и исполнителя (правка ответа, возврат формы, повтор запроса, заказ сигнала, дефект машины, отброшенное событие) и коды машин продукта (чат, диалог, пробные машины). Форма та же, что у таблицы методики: `Машина | Код события | Русский шаблон | Параметры` (формат Портолана 2.12, раздел 5, Я-31). Проверка сверяет код и параметры строки с объединением двух таблиц; код продукта не повторяет код методики и не заменяет код, который пишет сам формат (`signal_passed`, `input_rejected`, `machine_error`, `machine_data`). Реестр хозяина (`standard_registry()`) называет эту таблицу. Новая машина продукта, которой нужно своё событие, вносит строку сюда.

| Машина | Код события | Русский шаблон | Параметры |
|---|---|---|---|
| движок продукта | `machine_started` | машина запущена: {machine} | `machine` |
| движок продукта | `event_accepted` | принято событие {name} ({kind}); источник {source}; вход {input} | `kind`, `name`; необязательные `source`, `input` |
| движок продукта | `reply_discarded` | ответ отброшен: {reason} | `reason` |
| движок продукта | `request_ordered` | заказан запрос стороны {party}, попытка {attempt} | `party`, `attempt` |
| движок продукта | `request_sent` | запрос отправлен, попытка {attempt} | `attempt` |
| движок продукта | `request_repeated` | запрос отправлен снова, попытка {attempt} | `attempt` |
| движок продукта | `request_closed` | запрос закрыт: {how}; код {code} | `how`; необязательные `code` |
| движок продукта | `cancel_ordered` | заказана отмена запроса: {reason} | `reason` |
| движок продукта | `cancel_sent` | отмена отправлена | — |
| движок продукта | `cancel_without_request` | отмена стороны {party}, открытого запроса нет | `party` |
| движок продукта | `snapshot_ordered` | заказан снимок состояния, шаг {step} | `step` |
| движок продукта | `machine_finished` | машина закончена: {outcome}; код {code} | `outcome`, `code` |
| движок продукта | `engine_resumed` | движок поднят из снимка: шаг {snapshot_step}, открытых {open}, не отправлено {not_sent}, отброшено строк {ignored_lines} | `snapshot_step`, `open`, `not_sent`, `ignored_lines` |
| движок продукта | `signal_ordered` | заказан сигнал {signal} запросу {request} | `signal`, `request` |
| исполнитель продукта | `machine_defect` | дефект машины: {kind}: {message} | `kind`, `message` |
| исполнитель продукта | `event_ignored` | событие {event} в состоянии {state} отброшено | `event`, `state` |
| исполнитель продукта | `event_unknown` | событие {name} машине не известно | `name` |
| исполнитель продукта | `event_malformed` | событие {name} не читается | `name` |
| исполнитель продукта | `answer_held` | ответ запроса {request} получен в состоянии {state}, которое его не ждёт: удержан до возврата в обращение | `request`, `state` |
| исполнитель продукта | `answer_replayed` | удержанный ответ запроса {request} принят после возврата в обращение | `request` |
| исполнитель продукта | `answer_edited` | ответ стороны {party} не принят: объект правки изменился, запрос {request} | `party`, `request` |
| исполнитель продукта | `form_returned` | ответ стороны {party} возвращён по форме: возврат {returns}, запрос {request} | `party`, `returns`, `request` |
| чат, диалог | `agent_chunk` | часть ответа агента: {text} | `text` |
| чат, диалог | `agent_done` | агент закончил ответ | — |
| чат, диалог | `agent_refused` | агент отказал: {code} | `code` |
| чат | `cancelled_before_request` | отмена до запроса | — |
| чат, диалог | `cancelled_while_waiting` | отмена в ожидании ответа | — |
| чат, диалог | `no_answer_in_time` | ответа в срок нет | — |
| чат, диалог, диалог по шагам | `user_message` | сообщение пользователя: {text} | `text` |
| диалог, диалог по шагам | `session_closed` | сессия закрыта | — |
| диалог по шагам | `turn_answered` | ход отвечен: сессия {session} | `session` |
| диалог по шагам | `turn_refused` | ход не состоялся: {code} | `code` |
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
