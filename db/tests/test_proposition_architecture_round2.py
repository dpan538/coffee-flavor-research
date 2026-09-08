"""Round 2 — the proposition architecture, and the four defects that produced it.

Each defect below was found by feeding real product data to code that claimed
to be the product path. Every one is pinned by a test here so it cannot return
quietly.

ROUND2-OP2  the shipped generator read the k1 dimensions as a list of rows; the
            frozen R9 schema is a Mapping. Every real state raised.
ROUND2-OP3  direct evidence required an option id to be a registry concept. No
            option ever is: all 28 are partition names. Direct evidence was
            unreachable in production.
ROUND2-OP4  broad.citrus was the only fruity representative, so evidence that
            supported no more than "fruity" was reported as "citrus".
ROUND2-OP5  intersecting all answers into one candidate set would empty out on
            any two unrelated answers, e.g. fruit then nuts.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evidence_reader_round2 as reader  # noqa: E402
import inference_state_machine_round2 as fsm  # noqa: E402
import proposition_lattice_round2 as lattice  # noqa: E402
from output_generator_round2 import generate_output, load_registry  # noqa: E402

REGISTRY = load_registry()
PROPS = lattice.build_propositions(REGISTRY)
AXES = fsm.load_axes()

FROZEN_R9_STATE = {
    "qa_pairs": [{"selected_option_ids": ["citrus"]}],
    "k1": {
        "confirmed_concepts": ["sensory.lemon", "sensory.honey"],
        "dimensions": {
            "fruity": {"supported": 1.0},
            "floral": {"supported": 1.0},
            "sweet": {"supported": 0.0},
        },
    },
}


class StateSchema(unittest.TestCase):
    """ROUND2-OP2 — the frozen R9 state shape must be readable."""

    def test_frozen_mapping_schema_is_accepted(self):
        status = reader.normalise_k1_dimensions(FROZEN_R9_STATE)
        self.assertEqual(status["fruity"], reader.SUPPORTED)
        self.assertEqual(status["floral"], reader.SUPPORTED)
        # present with supported == 0 is activated but not confirmed
        self.assertEqual(status["sweet"], reader.PROPOSED)

    def test_shipped_generator_does_not_raise_on_a_real_state(self):
        output = generate_output(FROZEN_R9_STATE, REGISTRY)
        self.assertIn("main", output)

    def test_confirmed_concepts_are_direct_evidence(self):
        evidence = reader.read_evidence(FROZEN_R9_STATE, REGISTRY)
        self.assertIn("sensory.honey", evidence["direct"])

    def test_legacy_list_schema_still_read(self):
        legacy = {"k1": {"dimensions": [
            {"dimension_id": "sweet", "status": reader.SUPPORTED}]}}
        self.assertEqual(reader.normalise_k1_dimensions(legacy),
                         {"sweet": reader.SUPPORTED})


class OptionResolution(unittest.TestCase):
    """ROUND2-OP3 — options are partition names, never registry concepts."""

    def test_no_product_option_is_a_registry_concept(self):
        partitions = reader.load_partitions()
        self.assertTrue(partitions, "the axis file must be present for this suite")
        self.assertFalse(
            {name for name in partitions if name in REGISTRY},
            "a partition name collided with a registry concept id; the "
            "singleton rule below would then be ambiguous",
        )

    def test_singleton_partition_becomes_direct_evidence(self):
        state = {"qa_pairs": [{"selected_option_ids": ["white_floral"]}]}
        self.assertEqual(reader.read_evidence(state, REGISTRY)["direct"],
                         {"sensory.jasmine"})

    def test_multi_member_partition_is_not_promoted_to_a_word(self):
        state = {"qa_pairs": [{"selected_option_ids": ["nuts"]}]}
        evidence = reader.read_evidence(state, REGISTRY)
        self.assertEqual(evidence["direct"], set(),
                         "a two-member answer names no single concept")
        self.assertEqual(evidence["set_evidence"]["nuts"],
                         {"sensory.almond", "sensory.hazelnut"})

    def test_abstention_is_recorded_not_dropped(self):
        state = {"qa_pairs": [{"selected_option_ids": ["unsure"]}]}
        evidence = reader.read_evidence(state, REGISTRY)
        self.assertEqual(evidence["abstentions"], ["unsure"])
        self.assertEqual(evidence["direct"], set())


class Entailment(unittest.TestCase):
    def test_entailment_is_subset_containment(self):
        lemon = PROPS["sensory.lemon"]
        self.assertTrue(lattice.entails(lemon, frozenset({"sensory.lemon"})))
        self.assertFalse(
            lattice.entails(lemon, frozenset({"sensory.lemon", "sensory.orange"})),
            "a two-member constraint is not a claim about lemon alone",
        )

    def test_empty_constraint_entails_nothing(self):
        self.assertFalse(lattice.entails(PROPS["sensory.lemon"], frozenset()))

    def test_generalisation_returns_the_smallest_extent(self):
        hit = lattice.minimal_sufficient_generalisation(
            frozenset({"sensory.lemon", "sensory.orange"}), PROPS, (lattice.NAMED,))
        self.assertEqual(hit.concept_id, "broad.citrus")

    def test_pinned_concept_generalises_to_itself(self):
        hit = lattice.minimal_sufficient_generalisation(
            frozenset({"sensory.lemon"}), PROPS, (lattice.NAMED,))
        self.assertEqual(hit.concept_id, "sensory.lemon")


class NoOverClaiming(unittest.TestCase):
    """ROUND2-OP4 — the regression that motivated the whole rewrite."""

    def test_dimension_level_fruity_never_yields_citrus(self):
        """Asserted as non-entailment, not as 'the answer was not citrus'.

        Checking only the returned id would also pass when nothing is returned,
        which is a different outcome and would hide a regression that made the
        lattice silent instead of wrong.
        """
        fruity = lattice.dimension_closure(REGISTRY, {"fruity"})
        self.assertGreater(len(fruity), 2)
        citrus = PROPS["broad.citrus"]
        self.assertFalse(
            lattice.entails(citrus, fruity),
            "evidence supporting only 'fruity' entailed 'citrus'; a participant "
            "who tasted mango is told something false, not vague",
        )
        hit = lattice.minimal_sufficient_generalisation(fruity, PROPS, (lattice.NAMED,))
        self.assertNotEqual(getattr(hit, "concept_id", None), "broad.citrus")

    def test_mutating_an_extent_is_caught(self):
        """Guards the guard: widen broad.citrus to the whole dimension and the
        non-entailment above must break. Without this, the test could pass
        because entailment stopped working at all."""
        declared = dict(lattice.load_declared_extents())
        declared["broad.citrus"] = sorted(lattice.dimension_closure(REGISTRY, {"fruity"}))
        mutated = lattice.build_propositions(REGISTRY, declared)
        fruity = lattice.dimension_closure(REGISTRY, {"fruity"})
        self.assertTrue(
            lattice.entails(mutated["broad.citrus"], fruity),
            "entailment failed to fire on a deliberately widened extent, so the "
            "non-entailment assertion above proves nothing",
        )

    def test_every_named_generalisation_covers_its_constraint(self):
        """The property, not one instance: nothing shown may claim less than
        the evidence allows."""
        for dimension in {"fruity", "floral", "sweet", "spices", "nutty_cocoa"}:
            closure = lattice.dimension_closure(REGISTRY, {dimension})
            hit = lattice.minimal_sufficient_generalisation(
                closure, PROPS, (lattice.NAMED,))
            if hit is not None:
                with self.subTest(dimension=dimension):
                    self.assertTrue(closure <= hit.extent)

    def test_undeclared_broad_concept_is_unusable(self):
        self.assertIn("broad.chocolate", lattice.unusable_concepts(REGISTRY))
        self.assertNotIn("broad.chocolate", PROPS)

    def test_undeclared_concept_is_never_silently_widened(self):
        props = lattice.build_propositions(REGISTRY, declared={})
        self.assertFalse([c for c in props if c.startswith("broad.")])


class Branching(unittest.TestCase):
    """ROUND2-OP5 — unrelated answers must not annihilate each other."""

    def test_two_unrelated_answers_produce_two_branches(self):
        state = fsm.initial_state(REGISTRY)
        state = fsm.apply_answer(state, "family_direction", ["fruit"], AXES)
        state = fsm.apply_answer(state, "browned_sweet_reference", ["nuts"], AXES)
        self.assertEqual(len(state.branches), 2)
        self.assertTrue(all(b.size > 0 for b in state.branches))

    def test_related_answer_refines_rather_than_opening(self):
        state = fsm.initial_state(REGISTRY)
        state = fsm.apply_answer(state, "family_direction", ["fruit"], AXES)
        before = state.branches[0].size
        state = fsm.apply_answer(state, "fruit_region", ["citrus"], AXES)
        self.assertEqual(len(state.branches), 1)
        self.assertLess(state.branches[0].size, before)

    def test_apply_answer_does_not_mutate_the_input_state(self):
        state = fsm.initial_state(REGISTRY)
        state = fsm.apply_answer(state, "family_direction", ["fruit"], AXES)
        snapshot = state.snapshot()
        fsm.apply_answer(state, "fruit_region", ["citrus"], AXES)
        self.assertEqual(state.snapshot(), snapshot,
                         "a strategy must be able to explore an answer without "
                         "committing it")


class OutputContract(unittest.TestCase):
    def _session(self, answers):
        state = fsm.initial_state(REGISTRY)
        for axis_id, options in answers:
            state = fsm.apply_answer(state, axis_id, options, AXES)
        for branch in state.branches:
            for cid in branch.constraint:
                for dim in REGISTRY[cid].get("support_dimension_ids") or []:
                    state.dim_status[dim] = fsm.SUPPORTED
        return fsm.build_output(state, REGISTRY, PROPS)

    def test_budget_is_three_two_three(self):
        out = self._session([("family_direction", ["fruit", "floral_tea"]),
                             ("fruit_region", ["citrus"])])
        self.assertLessEqual(len(out["main"]), 3)
        self.assertLessEqual(len(out["secondary"]), 2)
        self.assertLessEqual(len(out["overall_profile"]), 3)

    def test_main_and_secondary_are_never_directions(self):
        out = self._session([("family_direction", ["fruit"])])
        for row in out["main"] + out["secondary"]:
            self.assertEqual(REGISTRY[row["candidate_id"]]["role"], lattice.NAMED)

    def test_profile_is_only_directions(self):
        out = self._session([("family_direction", ["fruit"])])
        for row in out["overall_profile"]:
            self.assertEqual(REGISTRY[row["candidate_id"]]["role"], lattice.DIRECTION)

    def test_no_duplicate_across_main_and_secondary(self):
        out = self._session([("family_direction", ["fruit", "cocoa_nut_caramel"]),
                             ("fruit_region", ["citrus"])])
        ids = [r["candidate_id"] for r in out["main"] + out["secondary"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_pinned_answer_reaches_main(self):
        out = self._session([("floral_tea_reference", ["white_floral"])])
        self.assertIn("sensory.jasmine",
                      [r["candidate_id"] for r in out["main"]])

    def test_more_specific_answer_is_ordered_first(self):
        out = self._session([("family_direction", ["fruit", "floral_tea"]),
                             ("floral_tea_reference", ["white_floral"])])
        ids = [r["candidate_id"] for r in out["main"]]
        if "sensory.jasmine" in ids and "broad.citrus" in ids:
            self.assertLess(ids.index("sensory.jasmine"), ids.index("broad.citrus"))


class Strategy(unittest.TestCase):
    def test_selected_axis_actually_splits_the_open_branch(self):
        state = fsm.initial_state(REGISTRY)
        state = fsm.apply_answer(state, "family_direction", ["fruit"], AXES)
        axis_id = fsm.select_next_axis(state, AXES, require_product_eligible=False)
        self.assertIsNotNone(axis_id)
        cells, _ = fsm.split_quality(AXES[axis_id], state.branches[0].constraint)
        self.assertGreater(cells, 1, "a question that cannot divide teaches nothing")

    def test_an_axis_is_never_asked_twice(self):
        state = fsm.initial_state(REGISTRY)
        state = fsm.apply_answer(state, "family_direction", ["fruit"], AXES)
        self.assertNotEqual(
            fsm.select_next_axis(state, AXES, require_product_eligible=False),
            "family_direction")

    def test_stop_on_absolute_question_limit(self):
        state = fsm.initial_state(REGISTRY)
        state.asked_axes = ["a", "b", "c", "d", "e"]
        stop, reason = fsm.should_stop(state, None, AXES, False)
        self.assertTrue(stop)
        self.assertEqual(reason, "ABSOLUTE_QUESTION_LIMIT")

    def test_stop_when_an_answer_changed_nothing(self):
        state = fsm.initial_state(REGISTRY)
        state = fsm.apply_answer(state, "family_direction", ["fruit"], AXES)
        stalled = fsm.apply_answer(state, "fruit_region", ["unsure"], AXES)
        stop, reason = fsm.should_stop(stalled, state, AXES, False)
        self.assertTrue(stop)
        self.assertEqual(reason, "NO_NEW_EVIDENCE_FROM_LAST_ANSWER")

    def test_stop_when_every_branch_is_pinned(self):
        state = fsm.initial_state(REGISTRY)
        state = fsm.apply_answer(state, "floral_tea_reference", ["white_floral"], AXES)
        stop, reason = fsm.should_stop(state, None, AXES, False)
        self.assertTrue(stop)
        self.assertEqual(reason, "ALL_BRANCHES_PINNED")


class ReachableSpace(unittest.TestCase):
    """The measured limit, pinned so a later change to the axes shows up here."""

    def test_most_specific_words_cannot_be_reached_by_any_question(self):
        partitions = reader.load_partitions()
        reachable = {c for members in partitions.values() for c in members}
        specific = lattice.specific_concepts(REGISTRY)
        self.assertLess(
            len(reachable & specific), len(specific) / 2,
            "if this ever passes, question coverage has improved enough that "
            "the reachable-vocabulary finding should be re-measured",
        )


if __name__ == "__main__":
    unittest.main()
