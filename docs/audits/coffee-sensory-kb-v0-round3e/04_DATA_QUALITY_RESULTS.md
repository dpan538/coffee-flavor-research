# Data-quality results

| Snapshot          | Rows admitted / excluded | Key profile results                                                                             | Unrepaired flags                                                                  |
| ----------------- | -----------------------: | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| FT-NIR            |                  320 / 0 | 64 samples; 3 score replicates each; 64 green-labelled and 256 roasted-series rows              | preparation/assessor absent; geographic columns end early; no seven-level mapping |
| taste sensitivity |                   93 / 0 | 90 unique pseudonymous participant IDs; 0 exact duplicate rows; PII scan passed                 | numeric codebooks incomplete; age/gender are source demographics                  |
| Wikidata          |                   14 / 0 | English and Chinese label/alias coverage; 10 preparation mapping regions including 2 unresolved | community-edited and lexical only; regional equivalence not assumed               |
| USDA FDC          |                  32 / 18 | 7 black, 23 milk, 2 unreported beverage descriptions                                            | first 50 search hits only; 18 non-beverage hits explicitly excluded               |

Suspicious or incomplete values were not silently repaired. Source-local units
remain unchanged, and quality flags are stored in the generated profile and
database import receipt.

`DATA_QUALITY_REPORT_HASH=804ae622caef23f68a5fab0aa87fdea56cd444faa7b5e15624427c516215c588`
