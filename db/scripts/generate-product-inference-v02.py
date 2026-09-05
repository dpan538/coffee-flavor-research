#!/usr/bin/env python3
"""Build v0.2 research catalog from frozen v0.1 inputs and proposed wording.

No corpus generation, source acquisition, statistical fitting or model training.
"""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "db/data/product-inference-v0"
OUT = ROOT / "db/data/product-inference-v0.2"


def rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def json_file(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def table(name, records, fields=None):
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fields or list(records[0]),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(records)


def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location("frozen_policy",ROOT/"db/scripts/generate-product-inference-v0.py")
    old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    wording={r["canonical_concept_id"]:r for r in rows(OUT/"PRODUCT_USER_EXPLANATION.tsv")}
    candidates=[]
    for r in rows(OLD/"PRODUCT_CONCEPT_CANDIDATE.tsv"):
        w=wording[r["canonical_concept_id"]]
        candidates.append(dict(id=r["canonical_concept_id"],label=w["RESULT_LABEL"],explanation=w["RESULT_EXPLANATION"],
            questionLanguage=w["QUESTION_LANGUAGE"],professionalLabel=w["PROFESSIONAL_CONCEPT_LABEL"],
            baseScore=float(r["base_decision_score"]),rightsEligible=r["public_research_simulation_rights_eligible"]=="true",
            directSupport=int(r["direct_professional_assertion_support"]),governedSupport=int(r["governed_normalization_support"])+int(r["governed_semantic_relation_support"]),
            reviewOnly=False,unresolved=False,redundancyGroup=r["redundancy_group"],lineage=r["lineage_paths"],wordingStatus=w["wording_status"]))
    labels={
      "fruit_region":("水果的感觉更接近哪些例子？",{"citrus":"柠檬、橙这类水果","berry":"蓝莓这类小浆果"}),
      "browned_sweet_reference":("下面哪些香气让你有相似的联想？",{"caramel_honey":"蜂蜜，或糖加热后的香气","brown_sugar":"红糖的浓厚甜香","nuts":"杏仁、榛子这类坚果","dark_chocolate":"甜味较少的黑巧克力"}),
      "floral_tea_reference":("再想想香气，下面哪些例子比较接近？",{"white_floral":"茉莉这类轻柔花香","rose_floral":"玫瑰花的香气","citrus_blossom":"柑橘树开花时的花香","tea":"泡开绿茶后的香气"}),
      "roast_smoke_reference":("这些香气中，哪些让你有联想？",{"warming_spice":"肉桂这类温暖香料","smoke":"木柴燃烧留下的烟气","wood_tobacco":"干木头，或干烟叶的香气"}),
      "fermentation_character":("下面哪些气味联想比较接近？",{"earthy":"雨后泥土的气味","fermented":"熟透水果带一点发酵的气味","winey":"葡萄酒的果香和发酵香"}),
      "acidity_character":("水果的联想更像哪些例子？",{"citrus_like":"柠檬、橙这类水果","berry_like":"蓝莓这类小浆果"}),
    }
    axes=rows(OLD/"PRODUCT_QUESTION_AXIS.tsv")
    questions=[]
    for a in axes:
        axis=a["question_axis_id"]
        if axis not in labels: continue
        prompt, names=labels[axis]
        partitions=json.loads(a["candidate_partitions_json"])
        questions.append(dict(id=axis,semanticKey="fruit-region" if axis in ("fruit_region","acidity_character") else axis,
            prompt=prompt,options=[dict(id=o,label=names[o],examples="",conceptIds=ids) for o,ids in partitions.items()],
            variants=["A","B"],governed=a["offline_simulation_eligible"]=="true",lineage=a["lineage_paths"],
            evidenceStatus="GOVERNED_AXIS_FORMATIVE_WORDING_NOT_USER_VALIDATED"))
    family=json.loads(axes[0]["candidate_partitions_json"])
    option=lambda oid,label,examples,ids:dict(id=oid,label=label,examples=examples,conceptIds=ids)
    common=[
      option("sweet_nut_cocoa","甜香、坚果或巧克力","例如蜂蜜、焦糖、杏仁、巧克力",family["cocoa_nut_caramel"]),
      option("roast_spice_ferment","烘烤、香料或发酵","例如肉桂、烟熏、酒香、土壤感",family["roast_spice_smoke"]+family["earthy_fermented"]),
    ]
    for variant,options in [
      ("A",[option("fruit","水果","例如柠檬、橙、莓果",family["fruit"]),option("floral_tea","花香或茶","例如茉莉、轻柔花香、绿茶",family["floral_tea"]),*common]),
      ("B",[option("fruit_flower","像水果或花","也可以包含茶的香气",family["fruit"]+family["floral_tea"]),
            {**common[0],"label":"像糖、坚果或巧克力"},{**common[1],"label":"像烘烤、香料或发酵"}]),
    ]:
        questions.append(dict(id=f"direction_{variant}",semanticKey="family-direction",prompt="这杯咖啡最先让你想到哪些方向？",options=options,
                              variants=[variant],governed=True,lineage=axes[0]["lineage_paths"],evidenceStatus="GOVERNED_PARENT_AXIS_RESEARCH_RECOMBINATION"))
    questions.append(dict(id="fruit_flower_branch",semanticKey="fruit-flower-branch",prompt="再分开想想，哪些例子比较接近？",
        options=[option("fruit","柠檬、橙或蓝莓的果香","",family["fruit"]),
                 option("flower","茉莉、玫瑰这类花香","",[c for c in family["floral_tea"] if c!="sensory.green_tea"]),
                 option("tea","泡开绿茶后的香气","",["sensory.green_tea"])],
        variants=["B"],governed=True,lineage=axes[0]["lineage_paths"],evidenceStatus="GOVERNED_PARENT_AXIS_RESEARCH_RECOMBINATION"))
    preparations=[]
    cn=[("手冲 / 滴滤","V60、滤杯、滴滤机；水流过咖啡粉"),("浸泡","法压壶、杯测；咖啡粉先浸在水里"),
        ("手压 / 混合","AeroPress 等手压器具"),("浓缩","Espresso；这里不包括摩卡壶"),("浓缩加水","美式、Long Black"),
        ("炉煮 / 摩卡壶","Moka、土耳其咖啡；使用炉上器具"),("冷萃","Cold Brew；冷水或室温长时间浸泡"),("奶咖","拿铁、Flat White、卡布奇诺")]
    for (pid,_,_), (label,examples) in zip(old.PREPARATIONS,cn):
        preparations.append(dict(id=pid,label=label,examples=examples))
    roasts=[dict(id=r[0],label=label,ordinal=r[2]) for r,label in zip(old.ROASTS,["极浅","浅","中浅","中","中深","深","极深"])]
    priors=[dict(preparation=r["preparation_family_key"],conceptId=r["canonical_concept_id"],adjustment=float(r["c0_prior_adjustment"]),lineage=r["c0_evidence_locator"])
            for r in rows(OLD/"PRODUCT_CONTEXT_PRIOR.tsv") if r["roast_code"]=="medium" and float(r["c0_prior_adjustment"])!=0]
    catalog=dict(version="product-inference-v0.2",candidates=candidates,questions=questions,preparations=preparations,roasts=roasts,c0Priors=priors,
                 policy=dict(positive=3,boundedNone=-1.25,headlineMax=3,expandedMainMax=2,explorationMax=3,ordinaryMax=4,recoveryMax=5,
                             mainDirectSupportMin=1,c1Prior=0,forceFill=False,trainingAuthorized=False,productionAuthorized=False))
    json_file("PRODUCT_RUNTIME_CATALOG.json",catalog)
    table("PRODUCT_LANGUAGE_VARIANT.tsv",[dict(variant_id=v,question_id=q["id"],option_id=o["id"],question_language=q["prompt"],option_language=o["label"],examples=o["examples"],concept_ids="|".join(o["conceptIds"]),semantic_key=q["semanticKey"],wording_status="FORMATIVE_WORDING_NOT_USER_VALIDATED",lineage=q["lineage"]) for q in questions for v in q["variants"] for o in q["options"]])
    json_file("PRODUCT_MULTISELECT_CONTRACT.json",dict(selected="supports_once_per_concept_per_question",unselected="neutral",hard_maximum=None,
        instruction="选择所有明显符合的项目，通常 1–2 项就够了。",all_selected_is_not_conflict=True,
        instrument=["selected_option_count","all_options_selected","average_selected_count","candidate_reduction","remaining_eligible_axes"],weight_status="UNCALIBRATED_RESEARCH_HEURISTIC_OWNER_REVIEW_PENDING"))
    table("PRODUCT_NO_ANSWER_STATE.tsv",[
        dict(state="UNSURE",label="不确定",meaning="可能感觉到了，但分不清",adjustment="0",scope="neutral"),
        dict(state="NONE_OF_THESE",label="都不像",meaning="当前显示的这些例子都不像",adjustment="-1.25",scope="union_of_explicitly_displayed_option_concepts_only; heuristic_not_sensory_ground_truth"),
        dict(state="SKIP",label="跳过",meaning="不想回答或暂时无法判断",adjustment="0",scope="neutral"),
    ])
    table("PRODUCT_QUESTION_FLOW.tsv",[
        dict(position="Q1",eligibility="mandatory typed response before results",selection="assigned A/B family direction",stop="no result while unanswered"),
        dict(position="Q2-Q4",eligibility="governed; at least two live partitions; nonzero separation; changes possible visible output; semantic key not used",selection="B fruit/flower branch first when supported; otherwise maximum deterministic separation",stop="at least two responses and three headline results; or no useful axis; or open/conflict state; or participant opts to see partial result"),
        dict(position="Q5",eligibility="four prior questions; fewer than three headlines; material eligible axis; no open/conflict state; explicit opt-in",selection="same eligibility tests as ordinary path",stop="absolute five-question limit"),
    ])
    table("PRODUCT_RESULT_PRESENTATION.tsv",[dict(tier=t,maximum=m,label=l,rule=r) for t,m,l,r in [
        ("HEADLINE",3,"目前最明确","positive explicit support, direct and governed support, rights eligible, resolved; deduplicate"),
        ("EXPANDED_MAIN",2,"其他有支持的联想","same eligibility as headlines; initially collapsed"),
        ("EXPLORE",3,"还可以继续留意","remaining supported eligible candidates, or review-only support; never independently headline"),
    ]])
    table("PRODUCT_RECOVERY_POLICY.tsv",[dict(rule_id="RECOVERY01",trigger="ordinary flow completed four questions and headlines <3",gate="material separating governed unused axis; no open/conflict state",primary_action="再回答一题，让结果更具体",secondary_action="先看当前结果",force_fill="false",requires_explicit_acceptance="true")])
    # JSON Schema describes the actual local export. Runtime validator adds relational checks.
    scalar={"type":"integer","minimum":0}
    event=dict(type="object",additionalProperties=False,required=["questionId","semanticKey","optionIdsShown","selectedOptionIds","responseState","responseTimeMs","candidateIdsBefore","candidateIdsAfter","candidateCountBefore","candidateCountAfter","selectedOptionCount","allOptionsSelected","remainingEligibleAxes","selectionReason"],properties={
      "questionId":{"type":"string"},"semanticKey":{"type":"string"},"optionIdsShown":{"type":"array","items":{"type":"string"},"uniqueItems":True},
      "selectedOptionIds":{"type":"array","items":{"type":"string"},"uniqueItems":True},"responseState":{"enum":["SELECTED","UNSURE","NONE_OF_THESE","SKIP"]},
      "responseTimeMs":scalar,"candidateIdsBefore":{"type":"array","items":{"type":"string"}},"candidateIdsAfter":{"type":"array","items":{"type":"string"}},
      "candidateCountBefore":scalar,"candidateCountAfter":scalar,"selectedOptionCount":scalar,"allOptionsSelected":{"type":"boolean"},
      "remainingEligibleAxes":{"type":"array","items":{"type":"string"}},"selectionReason":{"type":"string"}})
    props={"version":{"const":"product-inference-v0.2"},"sessionId":{"type":"string","format":"uuid"},"participantResearchId":{"type":"string","pattern":"^R3O-[0-9]{3}$"},
           "coffeeExposureStratum":{"enum":["novice","regular","experienced"]},"languageVariant":{"enum":["A","B"]},
           "c0Selection":{"enum":[p["id"] for p in preparations]},"c0SelectionTimeMs":scalar,"c1Selection":{"enum":[r["id"] for r in roasts]+[None]},"c1Unsure":{"type":"boolean"},"c1SelectionTimeMs":scalar,
           "questions":{"type":"array","items":event,"minItems":1,"maxItems":5},"totalQuestionCount":scalar,"averageSelectedCount":{"type":"number","minimum":0},
           "q5Offered":{"type":"boolean"},"q5Accepted":{"type":"boolean"},"headlineResultCount":{**scalar,"maximum":3},"expandedMainCount":{**scalar,"maximum":2},"explorationCount":{**scalar,"maximum":3},
           "expandClicked":{"type":"boolean"},"extraQuestionClicked":{"type":"boolean"},"resultHelpfulness":{"type":"integer","minimum":1,"maximum":5},
           "valuePropositionParaphraseResult":{"enum":["correct","partial","incorrect","not_assessed"]},"completionTimeMs":scalar,
           "earlyStopReason":{"type":"string"},"q5TriggerReason":{"type":"string"},"openSet":{"type":"boolean"},"resultState":{"type":"string"},
           "postTask":{"type":"object","additionalProperties":False,"required":["firstQuestionComprehension","partialOutputAcceptance","reuseIntent","completedWithoutHelp","difficulty"],"properties":{
              "firstQuestionComprehension":{"enum":["clear","partial","unclear"]},"partialOutputAcceptance":{"enum":["accept","unsure","reject","not_applicable"]},
              "reuseIntent":{"enum":["yes","maybe","no"]},"completedWithoutHelp":{"type":"boolean"},"difficulty":{"enum":["none","context","wording","choices","results"]}}}}
    json_file("PRODUCT_RESEARCH_EVENT_SCHEMA.json",{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","additionalProperties":False,"required":list(props),"properties":props})
    inputs=[*sorted(OLD.glob("*")),OUT/"PRODUCT_USER_EXPLANATION.tsv"]
    json_file("PRODUCT_INFERENCE_V0_2_MANIFEST.json",dict(version="product-inference-v0.2",generated_at="2026-09-05T00:00:00Z",status="FORMATIVE_WORDING_NOT_USER_VALIDATED",
        candidate_count=len(candidates),language_variant_count=2,c0_family_count=len(preparations),c1_level_count=len(roasts),context_cell_count=len(preparations)*len(roasts),
        c1_unsure_counts_as_level=False,frozen_parent="product-inference-v0",parent_policy_unchanged=True,governance_axis_count=len(axes),
        research_harness_only=True,training_authorized=False,training_run_count=0,production_deployment_authorized=False,
        agent_majority_auto_approval=False,final_human_decision_required=True,
        policy_delta="Multi-select positive union; typed neutral/closed-none states; semantic redundancy guard; visible-output separation; max 3+2+3; explicit Q5; no weight fitting",
        professional_definition_imports=0,external_assets_added=0,
        authoritative_input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs if p.is_file()}))
    print("GENERATED_PRODUCT_CATALOG",len(candidates),len(questions))


if __name__=="__main__": generate()
