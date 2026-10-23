# Реестр образцов: примитивы пилотов (шаг агента и совещание)

Данные для проверки образцов этой папки: 20 примитивов пилотов (шаг агента 3, совещание 17), которые раздел 7 спецификации называет примером реестра. Это не реестр методики: примитивы запуска сессии и раннера, а также наборы типов запуска и раннера остаются у методики. Примитивы `time_now` и `new_id` — язык (раздел 7а).

Форма — раздел 7 спецификации Алулы: имена — JSON-имена реестра хозяина; типы — как пишет дерево `machine/2` (`int>=0`, `?text`, `[]Finding`, `"a" \| "b"`); `\|` внутри ячейки — знак `|`; списки «читает» и «пишет» разделены `;`; `—` — пусто. Файл читает `parse_registry_table` пакета `alula` (`alula.machine_table`), программа `alula` берёт его рядом с машинами (`registry.md`) или флагом `--registry`.

## Primitives

| name | parameters | result | class | reads | writes |
|---|---|---|---|---|---|
| party_profile | party: text | AgentProfile | reading | project setting: role profiles | — |
| role_context | context: RoleContext | text | reading | project objects | — |
| call_trace | — | text | reading | envelope of the call | — |
| call_step | — | int>=0 | reading | envelope of the call | — |
| parse_agent_reply | reply: AgentReply; role: "witness" \| "author" \| "lens" | RoleResult | reading | object: artifact file of the reply | — |
| proposal_read | — | bool | reading | object: proposal | — |
| proposal_with_fingerprint | — | text | reading | object: proposal | — |
| proposal_changed_since_attempt | — | bool | reading | object: proposal | — |
| count_in_model_tally | finding: Finding | — | writing | — | buffer: model tally |
| journal_findings | findings: []Finding | — | writing | — | — |
| journal_machine_data | — | — | writing | all_data | — |
| journal_decision | decision: text; source: text; passes: int>=0; open: []Finding | — | writing | — | — |
| remove_unsound | number: int>=0 | — | writing | lens_findings | lens_findings |
| build_summary | number: int>=0 | ?Summary | writing | lens_findings; lenses | object: summary file |
| close_for_writing | object: text | — | irreversible | — | — |
| open_for_writing | object: text | — | irreversible | — | — |
| move_to_archive | number: int>=0; suffix: int>=0 | — | irreversible | — | — |
| reply_validation | — | ReplyCheck | reading | reply_text; reply_artifact; agent_request; objects: session files | service record: form remarks (read by the turn fix) |
| close_agent_turn | — | — | irreversible | — | — |
| check_cache | dialog_kind: "main" \| "delivery" | — | writing | — | service record: request start mark |

## Roles

| primitive | role | result | reads |
|---|---|---|---|
| parse_agent_reply | witness | []WitnessAnswer | object: proposal |
| parse_agent_reply | author | EditResult | — |
| parse_agent_reply | lens | LensResult | — |

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
| RoleResult | variant | WitnessOutcome(answers: []WitnessAnswer); LensOutcome(result: LensResult); EditOutcome(result: EditResult) |
| RoleContext | variant | WitnessContext(author_question: ?text, findings: ?[]Finding, proposal: text); LensContext(proposal: text, witness_answers: ?[]WitnessAnswer); FixContext(proposal: text, gate3_findings: []Finding, author_guidance: ?text); QuestionContext(author_question: text, proposal: text, gate3_findings: []Finding, human_answer: text) |
