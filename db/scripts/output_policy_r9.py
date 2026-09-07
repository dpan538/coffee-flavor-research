"""Deterministic R9 research output policies over one frozen endpoint state.

This module does not fit a model, select a question, inspect an evaluation target,
or replace the default finalizer.  Callers must supply the explicit concept-role
registry from the R9 contract and an already-finalized R4/R8 result.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

VERSION = "m2-r9.output-policy-adapter.v1"
POLICIES = ("OUT_MIXED", "OUT_SPECIFIC_FIRST", "OUT_SEPARATED")
PROFILE_DIRECTION = "PROFILE_DIRECTION"
NAMED_DESCRIPTOR = "NAMED_DESCRIPTOR"
OTHER_NATIVE_MEASUREMENT = "OTHER_NATIVE_MEASUREMENT"
ROLES = frozenset({PROFILE_DIRECTION, NAMED_DESCRIPTOR, OTHER_NATIVE_MEASUREMENT})
FORBIDDEN_EVALUATION_KEYS = frozenset(
    {
        "T",
        "full_T",
        "hidden_T",
        "participant_rating",
        "preference_label",
        "participant_preference",
        "participant_satisfaction",
        "perceived_fit_rating",
        "main_fit_rating_1_to_4",
        "specificity_choice",
        "new_expression_help_choice",
        "information_burden_choice",
        "profile_effect_choice",
        "post_output_acceptance",
        "profile_preference",
    }
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _ids(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("ORDERED_CANDIDATE_ROWS_REQUIRED")
    result = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("CANDIDATE_ROW_REQUIRED")
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("NONEMPTY_CANDIDATE_ID_REQUIRED")
        result.append(candidate_id)
    return result


def validate_role_registry(registry: Mapping[str, Mapping[str, Any]]) -> None:
    if not isinstance(registry, Mapping) or not registry:
        raise ValueError("EXPLICIT_CONCEPT_ROLE_REGISTRY_REQUIRED")
    for candidate_id, entry in registry.items():
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("NONEMPTY_ROLE_CONCEPT_ID_REQUIRED")
        if not isinstance(entry, Mapping) or entry.get("role") not in ROLES:
            raise ValueError("REGISTERED_CONCEPT_ROLE_REQUIRED:" + candidate_id)
        dimensions = entry.get("support_dimension_ids", [])
        if (
            isinstance(dimensions, (str, bytes))
            or not isinstance(dimensions, Sequence)
            or any(not isinstance(value, str) or not value for value in dimensions)
        ):
            raise ValueError("SUPPORT_DIMENSION_ID_LIST_REQUIRED:" + candidate_id)
        if entry["role"] == PROFILE_DIRECTION and not dimensions:
            raise ValueError("PROFILE_DIRECTION_SUPPORT_DIMENSION_REQUIRED")


def role_registry_from_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    table = contract.get("concept_role_registry")
    validate_role_registry(table)
    return copy.deepcopy(dict(table))


def _state_ranking(final_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    state = final_result.get("state")
    if not isinstance(state, Mapping):
        raise ValueError("FROZEN_ENDPOINT_STATE_REQUIRED")
    ranking = state.get("candidate_scores")
    if isinstance(ranking, (str, bytes)) or not isinstance(ranking, Sequence):
        raise ValueError("FROZEN_CANDIDATE_RANKING_REQUIRED")
    rows = [copy.deepcopy(dict(row)) for row in ranking]
    ids = _ids(rows)
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_FROZEN_CANDIDATE_ID")
    if any(row.get("legal") is False for row in rows):
        raise ValueError("INELIGIBLE_ROW_IN_FINAL_CANDIDATE_RANKING")
    return rows


def _supported_profile_rows(
    rows: Sequence[Mapping[str, Any]],
    state: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    k1 = state.get("k1")
    if not isinstance(k1, Mapping) or not isinstance(k1.get("dimensions"), Mapping):
        raise ValueError("FROZEN_SUPPORTED_DIRECTION_STATE_REQUIRED")
    dimensions = k1["dimensions"]
    result = []
    for row in rows:
        candidate_id = row["candidate_id"]
        entry = registry[candidate_id]
        if entry["role"] != PROFILE_DIRECTION:
            continue
        support_ids = entry["support_dimension_ids"]
        if any(
            isinstance(dimensions.get(identity), Mapping)
            and float(dimensions[identity].get("supported", 0)) > 0
            for identity in support_ids
        ):
            result.append(copy.deepcopy(dict(row)))
    return result[:3]


def _validate_source_return(final_result: Mapping[str, Any]) -> None:
    if not isinstance(final_result, Mapping):
        raise ValueError("FINAL_RESULT_MAPPING_REQUIRED")
    if FORBIDDEN_EVALUATION_KEYS & set(final_result):
        raise ValueError("OUTPUT_POLICY_MUST_NOT_RECEIVE_T_OR_PARTICIPANT_EVALUATION")
    if "main" not in final_result or "secondary" not in final_result:
        raise ValueError("ORIGINAL_MAIN_AND_SECONDARY_REQUIRED")
    main_ids = _ids(final_result["main"])
    secondary_ids = _ids(final_result["secondary"])
    combined = main_ids + secondary_ids
    if len(main_ids) > 5 or len(secondary_ids) > 3 or len(combined) > 8:
        raise ValueError("ORIGINAL_OUTPUT_BUDGET_VIOLATION")
    if len(combined) != len(set(combined)):
        raise ValueError("DUPLICATE_ORIGINAL_OUTPUT_ID")
    exposure = final_result.get("exposure")
    if exposure is not None:
        if not isinstance(exposure, Mapping):
            raise ValueError("ORIGINAL_EXPOSURE_MAPPING_REQUIRED")
        exposed = exposure.get("candidate_ids")
        if not isinstance(exposed, Sequence) or isinstance(exposed, (str, bytes)):
            raise ValueError("ORIGINAL_EXPOSURE_IDS_REQUIRED")
        if list(exposed) != combined:
            raise ValueError("ORIGINAL_EXPOSURE_MUST_MATCH_MAIN_SECONDARY")
        if exposure.get("eligible_for_final_comparison") is not (
            3 <= len(combined) <= 8
        ):
            raise ValueError("ORIGINAL_EXPOSURE_ELIGIBILITY_MISMATCH")


def _exposure(
    original: Mapping[str, Any] | None, candidate_ids: Sequence[str]
) -> dict[str, Any] | None:
    if original is None:
        return None
    result = copy.deepcopy(dict(original))
    result["candidate_ids"] = list(candidate_ids)
    result["eligible_for_final_comparison"] = 3 <= len(candidate_ids) <= 8
    return result


def adapt_output(
    final_result: Mapping[str, Any],
    concept_roles: Mapping[str, Mapping[str, Any]],
    policy_id: str,
) -> dict[str, Any]:
    """Apply one registered policy without changing ranks, rows, or evidence.

    ``OUT_MIXED`` copies the original main, secondary and exposure exactly.
    Experimental policies read only the frozen eligible candidate ranking and the
    frozen supported-direction state.  The function has no target/evaluation input.
    """
    if policy_id not in POLICIES:
        raise ValueError("REGISTERED_OUTPUT_POLICY_REQUIRED")
    validate_role_registry(concept_roles)
    _validate_source_return(final_result)
    rows = _state_ranking(final_result)
    ranking_ids = _ids(rows)
    for candidate_id in ranking_ids:
        if candidate_id not in concept_roles:
            raise ValueError("UNREGISTERED_CANDIDATE_ROLE:" + candidate_id)
    source_ids = _ids(final_result["main"]) + _ids(final_result["secondary"])
    if source_ids != ranking_ids[: len(source_ids)]:
        raise ValueError("ORIGINAL_OUTPUT_MUST_BE_FROZEN_RANK_PREFIX")

    if policy_id == "OUT_MIXED":
        main = copy.deepcopy(list(final_result["main"]))
        secondary = copy.deepcopy(list(final_result["secondary"]))
        overall_profile: list[dict[str, Any]] = []
        exposure = copy.deepcopy(final_result.get("exposure"))
    else:
        named = [
            row
            for row in rows
            if concept_roles[row["candidate_id"]]["role"] == NAMED_DESCRIPTOR
        ]
        profiles = [
            row
            for row in rows
            if concept_roles[row["candidate_id"]]["role"] == PROFILE_DIRECTION
        ]
        if policy_id == "OUT_SPECIFIC_FIRST":
            selected = (named + profiles)[:8]
            overall_profile = []
        else:
            selected = named[:8]
            overall_profile = _supported_profile_rows(
                rows, final_result["state"], concept_roles
            )
        main = copy.deepcopy(selected[:5])
        secondary = copy.deepcopy(selected[5:8])
        exposure = _exposure(final_result.get("exposure"), _ids(main) + _ids(secondary))

    main_ids = _ids(main)
    secondary_ids = _ids(secondary)
    profile_ids = _ids(overall_profile)
    pool = main_ids + secondary_ids
    if len(pool) != len(set(pool)):
        raise ValueError("DUPLICATE_POLICY_OUTPUT_ID")
    if set(pool) & set(profile_ids):
        raise ValueError("PROFILE_CANDIDATE_OVERLAPS_COMPARISON_POOL")
    if len(profile_ids) != len(set(profile_ids)):
        raise ValueError("DUPLICATE_PROFILE_ID")
    if len(main_ids) > 5 or len(secondary_ids) > 3 or len(pool) > 8:
        raise ValueError("POLICY_OUTPUT_BUDGET_VIOLATION")
    if exposure is not None and exposure["candidate_ids"] != pool:
        raise ValueError("POLICY_EXPOSURE_MISMATCH")

    payload = {
        "adapter_version": VERSION,
        "policy_id": policy_id,
        "stage": final_result.get("stage"),
        "main": main,
        "secondary": secondary,
        "overall_profile": overall_profile,
        "exposure": exposure,
        "comparison_pool_candidate_ids": pool,
        "final_comparison_status": (
            "ELIGIBLE"
            if 3 <= len(pool) <= 8
            else "NOT_EXECUTABLE_EXISTING_3_TO_8_CONTRACT"
        ),
        "source_return_sha256": digest(final_result),
    }
    payload["output_hash"] = digest(
        {
            "adapter_version": VERSION,
            "policy_id": policy_id,
            "model_bundle_id": (
                exposure.get("generation_version") if exposure is not None else None
            ),
            "answer_state_hash": (
                exposure.get("state_hash") if exposure is not None else None
            ),
            "main": main_ids,
            "secondary": secondary_ids,
            "overall_profile": profile_ids,
        }
    )
    return payload


def equivalence(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        "main": _ids(left["main"]) == _ids(right["main"]),
        "full_return": left["comparison_pool_candidate_ids"]
        == right["comparison_pool_candidate_ids"],
        "overall_profile": _ids(left["overall_profile"])
        == _ids(right["overall_profile"]),
    }
    return {
        **fields,
        "status": "EQUIVALENT_ON_CASE" if all(fields.values()) else "DIFFERENT_ON_CASE",
    }
