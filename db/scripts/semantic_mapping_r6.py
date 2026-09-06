"""Bounded R6 source-checked input interpretation; no target edits or model fit.

Source cells, original spans, observation identities and fold support are private.
The public rule table contains generic language patterns and declared boundaries.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import data_supervision_r5 as source
from flavor_m2_r1 import PARENTS, digest

VERSION = "m2-r6.training-ab-semantic-patch.v1"
ROOT = Path(__file__).resolve().parents[2]
MAX_RULES = 50
SOURCE_URL = "https://zenodo.org/records/20840464"
LEXICAL_REFERENCES = {
    "berry": "https://dictionary.cambridge.org/us/dictionary/english/berry",
    "nutty": "https://www.collinsdictionary.com/us/dictionary/english/nutty",
    "citrus": "https://dictionary.cambridge.org/dictionary/english/citrus-fruit",
    "stone_fruit": "https://dictionary.cambridge.org/us/dictionary/english/stone-fruit",
    "milk_chocolate": "https://dictionary.cambridge.org/dictionary/english/milk-chocolate",
    "floral": "https://dictionary.cambridge.org/us/dictionary/english/floral",
    "herbaceous": "https://www.collinsdictionary.com/us/dictionary/english/herbaceous",
}
NEGATION = re.compile(
    r"\b(?:no|not|without|none|never|lack|lacks|lacking|absent|absence)\b", re.I
)
COMPOSITE = re.compile(r"[/+&]|\b(?:and|or|versus|vs|rather than|instead of)\b", re.I)
UNCERTAIN = re.compile(r"\b(?:maybe|perhaps|possibly|uncertain|unsure)\b|\?", re.I)


def normalize_span(value):
    return " ".join(str(value).strip().rstrip(".").casefold().split())


def reviewed_rules():
    """Explicit finite forms, never substring extraction or ontology expansion."""
    rules = []

    def add(forms, concept, relation, basis, reference=None):
        for form in forms:
            if concept not in PARENTS:
                raise ValueError("R6_ONTOLOGY_EXPANSION_FORBIDDEN")
            rules.append(
                {
                    "rule_id": "R6-" + hashlib.sha256(form.encode()).hexdigest()[:12],
                    "normalized_span": form,
                    "concepts": [concept],
                    "status": "SOURCE_CHECKED",
                    "human_approval": "NOT_REVIEWED_BY_HUMAN",
                    "relation": relation,
                    "basis": basis,
                    "source_url": SOURCE_URL,
                    "lexical_reference_url": LEXICAL_REFERENCES.get(reference),
                    "polarity": "POSITIVE_ONLY",
                    "scope": "EXACT_COMPLETE_LIST_FRAGMENT",
                    "modifier_policy": "Original modifier retained in private evidence; no extra independent observation or fine child inferred",
                }
            )

    add(
        ["berry", "berries", "dark berries", "red berries", "black berries"],
        "attribute.fruity",
        "BROAD_CATEGORY_ONLY",
        "Berry references support fruit category only; colour does not identify a berry species",
        "berry",
    )
    add(
        [
            "dried fruits",
            "tropical fruits",
            "fruit",
            "yellow fruits",
            "overripe fruits",
        ],
        "attribute.fruity",
        "BROAD_CATEGORY_ONLY",
        "Explicit named fruit family; no constituent fruit inferred",
    )
    add(
        ["stone fruits", "stone fruit"],
        "attribute.fruity",
        "BROAD_CATEGORY_ONLY",
        "Stone fruit is a fruit family, not a particular peach or plum",
        "stone_fruit",
    )
    add(
        ["roasted nuts", "raw nuts", "nut", "nuts", "nutty"],
        "broad.nutty",
        "BROAD_CATEGORY_ONLY",
        "Explicit nut reference; roast/raw qualifier retained without inferring a nut species or a separate roast observation",
        "nutty",
    )
    add(
        ["milk chocolate"],
        "broad.chocolate",
        "BROAD_CATEGORY_ONLY",
        "Milk chocolate supports chocolate family only; never dark chocolate, cocoa, or dairy as extra positives",
        "milk_chocolate",
    )
    add(
        ["red apple", "yellow apple", "green apple", "baked apple"],
        "sensory.apple",
        "SCOPED_MODIFIER_CORE",
        "Apple is the explicit complete noun head; colour/baked modifier preserved, not generalized as a calibrated apple subtype",
    )
    for form, concept in [
        ("black currant", "sensory.blackcurrant"),
        ("prunes", "sensory.prune"),
        ("hazelnuts", "sensory.hazelnut"),
        ("walnuts", "sensory.walnut"),
        ("strawberries", "sensory.strawberry"),
    ]:
        add(
            [form],
            concept,
            "ORTHOGRAPHIC_OR_NUMBER_VARIANT",
            "Existing named concept; explicit word spacing or plural inflection only",
        )
    add(
        ["alcoholic notes", "alcohol"],
        "sensory.alcoholic",
        "EXPLICIT_AROMA_REFERENCE",
        "Source aroma/flavour language refers to alcoholic character, not chemical alcohol measurement or fermentation proof",
    )
    add(
        ["floral notes"],
        "attribute.floral",
        "BROAD_CATEGORY_ONLY",
        "Flower-like aroma family only; no jasmine or other flower species",
        "floral",
    )
    add(
        ["woody notes", "wood"],
        "sensory.woody",
        "EXPLICIT_AROMA_REFERENCE",
        "Explicit woody reference; no tree species inferred",
    )
    add(
        ["tobacco notes"],
        "sensory.tobacco",
        "EXPLICIT_AROMA_REFERENCE",
        "Explicit tobacco reference with discourse qualifier retained",
    )
    add(
        ["light citrus", "citrusy"],
        "broad.citrus",
        "BROAD_CATEGORY_ONLY",
        "Citrus family or its intensity-qualified adjective; no particular citrus fruit",
        "citrus",
    )
    add(
        ["grass", "grassy", "herbaceous", "herbs"],
        "attribute.green_vegetative",
        "BROAD_CATEGORY_ONLY",
        "Source green/herb character is retained at registered vegetative category; no hay, tea or specific herb inferred",
        "herbaceous",
    )
    add(
        ["tea"],
        "attribute.green_vegetative",
        "REGISTERED_PARENT_ONLY",
        "Unspecified tea maps only to shared registered parent of black and green tea; neither tea type inferred",
    )
    add(
        ["dark raisins"],
        "sensory.raisin",
        "SCOPED_MODIFIER_CORE",
        "Explicit raisin core; dark retained as a modifier, not a new target",
    )
    add(
        ["roasted peanuts"],
        "sensory.peanut",
        "SCOPED_MODIFIER_CORE",
        "Explicit peanut core; roast qualifier retained, no additional independent roast observation",
    )
    if len({r["normalized_span"] for r in rules}) != len(rules):
        raise ValueError("DUPLICATE_EXPLICIT_PATCH_RULE")
    return rules


def protocol():
    return {
        "version": VERSION,
        "mapping_base": source.proposal()["mapping_choice"],
        "mapping_patch": "Add only source-checked explicit positive concepts to original A/B interpretation; preserve original baseline concepts and all source evidence",
        "review_status": "SOURCE_CHECKED, never HUMAN_APPROVED or sensory truth",
        "candidate_selection": "Only actual training A/B rows; prioritize distinct coffee groups with a newly expressible registered concept, then occurrence count, then normalized span; no outcomes, T values or held-group frequencies",
        "maximum_active_rules": MAX_RULES,
        "minimum_training_coffee_support": 1,
        "fold_isolation": "Each outer and inner caller supplies training groups and excluded groups; active rules require training A/B support; lexical evidence may be cached independently of target outcomes",
        "scope": "Exact complete comma/semicolon/newline list fragments; no arbitrary substring mapping; retain original whole cell, offsets, span, modifiers, polarity and compound status",
        "negation": "Any negation in a source cell blocks additions from that whole cell, conservatively preserving unclear cross-fragment scope; unknown is not negative",
        "compound": "Slash, conjunction, alternative and comparison fragments are retained unresolved and never split into positive observations",
        "ontology": "Existing PARENTS only; category cannot confirm child; no C1 inference",
        "target_guard": "Only A/B and added input trace keys change; complete T, original R5 hidden T, ordinal targets, weights, candidate universe and original observation roles remain byte-equivalent after canonical serialization",
        "fit_count": 0,
        "source_rights": "Prior source restrictive noncommercial intersection; original cells and observation traces private",
        "reviewed_rules_sha256": digest(reviewed_rules()),
        "lexical_reference_urls": LEXICAL_REFERENCES,
    }


def extract_spans(unit):
    """Read only the given input observation; retain exact original string slices."""
    out = []
    for field, value in sorted(unit["description_fields"].items()):
        text = value.get("source_text")
        if not isinstance(text, str) or not text.strip():
            continue
        whole_negative = bool(NEGATION.search(text))
        for found in re.finditer(r"[^,;\n]+", text):
            span = found.group()
            normalized = normalize_span(span)
            if not normalized:
                continue
            polarity = (
                "NEGATIVE_OR_UNRESOLVED_SCOPE"
                if whole_negative
                else "UNCERTAIN" if UNCERTAIN.search(span) else "POSITIVE_MENTION"
            )
            composite = bool(COMPOSITE.search(span))
            out.append(
                {
                    "observation_unit_id": unit["observation_unit_id"],
                    "field": field,
                    "source_column": value["source_column"],
                    "source_text": text,
                    "source_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "raw_span": span,
                    "span_start": found.start(),
                    "span_end": found.end(),
                    "normalized_span": normalized,
                    "polarity": polarity,
                    "compound_status": (
                        "UNRESOLVED_COMPOSITE_NOT_SPLIT"
                        if composite
                        else "SINGLE_EXPLICIT_FRAGMENT"
                    ),
                    "positive_mapping_allowed": polarity == "POSITIVE_MENTION"
                    and not composite,
                }
            )
    return out


def load_inputs(owner):
    owner = Path(owner)
    parsed = json.loads(
        (owner / "revisions/r5/zenodo_source_parse.private.json").read_text()
    )
    examples = source.make_examples(
        parsed,
        ROOT
        / "db/data/backend-sequential-model-v2/revisions/r5/experiment_contract.json",
    )
    examples = [e for e in examples if e["old_split"] == "DEVELOPMENT"]
    allowed = {
        e[role + "_observation_unit_id"] for e in examples for role in ("A", "B")
    }
    units = {
        u["observation_unit_id"]: u
        for u in parsed["observation_units"]
        if u["observation_unit_id"] in allowed
    }
    return examples, units


def input_units(examples, units, training_groups):
    for e in examples:
        if e["group_id"] not in training_groups:
            continue
        ids = [e[role + "_observation_unit_id"] for role in ("A", "B")]
        if len(set(ids)) != 2 or set(ids) & set(e["T_observation_unit_ids"]):
            raise ValueError("R6_DISJOINT_INPUT_OBSERVATIONS_REQUIRED")
        for role, identity in zip(("A", "B"), ids, strict=True):
            unit = units[identity]
            if unit["group_id"] != e["group_id"]:
                raise ValueError("R6_INPUT_COFFEE_IDENTITY_MISMATCH")
            yield e, role, unit


def fit_patch(examples, units, training_groups, excluded_groups=()):
    """Select supported language rules, not a numerical predictor or score model."""
    training_groups, excluded_groups = set(training_groups), set(excluded_groups)
    if training_groups & excluded_groups:
        raise ValueError("R6_PATCH_TRAINING_GROUP_LEAKAGE")
    lookup = {r["normalized_span"]: r for r in reviewed_rules()}
    counts, groups, spans = Counter(), defaultdict(set), defaultdict(list)
    inspected = 0
    for example, role, unit in input_units(examples, units, training_groups):
        inspected += 1
        baseline = set(unit["strict_D0_concepts"])
        for span in extract_spans(unit):
            rule = lookup.get(span["normalized_span"])
            if (
                rule is None
                or not span["positive_mapping_allowed"]
                or set(rule["concepts"]) <= baseline
            ):
                continue
            form = rule["normalized_span"]
            counts[form] += 1
            groups[form].add(example["group_id"])
            spans[form].append(
                {
                    **span,
                    "record_id": example["record_id"],
                    "group_id": example["group_id"],
                    "role": role,
                }
            )
    ordered = sorted(
        counts, key=lambda form: (-len(groups[form]), -counts[form], form)
    )[:MAX_RULES]
    active = [
        {
            **lookup[form],
            "training_coffee_groups": sorted(groups[form]),
            "training_coffee_support": len(groups[form]),
            "training_span_occurrences": counts[form],
        }
        for form in ordered
    ]
    value = {
        "version": VERSION,
        "protocol_sha256": digest(protocol()),
        "rules": active,
        "training_groups": sorted(training_groups),
        "excluded_groups": sorted(excluded_groups),
        "inspected_input_units": inspected,
        "fit_count": 0,
        "training_support_trace": {form: spans[form] for form in ordered},
    }
    value["patch_sha256"] = digest(value)
    return value


def check_patch(patch):
    if patch.get("version") != VERSION or patch.get("protocol_sha256") != digest(
        protocol()
    ):
        raise ValueError("R6_PATCH_VERSION_MISMATCH")
    expected = {k: v for k, v in patch.items() if k != "patch_sha256"}
    if digest(expected) != patch.get("patch_sha256"):
        raise ValueError("R6_PATCH_PAYLOAD_CHANGED")
    if set(patch["training_groups"]) & set(patch["excluded_groups"]):
        raise ValueError("R6_PATCH_TRAINING_GROUP_LEAKAGE")
    registered = {r["rule_id"]: r for r in reviewed_rules()}
    for rule in patch["rules"]:
        fixed = registered.get(rule["rule_id"])
        if fixed is None or any(rule.get(k) != value for k, value in fixed.items()):
            raise ValueError("R6_UNCHECKED_RULE_SUBSTITUTION")
        support = set(rule["training_coffee_groups"])
        if (
            not support
            or support - set(patch["training_groups"])
            or support & set(patch["excluded_groups"])
        ):
            raise ValueError("R6_RULE_SUPPORT_NOT_TRAIN_ONLY")


def apply_inputs(example, units, patch):
    check_patch(patch)
    original = copy.deepcopy(example)
    result = copy.deepcopy(example)
    rules = {r["normalized_span"]: r for r in patch["rules"]}
    traces = []
    for _, role, unit in input_units([example], units, {example["group_id"]}):
        concepts = set(example[role])
        for span in extract_spans(unit):
            rule = rules.get(span["normalized_span"])
            if rule is None or not span["positive_mapping_allowed"]:
                continue
            added = sorted(set(rule["concepts"]) - concepts)
            concepts.update(rule["concepts"])
            traces.append(
                {
                    **span,
                    "role": role,
                    "rule_id": rule["rule_id"],
                    "concepts": rule["concepts"],
                    "added_concepts": added,
                    "status": "SOURCE_CHECKED",
                    "human_approval": "NOT_REVIEWED_BY_HUMAN",
                    "rule_basis": rule["basis"],
                }
            )
        result[role] = sorted(concepts)
    result["mapping_patch_sha256"] = patch["patch_sha256"]
    result["mapping_input_trace"] = traces
    protected = lambda row: {
        k: v
        for k, v in row.items()
        if k not in {"A", "B", "mapping_patch_sha256", "mapping_input_trace"}
    }
    if digest(protected(result)) != digest(protected(original)):
        raise ValueError("R6_EVALUATION_TARGET_OR_ROLE_CHANGED")
    return result


def audit_inputs(examples, units):
    """Descriptive A/B loss audit only; no independent T inspected or scored."""
    groups = {e["group_id"] for e in examples}
    patch = fit_patch(examples, units, groups)
    reviewed = {r["normalized_span"]: r for r in reviewed_rules()}
    base_lexical = source.legacy.fixed_terms()
    unresolved, counts = [], Counter()
    for example, role, unit in input_units(examples, units, groups):
        for span in extract_spans(unit):
            if (
                span["normalized_span"] not in reviewed
                or not span["positive_mapping_allowed"]
            ):
                reason = source.diagnostic_unmapped_reason(span["normalized_span"])
                if (
                    base_lexical.get(span["normalized_span"])
                    in unit["strict_D0_concepts"]
                ):
                    reason = "BASE_ALREADY_REGISTERED_NOT_PATCHED"
                if span["normalized_span"] == "tropical":
                    reason = "AMBIGUOUS_MODIFIER_WITHOUT_NAMED_CORE_NOT_MAPPED"
                if not span["positive_mapping_allowed"]:
                    reason = (
                        span["polarity"]
                        if span["polarity"] != "POSITIVE_MENTION"
                        else span["compound_status"]
                    )
                counts[reason] += 1
                unresolved.append(
                    {
                        **span,
                        "group_id": example["group_id"],
                        "record_id": example["record_id"],
                        "role": role,
                        "review_disposition": reason,
                    }
                )
    applied = [apply_inputs(e, units, patch) for e in examples]
    changes = [
        {
            "record_id": old["record_id"],
            "group_id": old["group_id"],
            "A_added": sorted(set(new["A"]) - set(old["A"])),
            "B_added": sorted(set(new["B"]) - set(old["B"])),
        }
        for old, new in zip(examples, applied, strict=True)
    ]
    summary = {
        "version": VERSION,
        "protocol_sha256": digest(protocol()),
        "reviewed_forms": len(reviewed),
        "all_development_supported_forms": len(patch["rules"]),
        "source_records": len(examples),
        "coffee_groups": len(groups),
        "input_units": patch["inspected_input_units"],
        "changed_A_records": sum(bool(c["A_added"]) for c in changes),
        "changed_B_records": sum(bool(c["B_added"]) for c in changes),
        "changed_coffee_groups": len(
            {c["group_id"] for c in changes if c["A_added"] or c["B_added"]}
        ),
        "unresolved_or_nonpatch_span_counts": dict(counts),
        "evaluation_T_edits": 0,
        "model_fit_count": 0,
        "scope": "All-development A/B mapping inventory only; main comparisons must regenerate fold-specific patch from training groups; no outcome comparison",
        "human_semantic_review": "NOT_EVALUATED",
        "source_rights": protocol()["source_rights"],
    }
    return {
        "summary": summary,
        "all_development_patch_not_outer_patch": patch,
        "input_changes": changes,
        "unresolved_spans": unresolved,
    }


def write_public_table(path, supported_forms=()):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    supported_forms = set(supported_forms)
    columns = [
        "rule_id",
        "normalized_span",
        "concepts",
        "status",
        "human_approval",
        "relation",
        "scope",
        "activation",
        "all_development_input_support",
        "basis",
        "lexical_reference_url",
    ]
    with path.open("w") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for rule in reviewed_rules():
            row = {
                **rule,
                "activation": "REQUIRES_THIS_FOLD_TRAIN_AB_SUPPORT",
                "all_development_input_support": (
                    "SUPPORTED_INPUT_ONLY_NOT_EVALUATED"
                    if rule["normalized_span"] in supported_forms
                    else "NOT_APPLIED_NO_NEW_INPUT_SUPPORT"
                ),
            }
            writer.writerow(
                {
                    k: (
                        "|".join(row[k])
                        if isinstance(row[k], list)
                        else row.get(k) or ""
                    )
                    for k in columns
                }
            )


def run(owner):
    examples, units = load_inputs(owner)
    value = audit_inputs(examples, units)
    private = Path(owner) / "revisions/r6"
    private.mkdir(parents=True, exist_ok=True)
    path = private / "semantic_input_audit.private.json"
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError("R6_EXISTING_SEMANTIC_AUDIT_CHANGED")
    else:
        path.write_text(
            json.dumps(
                value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False
            )
            + "\n"
        )
        path.chmod(0o600)
    write_public_table(
        ROOT / "db/data/backend-sequential-model-v2/revisions/r6/semantic_patch.tsv",
        [
            r["normalized_span"]
            for r in value["all_development_patch_not_outer_patch"]["rules"]
        ],
    )
    return {
        **value["summary"],
        "audit_owner_relative_path": str(path.relative_to(Path(owner))),
        "audit_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run(Path(args.owner_dir)), sort_keys=True, indent=2))
