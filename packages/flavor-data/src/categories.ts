import { CategorySchema, type Category } from "./schema";

export const rawCategories = [
  {
    id: "floral",
    slug: "floral",
    labels: { en: "Floral", zhHans: "花香" },
    shortLabel: { en: "Floral", zhHans: "花" },
    description: {
      en: "Light, volatile aromatics that read as petals, blossoms, or perfume-like lift.",
      zhHans: "轻盈、挥发性强的香气联想，接近花瓣、花朵或细微香氛。",
    },
    colorToken: "var(--category-floral)",
  },
  {
    id: "fruit",
    slug: "fruit",
    labels: { en: "Fruit", zhHans: "水果" },
    shortLabel: { en: "Fruit", zhHans: "果" },
    description: {
      en: "Citrus, berry, and dried-fruit associations that often sit between acidity and sweetness.",
      zhHans: "柑橘、浆果与干果类联想，常位于酸感和甜感之间。",
    },
    colorToken: "var(--category-fruit)",
  },
  {
    id: "sweet",
    slug: "sweet",
    labels: { en: "Sweet", zhHans: "甜香" },
    shortLabel: { en: "Sweet", zhHans: "甜" },
    description: {
      en: "Aromas that suggest sugars, syrups, browning, or warm confectionery notes.",
      zhHans: "让人联想到糖、糖浆、褐变反应或温暖甜点的香气。",
    },
    colorToken: "var(--category-sweet)",
  },
  {
    id: "nut-cocoa",
    slug: "nut-cocoa",
    labels: { en: "Nut and Cocoa", zhHans: "坚果与可可" },
    shortLabel: { en: "Nut/Cocoa", zhHans: "坚果" },
    description: {
      en: "Roasted seed, nut, and cacao-like associations with more body and bitterness.",
      zhHans: "接近烘烤种子、坚果和可可的联想，通常伴随更明显的厚度和苦感。",
    },
    colorToken: "var(--category-nut-cocoa)",
  },
  {
    id: "spice-roasted",
    slug: "spice-roasted",
    labels: { en: "Spice and Roasted", zhHans: "香料与烘烤" },
    shortLabel: { en: "Spice", zhHans: "香料" },
    description: {
      en: "Warm spice, wood smoke, and roast-adjacent impressions from the aromatic edge of coffee.",
      zhHans: "温暖香料、木质烟感和接近烘烤边界的香气印象。",
    },
    colorToken: "var(--category-spice-roasted)",
  },
  {
    id: "green-earthy",
    slug: "green-earthy",
    labels: { en: "Green and Earthy", zhHans: "青绿与土壤" },
    shortLabel: { en: "Green", zhHans: "青绿" },
    description: {
      en: "Leafy, woody, resinous, or soil-like associations that can feel quiet or grounding.",
      zhHans: "叶片、木质、树脂或土壤类联想，常显得安静、沉稳。",
    },
    colorToken: "var(--category-green-earthy)",
  },
  {
    id: "fermented",
    slug: "fermented",
    labels: { en: "Fermented and Boundary", zhHans: "发酵与边界" },
    shortLabel: { en: "Ferment", zhHans: "发酵" },
    description: {
      en: "Wine-like, cultured, or process-linked impressions that need careful context.",
      zhHans: "葡萄酒样、培养物样或与处理过程相关的联想，需要谨慎解释。",
    },
    colorToken: "var(--category-fermented)",
  },
  {
    id: "unresolved",
    slug: "unresolved",
    labels: { en: "Unresolved", zhHans: "待验证" },
    shortLabel: { en: "Draft", zhHans: "试验" },
    description: {
      en: "Pilot nodes kept visible because their translation or sensory boundary is still uncertain.",
      zhHans: "因翻译、边界或感官对应关系仍不稳定而保留的试验节点。",
    },
    colorToken: "var(--category-unresolved)",
  },
] satisfies Category[];

export const categories = CategorySchema.array().parse(rawCategories);
