import { Link } from "react-router";
import {
  categories,
  descriptors,
  getCategory,
  scoreDimensions,
  sortByCategoryThenName,
} from "flavor-data";
import { DescriptorField } from "@/components/DescriptorField";
import { SensoryMap } from "@/components/SensoryMap";
import { useCursorController } from "@/hooks/useCursorController";
import { useAnimeScope } from "@/motion/animeScope";
import { useScrollScene } from "@/motion/scrollObservers";
import { useTextReveal } from "@/motion/textEffects";

export function meta() {
  return [
    { title: "Coffee Flavor Atlas / 咖啡风味图谱" },
    {
      name: "description",
      content:
        "An experimental descriptor field for bilingual coffee flavor language and project-curated sensory association profiles.",
    },
  ];
}

export default function HomeRoute() {
  const cursor = useCursorController();
  const { rootRef } = useAnimeScope<HTMLDivElement>();
  useScrollScene(rootRef);
  useTextReveal(rootRef);
  const sortedDescriptors = sortByCategoryThenName(descriptors, categories);

  return (
    <div ref={rootRef} className="page dark-field home-publication">
      <section
        className="field-scene editorial-grid"
        aria-label="Interactive descriptor field"
      >
        <DescriptorField
          descriptors={sortedDescriptors}
          categories={categories}
          cursor={cursor}
        />
        <div className="field-scene__title" data-reveal>
          <p className="meta-label">FIELD 00 / v0.2 / 24 pilot descriptors</p>
          <h1 className="display-title" data-text-reveal>
            Atlas
            <span className="cjk">咖啡风味图谱</span>
          </h1>
        </div>
        <aside className="field-scene__side" data-reveal>
          <p className="meta-label">INDEX NOTE</p>
          <p>
            A bilingual sensory specimen index. Scores are project-curated draft
            association profiles, not chemical measurements or fixed cupping
            results.
          </p>
          <Link
            className="text-button"
            to="/atlas"
            onPointerEnter={() => cursor.setCursor("open", "ATLAS")}
            onPointerLeave={cursor.resetCursor}
          >
            Enter Atlas / 进入索引
          </Link>
        </aside>
      </section>

      <section className="scroll-strip" data-scroll-scene>
        <div className="scroll-strip__index">01 / CATEGORY RELATIONS</div>
        <div className="scroll-strip__main" data-reveal>
          <h2 className="strip-title">
            category is a reading path, not a flavor wheel
          </h2>
          <nav className="category-network" aria-label="Category navigation">
            {categories.map((category, index) => (
              <Link
                key={category.id}
                to={`/atlas?category=${category.id}&view=field`}
                onPointerEnter={() =>
                  cursor.setCursor("category", category.labels.en)
                }
                onPointerLeave={cursor.resetCursor}
              >
                <span className="meta-label">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <strong>{category.labels.en}</strong>
                <span>{category.labels.zhHans}</span>
              </Link>
            ))}
          </nav>
        </div>
        <aside className="scroll-strip__side" data-reveal>
          <p>
            Category boundaries stay provisional. The pilot uses morphology,
            position and metadata before saturated color, so the field can
            remain legible in black and white.
          </p>
        </aside>
      </section>

      <section className="scroll-strip" data-scroll-scene>
        <div className="scroll-strip__index">02 / ASSOCIATION</div>
        <div className="scroll-strip__main" data-reveal>
          <h2 className="strip-title">six dimensions, always as range</h2>
          <div className="dimension-ledger">
            {scoreDimensions.map((dimension, index) => (
              <div key={dimension.id}>
                <span className="meta-label">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <strong>{dimension.labels.en}</strong>
                <span>{dimension.labels.zhHans}</span>
              </div>
            ))}
          </div>
        </div>
        <aside className="scroll-strip__side" data-reveal>
          <p>
            Sour, sweet and bitter are shown as sensory association profiles.
            They describe editorial inference and typical relation, not
            objective certainty.
          </p>
        </aside>
      </section>

      <section className="scroll-strip scroll-strip--map" data-scroll-scene>
        <div className="scroll-strip__index">03 / FIELD MAP</div>
        <div
          className="scroll-strip__main scroll-strip__main--wide"
          data-reveal
        >
          <SensoryMap
            descriptors={descriptors}
            categories={categories}
            cursor={cursor}
          />
        </div>
      </section>

      <section className="scroll-strip" data-scroll-scene>
        <div className="scroll-strip__index">04 / APPENDIX</div>
        <div className="scroll-strip__main" data-reveal>
          <h2 className="strip-title">method before authority</h2>
          <p className="body-copy">
            The Atlas keeps source registry, evidence status, confidence and
            copyright boundaries visible. It does not copy complete reference
            lexicons or claim scientific finality for prototype values.
          </p>
          <Link
            className="text-button"
            to="/methodology"
            onPointerEnter={() => cursor.setCursor("source", "METHOD")}
            onPointerLeave={cursor.resetCursor}
          >
            Methodology appendix / 方法附录
          </Link>
        </div>
        <aside className="scroll-strip__side" data-reveal>
          <p className="meta-label">RELATED NODE</p>
          <p>
            Boundary examples:{" "}
            {descriptors
              .filter(
                (descriptor) => descriptor.descriptorStatus !== "canonical",
              )
              .slice(0, 4)
              .map(
                (descriptor) =>
                  `${descriptor.labels.en} / ${descriptor.labels.zhHans}`,
              )
              .join("; ")}
            .
          </p>
        </aside>
      </section>
    </div>
  );
}
