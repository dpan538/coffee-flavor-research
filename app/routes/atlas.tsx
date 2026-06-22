import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";
import {
  categories,
  confidenceLabels,
  descriptors,
  evidenceLabels,
  filterDescriptors,
  getCategory,
  getDescriptorHref,
  sortByCategoryThenName,
  statusLabels,
} from "flavor-data";
import type { Descriptor } from "flavor-data";
import { CompareOverlay } from "@/components/CompareOverlay";
import { DescriptorField } from "@/components/DescriptorField";
import { SensoryMap } from "@/components/SensoryMap";
import { useCursorController } from "@/hooks/useCursorController";
import { useAnimeScope } from "@/motion/animeScope";
import { useTextReveal } from "@/motion/textEffects";

type AtlasView = "field" | "index" | "map";

const validViews = new Set(["field", "index", "map"]);

export function meta() {
  return [
    { title: "Atlas / Coffee Flavor Atlas" },
    {
      name: "description",
      content:
        "Search, filter, map and compare 24 bilingual coffee flavor descriptors.",
    },
  ];
}

function useAtlasParams() {
  const [params, setParams] = useSearchParams();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  const activeParams = hydrated ? params : new URLSearchParams();
  const query = activeParams.get("q") ?? "";
  const categoryId = activeParams.get("category") ?? "";
  const viewParam = activeParams.get("view") ?? "field";
  const view = (validViews.has(viewParam) ? viewParam : "field") as AtlasView;
  const compareSlugs = (activeParams.get("compare") ?? "")
    .split(",")
    .map((slug) => slug.trim())
    .filter(Boolean)
    .slice(0, 2);

  const updateParams = (updates: Record<string, string | null>) => {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        Object.entries(updates).forEach(([key, value]) => {
          if (value) {
            next.set(key, value);
          } else {
            next.delete(key);
          }
        });
        return next;
      },
      { replace: false },
    );
  };

  const selectCompare = (descriptor: Descriptor) => {
    setParams(
      (previous) => {
        const nextParams = new URLSearchParams(previous);
        const previousSlugs = (nextParams.get("compare") ?? "")
          .split(",")
          .map((slug) => slug.trim())
          .filter(Boolean)
          .slice(0, 2);
        const nextSlugs = previousSlugs.includes(descriptor.slug)
          ? previousSlugs
          : [...previousSlugs, descriptor.slug].slice(-2);

        nextParams.set("compare", nextSlugs.join(","));
        return nextParams;
      },
      { replace: false },
    );
  };

  return {
    query,
    categoryId,
    view,
    compareSlugs,
    updateParams,
    selectCompare,
  };
}

export default function AtlasRoute() {
  const cursor = useCursorController();
  const { rootRef } = useAnimeScope<HTMLDivElement>();
  useTextReveal(rootRef);
  const { query, categoryId, view, compareSlugs, updateParams, selectCompare } =
    useAtlasParams();

  const filtered = useMemo(
    () =>
      sortByCategoryThenName(
        filterDescriptors(descriptors, {
          query,
          categoryId,
        }),
        categories,
      ),
    [categoryId, query],
  );

  const selected = compareSlugs
    .map((slug) => descriptors.find((descriptor) => descriptor.slug === slug))
    .filter((descriptor): descriptor is Descriptor => Boolean(descriptor));

  return (
    <div ref={rootRef} className="atlas-shell light-field">
      <section className="atlas-controls" aria-label="Atlas controls">
        <label>
          <span className="meta-label">SEARCH / 中英 aliases</span>
          <input
            aria-label="Search English Chinese aliases"
            value={query}
            placeholder="jasmine / 茉莉 / cacao"
            onChange={(event) => updateParams({ q: event.target.value })}
          />
        </label>
        <div className="view-switch" aria-label="View switch">
          {(["field", "index", "map"] as const).map((item) => (
            <button
              key={item}
              type="button"
              aria-pressed={view === item}
              onClick={() => updateParams({ view: item })}
            >
              {item.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="category-switch" aria-label="Category filter">
          <button
            type="button"
            aria-pressed={!categoryId}
            onClick={() => updateParams({ category: null })}
          >
            ALL
          </button>
          {categories.map((category) => (
            <button
              key={category.id}
              type="button"
              aria-pressed={categoryId === category.id}
              onClick={() => updateParams({ category: category.id })}
            >
              {category.shortLabel.en}
            </button>
          ))}
        </div>
      </section>

      <section className="atlas-opening">
        <div className="atlas-opening__label">
          <p className="meta-label">
            ATLAS / {filtered.length} visible descriptors
          </p>
          <p>
            Default FIELD view. Use INDEX for catalogue scanning or MAP for
            sensory position.
          </p>
        </div>
        {view === "field" ? (
          <div className="spatial-index" aria-label="Spatial descriptor index">
            <DescriptorField
              descriptors={filtered}
              categories={categories}
              cursor={cursor}
              compact
              onCompare={selectCompare}
            />
          </div>
        ) : null}
        {view === "index" ? (
          <table className="index-table">
            <caption className="sr-only">Descriptor index</caption>
            <thead>
              <tr>
                <th scope="col">No.</th>
                <th scope="col">中文</th>
                <th scope="col">English</th>
                <th scope="col">Category</th>
                <th scope="col">Status</th>
                <th scope="col">Evidence</th>
                <th scope="col">Compare</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((descriptor, index) => {
                const category = getCategory(categories, descriptor.categoryId);
                return (
                  <tr key={descriptor.slug}>
                    <td>{String(index + 1).padStart(2, "0")}</td>
                    <td>
                      <Link
                        to={getDescriptorHref(descriptor)}
                        onPointerEnter={() => cursor.setCursor("open", "OPEN")}
                        onPointerLeave={cursor.resetCursor}
                      >
                        {descriptor.labels.zhHans}
                      </Link>
                    </td>
                    <td>{descriptor.labels.en}</td>
                    <td>{category.labels.en}</td>
                    <td>{statusLabels[descriptor.descriptorStatus].en}</td>
                    <td>
                      {evidenceLabels[descriptor.evidenceStatus].en} /{" "}
                      {confidenceLabels[descriptor.confidence].en}
                    </td>
                    <td>
                      <button
                        className="text-button"
                        type="button"
                        onClick={() => selectCompare(descriptor)}
                        onPointerEnter={() =>
                          cursor.setCursor("compare", "COMPARE")
                        }
                        onPointerLeave={cursor.resetCursor}
                      >
                        Compare {descriptor.labels.en}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : null}
        {view === "map" ? (
          <SensoryMap
            descriptors={filtered}
            categories={categories}
            cursor={cursor}
          />
        ) : null}
      </section>

      <CompareOverlay
        descriptors={filtered}
        categories={categories}
        selected={selected}
        onClose={() => updateParams({ compare: null })}
        onRemove={(descriptor) => {
          const next = selected
            .filter(
              (selectedDescriptor) =>
                selectedDescriptor.slug !== descriptor.slug,
            )
            .map((selectedDescriptor) => selectedDescriptor.slug);
          updateParams({ compare: next.length > 0 ? next.join(",") : null });
        }}
      />
    </div>
  );
}
