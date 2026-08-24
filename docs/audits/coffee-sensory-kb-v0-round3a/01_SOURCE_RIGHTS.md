# Source and rights audit

## Result

Three context dataset source versions have verified CC0 policies and `production_export_allowed=true`:

| Dataset key                                 | DOI                                                                | Rights decision                        |
| ------------------------------------------- | ------------------------------------------------------------------ | -------------------------------------- |
| `dataset.liang_2024_full_immersion_context` | [10.5061/dryad.v15dv423h](https://doi.org/10.5061/dryad.v15dv423h) | Dryad CC0; candidate data not imported |
| `dataset.cotter_2020_black_coffee_context`  | [10.25338/B8993H](https://doi.org/10.25338/B8993H)                 | Dryad CC0; candidate data not imported |
| `dataset.cotter_2023_acids_meta_analysis`   | [10.25338/B8C91C](https://doi.org/10.25338/B8C91C)                 | Dryad CC0; candidate data not imported |

Journal articles, SCA pages, and standards metadata use `license.context_publication_metadata_only.unknown.v1`:

```text
access_class=metadata_only
rights_status=unknown
redistributable=false
derivative_work_allowed=false
commercial_use_allowed=false
machine_use_allowed=false
production_export_allowed=false
```

The conservative status means the database can identify the source supporting an interpretation without exporting article text, tables, standards, or definitions.

Project-authored taxonomy and prose use `license.project_context.cc_by_4_0.v1`. Every description was independently written.

## Checks

- No source was scraped.
- No commercial roaster page was acquired.
- No SCA/WCR protected definition or table was copied.
- Dataset and associated-article rights remain separate.
- Licence policy is mandatory on every source version.
- Historical source deletion is restricted by context foreign keys.
- Rights-cleared source count is machine-validated as exactly 3.

The detailed source/version/field/limitation matrix is [09_CONTEXT_DATA_SOURCE_MATRIX.md](../../research/coffee-sensory-kb-v0-round3a/09_CONTEXT_DATA_SOURCE_MATRIX.md).
