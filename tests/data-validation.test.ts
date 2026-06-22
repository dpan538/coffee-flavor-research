import { describe, expect, it } from "vitest";
import {
  descriptors,
  rawCategories,
  rawDescriptors,
  rawSources,
  validateAtlasData,
} from "flavor-data";

describe("atlas data validation", () => {
  it("validates the complete pilot dataset", () => {
    expect(() =>
      validateAtlasData({
        categories: rawCategories,
        sources: rawSources,
        descriptors: rawDescriptors,
      }),
    ).not.toThrow();
  });

  it("contains exactly 24 pilot descriptors with unique ids and slugs", () => {
    expect(descriptors).toHaveLength(24);
    expect(new Set(descriptors.map((descriptor) => descriptor.id)).size).toBe(
      24,
    );
    expect(new Set(descriptors.map((descriptor) => descriptor.slug)).size).toBe(
      24,
    );
  });

  it("keeps prototype sensory profiles marked as project-curated drafts", () => {
    expect(
      descriptors.every(
        (descriptor) => descriptor.evidenceStatus === "project_curated_draft",
      ),
    ).toBe(true);
  });

  it("marks boundary and unresolved pilot nodes transparently", () => {
    const bellflower = descriptors.find(
      (descriptor) => descriptor.slug === "bellflower",
    );
    const cheese = descriptors.find(
      (descriptor) => descriptor.slug === "cheese",
    );
    const winey = descriptors.find((descriptor) => descriptor.slug === "winey");
    const redBerries = descriptors.find(
      (descriptor) => descriptor.slug === "red-berries",
    );

    expect(bellflower?.descriptorStatus).toBe("unresolved");
    expect(bellflower?.editorialNote?.en).toContain("unresolved");
    expect(cheese?.descriptorStatus).toBe("boundary");
    expect(cheese?.editorialNote?.en).toContain("boundary");
    expect(winey?.descriptorStatus).toBe("compound");
    expect(winey?.editorialNote?.en).toContain("compound");
    expect(redBerries?.editorialNote?.en).toContain("broad pilot node");
  });
});
