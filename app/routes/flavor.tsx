import { Link, useParams } from "react-router";
import {
  categories,
  confidenceLabels,
  descriptors,
  evidenceLabels,
  getCategory,
  getRelatedDescriptors,
  modalityLabels,
  scoreDimensions,
  sources,
  statusLabels,
} from "flavor-data";
import { RangeTrack } from "@/components/RangeTrack";
import { SpecimenVisual } from "@/components/SpecimenVisual";
import { useCursorController } from "@/hooks/useCursorController";
import { useAnimeScope } from "@/motion/animeScope";
import { useTextReveal } from "@/motion/textEffects";

export function meta() {
  return [{ title: "Descriptor specimen / Coffee Flavor Atlas" }];
}

export default function FlavorRoute() {
  const { slug } = useParams();
  const descriptor = descriptors.find((item) => item.slug === slug);
  const cursor = useCursorController();
  const { rootRef } = useAnimeScope<HTMLDivElement>();
  useTextReveal(rootRef);

  if (!descriptor) {
    throw new Response("Descriptor not found", { status: 404 });
  }

  const category = getCategory(categories, descriptor.categoryId);
  const related = getRelatedDescriptors(descriptor, descriptors, 4);
  const descriptorSources = sources.filter((source) =>
    descriptor.sourceIds.includes(source.id),
  );

  return (
    <div ref={rootRef} className="specimen-page light-field">
      <section
        className="specimen-layout editorial-grid"
        aria-label="Descriptor specimen"
      >
        <div className="specimen-figure">
          <SpecimenVisual descriptor={descriptor} />
        </div>
        <article className="specimen-data">
          <p className="meta-label">
            SPECIMEN / {descriptor.id} / {category.labels.en} /{" "}
            {statusLabels[descriptor.descriptorStatus].en}
          </p>
          <h1 className="specimen-name" data-text-reveal>
            {descriptor.labels.en}
            <span className="cjk">{descriptor.labels.zhHans}</span>
          </h1>
          <p className="body-copy">
            {descriptor.summary.en} / {descriptor.summary.zhHans}
          </p>
          <p className="method-warning">
            该画像描述典型关联和项目推断，不是化学指标，也不是具体咖啡的固定分数。
          </p>
          <div className="metadata-grid">
            <div>
              <span className="meta-label">Aliases</span>
              <p>
                {descriptor.aliases.en.join(", ")} /{" "}
                {descriptor.aliases.zhHans.join("、")}
              </p>
            </div>
            <div>
              <span className="meta-label">Modalities</span>
              <p>
                {descriptor.sensoryModalities
                  .map(
                    (modality) =>
                      `${modalityLabels[modality].en} / ${modalityLabels[modality].zhHans}`,
                  )
                  .join("; ")}
              </p>
            </div>
            <div>
              <span className="meta-label">Evidence</span>
              <p>
                {evidenceLabels[descriptor.evidenceStatus].en} /{" "}
                {confidenceLabels[descriptor.confidence].en} confidence
              </p>
            </div>
            <div>
              <span className="meta-label">Visual profile</span>
              <p>
                {descriptor.visualProfile.motif}; density{" "}
                {descriptor.visualProfile.density}; curvature{" "}
                {descriptor.visualProfile.curvature}
              </p>
            </div>
          </div>
          <section aria-label="Sensory range profile">
            <p className="meta-label">
              Sensory association profile / project-curated draft
            </p>
            {scoreDimensions.map((dimension) => (
              <RangeTrack
                key={dimension.id}
                label={`${dimension.shortLabel.zhHans} / ${dimension.shortLabel.en}`}
                score={descriptor.sensoryAssociation[dimension.id]}
              />
            ))}
          </section>
          {descriptor.editorialNote ? (
            <aside className="editorial-note">
              <p className="meta-label">Editorial note</p>
              <p>
                {descriptor.editorialNote.en} /{" "}
                {descriptor.editorialNote.zhHans}
              </p>
            </aside>
          ) : null}
          <section aria-label="Sources">
            <p className="meta-label">Sources / usage status</p>
            <ul className="plain-list">
              {descriptorSources.map((source) => (
                <li key={source.id}>
                  <span>{source.name}</span>
                  <span>
                    {source.reusePolicy} / {source.licenseStatus}
                  </span>
                </li>
              ))}
            </ul>
          </section>
          <nav className="related-list" aria-label="Related descriptors">
            {related.map((item) => (
              <Link
                key={item.slug}
                to={`/flavor/${item.slug}`}
                onPointerEnter={() =>
                  cursor.setCursor("open", item.labels.en.toUpperCase())
                }
                onPointerLeave={cursor.resetCursor}
              >
                {item.labels.zhHans} / {item.labels.en}
              </Link>
            ))}
          </nav>
          <div className="specimen-actions">
            <Link
              className="text-button"
              to={`/atlas?compare=${descriptor.slug}&view=index`}
              onPointerEnter={() => cursor.setCursor("compare", "COMPARE")}
              onPointerLeave={cursor.resetCursor}
            >
              Add to comparison / 加入比较
            </Link>
            <Link
              className="text-button"
              to="/atlas"
              onPointerEnter={() => cursor.setCursor("back", "ATLAS")}
              onPointerLeave={cursor.resetCursor}
            >
              Back to Atlas / 返回索引
            </Link>
          </div>
        </article>
      </section>
    </div>
  );
}
