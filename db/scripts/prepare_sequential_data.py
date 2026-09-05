"""Versioned v2 input parsing; preserve source identity, native categories and units."""

from __future__ import annotations
import csv, hashlib, json, re
from collections import defaultdict
from pathlib import Path
from lxml import etree, html
from flavor_backend import C0

ROOT = Path(__file__).resolve().parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, x):
    p.write_text(json.dumps(x, sort_keys=True, ensure_ascii=False, indent=2) + "\n")


def tsv(p):
    return list(csv.DictReader(p.open(), delimiter="\t"))


def grid(table):
    result = []
    pending = {}
    for row in table.xpath(".//tr"):
        cells = {}
        nxt = {}
        for i, (value, remaining) in pending.items():
            cells[i] = value
            if remaining > 1:
                nxt[i] = (value, remaining - 1)
        col = 0
        for cell in row.xpath("./th|./td"):
            while col in cells:
                col += 1
            value = " ".join(" ".join(cell.xpath(".//text()")).split())
            rs = int(cell.get("rowspan", "1"))
            cs = int(cell.get("colspan", "1"))
            for j in range(cs):
                cells[col + j] = value
                if rs > 1:
                    nxt[col + j] = (value, rs - 1)
            col += cs
        result.append([cells.get(i, "") for i in range(max(cells, default=-1) + 1)])
        pending = nxt
    return result


def number(s):
    found = re.match(r"\s*([-+]?\d+(?:\.\d+)?)", s)
    if not found:
        raise ValueError("Cannot transcribe number: " + s)
    return float(found[1])


def wide(records, dataset, role, effect):
    groups = defaultdict(dict)
    meta = {}
    names = sorted({r["target"] for r in records})
    for r in records:
        k = (r["coffee"], r["preparation"], r["source_roast"])
        groups[k][r["target"]] = r["value"]
        meta[k] = r
    output = []
    for k, y in groups.items():
        if set(y) != set(names):
            continue
        r = meta[k]
        units = {x["target"]: x["unit"] for x in records}
        output.append(
            {
                "dataset": dataset,
                "group_id": dataset + ":" + r["coffee"],
                "condition_id": dataset + ":" + ":".join(str(v) for v in k),
                "coffee_id": r["coffee"],
                "c0": r["c0"],
                "source_roast": r["source_roast"],
                "source_preparation": r["preparation"],
                "targets": [y[n] for n in names],
                "target_names": names,
                "units": [units[n] for n in names],
                "role": role,
                "effect_type": effect,
                "observation_unit": "AGGREGATE_ONLY",
                "source_rows": [
                    x
                    for x in records
                    if (x["coffee"], x["preparation"], x["source_roast"]) == k
                ],
            }
        )
    return output


def numerical(owner):
    cache = owner / "sources"
    sources = []
    datasets = {}
    path = cache / "iswaldi.html"
    doc = html.parse(str(path))
    assert "https://creativecommons.org/licenses/by/4.0/" in doc.xpath("//a/@href")
    rows = []
    for r in grid(doc.xpath("//table")[1])[2:]:
        assert len(r) == 5, r
        for i, origin in enumerate(["gayo", "flores_bajawa"]):
            rows.append(
                {
                    "coffee": origin,
                    "preparation": r[2].lower().replace(" ", "_"),
                    "source_roast": r[1],
                    "c0": C0[0] if r[2] == "V60" else C0[6],
                    "target": r[0],
                    "unit": r[0][r[0].find("(") + 1 : r[0].rfind(")")],
                    "value": number(r[3 + i]),
                    "source_value_with_error": r[3 + i],
                    "method": "Table 2 published chemical/antioxidant mean; exact original unit retained",
                    "replication": "Published aggregate, not reconstructed technical or consumer rows",
                }
            )
    datasets["iswaldi_chemical"] = wide(
        rows, "iswaldi_chemical", "AUX_CONTEXT", "PHYSICOCHEMICAL_EFFECT"
    )
    native = tsv(
        ROOT / "db/data/round3h/batch1/iswaldi_2026_table3_sensory_aggregates.tsv"
    )
    rows = []
    for r in native:
        if r["sensory_attribute"] == "liking":
            continue
        rows.append(
            {
                "coffee": r["coffee_origin"],
                "preparation": r["preparation"],
                "source_roast": r["roast_source_label"],
                "c0": C0[0] if r["preparation"] == "v60" else C0[6],
                "target": r["sensory_attribute"],
                "unit": r["source_unit"],
                "value": float(r["parsed_mean"]),
                "source_value_with_error": r["raw_value"],
                "method": "Table 3 RATA consumer aggregate; 50 consumers are not 50 coffees",
                "replication": "AGGREGATE_ONLY",
            }
        )
    datasets["iswaldi_consumer_sensory"] = wide(
        rows,
        "iswaldi_consumer_sensory",
        "AUX_COFFEE_WEAK_LABEL",
        "SENSORY_ATTRIBUTE_EFFECT",
    )
    sources.append(
        {
            "id": "iswaldi",
            "url": "https://doi.org/10.1590/1981-6723.1062025",
            "artifact_sha256": sha(path),
            "license": "CC BY 4.0",
            "author": "Ihsan Iswaldi et al.",
            "version": "2026 article",
            "conditions_satisfied": True,
            "modification": "Tables transcribed to numeric aggregate matrices; unit/scales unaltered. Consumer data not promoted to trained-panel evidence.",
            "context_mapping": "V60=filter_percolation; cold brew=cold_extraction from methods; roast light/medium/dark remain source-native (205C/8min,220C/10min,230C/13min), not seven bins",
            "design": "2 origin/coffee groups × 3 roast treatments × 2 methods; origin IDs are grouping only; no reconstructed person-level rows",
            "total_vs_conditional": "Total recipe/treatment associations; no row-level mediator-adjusted effect estimable",
        }
    )
    path = cache / "stanek.xml"
    doc = etree.parse(str(path))
    assert "https://creativecommons.org/licenses/by/4.0/" in doc.xpath(
        '//@*[contains(.,"creativecommons")]'
    )
    rows = []
    table = doc.xpath('//table-wrap[@id="Tab1"]/table')[0]
    expanded = grid(table)
    coffees = expanded[0][-6:]
    for r in expanded[1:]:
        assert len(r) == 8, r
        for i, c in enumerate(coffees):
            rows.append(
                {
                    "coffee": c,
                    "preparation": r[1],
                    "source_roast": None,
                    "c0": C0[0] if r[1] == "P" else C0[6],
                    "target": r[0],
                    "unit": "mg/100 g (source coffee-brew report basis)",
                    "value": number(r[i + 2]),
                    "source_value_with_error": r[i + 2],
                    "method": "HPLC Table 1; published means/errors; CB and HT both cold-extraction family but distinct protocols retained",
                    "replication": "Six coffee/lot IDs, never chromatographic duplicates",
                }
            )
    datasets["stanek_chemical"] = wide(
        rows, "stanek_chemical", "AUX_CONTEXT", "PHYSICOCHEMICAL_EFFECT"
    )
    sources.append(
        {
            "id": "stanek",
            "url": "https://doi.org/10.1038/s41598-021-01001-2",
            "artifact_sha256": sha(path),
            "license": "CC BY 4.0",
            "author": "Natalia Stanek et al.",
            "version": "2021-11-01 article",
            "conditions_satisfied": True,
            "modification": "HPLC Table 1 transcribed, uncertainty strings and units retained; six original coffee groups",
            "context_mapping": "P=source-described hot filter; CB and HT=cold_extraction. Specific cold protocols remain distinct metadata. Roast contrast absent: no C1 labels inferred.",
            "total_vs_conditional": "Published protocol targets constant TDS; context contrast is under that design condition. No measured mediator row matrix to estimate an additional adjustment. Not a pure universal brew-method causal coefficient.",
        }
    )
    path = cache / "vezzulli.xml"
    doc = etree.parse(str(path))
    assert "https://creativecommons.org/licenses/by/4.0/" in doc.xpath(
        '//@*[contains(.,"creativecommons")]'
    )
    rows = []
    for r in tsv(
        ROOT / "db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv"
    ):
        mapping = {
            "moka": C0[5],
            "neapolitan_pot": C0[0],
            "espresso": C0[3],
            "filter": C0[0],
        }
        assert r["preparation"] in mapping, r["preparation"]
        rows.append(
            {
                "coffee": r["coffee_species"],
                "preparation": r["preparation"],
                "source_roast": None,
                "c0": mapping[r["preparation"]],
                "target": r["source_descriptor"],
                "unit": r["source_unit"],
                "value": float(r["parsed_value"]),
                "source_value_with_error": r["raw_value"],
                "method": "Trained-panel published median, source descriptor kept whole",
                "replication": "Two coffee/species samples × four methods; six panelists not independent coffees",
            }
        )
    datasets["vezzulli_panel"] = wide(
        rows, "vezzulli_panel", "CORE_PROFESSIONAL", "SENSORY_ATTRIBUTE_EFFECT"
    )
    sources.append(
        {
            "id": "vezzulli",
            "url": "https://doi.org/10.3390/foods11060807",
            "artifact_sha256": sha(path),
            "license": "CC BY 4.0",
            "author": "Fosca Vezzulli et al. (full author list in retained source)",
            "version": "2022 article",
            "conditions_satisfied": True,
            "modification": "Published panel medians; no copied WCR definitions or inferred child labels",
            "context_mapping": "Moka=stovetop; espresso=espresso_pressure; gravity Neapolitan/filter=filter_percolation. No source roast variation encoded.",
            "total_vs_conditional": "Total source-protocol association; dose/strength differ, no unconfounded mediator decomposition.",
        }
    )
    result = {
        "datasets": datasets,
        "sources": sources,
        "not_estimable": {
            "production_seven_level_C1": "No reviewed mapping from numeric source roasting protocols to all seven production bins",
            "all_56_cells": "No 56-cell empirical coverage claimed",
            "liang_raw": "Dryad response explicitly says identifier cannot be viewed; do not infer permission/access from HTTP 200",
            "row_level_context_supervision": "These context sources provide aggregates, not independently reconstructed panel rows",
        },
    }
    save(owner / "numeric_context_records.json", result)
    (owner / "numeric_context_records.json").chmod(0o600)
    return result
