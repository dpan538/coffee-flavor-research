import type { CSSProperties } from "react";
import { Link } from "react-router";
import type { Category, Descriptor } from "flavor-data";
import { getCategory, getDescriptorHref } from "flavor-data";
import type { CursorController } from "@/motion/cursorEffects";

function positionFor(descriptor: Descriptor, index: number, total: number) {
  const categoryBands: Record<string, number> = {
    floral: 18,
    fruit: 31,
    sweet: 45,
    "nut-cocoa": 59,
    "spice-roasted": 70,
    "green-earthy": 80,
    fermented: 89,
    unresolved: 12,
  };
  const band = categoryBands[descriptor.categoryId] ?? 50;
  const seed = descriptor.id
    .split("")
    .reduce((totalValue, char) => totalValue + char.charCodeAt(0), 0);
  const orbit = (index / Math.max(1, total - 1)) * Math.PI * 2;
  const sweetness = descriptor.sensoryAssociation.sweetness.typical / 5;
  const sourness = descriptor.sensoryAssociation.sourness.typical / 5;

  return {
    x: Math.max(8, Math.min(92, 14 + sweetness * 72 + Math.sin(seed) * 7)),
    y: Math.max(
      13,
      Math.min(88, band + Math.cos(orbit + seed) * 8 - sourness * 9),
    ),
  };
}

type DescriptorFieldProps = {
  descriptors: Descriptor[];
  categories: Category[];
  cursor?: CursorController;
  compact?: boolean;
  onCompare?: (descriptor: Descriptor) => void;
};

export function DescriptorField({
  descriptors,
  categories,
  cursor,
  compact = false,
  onCompare,
}: DescriptorFieldProps) {
  return (
    <div
      className={
        compact
          ? "descriptor-field descriptor-field--compact"
          : "descriptor-field"
      }
    >
      <svg
        className="field-line"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {descriptors.map((descriptor, index) => {
          const point = positionFor(descriptor, index, descriptors.length);
          const next = positionFor(
            descriptors[(index + 1) % descriptors.length]!,
            (index + 1) % descriptors.length,
            descriptors.length,
          );
          return (
            <line
              key={descriptor.slug}
              x1={point.x}
              y1={point.y}
              x2={next.x}
              y2={next.y}
              stroke="currentColor"
              strokeWidth="0.08"
              opacity="0.32"
            />
          );
        })}
      </svg>
      {descriptors.map((descriptor, index) => {
        const category = getCategory(categories, descriptor.categoryId);
        const point = positionFor(descriptor, index, descriptors.length);
        const style = {
          "--node-x": `${point.x}%`,
          "--node-y": `${point.y}%`,
          "--node-size": `${1.5 + descriptor.sensoryAssociation.aromaProminence.typical * 0.46}rem`,
        } as CSSProperties;

        return (
          <span className="field-node-wrap" style={style} key={descriptor.slug}>
            <Link
              className="field-node"
              to={getDescriptorHref(descriptor)}
              aria-label={`Open ${descriptor.labels.en} detail page / 打开${descriptor.labels.zhHans}`}
              onPointerEnter={() =>
                cursor?.setCursor("open", descriptor.labels.en.toUpperCase())
              }
              onPointerLeave={cursor?.resetCursor}
              data-category={category.slug}
            >
              <span className="field-node__index">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="field-node__label">
                {descriptor.labels.zhHans} / {descriptor.labels.en}
              </span>
            </Link>
            {onCompare ? (
              <button
                className="field-compare"
                type="button"
                onClick={() => onCompare(descriptor)}
                onPointerEnter={() => cursor?.setCursor("compare", "COMPARE")}
                onPointerLeave={cursor?.resetCursor}
              >
                Compare {descriptor.labels.en}
              </button>
            ) : null}
          </span>
        );
      })}
    </div>
  );
}
