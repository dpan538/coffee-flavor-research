# Expression extraction and normalization

Every admitted row in
`db/data/round3j/global-corpus/ADMITTED_FLAVOR_EXPRESSION_OCCURRENCE.tsv` is an
exact source substring. The only declared normalization operations are Unicode
normalization and outer-whitespace normalization; no translation, paraphrase,
synonym generation, imagery expansion, ingredient inference, or synthetic
combination is allowed.

The `guchengf` rows preserve the HTML file hash, document, paragraph/character
locator, raw phrase, and Simplified-Chinese normalized phrase. The article rows
preserve the official PDF hash, page/list locator, source language, and exact
term. The MFACT overall-score field (`nota geral`) is preference/overall
evidence and is not admitted as a flavor expression.

All 37 admitted occurrences have `label_disposition=UNRESOLVED` and an empty
target array. Ten English normalized forms already exist in the frozen
language surface, leaving 27 genuinely new normalized expressions. Their
training eligibility means they may serve as unresolved/abstain examples with
complete provenance; it does not make them gold canonical labels. Roles remain
source-local and CATA, consumer structured sensory, and author tasting prose
are not pooled into a universal scale.
