import {
  categories,
  descriptors,
  evidenceLabels,
  scoreDimensions,
  sources,
  validateAtlasData,
} from "flavor-data";
import { descriptorAssets } from "@/assets/descriptor-assets";
import { SpecimenVisual } from "@/components/SpecimenVisual";
import { useAnimeScope } from "@/motion/animeScope";
import { useScrollScene } from "@/motion/scrollObservers";

export function meta() {
  return [
    { title: "Methodology Appendix / Coffee Flavor Atlas" },
    {
      name: "description",
      content:
        "Data model, uncertainty, source policy and asset spike notes for Coffee Flavor Atlas.",
    },
  ];
}

const validation = validateAtlasData({ categories, sources, descriptors });

export default function MethodologyRoute() {
  const { rootRef } = useAnimeScope<HTMLDivElement>();
  useScrollScene(rootRef);

  return (
    <div ref={rootRef} className="method-page light-field">
      <section
        className="method-opening editorial-grid"
        aria-label="Method index"
      >
        <nav className="method-index" aria-label="Method sections">
          {[
            ["01", "data model"],
            ["02", "range profile"],
            ["03", "evidence"],
            ["04", "translation"],
            ["05", "source policy"],
            ["06", "asset spike"],
          ].map(([number, label]) => (
            <a href={`#method-${number}`} key={number}>
              <span className="meta-label">{number}</span>
              <strong>{label}</strong>
            </a>
          ))}
        </nav>
        <div className="method-status">
          <div>
            <span className="meta-label">VERSION</span>
            <strong>v0.2</strong>
            <span>React field migration</span>
          </div>
          <div>
            <span className="meta-label">DATA STATUS</span>
            <strong>{validation.descriptors.length}/24</strong>
            <span>schema-valid descriptors</span>
          </div>
          <div>
            <span className="meta-label">SOURCE LEVELS</span>
            <strong>{sources.length}</strong>
            <span>reference, open data, project-created</span>
          </div>
          {scoreDimensions.map((dimension) => (
            <div key={dimension.id}>
              <span className="meta-label">{dimension.shortLabel.en}</span>
              <strong>{dimension.shortLabel.zhHans}</strong>
              <span>RangeScore 0-5</span>
            </div>
          ))}
        </div>
      </section>

      <section className="scroll-strip" id="method-01" data-scroll-scene>
        <div className="scroll-strip__index">01 / DATA MODEL</div>
        <div className="scroll-strip__main" data-reveal>
          <h1 className="strip-title">descriptor is not observation</h1>
          <p className="body-copy">
            A descriptor is a bilingual vocabulary node. It can be canonical,
            boundary, compound or unresolved. It is not a specific coffee
            sample, not a chemical reading and not a final cup score. The
            current version keeps exactly 24 pilot descriptors to test structure
            before expansion.
          </p>
          <pre
            className="schema-diagram"
            aria-label="Descriptor schema diagram"
          >{`Descriptor
  labels: en / zhHans
  aliases: en[] / zhHans[]
  categoryId -> Category
  sensoryAssociation -> six RangeScore values
  confidence + evidenceStatus
  sourceIds -> Source registry
  editorialNote?`}</pre>
        </div>
      </section>

      <section className="scroll-strip" id="method-02" data-scroll-scene>
        <div className="scroll-strip__index">02 / RANGE PROFILE</div>
        <div className="scroll-strip__main" data-reveal>
          <h2 className="strip-title">range over single value</h2>
          <p className="body-copy">
            Each RangeScore stores min, typical and max from 0-5. The typical
            value is used for map position, while the range keeps uncertainty
            visible. All prototype sensoryAssociation values remain
            project-curated draft.
          </p>
        </div>
        <aside className="scroll-strip__side" data-reveal>
          <p className="meta-label">UNCERTAINTY EXAMPLE</p>
          <p>
            Red berries is retained as a pilot canonical node, but its
            generalized nature is documented instead of being presented as a
            narrow chemical category.
          </p>
        </aside>
      </section>

      <section className="scroll-strip" id="method-03" data-scroll-scene>
        <div className="scroll-strip__index">03 / EVIDENCE</div>
        <div className="scroll-strip__main" data-reveal>
          <h2 className="strip-title">evidence is a usage label</h2>
          <div className="dimension-ledger">
            {Object.entries(evidenceLabels).map(([key, label]) => (
              <div key={key}>
                <span className="meta-label">{key}</span>
                <strong>{label.en}</strong>
                <span>{label.zhHans}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="scroll-strip" id="method-04" data-scroll-scene>
        <div className="scroll-strip__index">04 / SOURCE MATRIX</div>
        <div
          className="scroll-strip__main scroll-strip__main--wide"
          data-reveal
        >
          <table className="source-matrix">
            <caption className="sr-only">
              Source registry and reuse policy
            </caption>
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">Type</th>
                <th scope="col">Reuse</th>
                <th scope="col">License status</th>
                <th scope="col">Notes</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.id}>
                  <td>{source.name}</td>
                  <td>{source.sourceType}</td>
                  <td>{source.reusePolicy}</td>
                  <td>{source.licenseStatus}</td>
                  <td>{source.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="scroll-strip" id="method-05" data-scroll-scene>
        <div className="scroll-strip__index">05 / TRANSLATION + RIGHTS</div>
        <div className="scroll-strip__main" data-reveal>
          <h2 className="strip-title">translation is editorial</h2>
          <p className="body-copy">
            Chinese labels, category boundaries and prototype scores can include
            project editorial judgment. Reference frameworks are used for
            orientation only. The Atlas does not copy full protected word lists,
            definitions, diagrams or commercial descriptions.
          </p>
        </div>
      </section>

      <section className="scroll-strip" id="method-06" data-scroll-scene>
        <div className="scroll-strip__index">06 / ASSET SPIKE</div>
        <div
          className="scroll-strip__main scroll-strip__main--wide"
          data-reveal
        >
          <h2 className="strip-title">
            six candidate marks before twenty-four
          </h2>
          <div className="asset-grid">
            {descriptorAssets.map((asset) => {
              const descriptor = descriptors.find(
                (item) => item.slug === asset.slug,
              )!;
              return (
                <article key={asset.slug}>
                  <SpecimenVisual descriptor={descriptor} variant="mini" />
                  <h3>
                    {descriptor.labels.zhHans} / {descriptor.labels.en}
                  </h3>
                  <p className="meta-label">
                    {asset.library}; {asset.originalIconName}; {asset.author};{" "}
                    {asset.license}
                  </p>
                  <p>
                    Recognizability {asset.evaluation.recognizability}; style{" "}
                    {asset.evaluation.styleFit}; animation{" "}
                    {asset.evaluation.animationFit}; monochrome{" "}
                    {asset.evaluation.monochromeFit}.
                  </p>
                </article>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
