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

# Project-local modules, safe to evict and re-import because they are pure
# Python with no extension state.
LOCAL_MODULES = frozenset(p.stem for p in SCRIPTS.glob("*.py"))


class RuntimeBoundary(unittest.TestCase):
    """Detection is by interposing on __import__, never by evicting the target.

    An earlier version of this test evicted sklearn, scipy and numpy from
    sys.modules to force a fresh import. numpy cannot survive that: once
    removed, every later import of it in the same process fails inside its own
    partially-initialised package, and the whole fitting-era suite failed with
    six errors that had nothing to do with the code under test.

    Eviction was never needed. The import statement calls __import__ on every
    execution, cached or not, so a guard on __import__ sees the import whether
    or not the module is already in sys.modules. Only project-local modules are
    evicted here, and only so that a runtime module's own top-level imports
    actually re-execute under the guard.
    """

    def _violations(self, module_name: str, blocked: frozenset[str]) -> list[str]:
        """Import under the guard and report which blocked modules were reached."""
        real_import = builtins.__import__
        violations: list[str] = []

        def guarded(name, globals=None, locals=None, fromlist=(), level=0):
            root = name.split(".")[0]
            if root in blocked:
                violations.append(name)
                raise ImportError(f"blocked by runtime boundary: {name}")
            return real_import(name, globals, locals, fromlist, level)

        # Evict only local modules, so the runtime module and its local
        # dependencies re-execute their imports. Third-party modules stay
        # cached; the guard catches them regardless.
        evicted = {name: sys.modules[name] for name in LOCAL_MODULES if name in sys.modules}
        for name in evicted:
            del sys.modules[name]

        builtins.__import__ = guarded
        try:
            importlib.import_module(module_name)
        except ImportError:
            pass  # the guard raised; violations already records what was reached
        finally:
            builtins.__import__ = real_import
            # Drop anything left behind by a failed import, then restore.
            for name in LOCAL_MODULES:
                sys.modules.pop(name, None)
            sys.modules.update(evicted)
        return violations

    def test_runtime_does_not_import_fitting_era(self):
        for module_name in RUNTIME_MODULES:
            with self.subTest(module=module_name):
                self.assertEqual(
                    self._violations(module_name, FITTING_ERA_MODULES), [],
                    f"{module_name} reaches the fitting era",
                )

    def test_runtime_does_not_need_scientific_stack(self):
        for module_name in RUNTIME_MODULES:
            with self.subTest(module=module_name):
                self.assertEqual(
                    self._violations(module_name, FORBIDDEN_THIRD_PARTY), [],
                    f"{module_name} reaches the scientific stack",
                )

    def test_guard_catches_a_known_violator(self):
        """Positive control.

        Without this, both tests above would still pass if the guard silently
        stopped firing, and the boundary would be unenforced while looking
        green. audit_semantic_integrity_r9 genuinely imports flavor_m2_r1, so
        the guard must report it.
        """
        found = self._violations("audit_semantic_integrity_r9", FITTING_ERA_MODULES)
        self.assertIn(
            "flavor_m2_r1", found,
            "the guard failed to detect a fitting-era import that is known to exist; "
            "the two boundary tests above cannot be trusted while this fails",
        )

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
