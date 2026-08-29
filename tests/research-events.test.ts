import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  COLLECTION_MODE,
  exportSyntheticPreview,
  previewSyntheticEvent,
  readSyntheticPreviews,
  saveSyntheticPreview,
  STORAGE_MODE,
  withdrawAndDeleteLocalPreviews,
} from "@/lib/research-events";

function localStorageFixture() {
  const values = new Map<string, string>();
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
  };
}

describe("local-only synthetic event contract", () => {
  beforeEach(() => {
    vi.stubGlobal("window", { localStorage: localStorageFixture() });
  });

  it("defaults to no remote collection and local-only storage", () => {
    expect(COLLECTION_MODE).toBe("NO_REMOTE_COLLECTION");
    expect(STORAGE_MODE).toBe("LOCAL_ONLY_OR_NO_OP");
    expect(previewSyntheticEvent().model_use_consent).toBe(false);
  });

  it("exports and deletes only synthetic local preview rows", () => {
    saveSyntheticPreview(previewSyntheticEvent({ answer: "jasmine" }));
    expect(readSyntheticPreviews()).toHaveLength(1);
    expect(JSON.parse(exportSyntheticPreview()).empirical_data).toBe(false);
    expect(withdrawAndDeleteLocalPreviews()).toBe(1);
    expect(readSyntheticPreviews()).toHaveLength(0);
  });
});
