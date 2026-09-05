"""Source-native numerical context models; production mappings remain explicit."""

from __future__ import annotations
import math
import numpy as np
from sklearn.linear_model import Ridge
from flavor_backend import C0, C1, validate_context

CONTEXT_VERSION = "context.v2.source-native-separated"
VARIANTS = ["C_BASE", "C_C0", "C_C1", "C_ADD", "C_JOINT"]
NATIVE_ROASTS = ["light", "medium", "dark"]


def encode_context(context, variant, scope="PRODUCTION"):
    if variant not in VARIANTS:
        raise ValueError("Unknown context model")
    if scope == "PRODUCTION":
        validate_context(context)
        c0 = context["c0"]
        roast = None
    elif scope == "SOURCE_NATIVE":
        c0 = context.get("c0")
        roast = context.get("source_roast")
        if c0 is not None and c0 not in C0:
            raise ValueError("Invalid source C0 mapping")
        if roast is not None and roast not in NATIVE_ROASTS:
            raise ValueError("Unreviewed source roast encoding")
    else:
        raise ValueError("Unknown context encoding scope")
    a = [float(c0 == x) if variant in {"C_C0", "C_ADD", "C_JOINT"} else 0.0 for x in C0]
    b = [
        float(roast == x) if variant in {"C_C1", "C_ADD", "C_JOINT"} else 0.0
        for x in NATIVE_ROASTS
    ]
    # Strong fixed shrinkage of interaction columns; categorical, never C0 distance.
    cross = [0.25 * x * y if variant == "C_JOINT" else 0.0 for x in a for y in b]
    return a + b + cross


def fit_context(rows, variant, alpha=1.0):
    y = np.array([r["targets"] for r in rows], float)
    mean = y.mean(0)
    scale = y.std(0)
    scale[scale < 1e-12] = 1.0
    X = np.array([encode_context(r, variant, "SOURCE_NATIVE") for r in rows])
    clf = Ridge(alpha=alpha).fit(X, (y - mean) / scale)
    return {
        "context_mapping_version": CONTEXT_VERSION,
        "variant": variant,
        "scope": "SOURCE_NATIVE_AUXILIARY",
        "target_names": rows[0]["target_names"],
        "units": rows[0]["units"],
        "scaler_parameters": {"mean": mean.tolist(), "scale": scale.tolist()},
        "coefficients": clf.coef_.tolist(),
        "intercepts": np.atleast_1d(clf.intercept_).tolist(),
        "alpha": alpha,
        "supported_c0": sorted({r["c0"] for r in rows if r["c0"]}),
        "source_roast_categories": sorted(
            {r["source_roast"] for r in rows if r["source_roast"]}
        ),
        "production_seven_bin_C1_mapping": None,
    }


def predict_context(context, model, scope="SOURCE_NATIVE"):
    if model["context_mapping_version"] != CONTEXT_VERSION:
        raise ValueError("CONTEXT_VERSION_MISMATCH")
    if scope == "PRODUCTION" and model["variant"] not in {"C_BASE", "C_C0"}:
        raise ValueError("NO_VALIDATED_SEVEN_BIN_SOURCE_MAPPING")
    x = np.array(encode_context(context, model["variant"], scope))
    z = np.array(model["coefficients"]) @ x + np.array(model["intercepts"])
    s = model["scaler_parameters"]
    return (z * np.array(s["scale"]) + np.array(s["mean"])).tolist()


def estimate_context_attributes(context, models):
    validate_context(context)
    out = {}
    for source, model in models.items():
        supported = context["c0"] in model["supported_c0"]
        out[source] = {
            "values": (
                predict_context(context, model, "PRODUCTION") if supported else None
            ),
            "target_names": model["target_names"],
            "units": model["units"],
            "supported": supported,
            "basis": "PREDICTED_FROM_C0_ONLY; no lab truth or source-native C1 supplied at runtime",
            "effect_scope": "Source-specific aggregate prediction, not descriptor confirmation",
        }
    return out
