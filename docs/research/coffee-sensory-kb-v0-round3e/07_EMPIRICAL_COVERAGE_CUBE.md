# Empirical coverage cube

The generated cube reports only observed source-local cells across:

`source × coffee identity × C0 preparation × C1 roast × black/milk × sensory method × participant type × language`.

It contains 52 observed rows after including the frozen Round 2B corpus,
Round 3B evidence, and four Round 3E snapshots. Omitted combinations are not
labelled empty because absence cannot be inferred from these files.

| Evidence region                          | Present evidence                                                                                             | Explicit limit                                                                                                                 |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Controlled black sensory                 | Dryad Cotter: 3,186 ordinary-consumer tastings, one Honduras medium-roast drip condition family              | preparation, roast and their interaction remain `NOT_ESTIMABLE`                                                                |
| Chemistry/context                        | Dryad Yeager: 1,631 source records across reported preparations/roasts, including three milk-context records | no sensory outcome; cannot support a milk model                                                                                |
| Specialty score/sample metadata          | Mendeley FT-NIR: 64 Colombian samples, 320 selected source rows                                              | preparation and seven-level roast absent                                                                                       |
| Consumer information response            | Mendeley taste-sensitivity: 93 ordinary-consumer rows                                                        | coffee condition and codebooks incomplete; no pooling with Cotter                                                              |
| Contemporary preparation language        | Wikidata: 14 versioned entities; USDA: 32 beverage descriptions                                              | lexical/reference evidence, not tasting outcomes                                                                               |
| Contemporary tasting-note corpus         | historical Firstbloom snapshot remains present                                                               | source-concentrated; Round 3E found no second lawful versioned tasting-note corpus suitable for import                         |
| Milk sensory outcome                     | none                                                                                                         | empty observation region is stated only because imported sensory outcome sources contain zero declared milk-condition outcomes |
| Simplified-Chinese human sensory outcome | none                                                                                                         | no participant collection and no imported bilingual outcome table                                                              |

Coverage counts are evidence-presence counts, not model-readiness metrics.
