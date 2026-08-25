# Source acquisition plan

This plan was frozen after six read-only discovery lanes and before the first
Round 3H file download. It follows the readiness contract at checkpoint
`a2d85ecc1e03a96f129342f4ee4ed9755d7c4a75` and the machine-readable named
register at `db/data/round3h/source_candidate_register.tsv`.

## Lane A — coffee sensory repositories

Prioritize independent coffee-sensory outcomes with reusable, attributable
aggregates. The first batch will use Iswaldi et al. (2026), Vezzulli et al.
(2022), and Bollen et al. (2024). They collectively add ordinary-consumer RATA,
trained intensity/descriptive analysis, trained Q-grader profiles, explicit
preparation and roast contexts, and source-local descriptor evidence. Bollen's
Figshare workbook may be acquired only after its exact file identity, byte
count, hash, schema, and absence of participant identifiers are verified.

## Lane B — preparation and roast sensory studies

Iswaldi supplies 12 observed origin × roast × preparation cells across V60 and
cold brew and three measured roast categories. Vezzulli supplies eight
species × extraction cells across Moka, Neapolitan pot, espresso, and filter.
No source-local label will be silently projected across roast schemes or
converted between RATA, CATA, liking, and intensity scales. Liang/Dryad and
Gloess/Springer remain follow-up candidates pending exact file/rights audits;
request-only or ND/NC sources are not imported.

## Lane C — milk coffee

Gorman et al. (2021) and Nguyen et al. (2026) are the preferred aggregate-only
milk sources. Both are CC BY 4.0 and report actual sensory outcomes for coffee
served with dairy or plant-based alternatives. They create distinct federated
partitions: Gorman is hot coffee with dairy/soy/almond/oat and consumer
CATA/liking; Nguyen is chilled, sweetened espresso with five plant alternatives
and trained plus consumer measures. Participant rows will not be manufactured.
Stokes remains a cautionary aggregate source; CC BY-NC and rights-unclear milk
studies remain metadata-only.

## Lane D — contemporary tasting language

No source is admitted at register freeze. Open Food Facts is legally reusable
under ODbL/DbCL but needs a fixed-dump content profile and a separate
share-alike partition before any tasting-language count. RoastDB and LoffeeLabs
contain relevant product notes but their current terms prohibit the required
redistribution or require a negotiated commercial agreement. Scraped mirrors,
AI-normalized terms, Coffee Review, CQI, Kaggle, and Hugging Face copies are
rejected. This lane is targeted acquisition batch 3; if no lawful source
produces meaningful coverage, it is recorded as no-gain batch 1.

## Lane E — Simplified-Chinese coffee language

No source is admitted at register freeze. Open Food Facts may contain observed
zh-Hans product text, but exact script, coffee scope, sensory status, and ODbL
partitioning are unprofiled. Exact Chinese-Wikipedia revisions are CC BY-SA,
but automatic script conversion cannot be counted as source-authored
Simplified Chinese. OPUS GlobalVoices contains human-published Simplified
Chinese under CC BY 3.0 but its coffee-sensory yield is unknown. Copyrighted
lexicons, standards, noncommercial reviews, unclear web corpora, and synthetic
translations are rejected. This is targeted batch 4 and, absent lawful gain,
becomes no-gain batch 2 and triggers the frozen stopping rule.

## Lane F — question and instrument evidence

Gorman, Condelli, Heo, and Coffee Cuality provide independently published CATA,
JAR, liking, descriptive, or open-response structures. They may support
research targets and preserve contrasts such as acidic versus sour, roasted
versus burnt versus smoky, and body versus astringency. They do not validate
Atlas wording, user comprehension, or information gain. The two existing data
requests remain finalized but unsent: Foods 2022 2440 and JFS 15326.

## Staged cadence

1. Batch 1: Iswaldi, Vezzulli, and Bollen sensory/context aggregates; hash,
   import, measure coverage, commit, and push.
2. Batch 2: Gorman and Nguyen milk aggregates; hash, import, measure coverage,
   commit, and push.
3. Batch 3: contemporary-language content/rights resolution; commit and push
   even if the result is a documented no-gain decision.
4. Batch 4: zh-Hans content/rights resolution; commit and push. Two consecutive
   targeted no-gain batches stop acquisition honestly.
5. Batch 5: compute evidence-specific source-local statistics and question
   research mappings from admitted partitions; never add memberships or
   canonical concepts.

Every admitted source must have a canonical origin, exact version, license,
rights and privacy decisions, file/derived-artifact hashes, raw/parsed/
normalized preservation, public-export status, and a source-local partition.
