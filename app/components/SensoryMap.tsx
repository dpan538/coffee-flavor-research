import type { Descriptor, Category } from "flavor-data";
import { getCategory, getDescriptorHref, getMapPoint } from "flavor-data";
import { Link } from "react-router";
import type { CursorController } from "@/motion/cursorEffects";

type SensoryMapProps = {
  descriptors: Descriptor[];
  categories: Category[];
  cursor?: CursorController;
};

const confidenceOpacity = {
  low: 0.42,
  medium: 0.68,
  high: 0.92,
};

export function SensoryMap({
  descriptors,
  categories,
  cursor,
}: SensoryMapProps) {
  return (
    <section
      className="sensory-map-editorial"
      aria-label="Sensory association map section"
    >
      <aside className="map-notes">
        <p className="meta-label">MAP / SWEETNESS X SOURNESS</p>
        <p>
          位置表示项目整理的典型感官关联，不代表固定杯测结果。Node size follows
          aroma prominence; outline weight follows confidence.
        </p>
        <ol>
          <li>X: sweetness association</li>
          <li>Y: sourness association</li>
          <li>halo: prototype uncertainty</li>
        </ol>
      </aside>
      <svg
        className="map-canvas"
        viewBox="0 0 100 100"
        role="img"
        aria-label="Sensory association map of filtered coffee flavor descriptors"
      >
        <title>Sensory association map</title>
        <defs>
          <pattern
            id="map-grid"
            width="10"
            height="10"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 10 0 L 0 0 0 10"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.08"
            />
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#map-grid)" opacity="0.46" />
        <text x="2" y="5" className="map-edge-label">
          sourness +
        </text>
        <text x="70" y="96" className="map-edge-label">
          sweetness +
        </text>
        {descriptors.map((descriptor, index) => {
          const point = getMapPoint(descriptor);
          const category = getCategory(categories, descriptor.categoryId);
          return (
            <Link
              key={descriptor.slug}
              to={getDescriptorHref(descriptor)}
              aria-label={`Open ${descriptor.labels.en} detail page`}
              onPointerEnter={() =>
                cursor?.setCursor("open", descriptor.labels.en.toUpperCase())
              }
              onPointerLeave={cursor?.resetCursor}
            >
              <g className="map-node" data-category={category.slug}>
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={point.radius * 0.35 + 2.2}
                  fill="currentColor"
                  opacity={0.07}
                  filter="blur(1.2px)"
                />
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={point.radius * 0.22 + 1.2}
                  fill="var(--page-bg)"
                  stroke="currentColor"
                  strokeWidth={descriptor.confidence === "high" ? 0.68 : 0.38}
                  opacity={confidenceOpacity[descriptor.confidence]}
                />
                <text
                  x={point.x}
                  y={point.y + 0.8}
                  textAnchor="middle"
                  className="map-node__index"
                >
                  {String(index + 1).padStart(2, "0")}
                </text>
                <text
                  x={point.x + 2.6}
                  y={point.y - 2.6}
                  className="map-node__label"
                >
                  {descriptor.labels.zhHans}
                </text>
              </g>
            </Link>
          );
        })}
      </svg>
      <div
        className="map-alt-list"
        aria-label="Map alternative descriptor list"
      >
        {descriptors.map((descriptor) => (
          <Link key={descriptor.slug} to={getDescriptorHref(descriptor)}>
            {descriptor.labels.zhHans} / {descriptor.labels.en}
          </Link>
        ))}
      </div>
    </section>
  );
}
