import type { Descriptor } from "flavor-data";
import { descriptorAssetBySlug } from "@/assets/descriptor-assets";

type SpecimenVisualProps = {
  descriptor: Descriptor;
  variant?: "dark" | "light" | "mini";
};

function ProceduralMark({ descriptor }: { descriptor: Descriptor }) {
  const seed = descriptor.id
    .split("")
    .reduce((total, char) => total + char.charCodeAt(0), 0);
  const points = Array.from({ length: 9 }, (_, index) => {
    const angle = (Math.PI * 2 * index) / 9 + seed * 0.011;
    const radius = 34 + ((seed + index * 17) % 42);
    return {
      x: 100 + Math.cos(angle) * radius,
      y: 100 + Math.sin(angle) * radius,
      r: 3 + ((seed + index) % 5),
    };
  });

  return (
    <svg className="specimen-mark" viewBox="0 0 200 200" aria-hidden="true">
      <defs>
        <radialGradient id={`glow-${descriptor.slug}`}>
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.24" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="100" r="82" fill={`url(#glow-${descriptor.slug})`} />
      <g fill="none" stroke="currentColor" strokeWidth="1.1">
        {points.map((point, index) => (
          <line
            key={`line-${point.x}-${point.y}`}
            x1="100"
            y1="100"
            x2={point.x}
            y2={point.y}
            opacity={0.2 + index * 0.035}
          />
        ))}
      </g>
      <g fill="currentColor">
        <circle cx="100" cy="100" r="8" />
        {points.map((point) => (
          <circle
            key={`${point.x}-${point.y}`}
            cx={point.x}
            cy={point.y}
            r={point.r}
          />
        ))}
      </g>
    </svg>
  );
}

export function SpecimenVisual({
  descriptor,
  variant = "light",
}: SpecimenVisualProps) {
  const asset = descriptorAssetBySlug[descriptor.slug];

  return (
    <figure
      className={`specimen-visual specimen-visual--${variant}`}
      data-motion-family={
        asset?.motionFamily ?? descriptor.visualProfile.motion
      }
    >
      {asset ? (
        <img
          className="asset-specimen"
          src={asset.localPath}
          alt={`${descriptor.labels.en} visual candidate from ${asset.library}`}
        />
      ) : (
        <ProceduralMark descriptor={descriptor} />
      )}
      <figcaption className="meta-label">
        {asset
          ? `${asset.library} candidate / ${asset.originalIconName}`
          : `procedural category mark / ${descriptor.visualProfile.motif}`}
      </figcaption>
    </figure>
  );
}
