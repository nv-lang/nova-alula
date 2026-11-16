# Реестр пакета: универсальные примитивы тонкого хозяина

Канонический источник 13 универсальных примитивов тонкого хозяина (эпик «Тонкий хозяин в пакете», задача 118 методики, П-1; REQ-1). Сигнатуры и классы — дословно из реестра методики `alula-machines/registry.md` (редакция 5633435, строки «Primitives»), минус ядро-4 (issue_token, verify_token, journal_write, release_lock — контракты типизированы объектами методики, остаются в методике). Классы — по host-spec задачи 111 (volatile — читающие, acting — пишущие и процессы, pure — sha256). Примитив `new_id` — язык (раздел 7а). Актинг-примитивы исполняются только через outbox-хост эффектов (интент + receipt, устойчивая идентичность, права на submit и replay, unknown ≠ успех).

Форма — раздел 7 спецификации Алулы: имена — JSON-имена; типы — как пишет дерево `machine/2`; `\|` внутри ячейки — знак `|`; `—` — пусто. Файл читает `parse_registry_table` пакета; страж методики (задача 103, М-1) сверяет эти 13 строк построчно с реестром методики.

## Primitives

| name | parameters | result | class | reads | writes |
|---|---|---|---|---|---|
| read_file | path: text | text | volatile | — | — |
| write_file | path: text; content: text | — | acting | — | objects: the file |
| move_file | from: text; to: text | — | acting | — | objects: the moved file |
| delete_file | path: text | — | acting | — | objects: the deleted file |
| file_exists | path: text | bool | volatile | objects: the file | — |
| list_dir | path: text | []text | volatile | objects: the folder | — |
| start_process | command: text; dir: text; log_path: text | int>=1 | acting | — | objects: the process and its log |
| stop_process | pid: int>=1 | — | acting | — | objects: the process |
| process_running | pid: int>=1 | bool | volatile | objects: the process | — |
| run_command | command: text; dir: text | ExecResult | acting | — | — |
| acquire_lock | path: text; token: text | bool | acting | — | objects: the lock |
| parse_agent | instruction: text; input: text | text | volatile | service: the cheap agent | — |
| sha256 | text: text | text | pure | — | — |

## Types

| type | kind | members |
|---|---|---|
| ExecResult | record | code: int; stdout: text |
