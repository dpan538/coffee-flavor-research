# Learning curve and saturation plan

## Purpose

The project needs evidence about marginal value, not a single aspirational data
target. Learning curves should reveal whether new reviewed labels, source
families, languages, contexts, or first-party sessions improve held-out
performance and where remaining errors concentrate.

## Descriptor gates

These gates count reviewed P1/P2 strict assertions and require companion
provenance, rights, diversity, and held-out evaluation conditions:

|   Gate | Intended checkpoint               |
| -----: | --------------------------------- |
|    500 | deterministic evaluation          |
|  2,000 | experimental normalization        |
|  5,000 | experimental 5+3 ranking          |
| 10,000 | research-grade normalization      |
| 15,000 | association/co-assertion learning |
| 20,000 | research-grade 5+3 ranking        |
| 40,000 | deployment-candidate ranking      |

Acquisition artifacts or publication rows cannot be substituted for these
reviewed assertions.

## Curve design

At each eligible checkpoint:

1. freeze a grouped train/development/test manifest;
2. sample nested training subsets without changing the held-out groups;
3. run the deterministic baseline and only authorized learned baselines;
4. repeat sampling where variance estimation is feasible;
5. report overall, tail-label, source-family, language, context, and abstention
   measures;
6. record annotation/review effort and marginal gain; and
7. retain negative or flat curves.

## Saturation indicators

- held-out gain is within a prespecified negligible band across successive
  evidence increments;
- tail labels or families remain blocked despite overall gain;
- new rows mostly repeat existing coffees, publication layers, phrases, or
  services;
- review disagreement or unresolved rate dominates data volume;
- model-rights rate, source diversity, preparation/roast coverage, or language
  coverage fails to improve; or
- user burden no longer decreases as policy data grows.

Saturation in one source family is not global saturation. A flat aggregate can
hide valuable improvements for an underrepresented language or context.

## Acquisition and review decision

Prefer the next source/review batch with the highest expected contribution to a
named gap: new professional descriptors, source-family independence, context,
language, challenge cases, multi-target records, or model rights. Do not optimize
raw row yield alone.

## Current state

`LEARNING_CURVE_STATUS=BLOCKED`

The reviewed and model-eligible universes do not meet the first gate. No curve
or fabricated performance chart is produced.
