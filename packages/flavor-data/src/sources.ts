import { SourceSchema, type Source } from "./schema";

export const rawSources = [
  {
    id: "wcr-sensory-lexicon",
    name: "WCR Sensory Lexicon",
    sourceType: "reference_framework",
    licenseStatus:
      "Reference framework; not copied or redistributed in this MVP.",
    reusePolicy: "reference_only",
    attributionRequired: true,
    notes:
      "Used only as background awareness for coffee sensory vocabulary practice. No definitions or long passages are reproduced.",
  },
  {
    id: "sca-coffee-value-assessment",
    name: "SCA Coffee Value Assessment",
    sourceType: "reference_framework",
    licenseStatus:
      "Reference framework; no proprietary forms, scales, or graphics copied.",
    reusePolicy: "reference_only",
    attributionRequired: true,
    notes:
      "Used as context for separating descriptive language from value judgments. The Atlas does not reproduce SCA graphics or full vocabulary.",
  },
  {
    id: "uc-davis-black-coffee-consumer-dataset",
    name: "UC Davis Black Coffee Consumer Dataset",
    sourceType: "open_dataset",
    licenseStatus:
      "Open data candidate for later validation; not yet used to compute MVP scores.",
    reusePolicy: "open_reuse",
    attributionRequired: true,
    notes:
      "Listed as a future validation source. Current prototype scores are not derived from this dataset.",
  },
  {
    id: "coffee-flavor-atlas-editorial-pilot",
    name: "Coffee Flavor Atlas Editorial Pilot",
    sourceType: "project_curation",
    licenseStatus: "Project-created draft data for interface prototyping.",
    reusePolicy: "project_created",
    attributionRequired: false,
    notes:
      "All sensory association profiles in this MVP are project-curated draft values created to test the data model and interface.",
  },
] satisfies Source[];

export const sources = SourceSchema.array().parse(rawSources);
