# Firstbloom pilot attribution and boundary

The Round 2B pilot derives structured observations from **Firstbloom Data** by
Alex Caza, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The exact source is the pinned repository commit
`a6cb0026d1af9642724793c799bbc48dc189ba35` at
<https://github.com/alexcaza/firstbloom-data>.

The project records selected product-release metadata, hashes, aggregate
statistics, and only short partial tasting-note phrases admitted by two
independent Codex-assisted project-curation passes. The passes are project
curation, not human-review evidence or automated language detection. A phrase
is tagged English only when both passes classify it as English tasting
language. Complete-field surfaces, disagreements, narrative, non-English and
uncertain fragments, and fragments longer than 80 Unicode characters are
hash-only. The repository does not reproduce roaster descriptions, consumer
reviews, or complete tasting-note strings. The original dataset is a secondary
aggregation; its CC BY grant does not make industry language objective sensory
truth or establish that the original roaster authorized every upstream use.

Changes made by this project include deterministic stratified selection,
delimiter parsing, global complete-field redaction, dual-review expression
admission, Unicode/case/whitespace normalization, and statistical derivation.
Missing product metadata remains empty rather than being inferred. Roaster
country is not inferred from domains or time zones.
