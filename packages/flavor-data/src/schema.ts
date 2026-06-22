import { z } from "zod";

export const ModalitySchema = z.enum([
  "orthonasal",
  "retronasal",
  "taste",
  "mouthfeel",
]);
export const DescriptorStatusSchema = z.enum([
  "canonical",
  "boundary",
  "compound",
  "unresolved",
]);
export const ConfidenceSchema = z.enum(["low", "medium", "high"]);
export const EvidenceStatusSchema = z.enum([
  "reference_supported",
  "open_data_supported",
  "project_curated_draft",
  "unresolved",
]);
export const MotionModeSchema = z.enum(["breathe", "bloom", "drift", "echo"]);
export const SourceTypeSchema = z.enum([
  "reference_framework",
  "open_dataset",
  "project_curation",
]);
export const ReusePolicySchema = z.enum([
  "reference_only",
  "open_reuse",
  "project_created",
]);

export const RangeScoreSchema = z
  .object({
    min: z.number().min(0).max(5),
    typical: z.number().min(0).max(5),
    max: z.number().min(0).max(5),
  })
  .superRefine((score, ctx) => {
    if (score.min > score.typical) {
      ctx.addIssue({
        code: "custom",
        message: "RangeScore min must be less than or equal to typical",
        path: ["min"],
      });
    }

    if (score.typical > score.max) {
      ctx.addIssue({
        code: "custom",
        message: "RangeScore typical must be less than or equal to max",
        path: ["typical"],
      });
    }
  });

const LocalizedLabelSchema = z.object({
  en: z.string().trim().min(1),
  zhHans: z.string().trim().min(1),
});

export const CategorySchema = z.object({
  id: z.string().trim().min(1),
  slug: z.string().trim().min(1),
  labels: LocalizedLabelSchema,
  shortLabel: LocalizedLabelSchema,
  description: LocalizedLabelSchema,
  colorToken: z.string().trim().min(1),
});

export const SourceSchema = z.object({
  id: z.string().trim().min(1),
  name: z.string().trim().min(1),
  sourceType: SourceTypeSchema,
  licenseStatus: z.string().trim().min(1),
  reusePolicy: ReusePolicySchema,
  attributionRequired: z.boolean(),
  notes: z.string().trim().min(1),
  url: z.url().optional(),
});

export const DescriptorSchema = z.object({
  id: z.string().trim().min(1),
  slug: z.string().trim().min(1),
  labels: LocalizedLabelSchema,
  aliases: z.object({
    en: z.array(z.string().trim().min(1)),
    zhHans: z.array(z.string().trim().min(1)),
  }),
  categoryId: z.string().trim().min(1),
  descriptorStatus: DescriptorStatusSchema,
  sensoryModalities: z.array(ModalitySchema).min(1),
  summary: LocalizedLabelSchema,
  sensoryAssociation: z.object({
    sourness: RangeScoreSchema,
    sweetness: RangeScoreSchema,
    bitterness: RangeScoreSchema,
    aromaProminence: RangeScoreSchema,
    body: RangeScoreSchema,
    roastFermentation: RangeScoreSchema,
  }),
  confidence: ConfidenceSchema,
  evidenceStatus: EvidenceStatusSchema,
  sourceIds: z.array(z.string().trim().min(1)).min(1),
  visualProfile: z.object({
    motif: z.string().trim().min(1),
    density: z.number().min(0).max(1),
    curvature: z.number().min(0).max(1),
    halo: z.number().min(0).max(1),
    motion: MotionModeSchema,
  }),
  editorialNote: LocalizedLabelSchema.optional(),
});

export type RangeScore = z.infer<typeof RangeScoreSchema>;
export type Modality = z.infer<typeof ModalitySchema>;
export type DescriptorStatus = z.infer<typeof DescriptorStatusSchema>;
export type Confidence = z.infer<typeof ConfidenceSchema>;
export type EvidenceStatus = z.infer<typeof EvidenceStatusSchema>;
export type MotionMode = z.infer<typeof MotionModeSchema>;
export type Category = z.infer<typeof CategorySchema>;
export type Source = z.infer<typeof SourceSchema>;
export type Descriptor = z.infer<typeof DescriptorSchema>;

function assertUnique(values: string[], label: string) {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  for (const value of values) {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  }

  if (duplicates.size > 0) {
    throw new Error(
      `${label} must be unique. Duplicates: ${Array.from(duplicates).join(", ")}`,
    );
  }
}

export function validateAtlasData(input: {
  categories: unknown[];
  sources: unknown[];
  descriptors: unknown[];
}) {
  const categories = z.array(CategorySchema).parse(input.categories);
  const sources = z.array(SourceSchema).parse(input.sources);
  const descriptors = z.array(DescriptorSchema).parse(input.descriptors);

  assertUnique(
    categories.map((category) => category.id),
    "Category ids",
  );
  assertUnique(
    sources.map((source) => source.id),
    "Source ids",
  );
  assertUnique(
    descriptors.map((descriptor) => descriptor.id),
    "Descriptor ids",
  );
  assertUnique(
    descriptors.map((descriptor) => descriptor.slug),
    "Descriptor slugs",
  );

  const categoryIds = new Set(categories.map((category) => category.id));
  const sourceIds = new Set(sources.map((source) => source.id));
  const relationshipIssues: string[] = [];

  for (const descriptor of descriptors) {
    if (!categoryIds.has(descriptor.categoryId)) {
      relationshipIssues.push(
        `${descriptor.slug} references missing category ${descriptor.categoryId}`,
      );
    }

    for (const sourceId of descriptor.sourceIds) {
      if (!sourceIds.has(sourceId)) {
        relationshipIssues.push(
          `${descriptor.slug} references missing source ${sourceId}`,
        );
      }
    }
  }

  if (relationshipIssues.length > 0) {
    throw new Error(
      `Atlas relationship validation failed:\n${relationshipIssues.join("\n")}`,
    );
  }

  return {
    categories,
    sources,
    descriptors,
  };
}
