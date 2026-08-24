# Roast taxonomy

## Project target

The single project-normalized user scheme is `roast.scheme.project_v0_five_level`.

| Ordinal position | Stable key                 | Label      |
| ---------------: | -------------------------- | ---------- |
|                1 | `roast.project.very_light` | Very light |
|                2 | `roast.project.light`      | Light      |
|                3 | `roast.project.medium`     | Medium     |
|                4 | `roast.project.dark`       | Dark       |
|                5 | `roast.project.very_dark`  | Very dark  |

The ordinal positions permit ordered presentation. They do not imply equal intervals, Agtron boundaries, sensory distances, or ranking coefficients.

## Separately represented schemes

### Common three-level labels

`roast.scheme.common_three_level` contains source-style light, medium, and dark categories. Each maps approximately to the corresponding project label. The mapping is project-authored and explicitly `approximate` because category boundaries vary.

### Traditional and regional trade terminology

`roast.scheme.traditional_trade_labels` currently records candidate terms:

- City
- Full City
- Vienna
- French
- Italian
- Nordic

The scheme is unordered. It deliberately omits invented positions. `City+` remains an open curation item because a stable, rights-safe, source-specific definition has not been adopted.

### Brew-intent terminology

`roast.scheme.brew_intent_labels` records:

- filter roast
- espresso roast
- omniroast

These categories are unordered intended-use/style labels. None maps automatically to dark, light, or medium.

## Seven-level hypothesis

The proposed seven labels are rejected as the V1 project target. Four additional expressions—extremely light, medium-light, medium-dark, and extremely dark—remain in the unresolved queue. Their preservation prevents information loss without pretending that a safe normalization exists.

Status: `SEVEN_LEVEL_ROAST_HYPOTHESIS=rejected_for_v1_use_five_coarse_levels`.

## Unknown and not reported

The observation model distinguishes:

- `known`: a reviewed normalized category is present;
- `reported_unresolved`: a source expression is present but has no safe normalized target;
- `unknown`: the user explicitly does not know;
- `not_reported`: the source omitted the field;
- `not_applicable`: the field does not apply.

Unknown is absent from every roast scheme. This prevents accidental ordering and default-to-medium behavior.

## Measurement taxonomy

Four measurement-method records demonstrate the necessary distinction:

- Agtron Gourmet, whole-bean basis;
- Agtron Gourmet, ground-coffee basis;
- CIELAB L\*, whole-bean basis;
- CIELAB L\*, ground-coffee basis.

Each method declares bounds and direction. No table maps a measurement range to a project category in Round 3A. Future range mappings require a versioned method, evidence, and validation.

## Keys and provenance

Every scheme has a stable key, source version, lifecycle state, and independently authored description. Category mappings contain the source category, target category, certainty code, source version, assertion role, and evidence locator. Source-scheme positions remain recoverable through `context.v_roast_normalization`.
