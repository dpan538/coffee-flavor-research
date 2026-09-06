"""R6 examples: mapping guards, observable-only I2, and a fixed evaluation surface.

Run: python r6_mapping_i2_helpers.py --self-test
Python 3.10+; standard library only. No source data, weights, or network access.

These are proposed integration helpers, NOT replacements for the repository's
sensory metrics or training pipeline. Unit-test fixtures are synthetic and do
not validate any coffee relation or product effect. Convert repository objects
at a thin boundary; keep targets and unrevealed reports out of the selector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import unicodedata
import unittest
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


def normalize_span(text: str) -> str:
    """No stemming, substring extraction, or automatic compound splitting."""
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


@dataclass(frozen=True)
class Span:
    text: str
    polarity: str  # 'positive', 'negative', or 'unknown', supplied by the parser


@dataclass(frozen=True)
class PatchRule:
    source_span: str
    concept_id: str
    evidence_ref: str
    decision: str  # SOURCE_CHECKED or HUMAN_APPROVED; never inferred confidence


def compile_patch(
    rules: Sequence[PatchRule], allowed_concepts: frozenset[str]
) -> dict[str, PatchRule]:
    result: dict[str, PatchRule] = {}
    for rule in rules:
        key = normalize_span(rule.source_span)
        if not key or not rule.evidence_ref.strip():
            raise ValueError("A patch requires a full span and source evidence")
        if rule.decision not in {"SOURCE_CHECKED", "HUMAN_APPROVED"}:
            raise ValueError("Unresolved mapping is not an executable patch")
        if rule.concept_id not in allowed_concepts:
            raise ValueError("Patch must not expand the frozen concept vocabulary")
        if key in result:
            raise ValueError("Duplicate/conflicting normalized patch span")
        result[key] = rule
    return result


def map_positive_span(
    span: Span,
    base_concepts: Sequence[str],
    patch: Mapping[str, PatchRule],
) -> tuple[tuple[str, ...], str | None]:
    """Add only a source-checked, whole-span mapping; return its evidence ref.

    The upstream parser MUST preserve polarity. This function cannot discover
    a negation that the parser has incorrectly removed. Already mapped spans
    are unchanged; this sprint does not silently rewrite old decisions.
    """
    if span.polarity not in {"positive", "negative", "unknown"}:
        raise ValueError("Invalid polarity")
    base = tuple(sorted(set(base_concepts)))
    rule = patch.get(normalize_span(span.text))
    if base or span.polarity != "positive" or rule is None:
        return base, None
    return (rule.concept_id,), rule.evidence_ref


@dataclass(frozen=True)
class TrainingB:
    observation_id: str
    group_id: str
    sample_id: str
    concepts: frozenset[str]


def fit_grouped_coverage(
    rows: Sequence[TrainingB],
    *,
    evaluation_groups: frozenset[str],
) -> dict[str, float]:
    """Equal coffee group, sample within group, observation within sample.

    Caller supplies TRAINING B only. No target T, evaluation B, or identities
    may be used as predictive features. Empty mapped observations stay in the
    denominator. A single observation mentioning a concept twice counts once.
    """
    if not rows:
        raise ValueError("No training observations")
    groups: dict[str, dict[str, list[frozenset[str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    seen: set[str] = set()
    sample_group: dict[str, str] = {}
    for row in rows:
        if not row.observation_id or not row.group_id or not row.sample_id:
            raise ValueError("Missing source identity")
        if row.observation_id in seen:
            raise ValueError("Duplicate observation ID")
        if row.group_id in evaluation_groups:
            raise ValueError("Evaluation coffee entered coverage fitting")
        if sample_group.setdefault(row.sample_id, row.group_id) != row.group_id:
            raise ValueError("A sample was assigned to different coffee groups")
        seen.add(row.observation_id)
        groups[row.group_id][row.sample_id].append(row.concepts)

    counts: dict[str, float] = defaultdict(float)
    for samples in groups.values():
        for observations in samples.values():
            weight = 1.0 / (len(groups) * len(samples) * len(observations))
            for concepts in observations:
                for concept in sorted(concepts):
                    counts[concept] += weight
    return dict(sorted(counts.items()))


@dataclass(frozen=True)
class Option:
    option_id: str
    concept_id: str
    attributes: frozenset[str]


@dataclass(frozen=True)
class Question:
    axis: str
    options: tuple[Option, ...]


def choose_i2_live(
    questions: Sequence[Question],
    *,
    initial_observed_concepts: frozenset[str],
    used_axes: frozenset[str],
    train_coverage: Mapping[str, float],
    fixed_parents: Mapping[str, frozenset[str]],
    option_budget: int = 4,
    related_multiplier: float = 2.0,
) -> Question:
    """Proposed I2_LIVE: initial support comes ONLY from exposed Q0/Q1 answers.

    Deliberately accepts no source record, raw A/B, target T, or future trace.
    This is a heuristic, not a calibrated probability or learned utility.
    The answer provider is a separate component, invoked AFTER selection.
    """
    if not 1 <= option_budget <= 4:
        raise ValueError("Ordinary question option budget must be in [1, 4]")
    if not math.isfinite(related_multiplier) or related_multiplier < 1.0:
        raise ValueError("Invalid related-direction multiplier")
    if any(not math.isfinite(v) or not 0.0 <= v <= 1.0
           for v in train_coverage.values()):
        raise ValueError("Coverage must be a finite training-side rate")

    initial_attributes: set[str] = set()
    for concept in initial_observed_concepts:
        initial_attributes.update(fixed_parents.get(concept, frozenset()))
        if concept.startswith("attribute."):
            initial_attributes.add(concept)

    choices: list[tuple[float, str, Question]] = []
    seen_axes: set[str] = set()
    for question in questions:
        if not question.axis or question.axis in seen_axes:
            raise ValueError("Question axis IDs must be unique and nonempty")
        seen_axes.add(question.axis)
        ids = [o.option_id for o in question.options]
        concepts = [o.concept_id for o in question.options]
        if len(ids) != len(set(ids)) or len(concepts) != len(set(concepts)):
            raise ValueError("Duplicate options/canonical concepts within an axis")
        if question.axis in used_axes or len(ids) < option_budget:
            continue
        # Retain the R5 principle: shortlist by TRAIN B coverage, then score
        # the axis using support actually observed during Q0/Q1.
        ordered = tuple(sorted(
            question.options,
            key=lambda o: (-train_coverage.get(o.concept_id, 0.0), o.option_id),
        )[:option_budget])
        value = sum(
            train_coverage.get(o.concept_id, 0.0)
            * (related_multiplier if o.attributes & initial_attributes else 1.0)
            for o in ordered
        )
        choices.append((-value, question.axis, Question(question.axis, ordered)))
    if not choices:
        raise ValueError("NO_LEGAL_AXIS_AT_FROZEN_BUDGET")
    # A deterministic tie-break is not evidence that the tied axis is better.
    return min(choices, key=lambda item: (item[0], item[1]))[2]


def evaluation_fingerprint(
    targets: Mapping[str, Mapping[str, float]],
    candidate_ids: Sequence[str],
    option_budgets: Mapping[str, int],
    metric_spec: Mapping[str, object],
) -> str:
    """Targets are preserved, including OOV targets and empty references.

    Run once before inputs are patched, then verify after every matrix cell.
    This guard detects mutation; it cannot prove semantic correctness or that
    an inference callback did not access targets elsewhere.
    """
    if len(candidate_ids) != len(set(candidate_ids)) or not candidate_ids:
        raise ValueError("Candidate universe must be unique and nonempty")
    for record_id, relevance in targets.items():
        if not record_id:
            raise ValueError("Missing target record ID")
        if any(not math.isfinite(float(v)) or float(v) < 0 for v in relevance.values()):
            raise ValueError("Invalid target relevance")
    if any(not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 4
           for v in option_budgets.values()):
        raise ValueError("Invalid ordinary-question budget")
    payload = {
        "targets": {r: dict(t) for r, t in targets.items()},
        "candidate_ids": sorted(candidate_ids),
        "option_budgets": dict(option_budgets),
        "metric_spec": dict(metric_spec),
    }
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def assert_evaluation_unchanged(expected: str, **kwargs: object) -> None:
    if evaluation_fingerprint(**kwargs) != expected:
        raise ValueError("Evaluation target/universe/budget/metric changed")


class HelperTests(unittest.TestCase):
    """Synthetic fixtures test software behavior, not coffee science."""

    def setUp(self) -> None:
        self.patch = compile_patch([
            PatchRule("fixture apple phrase", "sensory.apple",
                      "fixture:source-rule", "SOURCE_CHECKED")
        ], frozenset({"sensory.apple"}))
        self.questions = (
            Question("z.fruit", (Option("apple", "sensory.apple",
                                        frozenset({"attribute.fruity"})),)),
            Question("a.sweet", (Option("honey", "sensory.honey",
                                        frozenset({"attribute.sweet"})),)),
        )
        self.selector = dict(questions=self.questions, used_axes=frozenset(),
                             train_coverage={"sensory.apple": .4, "sensory.honey": .6},
                             fixed_parents={}, option_budget=1)
        self.surface = dict(targets={"r1": {"sensory.apple": 1.0}, "empty": {}},
                            candidate_ids=("sensory.apple", "sensory.honey"),
                            option_budgets={"Q0": 4, "Q1": 4},
                            metric_spec={"version": "fixture.metric.v1", "k": 5})

    def test_positive_exact_mapping(self) -> None:
        result, evidence = map_positive_span(Span(" FIXTURE apple phrase ", "positive"),
                                             (), self.patch)
        self.assertEqual(result, ("sensory.apple",))
        self.assertEqual(evidence, "fixture:source-rule")

    def test_no_negation_or_unknown_promotion(self) -> None:
        for polarity in ("negative", "unknown"):
            self.assertEqual(map_positive_span(Span("fixture apple phrase", polarity),
                                               (), self.patch), ((), None))

    def test_no_substring_mapping(self) -> None:
        result, _ = map_positive_span(Span("not fixture apple phrase", "positive"),
                                      (), self.patch)
        self.assertEqual(result, ())

    def test_existing_decision_unchanged(self) -> None:
        result, evidence = map_positive_span(Span("fixture apple phrase", "positive"),
                                             ("attribute.fruity",), self.patch)
        self.assertEqual(result, ("attribute.fruity",))
        self.assertIsNone(evidence)

    def test_invalid_patch_rejected(self) -> None:
        with self.assertRaises(ValueError):
            compile_patch([PatchRule("x", "new.concept", "source", "SOURCE_CHECKED")],
                          frozenset({"sensory.apple"}))
        with self.assertRaises(ValueError):
            compile_patch([PatchRule("x", "sensory.apple", "source", "PROPOSED")],
                          frozenset({"sensory.apple"}))

    def test_group_weighting(self) -> None:
        rows = [TrainingB("o1", "g1", "s1", frozenset({"a"})),
                TrainingB("o2", "g1", "s2", frozenset({"b"})),
                TrainingB("o3", "g2", "s3", frozenset({"c"}))]
        self.assertEqual(fit_grouped_coverage(rows, evaluation_groups=frozenset()),
                         {"a": .25, "b": .25, "c": .5})

    def test_empty_observation_retained(self) -> None:
        rows = [TrainingB("o1", "g1", "s1", frozenset({"a"})),
                TrainingB("o2", "g1", "s1", frozenset())]
        self.assertEqual(fit_grouped_coverage(rows, evaluation_groups=frozenset()),
                         {"a": .5})

    def test_training_group_leakage_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fit_grouped_coverage([TrainingB("o1", "held", "s1", frozenset({"a"}))],
                                 evaluation_groups=frozenset({"held"}))

    def test_duplicate_observation_rejected(self) -> None:
        row = TrainingB("o1", "g1", "s1", frozenset({"a"}))
        with self.assertRaises(ValueError):
            fit_grouped_coverage([row, row], evaluation_groups=frozenset())

    def test_initial_answers_drive_selection(self) -> None:
        none = choose_i2_live(**self.selector, initial_observed_concepts=frozenset())
        fruit = choose_i2_live(**self.selector,
                               initial_observed_concepts=frozenset({"attribute.fruity"}))
        self.assertEqual(none.axis, "a.sweet")
        self.assertEqual(fruit.axis, "z.fruit")

    def test_selected_specific_entails_parent(self) -> None:
        cfg = {**self.selector,
               "fixed_parents": {"sensory.apple": frozenset({"attribute.fruity"})}}
        self.assertEqual(choose_i2_live(**cfg,
            initial_observed_concepts=frozenset({"sensory.apple"})).axis, "z.fruit")

    def test_no_used_axis_repeated(self) -> None:
        cfg = {**self.selector, "used_axes": frozenset({"z.fruit"})}
        self.assertEqual(choose_i2_live(**cfg,
            initial_observed_concepts=frozenset({"attribute.fruity"})).axis, "a.sweet")

    def test_budget_failure_not_filled(self) -> None:
        for budget in (2, 5):
            with self.assertRaises(ValueError):
                choose_i2_live(**{**self.selector, "option_budget": budget},
                               initial_observed_concepts=frozenset())

    def test_fingerprint_order_invariant(self) -> None:
        baseline = evaluation_fingerprint(**self.surface)
        other = {**self.surface,
                 "candidate_ids": tuple(reversed(self.surface["candidate_ids"])),
                 "targets": dict(reversed(list(self.surface["targets"].items())))}
        self.assertEqual(baseline, evaluation_fingerprint(**other))

    def test_target_mutation_detected(self) -> None:
        baseline = evaluation_fingerprint(**self.surface)
        changed = {**self.surface, "targets": {"r1": {"sensory.honey": 1.0}, "empty": {}}}
        with self.assertRaises(ValueError):
            assert_evaluation_unchanged(baseline, **changed)

    def test_budget_or_metric_mutation_detected(self) -> None:
        baseline = evaluation_fingerprint(**self.surface)
        for changed in ({**self.surface, "option_budgets": {"Q0": 3, "Q1": 4}},
                        {**self.surface, "metric_spec": {"version": "other", "k": 5}}):
            with self.assertRaises(ValueError):
                assert_evaluation_unchanged(baseline, **changed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=[__file__], verbosity=2)
    else:
        parser.print_help()
