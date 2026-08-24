# Roast normalization

## Policy

Normalization is a governed interpretation, not numeric conversion. The pipeline preserves the reported expression and source scheme before considering a project category.

```text
reported roast expression
↓
source/source-version context
↓
source-specific roast category, when known
↓
reviewed mapping with certainty and provenance
↓
project five-level category
or REPORTED_UNRESOLVED
```

## Allowed mappings in V0

Only the common three-level scheme has active category mappings:

| Source category | Project target | Certainty   | Limitation                |
| --------------- | -------------- | ----------- | ------------------------- |
| common light    | project light  | approximate | no shared physical cutoff |
| common medium   | project medium | approximate | no shared physical cutoff |
| common dark     | project dark   | approximate | no shared physical cutoff |

Exact project expressions map to their own project categories. They are lexical identities within the project scheme, not claims about an external source.

## Mandatory abstentions

The following expressions remain unresolved:

- extremely light
- medium-light
- medium-dark
- extremely dark
- City roast
- Full City roast
- Vienna roast
- French roast
- Italian roast
- Nordic roast
- filter roast
- espresso roast
- omniroast

Unresolved does not mean unimportant. It means that a source expression is preserved without forcing a universal category.

## Measurements

A measured roast value is retained as:

```text
measurement method
+ material basis (whole bean / ground / beverage)
+ numeric value
+ source version
+ evidence locator
```

It is never stored as the ordinal category position. Whole-bean and ground measurements are not interchangeable, and CIELAB L\* is not an alias for an Agtron reading.

## Brew intent

`filter roast`, `espresso roast`, and `omniroast` are modeled in an unordered style scheme. A source may later report both an intended-use label and a measured/declared degree. Both facts can coexist.

Examples:

```text
style = espresso roast
declared category = not reported
measured color = not reported
normalized roast = unresolved
```

or:

```text
style = espresso roast
declared category = source medium
normalized roast = project medium (approximate)
```

The style never supplies the normalized degree by itself.

## Confidence semantics

`exact_project_label`, `approximate`, and `ambiguous_candidate` are governance metadata. They control review and query behavior. They are not multiplied into sensory similarity or displayed as true-flavor probability.

## Future admission gate

A new mapping requires:

1. a stable source expression/category identity;
2. a source version and rights decision;
3. an assertion role and evidence locator;
4. a stated certainty class;
5. no conflict with an active exact mapping unless every sense is explicitly ambiguous;
6. validation that the target belongs to the single project-normalized scheme.
