#!/usr/bin/env node
/**
 * Fixed six questions vs the dynamic question bank on simulated cups — 500 in-source + 500 cross-source (owner, 2026-09-20).
 *
 * A simulated drinker "tastes" exactly what a real review record says — its 12-dimension vector and the flavor concepts
 * the reviewer mentioned — and answers both flows by the same rule: the option that fits what they taste, with the same
 * share of careless answers (NOISE). Each flow can only record what it asks about; that is the comparison.
 *
 * The dynamic bank's pruning tables are rebuilt WITHOUT the test records (build-dynamic-question-bank.py --holdout),
 * so the options a cup sees were not fitted to it. Matrix_K and the sixteen profiles use every record in both flows
 * alike, so they do not favour either.
 *
 * usage: NEIGHBOURS=<holdout neighbour index json> node scripts/simulate-question-flows.mjs <holdout dynamic build json> [out json]
 *        TEST_SET=<another test set json> for the cross-source set (SIMULATION_TEST_SET_COE.json)
 *        NEIGHBOURS is the index of db/scripts/build-neighbour-index.py built with the same --holdout sets (the
 *        committed index contains the test cups: a cup would find itself among its neighbours); NEIGHBOURS=none runs
 *        the dynamic flow without the neighbour fill (R3-D47), words by rotation alone, as before it was adopted
 *        PER_CUP=<json> also writes every cup's means, to compare two runs cup by cup
 *        PRIOR_SLOTS=none gives words only to dimensions the reader's answers weigh on (measured, not adopted)
 *
 * Experiments with heavier computation (see docs/product/QUESTION_FLOW_SIMULATION.md), off by default. They are kept as
 * the record of what was measured and rejected; run them with NEIGHBOURS=none, so that only the experiment fills words.
 * What was adopted (R3-D47) is the engine's own neighbour fill, which scores by the rate against the corpus, not by share:
 *   EXPERIMENT_DATA=<json from db/scripts/build-flow-experiment-data.py> FLAGS="learned" | "knn" | "knn-fill"
 *   learned   option weights learned from the corpus instead of the hand-set ones
 *   knn       the 60 nearest records to the target vector choose every candidate word
 *   knn-fill  … only in the dimensions where the reader gave no signal, ranked by the plain share among the neighbours
 *             (rejected: orange on 75% of enumerated cards)
 */
import { build } from "esbuild";
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = resolve(new URL("..", import.meta.url).pathname);
const PV = join(ROOT, "db/data/product-vector-v1");
const [holdoutPath, outPath] = process.argv.slice(2);
if (!holdoutPath)
  throw new Error("pass the hold-out dynamic build (see the header)");
const NOISE = 0.15;
const FLAGS = new Set((process.env.FLAGS ?? "").split(" ").filter(Boolean));
const X = process.env.EXPERIMENT_DATA
  ? JSON.parse(readFileSync(process.env.EXPERIMENT_DATA, "utf8"))
  : null;
if (FLAGS.size && !X) throw new Error("FLAGS need EXPERIMENT_DATA");
const SEEDS = [1, 2, 3];

// ── the engine, bundled against the hold-out bank
const bundleJson = JSON.parse(
  readFileSync(join(PV, "product-vector-v1.json"), "utf8"),
);
bundleJson.dynamic_bank = JSON.parse(readFileSync(holdoutPath, "utf8"));
// PRIOR_SLOTS=none: a word only for dimensions the reader's own answers weigh on (measured, not adopted: R3-D49)
if (process.env.PRIOR_SLOTS)
  bundleJson.question_flow.first_description.prior_slots =
    process.env.PRIOR_SLOTS;
if (FLAGS.has("learned"))
  for (const options of Object.values(bundleJson.dynamic_bank.options))
    for (const o of options)
      if (X.learned[o.id]) o.deltas = X.learned[o.id].deltas;
const dir = mkdtempSync(join(tmpdir(), "flow-sim-"));
writeFileSync(join(dir, "bundle.json"), JSON.stringify(bundleJson));
if (!process.env.NEIGHBOURS)
  throw new Error("pass NEIGHBOURS=<hold-out index> or NEIGHBOURS=none");
const neighbourIndex = JSON.parse(
  readFileSync(join(PV, "product-vector-v1-neighbours.json"), "utf8"),
);
writeFileSync(
  join(dir, "neighbours.json"),
  process.env.NEIGHBOURS === "none"
    ? JSON.stringify({
        ...neighbourIndex,
        records: 0,
        vectors: "",
        mentions: "",
      })
    : readFileSync(process.env.NEIGHBOURS, "utf8"),
);
await build({
  entryPoints: [
    join(ROOT, "packages/flavor-data/src/product-vector-v1/session.ts"),
  ],
  bundle: true,
  format: "esm",
  platform: "node",
  outfile: join(dir, "session.mjs"),
  logLevel: "error",
  plugins: [
    {
      name: "holdout",
      setup: (b) => {
        b.onResolve({ filter: /product-vector-v1\.json$/ }, () => ({
          path: join(dir, "bundle.json"),
        }));
        b.onResolve({ filter: /product-vector-v1-neighbours\.json$/ }, () => ({
          path: join(dir, "neighbours.json"),
        }));
      },
    },
  ],
});
const S = await import(pathToFileURL(join(dir, "session.mjs")).href);

// ── what the words and the options stand for in the corpus
const tsv = (file) => {
  const [head, ...rows] = readFileSync(join(PV, file), "utf8")
    .trim()
    .split("\n")
    .map((l) => l.split("\t"));
  return rows.map((r) =>
    Object.fromEntries(head.map((h, i) => [h, r[i] ?? ""])),
  );
};
const bank = tsv("DYNAMIC_QUESTION_BANK.tsv");
const optionConcepts = new Map(
  bank.map((r) => [r.option_id, r.concepts ? r.concepts.split("|") : []]),
);
const FAMILY = {
  acidity: {
    orange: ["orange"],
    lemon: ["lemon", "lime"],
    grapefruit: ["grapefruit", "pink_grapefruit"],
    bergamot: ["bergamot"],
  },
  fruity: {
    stone: ["peach", "cherry", "plum"],
    berry: [
      "blueberry",
      "strawberry",
      "raspberry",
      "blackberry",
      "blackcurrant",
      "pomegranate",
    ],
    grape_pome: ["grape", "apple", "pear"],
    tropical: ["mango", "pineapple", "banana", "coconut"],
    dried: ["raisin", "prune"],
  },
  nutty_chocolate: {
    nut: ["almond", "hazelnut", "peanut", "walnut"],
    chocolate: ["cocoa", "dark_chocolate"],
    baked: ["toast", "malt", "baked_bread", "cereal_grain"],
  },
  sweetness: {
    honey: ["honey"],
    caramel: ["caramel", "brown_sugar"],
    dark_sugar: ["molasses"],
    vanilla: ["vanilla"],
    sugar: ["sweet"],
  },
  herbal_green: {
    tea: ["black_tea", "green_tea"],
    herb: ["mint", "lemongrass", "eucalyptus", "fresh_grass"],
  },
  woody_earthy: {
    wood: ["cedar", "woody"],
    earth: ["earthy", "mushroom", "leather"],
    tobacco: ["tobacco", "smoky", "ash"],
  },
};
const FLORAL = ["jasmine", "rose", "orange_blossom", "chamomile"];
const tags = tsv("CONCEPT_FLAVOR_TAGS.tsv").filter(
  (r) => r.kind === "dimension",
);
const wordInfo = new Map();
for (const r of tags) {
  const d = r.key.slice(4);
  const words = r.tags_zh_cn.split("|");
  const fams = (r.tag_families || "").split("|");
  words.forEach((w, i) =>
    wordInfo.set(w, {
      dimension: d,
      family: d === "floral" ? FLORAL : (FAMILY[d]?.[fams[i]] ?? null),
    }),
  );
}
for (const r of bank)
  if (r.kind === "second" && r.role === "word" && r.concepts)
    wordInfo.get(r.label_zh_cn).exact = r.concepts;

// ── the simulated drinker
const D = bundleJson.dimensions;
const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const norm = (a) => Math.sqrt(dot(a, a));
const cos = (a, b) =>
  norm(a) && norm(b) ? dot(a, b) / (norm(a) * norm(b)) : 0;
const rng = (seed) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const w = (cup, d) => cup.vector[D.indexOf(d)];
const vecOf = (spec) => D.map((d) => spec[d] ?? 0);
const mq = bundleJson.matrix_q;
const slotQ = Object.fromEntries(
  bundleJson.question_flow.slots.map((s) => [s.slot, s.question]),
);
const dynOptions = new Map(
  Object.values(bundleJson.dynamic_bank.options)
    .flat()
    .map((o) => [o.id, o]),
);

function bodyChoice(cup, shown, table) {
  // thin → heavy by the body weight; "drying" when the record says so
  if (
    cup.concepts.some((c) => c === "astringent" || c === "drying") &&
    table.dry &&
    shown.includes(table.dry)
  )
    return table.dry;
  const level =
    w(cup, "body") < 0.2
      ? 0
      : w(cup, "body") < 0.45
        ? 1
        : w(cup, "body") < 0.7
          ? 2
          : 3;
  const order = table.scale.filter((id) => shown.includes(id));
  return order[
    Math.min(order.length - 1, Math.round((level / 3) * (order.length - 1)))
  ];
}
function fixedAnswer(cup, slot, shown) {
  const opts = mq[slotQ[slot]];
  if (slot === "Q0" && w(cup, "acidity") < 0.2) return "C";
  if (slot === "Q3")
    return bodyChoice(cup, shown, { scale: ["A", "B", "C"], dry: "D" });
  if (slot === "Q4")
    return w(cup, "bitter_roasted") < 0.1
      ? "B"
      : w(cup, "bitter_roasted") < 0.35
        ? "A"
        : "C";
  const scored = shown
    .filter((o) => Object.keys(opts[o] ?? {}).length)
    .map((o) => ({
      o,
      fit: cos(vecOf(opts[o]), cup.vector),
      pull: dot(vecOf(opts[o]), cup.vector) / norm(vecOf(opts[o])),
    }))
    .sort((a, b) => b.fit - a.fit);
  const empty = shown.find((o) => !Object.keys(opts[o] ?? {}).length);
  return !scored.length || (empty && scored[0].pull < 0.15)
    ? (empty ?? scored[0].o)
    : scored[0].o;
}
function dynamicAnswer(cup, key, shown, unanswered) {
  const mentions = (id) =>
    optionConcepts.get(id)?.filter((c) => cup.concepts.includes(c)).length ?? 0;
  const fifth = shown.find((id) => dynOptions.get(id)?.role === "fifth");
  if (key.startsWith("S:"))
    return shown.find((id) => mentions(id) > 0) ?? unanswered ?? shown[0];
  if (key === "Q3")
    return (
      bodyChoice(cup, shown, {
        scale: ["D6", "D1", "D2", "D3", "D4"],
        dry: "D5",
      }) ?? fifth
    );
  // a scale shows four of its five levels (by roast): the drinker takes the level they mean, or the nearest one shown
  const nearestShown = (id) => {
    if (shown.includes(id)) return id;
    const rank = (x) => x.charCodeAt(x.length - 1);
    return [...shown]
      .filter((x) => x.slice(0, 2) === id.slice(0, 2))
      .sort(
        (x, y) => Math.abs(rank(x) - rank(id)) - Math.abs(rank(y) - rank(id)),
      )[0];
  };
  if (key === "Q4") {
    const b = w(cup, "bitter_roasted");
    return nearestShown(
      b < 0.1
        ? "E3a"
        : b < 0.25
          ? "E3b"
          : b < 0.45
            ? "E3c"
            : b < 0.7
              ? "E3d"
              : "E3e",
    );
  }
  if (key === "E1")
    return cup.aroma_level === "high"
      ? "E1b"
      : cup.aroma_level === "low"
        ? "E1c"
        : (unanswered ?? shown[0]);
  if (key === "E2")
    return cup.aftertaste_level === "high"
      ? "E2c"
      : cup.aftertaste_level === "mid"
        ? "E2b"
        : cup.aftertaste_level === "low"
          ? "E2a"
          : (unanswered ?? shown[0]);
  const data = shown.filter((id) => id !== fifth);
  const lead = { Q0: "acidity", Q2: "sweetness" }[key];
  if (lead && w(cup, lead) < (key === "Q0" ? 0.2 : 0.15))
    return fifth ?? data[0];
  // The same rule as in the fixed flow — what DOMINATES the cup, by the fit of the option's weights to the cup's vector —
  // among the options the drinker can truthfully choose: a family the record mentions, or an option that names no family
  // ("still mostly fruit", "clean sweetness"). A juror list of twelve descriptors mentions a flower in passing; that
  // does not make flowers the cup's main aroma. Mentions break ties between families of the same dimensions.
  const truthful = data.filter(
    (id) => mentions(id) > 0 || !(optionConcepts.get(id) ?? []).length,
  );
  const scored = truthful
    .map((id) => {
      const v = vecOf(dynOptions.get(id).deltas);
      return {
        id,
        fit: cos(v, cup.vector) + 0.05 * Math.min(mentions(id), 3),
        pull: dot(v, cup.vector) / (norm(v) || 1),
      };
    })
    .sort((a, b) => b.fit - a.fit);
  return scored.length && scored[0].pull >= 0.15
    ? scored[0].id
    : (fifth ?? scored[0]?.id ?? data[0] ?? shown[0]);
}

// ── experiment: the nearest records to the target vector choose the words (all of them, or only where the reader gave no signal)
const LIB = (X?.records ?? []).map((r) => ({
  v: r.v,
  n: Math.sqrt(r.v.reduce((a, x) => a + x * x, 0)) || 1,
  c: new Set(r.c),
}));
const CONCEPT_AT = new Map((X?.concepts ?? []).map((c, i) => [c, i]));
const WORDS_BY_DIM = new Map();
for (const [text, info] of wordInfo)
  WORDS_BY_DIM.set(info.dimension, [
    ...(WORDS_BY_DIM.get(info.dimension) ?? []),
    text,
  ]);
const FOCUS_DIM = new Map(
  bank
    .filter((r) => r.focus && !r.focus.endsWith(":*"))
    .map((r) => [r.option_id, r.focus.split(":")[0]]),
);
const knnStats = { ms: 0, runs: 0, slots: 0, chosen: 0 };
function nearestRecordWords(s) {
  const t0 = performance.now();
  const target = s.result.vTarget;
  const tn = norm(target) || 1;
  const near = LIB.map((r) => ({ r, sim: dot(r.v, target) / (r.n * tn) }))
    .sort((a, b) => b.sim - a.sim)
    .slice(0, 60);
  const total = near.reduce((a, x) => a + x.sim ** 4, 0) || 1;
  const p = (concept) => {
    const i = CONCEPT_AT.get(concept);
    return i === undefined
      ? 0
      : near.reduce((a, x) => a + (x.r.c.has(i) ? x.sim ** 4 : 0), 0) / total;
  };
  const score = (text) => {
    const info = wordInfo.get(text);
    if (info.exact) return p(info.exact);
    return info.family
      ? (0.3 * info.family.reduce((a, c) => a + p(c), 0)) / info.family.length
      : 0.01;
  };
  const signalled = new Set(
    Object.values(s.answers)
      .map((id) => FOCUS_DIM.get(id))
      .filter(Boolean),
  );
  const lead = new Set(
    Object.values(s.answers)
      .filter((id) => id.includes(":") && !id.endsWith("-"))
      .map((id) => id.split(":")[1]),
  );
  const slots = new Map();
  for (const x of s.description.all)
    slots.set(x.dimension, (slots.get(x.dimension) ?? 0) + 1);
  const chosen = new Map();
  for (const [dimension, k] of slots) {
    knnStats.slots += 1;
    const own = s.description.all.filter((x) => x.dimension === dimension);
    if (FLAGS.has("knn-fill") && signalled.has(dimension)) {
      chosen.set(
        dimension,
        own.map((x) => x.text),
      );
      continue;
    }
    knnStats.chosen += 1;
    const out = own.filter((x) => lead.has(x.text)).map((x) => x.text);
    const ranked = (WORDS_BY_DIM.get(dimension) ?? [])
      .filter((t) => !out.includes(t))
      .sort((a, b) => score(b) - score(a));
    const used = new Set(
      out.map((t) => (wordInfo.get(t).family ?? [t]).join()),
    );
    for (const pass of [0, 1])
      for (const t of ranked) {
        if (out.length >= k) break;
        const family = (wordInfo.get(t).family ?? [t]).join();
        if (out.includes(t) || (pass === 0 && used.has(family))) continue;
        out.push(t);
        used.add(family);
      }
    chosen.set(dimension, out);
  }
  const all = s.description.all.map((x) => ({
    text: chosen.get(x.dimension).shift() ?? x.text,
    dimension: x.dimension,
  }));
  knnStats.ms += performance.now() - t0;
  knnStats.runs += 1;
  return {
    ...s,
    description: {
      ...s.description,
      all,
      main: all.slice(0, 3),
      secondary: all.slice(3),
    },
  };
}

function run(cup, mode, seed) {
  const random = rng(seed * 100003 + cup.index);
  let s = S.createSession(cup.context, "zh-CN", [], 0, mode);
  let asked = 0;
  for (let guard = 0; s.stage === "questions" && guard < 10; guard += 1) {
    const step = S.nextStep(s);
    if (step.kind !== "ask") break;
    const shown = step.card.options.map((o) => o.option);
    const considered =
      mode === "dynamic"
        ? dynamicAnswer(
            cup,
            step.card.slot,
            shown,
            step.card.unanswered?.option,
          )
        : fixedAnswer(cup, step.card.slot, shown);
    const careless = random() < NOISE; // the same share of careless answers in both flows
    s = S.answer(
      s,
      step.card.slot,
      careless ? shown[Math.floor(random() * shown.length)] : considered,
    );
    asked += 1;
  }
  s = S.firstDescription(s);
  if ((FLAGS.has("knn") || FLAGS.has("knn-fill")) && mode === "dynamic")
    s = nearestRecordWords(s);
  const candidates = s.description.all;
  const tasted = (word) => {
    const info = wordInfo.get(word.text);
    return info?.family
      ? info.family.some((c) => cup.concepts.includes(c))
      : null;
  };
  const exact = (word) => {
    const info = wordInfo.get(word.text);
    return info?.exact ? cup.concepts.includes(info.exact) : null;
  };
  // the drinker keeps the words they can taste first, then fills up in the order offered
  const picks = [
    ...candidates.filter((x) => tasted(x)),
    ...candidates.filter((x) => !tasted(x)),
  ].slice(0, 5);
  s = S.submitPicks(s, picks);
  if (s.stage === "q6") {
    // The confirmation step shows WORDS ("jasmine", "cinnamon") and the card now carries the very word ticked, so the
    // drinker ticks like everywhere else: words they taste first, by the weight of their dimension in the cup; when
    // none of the words is tasted, the strongest dimension on offer.
    const byWeight = [...s.q6.options].sort(
      (a, b) => w(cup, b.dimension) - w(cup, a.dimension),
    );
    const ticks = byWeight.filter((o) => tasted(o) === true);
    const want = (ticks.length ? ticks : byWeight.slice(0, 1))
      .slice(0, 2)
      .map((o) => o.dimension);
    s = S.answerQ6(s, want);
  }
  const rate = (words, f) => {
    const v = words.map(f).filter((x) => x !== null);
    return v.length ? v.filter(Boolean).length / v.length : null;
  };
  const finalWords = s.card.picked.map((text) => ({ text }));
  const truthProfile = [...bundleJson.profiles].sort(
    (a, b) => cos(b.centroid, cup.vector) - cos(a.centroid, cup.vector),
  )[0].profile_id;
  const expressible = Object.values(FAMILY)
    .flatMap((f) => Object.values(f))
    .concat([FLORAL])
    .filter((cs) => cs.some((c) => cup.concepts.includes(c)));
  const covered = (words) =>
    expressible.length
      ? expressible.filter((cs) =>
          words.some(
            (x) =>
              wordInfo.get(x.text)?.family === cs ||
              (wordInfo.get(x.text)?.family ?? []).join() === cs.join(),
          ),
        ).length / expressible.length
      : null;
  return {
    asked,
    cosUser: cos(s.result.vUser, cup.vector),
    cosTarget: cos(s.result.vTarget, cup.vector),
    top1: s.result.profiles[0]?.profile.profile_id === truthProfile ? 1 : 0,
    top3: s.result.profiles
      .slice(0, 3)
      .some((p) => p.profile.profile_id === truthProfile)
      ? 1
      : 0,
    candFamily: rate(candidates, tasted),
    candExact: rate(candidates, exact),
    cardFamily: rate(finalWords, tasted),
    cardExact: rate(finalWords, exact),
    recallCand: covered(candidates),
    recallCard: covered(finalWords),
    q6: s.q6 ? 1 : 0,
  };
}

const cups = JSON.parse(
  readFileSync(
    process.env.TEST_SET ?? join(PV, "SIMULATION_TEST_SET.json"),
    "utf8",
  ),
).records.map((r, index) => ({ ...r, index }));
const METRICS = [
  "asked",
  "cosUser",
  "cosTarget",
  "top1",
  "top3",
  "candFamily",
  "candExact",
  "cardFamily",
  "cardExact",
  "recallCand",
  "recallCard",
  "q6",
];
const results = { fixed: [], dynamic: [] };
for (const cup of cups)
  for (const mode of ["fixed", "dynamic"]) {
    const runs = SEEDS.map((seed) => run(cup, mode, seed));
    results[mode].push(
      Object.fromEntries(
        METRICS.map((m) => {
          const v = runs.map((r) => r[m]).filter((x) => x !== null);
          return [m, v.length ? v.reduce((a, b) => a + b, 0) / v.length : null];
        }),
      ),
    );
  }
const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
const summary = {};
for (const m of METRICS) {
  const pairs = cups
    .map((_, i) => [results.fixed[i][m], results.dynamic[i][m]])
    .filter(([a, b]) => a !== null && b !== null);
  const diffs = pairs.map(([a, b]) => b - a);
  // paired bootstrap, 2,000 resamples, for the mean difference
  const random = rng(7);
  const boots = Array.from({ length: 2000 }, () =>
    mean(
      Array.from(
        { length: diffs.length },
        () => diffs[Math.floor(random() * diffs.length)],
      ),
    ),
  ).sort((a, b) => a - b);
  summary[m] = {
    n: pairs.length,
    fixed: mean(pairs.map((p) => p[0])),
    dynamic: mean(pairs.map((p) => p[1])),
    difference: mean(diffs),
    ci95: [boots[50], boots[1949]],
    dynamicBetter: diffs.filter((d) => d > 1e-9).length,
    fixedBetter: diffs.filter((d) => d < -1e-9).length,
  };
}
if (knnStats.runs)
  console.log(
    `nearest-record word choice: ${(knnStats.ms / knnStats.runs).toFixed(1)} ms per cup on this machine over ${LIB.length} records; it chose ${knnStats.chosen} of ${knnStats.slots} dimension slots`,
  );
const out = {
  cups: cups.length,
  seeds: SEEDS,
  noise: NOISE,
  holdout: true,
  summary,
};
if (outPath) writeFileSync(outPath, JSON.stringify(out, null, 1) + "\n");
// the per-cup means of both flows, for a paired comparison between two runs (with and without the neighbour fill)
if (process.env.PER_CUP)
  writeFileSync(process.env.PER_CUP, JSON.stringify(results) + "\n");
const pct = (x) => (x * 100).toFixed(1) + "%";
console.log(
  `cups ${cups.length} × seeds ${SEEDS.length}, careless answers ${pct(NOISE)}, dynamic bank built without the test cups`,
);
for (const [m, r] of Object.entries(summary)) {
  const f =
    m === "asked"
      ? (x) => x.toFixed(2)
      : m.startsWith("cos")
        ? (x) => x.toFixed(3)
        : pct;
  console.log(
    `${m.padEnd(11)} n=${String(r.n).padStart(3)}  fixed ${f(r.fixed).padStart(7)}  dynamic ${f(r.dynamic).padStart(7)}  diff ${(r.difference >= 0 ? "+" : "") + f(r.difference)}  95% CI [${f(r.ci95[0])}, ${f(r.ci95[1])}]  better: dynamic ${r.dynamicBetter} · fixed ${r.fixedBetter}`,
  );
}
