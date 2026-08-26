# Round 3J regional user-evidence expected state

Frozen on 2026-08-26 before any acquisition under the regional scope
extension. This contract reopens Round 3J for a region-stratified audit without
altering the completed audit of the original candidate frame.

The machine-readable contract is
`db/data/round3j/regional_user_evidence_expected_state.tsv`. New regional
candidates belong in the separate
`db/data/round3j/regional_source_candidate_register.tsv`; they must not be
appended to, deleted from, or used to reinterpret the original 17-candidate
register.

## Scope decision

```ini
ORIGINAL_CANDIDATE_FRAME_COUNT=17
ORIGINAL_STOP_RULE_VALID_WITHIN_ORIGINAL_FRAME=true
GLOBAL_ACQUISITION_COMPLETE=false
REGIONAL_SOURCE_FRAME_COMPLETE=false
ORIGINAL_STOP_RULE_SUPERSEDED_BY_REGIONAL_SCOPE_EXTENSION=true
```

The original Condition-B result established exhaustion of the original named
candidate frame after its four recorded batches. It remains valid within that
frame. It did not establish exhaustion of the target-user regional evidence
space, and it no longer has global stop effect.

The following committed artifacts are immutable inputs to this extension:

| Original artifact                                | SHA-256                                                            |
| ------------------------------------------------ | ------------------------------------------------------------------ |
| `db/data/round3j/source_candidate_register.tsv`  | `3cbc8890a4e3c1fd65b1c664794ce5fe5f986d4f889b835e07e3d6a71d3c2471` |
| `db/data/round3j/acquisition_outcome_ledger.tsv` | `a57aee1a59a33efe5a1110ece439e89a30be90e60f1c6583d646b6c80ef8f918` |
| `db/data/round3j/acquisition_batch_ledger.tsv`   | `10d60dc5727e48e3ff9291c065428dd19d3dc72734b06c5fa28a13f3ac7c2692` |

These hashes must remain unchanged throughout the regional audit. The new
regional register and batch ledger are additive, not revisions of those files.

## Regional frames

The four core frames are:

1. Mainland China
2. Taiwan
3. Australia / New Zealand
4. United States / Canada

The two secondary frames are Japan and South Korea. Latin American
user-language and preference evidence should be added when a rights-cleared
source is available, but it is not a blocking Round 3J stratum.

A source record stores these fields separately:

- `source_market_region`
- `collection_geography`
- `language_tag`
- `script`
- `source_platform`
- `author_declared_location_if_available`
- `population_scope`

Language, script, author location, collection geography, and intended market
are distinct metadata. Language alone must never be used to infer a person's
nationality, residence, or market. Canonical concepts may be shared across
language variants while source-local wording, spelling, script, register, and
provenance remain intact.

The minimum supported source-language tags are:

```text
zh-Hans-CN
zh-Hant-TW
en-AU
en-NZ
en-US
en-CA
ja-JP
ko-KR
```

Their default script records are `Hans`, `Hant`, `Latn`, `Latn`, `Latn`,
`Latn`, `Jpan`, and `Kore`, respectively. A source-specific mixed or alternate
script must be recorded explicitly rather than coerced to that default.

`zh-Hans` and `zh-Hant` must not be collapsed into one cultural source
category. `en-AU` and `en-US` must not be collapsed into one cultural source
category. A BCP 47 tag describes the source text; it does not prove the
author's identity or the population represented by a study.

The combined `AU_NZ` and `US_CANADA` frames require explicit audit coverage of
both listed language-market tags. Evidence for one member market cannot be
silently relabelled as evidence for the other. Unknown or undisclosed metadata
uses an explicit `NOT_REPORTED` or `NOT_APPLICABLE` value; it is never filled by
inference.

## Evidence modes

Each region is searched and audited independently across four non-equivalent
modes:

| Code | Mode                                            | What it can establish                                                            |
| ---- | ----------------------------------------------- | -------------------------------------------------------------------------------- |
| A    | `USER_GENERATED_SENSORY_LANGUAGE`               | Source-local consumer wording and register, subject to rights and privacy review |
| B    | `STRUCTURED_PREFERENCE_OR_LIKING`               | Structured preference or liking outcomes under the source's own scale and design |
| C    | `CONTROLLED_OR_SEMI_CONTROLLED_SENSORY_OUTCOME` | Source-local sensory outcomes under a declared method                            |
| D    | `PROFESSIONAL_OR_INDUSTRY_LANGUAGE`             | Professional or industry terminology in its source context                       |

The modes are not pooled into one measurement scale. Not every mode must exist
in every region, but every missing mode must be reported explicitly in the
regional audit result.

Structured survey ratings may support preference analysis. They must not be
treated as descriptor mappings unless sensory fields are actually present.
Consumption preference, purchase behaviour, sensory language, and professional
coffee terminology remain separate constructs.

## Required search routes

Each regional audit uses direct source, repository, rights, terms, API, and
request-path evidence. A search-result snippet is discovery evidence only and
cannot complete a candidate audit.

For Mainland China, search source-authored licensed blogs and static sites,
open academic repositories, Chinese university and institutional repositories,
licensed coffee product or review datasets, public GitHub or Gitee repositories
with explicit upstream licensing, official or explicitly authorized platform
APIs, and data-on-request Chinese sensory or consumer studies. Xiaohongshu,
Zhihu, Douban, Weibo, and other large platforms remain permission-controlled.

For Taiwan, search open university repositories, Taiwan consumer-preference and
specialty-coffee research, licensed blogs and review archives, open product or
review datasets, and data-on-request sensory studies. Dcard, PTT, and comparable
communities remain API-, permission-, or research-request candidates unless a
clearly reusable licensed snapshot exists.

For Australia / New Zealand, search university sensory and consumer
repositories, open coffee-preference surveys, specialty-coffee studies,
licensed tasting-note or product datasets, author-licensed coffee blogs, and
public data releases from research or industry bodies.

For United States / Canada, search Dryad, OSF, Zenodo, Figshare, university
repositories, controlled coffee-preference and sensory studies, licensed
coffee-review or product datasets, data-on-request studies, and community-data
permission routes. Reddit, Home-Barista, CoffeeGeek, and similar communities
remain API- or permission-controlled unless an explicitly reusable snapshot
and model-use permission exist.

For Japan, search Mendeley Data, Japanese university repositories,
J-STAGE-linked supplements, open consumer surveys, licensed source-authored
blogs, sensory and coffee-consumption datasets, and author or repository data
requests. Consumption preference, purchase behaviour, sensory language, and
professional coffee terminology are recorded independently.

For South Korea, search Korean university repositories, government or
institutional open data, journal supplements, licensed coffee-consumer surveys,
source-authored blogs with explicit licences, and data-on-request studies.
Naver, Daum, DCInside, and comparable platforms remain permission-controlled
unless an explicit research or API route exists.

## Completion thresholds

Each core regional source frame must satisfy all of the following before global
acquisition may stop:

```ini
NAMED_SOURCE_CANDIDATE_COUNT>=6
AUDITED_INDEPENDENT_SOURCE_FAMILY_COUNT>=2
STRUCTURED_PREFERENCE_OR_SENSORY_CANDIDATE_COUNT>=1
USER_GENERATED_OR_COMMUNITY_SOURCE_CANDIDATE_COUNT>=1
INDUSTRY_OR_PROFESSIONAL_LANGUAGE_CANDIDATE_COUNT>=1
RIGHTS_AND_ACCESS_DECISION_COMPLETENESS=1.0000
```

Japan and South Korea must each satisfy:

```ini
NAMED_SOURCE_CANDIDATE_COUNT>=4
AUDITED_INDEPENDENT_SOURCE_FAMILY_COUNT>=2
RIGHTS_AND_ACCESS_DECISION_COMPLETENESS=1.0000
```

Admission is preferred but is not mandatory. A rights-blocked source counts as
an audited candidate only when it is named, independently sourced, and has a
complete evidence-backed rights/access decision. It does not count as an
admitted source, document, response, sample, or training unit.

Candidate counts use distinct `candidate_key` values within a regional frame.
When one candidate requires multiple region-by-language audit rows, those rows
share one `candidate_key` and cannot inflate the candidate count. Mirrors and
repository copies share one `source_origin_key`. Independent-family counts use
distinct reviewed `source_family_key` values and an explicit independence
basis.

One regional register row represents one
`source_origin_key × regional_frame_key × source_market_region × language_tag`
audit cell and has a unique `regional_candidate_record_key`. Within a frame,
one canonical `candidate_key` maps to one origin; mirrors do not become extra
named candidates. `region_assignment_basis` is mandatory and may not be
language alone.

`RIGHTS_AND_ACCESS_DECISION_COMPLETENESS` is the number of named candidates in
the regional frame whose rows all have a populated allowed rights/access
decision, evidence URL, decision basis, and `rights_and_access_decision_complete=true`,
divided by the number of named candidates in that frame. A blank, generic
`PUBLIC_HTML`, or unsupported decision is incomplete.

General source decisions use one of:

```text
CLEARED_OPEN_LICENSE
CLEARED_PUBLIC_DOMAIN
CLEARED_OFFICIAL_API_FOR_DECLARED_USE
CLEARED_WRITTEN_PERMISSION
RESEARCH_ONLY_NONCOMMERCIAL
METADATA_ONLY
DATA_REQUEST_PREPARED
BLOCKED_ACCESS
BLOCKED_AUTOMATION
BLOCKED_COPYRIGHT
BLOCKED_PRIVACY
BLOCKED_MODEL_USE
BLOCKED_LICENSE_UNCLEAR
```

The separate forum/community decision is additionally mandatory for every
community candidate.

For non-community rows, `forum_or_community_decision=NOT_APPLICABLE`. For
community rows it must be one of the eleven allowed community decisions.
`PUBLIC_HTML` is invalid as a rights or forum/community decision. A factual
`access_state=PUBLIC_HTML_OBSERVABLE_ONLY` may be recorded, but it grants no
reuse, privacy, public-release, or model-use permission. `request_sent=false`
unless a later explicitly authorized action is recorded.
`sensory_gold_label_eligible`,
`canonical_concept_promotion_eligible`, and
`population_preference_estimate_eligible` default to `false` and require a
separate evidence decision to change.

## Rights-controlled communities

Ordinary public visibility is not reuse or model-use permission. Xiaohongshu,
Zhihu, Douban, Weibo, Dcard, PTT, Reddit, Home-Barista, CoffeeGeek, Naver, Daum,
DCInside, and comparable community platforms may be considered only through an
official API, written platform permission, written author permission, a clear
open-licensed snapshot, or another platform-approved research route. No
ordinary posts or comments may be collected through unofficial automation.

Every forum or community candidate receives exactly one of:

```text
AUTHORIZED_API
WRITTEN_PLATFORM_PERMISSION
WRITTEN_AUTHOR_PERMISSION
OPEN_LICENSED_SNAPSHOT
DERIVED_ONLY_AUTHORIZED
METADATA_ONLY
DATA_REQUEST_PREPARED
BLOCKED_AUTOMATION
BLOCKED_COPYRIGHT
BLOCKED_PRIVACY
BLOCKED_MODEL_USE
```

`PUBLIC_HTML` is not a valid community decision. Contact packages may be
prepared, but no platform, author, or repository request may be sent without
explicit user authorization.

Final forum metrics use fixed definitions. `FORUM_OR_COMMUNITY_CANDIDATE_COUNT`
is the number of distinct community `candidate_key` values.
`AUTHORIZED_FORUM_SOURCE_COUNT` includes decisions `AUTHORIZED_API`,
`WRITTEN_PLATFORM_PERMISSION`, `WRITTEN_AUTHOR_PERMISSION`,
`OPEN_LICENSED_SNAPSHOT`, and `DERIVED_ONLY_AUTHORIZED` only.
`FORUM_PERMISSION_REQUEST_COUNT` counts complete unsent dossiers with
`DATA_REQUEST_PREPARED` and `request_sent=false`. `BLOCKED_FORUM_SOURCE_COUNT`
includes `BLOCKED_AUTOMATION`, `BLOCKED_COPYRIGHT`, `BLOCKED_PRIVACY`, and
`BLOCKED_MODEL_USE`. `METADATA_ONLY` is audited but is neither authorized,
request-prepared, nor blocked for those three summary metrics.

For a major blocked platform or valuable data-on-request study, a prepared
request records the contact target, exact requested fields, requested date
range, whether raw text is required, a derived-only alternative, privacy
protections, intended model-research use, public-release boundary, and
deletion/withdrawal procedure.

## Privacy, export, and training eligibility

Any admitted user-generated data excludes usernames, profiles, email
addresses, avatars, exact personal locations, and unreviewed comments or
replies. Direct links are excluded from public training exports when they are
unnecessary. Internal provenance uses pseudonymous document keys and retains
only the source and rights evidence needed for audit, deletion, or withdrawal.
Long user quotations are not reproduced in public artifacts unless licensed.
The corpus must support source deletion or withdrawal when required by a
platform, licence, author agreement, or repository agreement.

Forum, review, and blog evidence may be eligible for:

- `REGIONAL_LANGUAGE_CORPUS`
- `PREFERENCE_LANGUAGE_CORPUS`
- `AMBIGUITY_TEST_SET`
- `REGION_HELD_OUT_TEST`

It is not automatically eligible for:

- `SENSORY_GOLD_LABEL`
- `CANONICAL_CONCEPT_PROMOTION`
- `POPULATION_PREFERENCE_ESTIMATE`

Eligibility is recorded per source and role. Admission into one role grants no
automatic eligibility for another.

## Coverage cube and reporting

The governed regional coverage cube uses these distinct dimensions:

```text
region
language
data_mode
source_family
preparation
roast
black_or_milk
consumer_or_professional
training_eligibility
```

`regional_frame` is retained as a grouping key while the cube's `region`
dimension is implemented by the atomic `source_market_region`; this prevents
the `AU_NZ` and `US_CANADA` groupings from erasing their member markets.

Its schema is frozen in
`db/data/round3j/regional_evidence_cube_contract.tsv`. Regional reporting keeps
these measures separate:

- `REGIONAL_LANGUAGE_DOCUMENT_COUNT`
- `REGIONAL_UNIQUE_EXPRESSION_COUNT`
- `REGIONAL_PREFERENCE_RESPONSE_COUNT`
- `REGIONAL_SENSORY_SAMPLE_COUNT`
- `REGIONAL_SOURCE_FAMILY_COUNT`
- `REGIONAL_TRAINING_ELIGIBLE_UNIT_COUNT`

Raw row count is not regional sample coverage. A unit must be counted under its
source-local semantics, and no dimension value may be inferred merely to fill a
cube cell.

For each region, report the largest source-family share, top-three
source-family share, and effective source-family count using the declared unit
for that metric. A region with one contributing source family is reported as
`REGIONAL_COVERAGE_PRESENT_BUT_SOURCE_CONCENTRATED`, never as regionally
representative. Round 3J makes no regional representativeness claim.

Australian preparation and beverage wording such as `flat white`,
`long black`, and `batch brew` is preserved source-locally. Its presence does
not establish that the vocabulary is unique to Australia/New Zealand or has a
universal interpretation.

## Regional and global stop rules

The global stop rule cannot trigger until both conditions are true:

```ini
ALL_CORE_REGIONAL_SOURCE_FRAMES_COMPLETE=true
ALL_SECONDARY_REGIONAL_SOURCE_FRAMES_AUDITED=true
```

Meeting those two prerequisites does not by itself set
`GLOBAL_ACQUISITION_COMPLETE=true`; the remaining Round 3J acquisition and
training-readiness gates must still be evaluated.

An unmet regional lane may stop only after two consecutive targeted
no-material-gain batches for that same region. Each qualifying batch must
include both a structured dataset/research search and a community/UGC
permission search. A global or cross-region no-gain count is invalid. Regional
batches are recorded in
`db/data/round3j/regional_acquisition_batch_ledger.tsv`.

The regional governance invariants, candidate outcome ledger, and admitted
evidence-unit grain are frozen in:

- `db/data/round3j/regional_governance_invariants.tsv`
- `db/data/round3j/regional_acquisition_outcome_ledger.tsv`
- `db/data/round3j/regional_evidence_unit_register.tsv`
- `db/data/round3j/regional_evidence_cube_membership.tsv`

A no-gain counter advances only when both required search lanes have populated
scope and evidence-path fields. It resets to zero after material gain or an
intervening batch that lacks either required lane. Material gain is a positive
audited delta toward an unmet regional candidate, family, required-class,
explicit-mode, rights-completeness, admission, or training-unit gate; raw row
growth alone is not material gain.

Round 3J must not be merged or closed until all six regional frames have been
audited under this contract.

## Frozen pre-acquisition decision

At this checkpoint, the regional register contains no candidates and all
regional observed metrics are `NOT_YET_AUDITED`. Therefore:

```ini
ALL_CORE_REGIONAL_SOURCE_FRAMES_COMPLETE=false
ALL_SECONDARY_REGIONAL_SOURCE_FRAMES_AUDITED=false
REGIONAL_SOURCE_FRAME_COMPLETE=false
REGIONAL_REPRESENTATIVENESS_CLAIM=false
GLOBAL_ACQUISITION_COMPLETE=false
```
