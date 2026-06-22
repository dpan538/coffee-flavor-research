import type { Descriptor, Category } from "flavor-data";
import {
  compareDescriptors,
  confidenceLabels,
  evidenceLabels,
  getCategory,
  modalityLabels,
  scoreDimensions,
} from "flavor-data";
import { RangeTrack } from "@/components/RangeTrack";
import { SpecimenVisual } from "@/components/SpecimenVisual";

type CompareOverlayProps = {
  descriptors: Descriptor[];
  categories: Category[];
  selected: Descriptor[];
  onClose: () => void;
  onRemove: (descriptor: Descriptor) => void;
};

function SharedNotes({
  first,
  second,
  categories,
}: {
  first: Descriptor;
  second: Descriptor;
  categories: Category[];
}) {
  const comparison = compareDescriptors(first, second);
  const sharedCategory = comparison.sharedCategory
    ? getCategory(categories, comparison.sharedCategory)
    : null;

  return (
    <div className="compare-notes">
      <p className="meta-label">SAME / 相同点</p>
      <p>
        {sharedCategory
          ? `Same category: ${sharedCategory.labels.en} / ${sharedCategory.labels.zhHans}. `
          : "Different categories. "}
        {comparison.sharedModalities.length > 0
          ? `Shared modalities: ${comparison.sharedModalities
              .map((modality) => modalityLabels[modality].en)
              .join(", ")}. `
          : "No shared modality in this pilot profile. "}
        {comparison.sameEvidenceStatus
          ? `Both evidence status: ${evidenceLabels[comparison.sameEvidenceStatus].en}.`
          : ""}
      </p>
      <p className="meta-label">MAX DIFFERENCE / 差异最大</p>
      <p>
        差异最大: {comparison.biggestDifference.dimension.labels.zhHans} /{" "}
        {comparison.biggestDifference.dimension.labels.en}, typical delta{" "}
        {comparison.biggestDifference.difference.toFixed(1)}.
      </p>
    </div>
  );
}

export function CompareOverlay({
  descriptors,
  categories,
  selected,
  onClose,
  onRemove,
}: CompareOverlayProps) {
  if (selected.length === 0) {
    return null;
  }

  const [first, second] = selected;

  if (!second && first) {
    return (
      <aside className="compare-dock" aria-label="Descriptor comparison">
        <p className="meta-label">COMPARE QUEUE</p>
        <p>
          {first.labels.zhHans} / {first.labels.en} selected. Choose one more
          descriptor.
        </p>
        <button className="text-button" type="button" onClick={onClose}>
          Clear
        </button>
      </aside>
    );
  }

  return (
    <aside className="compare-overlay" aria-label="Descriptor comparison">
      <div className="compare-toolbar">
        <h2>Descriptor comparison / 描述词比较</h2>
        <button className="text-button" type="button" onClick={onClose}>
          Close comparison
        </button>
      </div>
      {selected.map((descriptor) => {
        const category = getCategory(categories, descriptor.categoryId);
        return (
          <section className="compare-panel" key={descriptor.slug}>
            <button
              className="compare-remove"
              type="button"
              onClick={() => onRemove(descriptor)}
            >
              remove
            </button>
            <SpecimenVisual descriptor={descriptor} variant="mini" />
            <h3>
              {descriptor.labels.en}
              <span className="cjk">{descriptor.labels.zhHans}</span>
            </h3>
            <p className="meta-label">
              {category.labels.en} / {descriptor.descriptorStatus} /{" "}
              {confidenceLabels[descriptor.confidence].en} confidence /{" "}
              {evidenceLabels[descriptor.evidenceStatus].en}
            </p>
            <p className="meta-label">
              {descriptor.sensoryModalities
                .map((modality) => modalityLabels[modality].en)
                .join(" / ")}
            </p>
            {scoreDimensions.map((dimension) => (
              <RangeTrack
                key={dimension.id}
                label={dimension.shortLabel.zhHans}
                score={descriptor.sensoryAssociation[dimension.id]}
              />
            ))}
          </section>
        );
      })}
      {first && second ? (
        <SharedNotes first={first} second={second} categories={categories} />
      ) : (
        <div className="compare-notes">
          <p className="meta-label">SELECT SECOND SPECIMEN</p>
          <p>
            One descriptor selected. Choose another row or field node with
            Compare to calculate shared signals and largest dimensional
            difference.
          </p>
          <p className="meta-label">
            {descriptors.length} descriptors remain in current view
          </p>
        </div>
      )}
    </aside>
  );
}
