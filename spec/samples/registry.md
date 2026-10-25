# Реестр образцов: примитивы пилотов (шаг агента и совещание)

Данные для проверки образцов этой папки: 22 примитива пилотов (шаг агента 3, совещание 19), которые раздел 7 спецификации называет примером реестра. Это не реестр методики: примитивы запуска сессии и раннера, а также наборы типов запуска и раннера остаются у методики. Примитив `new_id` — язык (раздел 7а); время — штамп события `событие.момент`.

Форма — раздел 7 спецификации Алулы: имена — JSON-имена реестра хозяина; типы — как пишет дерево `machine/2` (`int>=0`, `?text`, `[]Finding`, `"a" \| "b"`); `\|` внутри ячейки — знак `|`; списки «читает» и «пишет» разделены `;`; `—` — пусто. Файл читает `parse_registry_table` пакета `alula` (`alula.machine_table`), программа `alula` берёт его рядом с машинами (`registry.md`) или флагом `--registry`.

## Primitives

| name | parameters | result | class | reads | writes |
|---|---|---|---|---|---|
| party_profile | party: text | AgentProfile | volatile | project setting: role profiles | — |
| role_context | context: RoleContext | text | volatile | project objects | — |
| call_trace | — | text | volatile | envelope of the call | — |
| call_step | — | int>=0 | volatile | envelope of the call | — |
| parse_witness_reply | reply: AgentReply | []WitnessAnswer | volatile | object: artifact file of the reply; object: proposal | — |
| parse_author_reply | reply: AgentReply | EditResult | volatile | object: artifact file of the reply | — |
| parse_lens_reply | reply: AgentReply | LensResult | volatile | object: artifact file of the reply | — |
| proposal_read | — | bool | volatile | object: proposal | — |
| proposal_with_fingerprint | — | text | volatile | object: proposal | — |
| proposal_changed_since_attempt | — | bool | volatile | object: proposal | — |
| count_in_model_tally | finding: Finding | — | acting | — | buffer: model tally |
| journal_findings | findings: []Finding | — | acting | — | — |
| journal_machine_data | — | — | acting | all_data | — |
| journal_decision | decision: text; source: text; passes: int>=0; open: []Finding | — | acting | — | — |
| remove_unsound | number: int>=0 | — | acting | lens_findings | lens_findings |
| build_summary | number: int>=0 | ?Summary | acting | lens_findings; lenses | object: summary file |
| close_for_writing | object: text | — | acting | — | — |
| open_for_writing | object: text | — | acting | — | — |
| move_to_archive | number: int>=0; suffix: int>=0 | — | acting | — | — |
| reply_validation | — | ReplyCheck | volatile | reply_text; reply_artifact; agent_request; objects: session files | service record: form remarks (read by the turn fix) |
| close_agent_turn | — | — | acting | — | — |
| check_cache | dialog_kind: "main" \| "delivery" | — | acting | — | service record: request start mark |

## Types

| type | kind | members |
|---|---|---|
| Finding | record | severity: Severity; evidence: text; repeat: bool; question: bool |
| Summary | record | critical: int>=0; probes: int>=0 |
| AgentProfile | record | family: text; model: text; effort: ?text |
| AgentModel | record | id: text; provider: text; variant: ?text |
| TokenUsage | record | input: ?int; output: ?int; reasoning: ?int; cache_read: ?int; cache_write: ?int |
| Usage | record | session: text; result: text; family: text; model: AgentModel; tokens: TokenUsage; cost: ?float; created: int; updated: int; context_used: ?int; trace: text; step: int |
| AgentReply | record | text: ?text; artifact: ?text; usage: Usage; request_started: ?int |
| Claim | record | kind: text; statement: text; source: text; excerpt: ?text; check: Check |
| LensResult | record | findings: []Finding; probes: int>=0 |
| JournalEvent | record | code: text; params: [](text, text) |
| Severity | variant | Critical; Significant; Desirable |
| Check | variant | Confirmed; ChannelDistortion; NotConfirmed |
| ReplyCheck | variant | Valid; Violated; Empty |
| WitnessAnswer | variant | Answered(claim: Claim); NotMeasured(claim: text) |
| EditResult | variant | Done(proposal: text); Question(proposal: text, question: text) |
| RoleContext | variant | WitnessContext(author_question: ?text, findings: ?[]Finding, proposal: text); LensContext(proposal: text, witness_answers: ?[]WitnessAnswer); FixContext(proposal: text, gate3_findings: []Finding, author_guidance: ?text); QuestionContext(author_question: text, proposal: text, gate3_findings: []Finding, human_answer: text) |
