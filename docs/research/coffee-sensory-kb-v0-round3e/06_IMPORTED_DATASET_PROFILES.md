# Imported dataset profiles

Machine-readable profiles are generated at
`db/data/round3e/generated/data_quality_profiles.json`.

## Mendeley FT-NIR v4 selected files

- Raw/imported: 320/320 source rows; 15 source-local fields across the selected
  data tables; 64 sample identities.
- Replication: three score rows per sample plus paired green/roasted metadata
  rows.
- Coverage: Colombian samples; green and roasted labels; no preparation field,
  no assessor count, no black/milk label, and no seven-level roast mapping.
- Quality flags: source uses an “SCA” score label, which is preserved as a raw
  label and is not endorsed, converted, or inserted into the canonical ontology.

## Mendeley taste-sensitivity v1

- Raw/imported: 93/93 pseudonymous consumer rows; 13 fields; 93 unique source
  IDs; zero exact duplicate rows detected.
- Fields include information treatment, bitterness, overall taste, preference,
  purchase likelihood, PROP score, coffee frequency/experience, age, and gender.
- The secondary worksheet is an aggregate analysis and is excluded from the
  participant-row import.
- Quality flags: numeric codebooks are incomplete in the workbook; preparation,
  roast, coffee identity, and black/milk condition are not reported there.

## Wikidata preparation entities

- Raw/imported: 14/14 entity records with entity revision IDs and timestamps.
- Derived: labels and aliases remain occurrence-level, language-tagged candidate
  mappings. Duplicate fallback forms are preserved rather than silently merged.
- Quality flags: community-edited lexical evidence is not sensory truth and is
  not automatically canonical.

## USDA FoodData Central FNDDS

- Raw snapshot: 50 search rows, 18 top-level source fields.
- Derived import: 32 coffee-beverage descriptions; 18 creamer/cake/bread hits
  excluded by an explicit deterministic rule.
- Coverage: English, United States, black and milk beverage terminology.
- Quality flags: this is food-description vocabulary, not controlled specialty
  sensory observation or product tasting-note evidence.

No suspicious value is repaired silently, and no unit is converted.
