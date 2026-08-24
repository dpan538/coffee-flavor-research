# Context data coverage

## Round 2B audit

The Firstbloom pilot contains:

```text
CURRENT_CORPUS_DOCUMENT_COUNT=2474
PREPARATION_KNOWN_DOCUMENT_COUNT=0
ROAST_KNOWN_DOCUMENT_COUNT=0
CURRENT_CORPUS_PREPARATION_COVERAGE=0.0000
CURRENT_CORPUS_ROAST_COVERAGE=0.0000
```

Structured source files include product, publisher, origin/region/producer/variety/process, capture, observation, and expression fields. They do not include preparation method, roast degree/label, brew intent, milk context, or served beverage type.

Product names occasionally contain words such as “espresso” or “dark roast.” Round 3A does not infer context from those strings because the field semantics are not explicit and the terms may denote product name, intended use, blend identity, or marketing language.

No unknown/not-reported context rows were bulk-inserted merely to increase row count. Absence is represented by zero coverage and documented source limitations. Future acquisition may add observation-context rows only when the source or protocol explicitly supports them.

## Candidate data

Three rights-cleared Dryad dataset versions are registered as candidates. Their files are not imported in this round. Consequently they do not change the frozen Round 2B corpus or the coverage denominator.

## Reproducible query

`context.v_context_coverage` limits the current corpus denominator to `corpus.firstbloom_a6cb002_pilot_v1`. This excludes two legacy smoke documents and prevents a misleading 2,476-document count.
