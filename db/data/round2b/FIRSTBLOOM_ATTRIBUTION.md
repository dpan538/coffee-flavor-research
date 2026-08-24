# Firstbloom pilot attribution and boundary

The Round 2B pilot derives structured observations from **Firstbloom Data** by
Alex Caza, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The exact source is the pinned repository commit
`a6cb0026d1af9642724793c799bbc48dc189ba35` at
<https://github.com/alexcaza/firstbloom-data>.

The project records selected product-release metadata, short delimiter-derived
tasting-note phrases, hashes, and aggregate statistics. It does not reproduce
roaster descriptions, consumer reviews, or complete tasting-note strings.
Fragments longer than 80 Unicode characters are represented by a hash and
length only. The original dataset is a secondary aggregation; its CC BY grant
does not make industry language objective sensory truth or establish that the
original roaster authorized every upstream use.

Changes made by this project include deterministic stratified selection,
delimiter parsing, rights-boundary redaction, Unicode/case/whitespace
normalization, and statistical derivation. Missing product metadata remains
empty rather than being inferred. Roaster country is not inferred from domains
or time zones.
