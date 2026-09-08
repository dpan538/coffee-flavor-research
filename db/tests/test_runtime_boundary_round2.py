"""A1 — assert the product runtime path stays free of the fitting era.

The R9 cluster is 20 modules, of which only a handful are shipped. Three
research modules still import the fitting era (analyze_participant_responses_r9
and generate_user_study_pack_r9 pull flavor_backend, audit_semantic_integrity_r9
pulls flavor_m2_r1), which is why running them needs sklearn, scipy and lxml.

Those three are research tools and are not shipped. What must be guaranteed is
that the runtime never acquires that dependency by accident. This test fails the
moment a runtime module imports a fitted-model module or a scientific stack.
"""

from __future__ import annotations

import builtins
import importlib
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# Modules the product actually runs.
RUNTIME_MODULES = (
    "output_policy_r9",
    "output_generator_round2",
    "flavor_backend",
)

# Fitted-model modules. A runtime import of any of these reintroduces model
# serving into a path that is meant to be deterministic.
FITTING_ERA_MODULES = frozenset(
    {
        "flavor_m2_r1",
        "flavor_sequential",
        "flavor_context",
        "flavor_coordination_r2",
        "flavor_constraints_r3",
        "flavor_conditioning_r4",
        "flavor_foundation_r1",
    }
)

# Third-party scientific stack. The runtime is standard library only, which is
# what makes it deployable without a build environment.
FORBIDDEN_THIRD_PARTY = frozenset({"sklearn", "scipy", "numpy", "lxml"})


class RuntimeBoundary(unittest.TestCase):
    def _import_with_guard(self, module_name: str, blocked: frozenset[str]) -> None:
        real_import = builtins.__import__
        violations: list[str] = []

        def guarded(name, globals=None, locals=None, fromlist=(), level=0):
            root = name.split(".")[0]
            if root in blocked:
                violations.append(name)
                raise ImportError(f"blocked by runtime boundary: {name}")
            return real_import(name, globals, locals, fromlist, level)

        for cached in [m for m in sys.modules if m.split(".")[0] in blocked]:
            del sys.modules[cached]
        sys.modules.pop(module_name, None)

        builtins.__import__ = guarded
        try:
            importlib.import_module(module_name)
        except ImportError as exc:  # noqa: PERF203 - the assertion needs the message
            self.fail(
                f"{module_name} imports a forbidden module: {violations or exc}"
            )
        finally:
            builtins.__import__ = real_import

    def test_runtime_does_not_import_fitting_era(self):
        for module_name in RUNTIME_MODULES:
            with self.subTest(module=module_name):
                self._import_with_guard(module_name, FITTING_ERA_MODULES)

    def test_runtime_does_not_need_scientific_stack(self):
        for module_name in RUNTIME_MODULES:
            with self.subTest(module=module_name):
                self._import_with_guard(module_name, FORBIDDEN_THIRD_PARTY)

    def test_research_modules_are_not_runtime(self):
        """Documents the boundary rather than enforcing it.

        These three legitimately depend on the fitting era. The test exists so a
        later reader does not mistake them for runtime and try to ship them.
        """
        research_with_fitting_dependency = {
            "analyze_participant_responses_r9",
            "generate_user_study_pack_r9",
            "audit_semantic_integrity_r9",
        }
        self.assertTrue(
            research_with_fitting_dependency.isdisjoint(RUNTIME_MODULES),
            "a research module carrying a fitting-era dependency entered the runtime list",
        )


if __name__ == "__main__":
    unittest.main()
