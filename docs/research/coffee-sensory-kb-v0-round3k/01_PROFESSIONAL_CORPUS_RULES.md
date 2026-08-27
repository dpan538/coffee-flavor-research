# Professional competition corpus rules

## Authority and scope

The machine-readable files in `db/data/round3k/` are authoritative. This
document explains their application. It does not convert planning estimates,
public webpages, score sheets, judge rows, or descriptor occurrences into
professional coffee records.

Round 3K constructs a reproducible competition-native training-corpus
candidate. It performs no model fitting, embedding work, learning-to-rank,
adaptive-policy fitting, hyperparameter search, or production ranking.

## Evidence roles

| Tier | Role                                            | Core gate use                                                 |
| ---- | ----------------------------------------------- | ------------------------------------------------------------- |
| P0   | Protocol and vocabulary authority               | Defines semantics and versioned fields; never a sample record |
| P1   | Official judge or panel observation             | Highest-priority core professional evidence                   |
| P2   | Organizer-published professional sensory record | Core professional evidence, kept distinct from P1             |
| P3   | Competitor-declared professional note           | Auxiliary terminology and candidate generation only           |
| P4   | Roaster or commercial product language          | Auxiliary retrieval and terminology only                      |
| P5   | Consumer or synthetic evidence                  | Excluded from the Round 3K professional corpus                |

P0 includes governed identifiers and versions for current SCA standards, WCR
sensory vocabulary, ISO vocabulary, WCC rules, and official scoresheets. P0
does not authorize copying protected definitions, reference preparations, or
proprietary forms.

Only P1 and P2 count toward the 7,000 observed and 10,000 model-eligible core
gates. P3 and P4 remain separately reportable auxiliary professional records.
P5 may remain in separately governed historical or evaluation partitions but
never supplies Round 3K professional labels.

## Fresh-preparation contract

Every credited core record has `FRESH_PREPARATION_CONFIRMED=true` and a link to
official category, protocol, rule, scoresheet, or entry evidence. Eligible
events are:

- standardized cupping;
- green-coffee competition cupping;
- production-roast cupping;
- filter, pour-over, or competition-defined batch filter;
- immersion;
- siphon;
- manual-pressure or hybrid brewing;
- espresso;
- espresso plus water;
- fresh cezve/ibrik;
- fresh cold extraction prepared for judging.

Fresh milk and plant-milk espresso are stored as an auxiliary context stratum
and never pooled into the black-coffee descriptor model. The following are
excluded from core evidence: ready-to-drink, bottled, canned, shelf-stable
cold brew, instant or soluble, flavored coffee, coffee cocktails, signature
drinks containing non-coffee ingredients, ordinary reviews, comments, social
posts, purchase/preference surveys, consumer liking without professional
judging, machine-generated notes, LLM-generated notes, and project-authored
notes.

## Effective record and linked observations

An `EFFECTIVE_PROFESSIONAL_COFFEE_RECORD` is one unique series, edition,
category, round, entry/lot, and preparation-service tuple with:

1. fresh-preparation evidence;
2. official judge/panel provenance for P1 or official organizer professional
   provenance for P2; and
3. at least one explicit official sensory score or professional descriptor.

Every effective record includes or links to competition series, edition, year,
category, round, entry or lot key, coffee identity or governed pseudonymous
coffee key, preparation service, rule version, applicable scoresheet version,
evidence tier, source, immutable snapshot, file hash, and six-dimensional
rights decision.

An organizer aggregate that cannot be resolved to an entry/lot, explicit round,
and preparation service may remain governed P2 evidence, but it is not an
effective professional coffee record and receives no 7,000/10,000 gate credit.

A coffee evaluated by twenty judges counts as one effective record, twenty
judge observations, the actual structured-score count, and the actual
descriptor-assertion count. A preliminary, semifinal, and final service may
produce three effective round-service records, but all three retain one coffee
identity, one entry identity, and explicit repeat relationships.

Every gate report exposes all of:

- `UNIQUE_COFFEE_IDENTITY_COUNT`;
- `UNIQUE_ENTRY_SERVICE_COUNT`;
- `EFFECTIVE_ROUND_SERVICE_RECORD_COUNT`;
- `JUDGE_OBSERVATION_COUNT`;
- `PROFESSIONAL_DESCRIPTOR_ASSERTION_COUNT`.

## Anti-inflation and duplicate policy

At the 7,000 milestone, at least 60% of credited effective records remain
distinct entry-by-preparation-service units before legitimate round
multiplication. The preferred 10,000 target is 65%; the hard minimum remains
60% unless a later authorized threshold revision says otherwise.

Corpus size never grows through judge-row multiplication, mirror snapshots,
repeated page captures, unlinked rounds, unlinked cross-category entries,
auction lots republished in roaster catalogs, synthetic descriptors, or
inferred descriptors. Mirrors and republishes retain audit rows and explicit
upstream origin, duplicate group, and repeat relationship while receiving only
one credited effective-record identity where appropriate.

At 12,000 observed records, a forensic audit becomes mandatory. Count alone is
not evidence of falsity. Passing requires zero synthetic core records, zero
inferred professional descriptors, zero unlinked repeats, and complete
provenance.

A source family is one independent upstream professional judging programme or
data custodian, established from organizer identity, method governance,
upstream data origin, and rights evidence. Multiple domains, mirrors, editions,
categories, export formats, or result pages do not create new families. A
national or country programme is counted independently only when it has
independently governed judging/data custody and a separate rights decision;
country labels alone are insufficient.

## Assertion types

Every descriptor assertion uses exactly one controlled type:

- `OFFICIAL_JUDGE_DESCRIPTOR`;
- `OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR`;
- `OFFICIAL_AGGREGATED_DESCRIPTOR`;
- `OFFICIAL_STRUCTURED_SCORE`;
- `COMPETITOR_DECLARED_DESCRIPTOR`;
- `ROASTER_SUBMITTED_DESCRIPTOR`;
- `ORGANIZER_MARKETING_DESCRIPTION`.

Only the first four can enter the P1/P2 core layer. Consensus is a derived
record with lineage to its judge observations and never overwrites those
observations. An organizer's public marketing description is not P1. A
competitor declaration is not judge confirmation.

`OFFICIAL_STRUCTURED_SCORE` is retained as the controlled evidence assertion
type, but its numeric value lives in `structured_score` and is reported through
a separate structured-score count. Only explicit descriptor text or an
explicit source-defined descriptor identity increments
`PROFESSIONAL_DESCRIPTOR_ASSERTION_COUNT`. A numeric acidity, balance, or
overall score cannot inflate the 15,000/40,000/60,000 descriptor thresholds.

For `EVIDENCE_CLASS_COUNT`, the counted classes are distinct core assertion
classes actually represented by acquired P1/P2 evidence. This definition
allows the 7,000 gate's required three classes without incorrectly treating P0,
P3, P4, or P5 as core evidence.

## No semantic invention

Adapters extract only explicit source fields, text spans, official scores,
official descriptors, and competition metadata. Permitted normalization is
limited to Unicode, case, whitespace, controlled punctuation, and
source-declared identifier normalization.

Round 3K does not infer flavor from origin, process, variety, score, roast,
category, or other metadata. It does not parse espresso or filter category into
roast depth, decompose metaphor into canonical targets automatically, or ask a
model to fill missing source fields. Codex/LLM review proposals remain
`CANDIDATE` and `NOT_TRAINING_LABEL` until a governed review decision exists.

## C0 preparation context

The product's mandatory C0 taxonomy remains:

1. filter/percolation;
2. immersion;
3. hybrid/manual pressure;
4. espresso/short pressure;
5. espresso plus water;
6. stovetop/boiled;
7. cold extraction;
8. espresso plus milk.

This interface taxonomy is not the competition preparation-service registry.
The latter retains detailed official services such as cupping, production
cupping, siphon, and cezve/ibrik. A C0 projection is made only from official
category, preparation protocol, scoresheet field, or entry metadata. Database
source states may be `NOT_REPORTED`, `SOURCE_UNKNOWN`,
`REPORTED_UNRESOLVED`, or `NOT_APPLICABLE`; the user-facing product does not
offer unknown.

## C1 roast context

C1 is the mandatory seven-level ordinal product scheme: extremely light,
light, medium-light, medium, medium-dark, dark, and extremely dark. The levels
are not equally spaced.

Every source-native scheme and value is preserved, including Agtron, CIELAB,
City, City+, Full City, Vienna, French, Nordic, filter roast, espresso roast,
omniroast, and competition-native fields. Any C1 projection is separate,
reviewed, versioned, and may remain `REPORTED_UNRESOLVED`. There is no automatic
espresso-roast-to-dark, filter-roast-to-light, or Nordic-to-extremely-light
mapping.

C0 and C1 are bounded context support, not flavor generators. A future ranking
system may combine professional evidence, bounded context support, and explicit
user answers, with context weight declining as answers accumulate. This round
does not fit or benchmark that system.

## Rights dimensions and counts

Each source independently records:

- `PUBLIC_RESULTS_USE`;
- `PUBLIC_DESCRIPTOR_USE`;
- `INTERNAL_RESEARCH_USE`;
- `PUBLIC_DERIVED_RELEASE`;
- `MODEL_RESEARCH_USE`;
- `COMMERCIAL_MODEL_USE`.

Public access is not reuse permission, and permission to analyze public result
metadata is not model-training permission. An observed core record is a real,
lawfully acquired P1/P2 record with fresh-preparation and source integrity. It
may have model rights pending. A model-eligible core record additionally has
`MODEL_RESEARCH_USE=true` and passes every label, provenance, diversity,
context, duplicate, split, and reproducibility gate.

No email, contact form, platform export, agreement, payment, purchase,
subscription, or contract action is authorized without a separate user
instruction. Request packets may be prepared but remain unsent.

## Label dispositions and review

Controlled dispositions are:

- `EXACT_CANONICAL_TARGET`;
- `MULTI_CANONICAL_TARGET`;
- `RANGE_LEVEL_TARGET`;
- `SOURCE_LOCAL_TARGET`;
- `AMBIGUOUS_TARGET`;
- `CONTRADICTORY_TARGET`;
- `UNRESOLVED`;
- `ABSTAIN`;
- `OUTSIDE_ONTOLOGY`.

Level-one deterministic mapping is allowed only for an exact governed WCR
attribute identifier, governed SCA term, approved project lexicalization,
official scoresheet field, or explicit source-defined descriptor identity.
Each rule retains its key, version, raw phrase, target, evidence source, and
mapping date.

The positive-record metric may include governed deterministic exact mappings
that satisfy this level-one contract. Multi-target, ambiguous, conflicting,
metaphorical, qualified, multilingual, or source-local mappings require actual
qualified reviewer evidence before they count as reviewed. Therefore the
10,000 gate remains blocked while `EXPERT_REVIEW_PERFORMED=false` if its
multi-target and ambiguity strata cannot otherwise be supported by supplied
governed review decisions.

Composite references, metaphors, qualifiers, multilingual expressions,
source-local terms, multi-target phrases, ambiguity, and conflicting
professional assertions enter an expert review queue. The recommended future
protocol uses two independent qualified reviewers and one adjudicator for
disagreement, with coffee-sensory/competition expertise and source-language
competence where required. No such review is claimed in Phase A.

Every training-candidate label joins to competition, edition, category, round,
entry/lot, preparation service, judge/panel or organizer evidence, source
snapshot, raw phrase, mapping rule or review decision, and target(s).
`TRAINING_LABEL_PROVENANCE_RATE` must equal 1.0000.

## Grouped split candidates

Random row splitting is prohibited. Deterministic candidate assignments use
competition-family, competition-year, coffee-identity, lot, roaster,
duplicate-group, repeat-group, preparation, and C1 holdouts. At the 10,000 gate
at least three competition families and one competition year are held out;
coffee-identity, duplicate, and mirror leakage counts are zero. These are
candidate splits only. Round 3K performs no model evaluation.

## Scale gates and scientific boundary

`SCALE_GATE.tsv` is authoritative for the complete gate portfolio. The 7,000
gate requires observed professional records; the 10,000 gate requires
model-eligible records. Both include assertion, diversity, context,
anti-inflation, rights, label, and provenance requirements. Counts are never
substituted for one another:

- 10,000 database rows are not necessarily 10,000 professional coffee
  samples;
- judge observations, descriptors, and result pages are not independent
  coffee records;
- 7,000 observed records are not training-ready when model rights are pending;
- a 10,000-record freeze candidate is not a trained or production-ready model.

The valid endpoint is a rights-cleared, professionally grounded,
competition-native training-corpus freeze candidate ready for a separately
authorized Round 4 programme.
