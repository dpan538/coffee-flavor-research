import { describe, expect, it } from "vitest";
import {
  categories,
  compareDescriptors,
  descriptors,
  filterDescriptors,
  getMapPoint,
  scoreDimensions,
  sensoryDistance,
} from "flavor-data";

describe("descriptor search", () => {
  it("matches English labels, Chinese labels, slugs, and aliases", () => {
    expect(
      filterDescriptors(descriptors, { query: "jasmine" }).map(
        (item) => item.slug,
      ),
    ).toContain("jasmine");
    expect(
      filterDescriptors(descriptors, { query: "茉莉" }).map(
        (item) => item.slug,
      ),
    ).toContain("jasmine");
    expect(
      filterDescriptors(descriptors, { query: "cacao" }).map(
        (item) => item.slug,
      ),
    ).toContain("dark-chocolate");
    expect(
      filterDescriptors(descriptors, { query: "红浆果" }).map(
        (item) => item.slug,
      ),
    ).toContain("red-berries");
  });

  it("filters descriptors by category", () => {
    const fruit = categories.find((category) => category.id === "fruit");
    expect(fruit).toBeDefined();

    const results = filterDescriptors(descriptors, { categoryId: fruit!.id });

    expect(results).toHaveLength(5);
    expect(
      results.every((descriptor) => descriptor.categoryId === "fruit"),
    ).toBe(true);
  });
});

describe("comparison and map utilities", () => {
  it("computes shared traits and largest differences from data", () => {
    const jasmine = descriptors.find(
      (descriptor) => descriptor.slug === "jasmine",
    );
    const darkChocolate = descriptors.find(
      (descriptor) => descriptor.slug === "dark-chocolate",
    );

    expect(jasmine).toBeDefined();
    expect(darkChocolate).toBeDefined();

    const comparison = compareDescriptors(jasmine!, darkChocolate!);
    expect(comparison.biggestDifference.difference).toBeGreaterThan(2);
    expect(scoreDimensions.map((dimension) => dimension.id)).toContain(
      comparison.biggestDifference.dimension.id,
    );
  });

  it("maps every descriptor into the SVG coordinate space", () => {
    for (const descriptor of descriptors) {
      const point = getMapPoint(descriptor);
      expect(point.x).toBeGreaterThanOrEqual(0);
      expect(point.x).toBeLessThanOrEqual(100);
      expect(point.y).toBeGreaterThanOrEqual(0);
      expect(point.y).toBeLessThanOrEqual(100);
      expect(point.radius).toBeGreaterThan(0);
    }
  });

  it("computes sensory distances for related descriptor sorting", () => {
    const lemon = descriptors.find((descriptor) => descriptor.slug === "lemon");
    const orange = descriptors.find(
      (descriptor) => descriptor.slug === "orange",
    );
    const smoky = descriptors.find((descriptor) => descriptor.slug === "smoky");

    expect(lemon && orange && smoky).toBeTruthy();
    expect(sensoryDistance(lemon!, orange!)).toBeLessThan(
      sensoryDistance(lemon!, smoky!),
    );
  });
});
