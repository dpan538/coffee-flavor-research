import type { Category, Descriptor } from "./schema";

export function sortByCategoryThenName(
  descriptors: Descriptor[],
  categories: Category[],
) {
  const categoryOrder = new Map(
    categories.map((category, index) => [category.id, index]),
  );

  return [...descriptors].sort((a, b) => {
    const categoryDiff =
      (categoryOrder.get(a.categoryId) ?? 0) -
      (categoryOrder.get(b.categoryId) ?? 0);

    if (categoryDiff !== 0) {
      return categoryDiff;
    }

    return a.labels.en.localeCompare(b.labels.en);
  });
}
