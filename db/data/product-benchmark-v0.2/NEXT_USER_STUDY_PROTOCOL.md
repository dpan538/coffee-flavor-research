# Round 3O next user task study

This is a prepared formative study, not a completed experiment. No new
participants have been recruited or tested in this checkpoint. Agent opinions
are not participant responses, sensory labels or owner approvals.

## Recruitment and assignment

Recruit 8–10 new participants: at least four low-exposure or novice users,
three or four regular users, and no more than two experienced users. For eight,
use four novice, three regular and one experienced participant. Ask about
coffee exposure directly; do not infer demographics or professional status.

Allocate unused codes of the form R3O-001 before exposure. Odd codes receive A,
even codes B. Allocate consecutive odd/even code pairs within each recruitment
stratum where possible. Conceal the allocation list until enrollment; do not
choose codes after seeing the participant's preferences. Record assignments
locally. A participant sees one wording variant once. Never reuse a participant
in the other variant or treat repeated attempts as independent observations.

The harness accepts no personal names. Keep any consent or recruitment linkage
outside this repository under the owner's restricted research root. Before
starting, explain the task, voluntary participation, local recording and the
planned use of coded aggregates. Let participants decline or stop. Do not send
their session files to external agents without separate owner authorization and
appropriate participant handling.

## Local setup

Use the existing frontend and explicitly enable the research build:

```bash
VITE_COFFEE_RESEARCH=1 npm run build
npm run preview -- --host 127.0.0.1 --port 4321
```

Open `/research/user-study` on that local server. The route is absent from a
default build and all production navigation. There is no remote storage,
analytics, login or service worker. The research flag authorizes this local
formative harness, not a deployed product. Use a controlled device for sessions;
do not expose the preview server publicly as part of this checkpoint.

## Moderator script and 5–8 minute task

1. Set the research code and self-reported exposure stratum. Ask the participant
   to think of a coffee in hand or a recent coffee; use the same task framing
   for both variants. Remembered coffee cannot establish sensory accuracy.
2. Show the value statement for five seconds, then hide it. Ask the participant
   to explain what the tool helps them do. Record only correct / partial /
   incorrect / not assessed. Correct means helping find words for their own
   sensory impressions, without claiming a unique correct flavor or measuring
   the coffee. Do not coach before recording this measure.
3. Let them select C0 and C1. Package-name guidance is available. C1 unsure is a
   valid null state, not an eighth roast. Do not correct selections as though
   this were a knowledge examination.
4. Let them answer the adaptive sensory questions. Multiple choices are allowed.
   Do not explain an unfamiliar option unless help is explicitly requested;
   record help in the post-task observation. Keep the distinction among unsure,
   none of these and skip. Any of these counts as a recorded response to Q1.
5. Let them inspect the headline results, expand other candidates if desired,
   and decide whether to answer a fifth question when it is offered. They may
   accept Q5 and then return to their current result without answering it.
   Acceptance measures the click; fifth-question completion is a separate
   derived measure (`totalQuestionCount == 5`). Do not force completion.
6. Complete the six post-task items. Generate and download the JSON locally.
   Move the export to restricted owner storage before reloading the page for the
   next participant. The page loses the session on reload and does not recover
   it remotely. Do not commit or upload individual session JSON.

Normal sensory questioning targets 2–4 questions and 30–60 seconds. These are
formative targets, not observed timings or guarantees. The entire study includes
setup, paraphrase and post-task reflection. The participant can see partial
results after answering Q1 even if that ends the sensory task before Q2.

## Measurement dictionary

| Measure | Definition and denominator |
| --- | --- |
| Value paraphrase | Correct categorical paraphrases / assessed participants; report partial, incorrect and unassessed separately. |
| Completion without help | Completed tasks with no moderator help beyond paraphrase recording / all started tasks. Record abandonment separately; an unexported session is not a success. |
| First-question comprehension | Clear / partial / unclear post-task responses, by variant and exposure stratum. |
| Selected-option count | Count per recorded question. Report sensory-selection responses separately from zero-selection escape states; the export's overall average includes all questions. |
| All options selected | Questions selecting the entire displayed list / selected-response questions. No inference of confusion without task observation. |
| Candidate reduction | Before count minus after count for the evidence-supported working set. Negative values are possible. This is not a discarded-candidate count, entropy estimate or proof of information gain. |
| Question count | Number of recorded sensory responses, including typed no-answer responses; maximum five. |
| Time | C0/C1 and question times are milliseconds from screen presentation to submission. Completion is from starting the value-proposition task through post-task submission; includes thinking time. |
| UNSURE / NONE / SKIP | Separate counts and rates per displayed/answered question; never treat unsubmitted questions as NONE. |
| Q5 offered | Sessions reaching four answers with fewer than three headlines, a material unused axis and no open-set/conflict guard / sessions with four answers. |
| Q5 acceptance | Explicit extra-question clicks / offers. A click followed by return is accepted but uncompleted. |
| Q5 completion | Sessions with five recorded answers / Q5 acceptances. |
| Headline helpfulness | 1–5 ordinal rating distribution, accompanied by headline count; do not report as calibrated confidence. |
| Expansion | At least one expansion click / sessions with expandable content. |
| Partial-output acceptance | Accept / unsure / reject, excluding not applicable from the assessed denominator. |
| Reuse intention | Yes / maybe / no; intention only, not retained usage. |

An incomplete participant who declines export must be recorded in the separate
restricted moderator log with only a study code and completion disposition.
The current export is generated after post-task questions, so exports alone
cannot measure the abandonment denominator. Keep that limitation explicit.

## Review decisions

Treat every numeric target as `FORMATIVE_DECISION_THRESHOLD`. Proposed owner
discussion triggers are: fewer than 75% correct assessed paraphrases, more than
25% unclear first-question reports in either variant, or any reproducible flow
dead end. These are small-sample design triggers, not hypothesis tests. Report
exact fractions and all missingness; do not present variant differences as
statistically significant. With 8–10 participants, use individual problems and
task observations to guide the next wording revision.

Priorities for owner review before sessions: combined fourth-family wording;
whether broad flower/berry references over-specify the output; the conservative
closed-none conflict display guard; selection stopping and Q5 burden; and
headline versus exploration usefulness. Complete the owner benchmark template
without using agent-majority votes as approval. No new ML proposal is authorized
until a human-reviewed, rights-cleared product-task benchmark exists.
