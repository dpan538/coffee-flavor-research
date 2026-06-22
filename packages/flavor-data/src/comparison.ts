import type { Category, Descriptor, Modality, RangeScore } from "./schema";

export type ScoreDimensionId = keyof Descriptor["sensoryAssociation"];

export const scoreDimensions: Array<{
  id: ScoreDimensionId;
  labels: { en: string; zhHans: string };
  shortLabel: { en: string; zhHans: string };
}> = [
  {
    id: "sourness",
    labels: { en: "Sourness association", zhHans: "酸感关联" },
    shortLabel: { en: "Sour", zhHans: "酸" },
  },
  {
    id: "sweetness",
    labels: { en: "Sweetness association", zhHans: "甜感关联" },
    shortLabel: { en: "Sweet", zhHans: "甜" },
  },
  {
    id: "bitterness",
    labels: { en: "Bitterness association", zhHans: "苦感关联" },
    shortLabel: { en: "Bitter", zhHans: "苦" },
  },
  {
    id: "aromaProminence",
    labels: { en: "Aroma prominence", zhHans: "香气显著度" },
    shortLabel: { en: "Aroma", zhHans: "香" },
  },
  {
    id: "body",
    labels: { en: "Body association", zhHans: "厚度关联" },
    shortLabel: { en: "Body", zhHans: "体" },
  },
  {
    id: "roastFermentation",
    labels: {
      en: "Roast and fermentation association",
      zhHans: "烘烤/发酵关联",
    },
    shortLabel: { en: "Roast/Ferment", zhHans: "烘/酵" },
  },
];

export const modalityLabels: Record<Modality, { en: string; zhHans: string }> =
  {
    orthonasal: { en: "Orthonasal aroma", zhHans: "鼻前香气" },
    retronasal: { en: "Retronasal aroma", zhHans: "鼻后香气" },
    taste: { en: "Taste", zhHans: "味觉" },
    mouthfeel: { en: "Mouthfeel", zhHans: "口感" },
  };

export const statusLabels = {
  canonical: { en: "Canonical pilot", zhHans: "核心试验词" },
  boundary: { en: "Boundary", zhHans: "边界词" },
  compound: { en: "Compound", zhHans: "复合词" },
  unresolved: { en: "Unresolved", zhHans: "待验证" },
} as const;

export const confidenceLabels = {
  low: { en: "Low", zhHans: "低" },
  medium: { en: "Medium", zhHans: "中" },
  high: { en: "High", zhHans: "高" },
} as const;

export const evidenceLabels = {
  reference_supported: { en: "Reference-supported", zhHans: "参考框架支持" },
  open_data_supported: { en: "Open-data-supported", zhHans: "开放数据支持" },
  project_curated_draft: {
    en: "Project-curated draft",
    zhHans: "项目整理草案",
  },
  unresolved: { en: "Unresolved", zhHans: "待验证" },
} as const;

export function normalizeTerm(input: string) {
  return input
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

export function descriptorSearchText(descriptor: Descriptor) {
  return normalizeTerm(
    [
      descriptor.labels.en,
      descriptor.labels.zhHans,
      ...descriptor.aliases.en,
      ...descriptor.aliases.zhHans,
      descriptor.slug,
      descriptor.id,
    ].join(" "),
  );
}

export function matchesDescriptor(descriptor: Descriptor, query: string) {
  const normalizedQuery = normalizeTerm(query);

  if (!normalizedQuery) {
    return true;
  }

  return descriptorSearchText(descriptor).includes(normalizedQuery);
}

export function filterDescriptors(
  descriptors: Descriptor[],
  filters: {
    query?: string;
    categoryId?: string;
  },
) {
  return descriptors.filter((descriptor) => {
    const matchesCategory = filters.categoryId
      ? descriptor.categoryId === filters.categoryId
      : true;
    return (
      matchesCategory && matchesDescriptor(descriptor, filters.query ?? "")
    );
  });
}

export function getCategory(categories: Category[], categoryId: string) {
  const category = categories.find((item) => item.id === categoryId);

  if (!category) {
    throw new Error(`Missing category ${categoryId}`);
  }

  return category;
}

export function getDescriptorHref(descriptor: Descriptor) {
  return `/flavor/${descriptor.slug}`;
}

export function scoreToPercent(scoreValue: number) {
  return Math.max(0, Math.min(100, (scoreValue / 5) * 100));
}

export function rangeWidth(scoreValue: RangeScore) {
  return scoreToPercent(scoreValue.max) - scoreToPercent(scoreValue.min);
}

export function sensoryDistance(a: Descriptor, b: Descriptor) {
  const sum = scoreDimensions.reduce((total, dimension) => {
    const diff =
      a.sensoryAssociation[dimension.id].typical -
      b.sensoryAssociation[dimension.id].typical;
    return total + diff * diff;
  }, 0);

  return Math.sqrt(sum);
}

export function getRelatedDescriptors(
  descriptor: Descriptor,
  allDescriptors: Descriptor[],
  limit = 4,
) {
  return allDescriptors
    .filter((candidate) => candidate.slug !== descriptor.slug)
    .sort((a, b) => {
      const categoryWeightA = a.categoryId === descriptor.categoryId ? -2 : 0;
      const categoryWeightB = b.categoryId === descriptor.categoryId ? -2 : 0;
      return (
        categoryWeightA +
        sensoryDistance(descriptor, a) -
        (categoryWeightB + sensoryDistance(descriptor, b))
      );
    })
    .slice(0, limit);
}

export function getMapPoint(descriptor: Descriptor) {
  const x = scoreToPercent(descriptor.sensoryAssociation.sweetness.typical);
  const y =
    100 - scoreToPercent(descriptor.sensoryAssociation.sourness.typical);
  const aroma = descriptor.sensoryAssociation.aromaProminence.typical;

  return {
    x,
    y,
    radius: 5 + aroma * 2.2,
  };
}

export function compareDescriptors(a: Descriptor, b: Descriptor) {
  const dimensionDiffs = scoreDimensions
    .map((dimension) => {
      const aScore = a.sensoryAssociation[dimension.id];
      const bScore = b.sensoryAssociation[dimension.id];
      return {
        dimension,
        difference: Math.abs(aScore.typical - bScore.typical),
        aScore,
        bScore,
      };
    })
    .sort((left, right) => right.difference - left.difference);

  const sharedModalities = a.sensoryModalities.filter((modality) =>
    b.sensoryModalities.includes(modality),
  );

  const similarDimensions = dimensionDiffs
    .filter((item) => item.difference <= 0.45)
    .map((item) => item.dimension);

  return {
    sharedCategory: a.categoryId === b.categoryId ? a.categoryId : null,
    sharedModalities,
    sameConfidence: a.confidence === b.confidence ? a.confidence : null,
    sameEvidenceStatus:
      a.evidenceStatus === b.evidenceStatus ? a.evidenceStatus : null,
    similarDimensions,
    biggestDifference: dimensionDiffs[0]!,
    dimensionDiffs,
  };
}
