# Product-task review packet v0.2

These are proposed deterministic outputs, not human-approved answers. Use the owner or agent TSV template to record decisions. Engine policy fixtures are not claimed to be live participant flows.

## PT001 · clear_headline

Concrete sweet/nut/cocoa direction followed by a separating question

Fixture: participant flow. Variant A. Questions: 2.

1. direction_A: SELECTED sweet_nut_cocoa
2. browned_sweet_reference: SELECTED brown_sugar, caramel_honey, dark_chocolate, nuts

Headline: 焦糖般的香气、蜂蜜般的香气、黑巧克力般的风味.

Expanded main: 杏仁般的风味.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 焦糖般的香气: 可把“焦糖香”作为参照；它不表示加了糖，也不等于烟熏味。
- 蜂蜜般的香气: 可把“蜂蜜香”作为参照；闻着甜不代表含糖量高，也不一定喝着甜。
- 黑巧克力般的风味: 可把“黑巧克力”作为参照；只有苦味，还不足以描述这种联想。
- 杏仁般的风味: 可把“杏仁”作为参照，看看是否贴近你的感觉；这个名称不表示添加了杏仁。

Owner decision: blank, pending review.

## PT002 · clear_headline

Multiple broad directions retain supported headline and expanded candidates

Fixture: participant flow. Variant A. Questions: 2.

1. direction_A: SELECTED fruit, sweet_nut_cocoa
2. browned_sweet_reference: SELECTED brown_sugar, caramel_honey, dark_chocolate, nuts

Headline: 焦糖般的香气、蜂蜜般的香气、黑巧克力般的风味.

Expanded main: 杏仁般的风味、橙子般的风味.

Explore: 蓝莓般的风味.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 焦糖般的香气: 可把“焦糖香”作为参照；它不表示加了糖，也不等于烟熏味。
- 蜂蜜般的香气: 可把“蜂蜜香”作为参照；闻着甜不代表含糖量高，也不一定喝着甜。
- 黑巧克力般的风味: 可把“黑巧克力”作为参照；只有苦味，还不足以描述这种联想。
- 杏仁般的风味: 可把“杏仁”作为参照，看看是否贴近你的感觉；这个名称不表示添加了杏仁。
- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT003 · variant_b

Progressive fruit/flower branch follows the assigned broad first question

Fixture: participant flow. Variant B. Questions: 2.

1. direction_B: SELECTED fruit_flower
2. fruit_flower_branch: SELECTED fruit, flower, tea

Headline: 茉莉花香、橙子般的风味、蓝莓般的风味.

Expanded main: 玫瑰花香、绿茶般的风味.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 茉莉花香: 可试着用“茉莉花香”描述这份花香；不需要同时有水果香或酸味。
- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。
- 玫瑰花香: 可试着用“玫瑰花香”描述这份花香，看看是否贴近你的感觉。
- 绿茶般的风味: 可把“绿茶”作为参照；如果只感觉像茶，也可以先保留“茶感”。

Owner decision: blank, pending review.

## PT004 · partial_output

Fruit/citrus aliases occupy one redundancy group

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: SELECTED fruit
2. fruit_region: SELECTED citrus

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT005 · partial_output

A single tea reference can produce fewer than three headlines

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: UNSURE 
2. floral_tea_reference: SELECTED tea

Headline: 绿茶般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 绿茶般的风味: 可把“绿茶”作为参照；如果只感觉像茶，也可以先保留“茶感”。

Owner decision: blank, pending review.

## PT006 · exploration_only

Review-only relations cannot independently produce headlines

Fixture: engine policy. Variant A. Questions: 1.

1. direction_A: SELECTED fruit

Headline: none.

Expanded main: none.

Explore: 橙子般的风味、蓝莓般的风味.

State: EXPLORATION_ONLY. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT007 · low_information

Four unsure answers preserve neutral scores and empty output

Fixture: participant flow. Variant A. Questions: 4.

1. direction_A: UNSURE 
2. floral_tea_reference: UNSURE 
3. roast_smoke_reference: UNSURE 
4. browned_sweet_reference: UNSURE 

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_INSUFFICIENT_EVIDENCE. Q5 offer: true.


Owner decision: blank, pending review.

## PT008 · extra_question

An unused separating fifth question may be offered after four neutral answers

Fixture: participant flow. Variant A. Questions: 4.

1. direction_A: UNSURE 
2. floral_tea_reference: UNSURE 
3. roast_smoke_reference: UNSURE 
4. browned_sweet_reference: UNSURE 

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_INSUFFICIENT_EVIDENCE. Q5 offer: true.


Owner decision: blank, pending review.

## PT009 · extra_question_accepted

Explicit recovery acceptance permits exactly one additional question

Fixture: participant flow. Variant A. Questions: 5.

1. direction_A: UNSURE 
2. floral_tea_reference: UNSURE 
3. roast_smoke_reference: UNSURE 
4. browned_sweet_reference: UNSURE 
5. fermentation_character: SELECTED earthy

Headline: 土壤感.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 土壤感: 可试着用“土壤感”描述泥土般的气味；它本身不能判断咖啡是否变质。

Owner decision: blank, pending review.

## PT010 · open_set

An explicit outside-vocabulary flag withholds claims and further recovery

Fixture: engine policy. Variant A. Questions: 1.

1. direction_A: SELECTED fruit

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_OPEN_SET. Q5 offer: false.


Owner decision: blank, pending review.

## PT011 · conflicting_answer

The later closed-none answer disputes every currently supported fruit reference

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: SELECTED fruit
2. fruit_region: NONE_OF_THESE 

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_CONFLICT. Q5 offer: false.


Owner decision: blank, pending review.

## PT012 · unsure

Mandatory Q1 has a typed unsure response without sensory adjustment

Fixture: participant flow. Variant A. Questions: 1.

1. direction_A: UNSURE 

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_INSUFFICIENT_EVIDENCE. Q5 offer: false.


Owner decision: blank, pending review.

## PT013 · unsure_after_support

Unsure does not erase earlier positive support

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: SELECTED fruit
2. fruit_region: UNSURE 

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT014 · none_of_these

A closed fruit list weakly affects only displayed fruit concepts

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: SELECTED fruit, floral_tea
2. fruit_region: NONE_OF_THESE 

Headline: 茉莉花香、玫瑰花香、绿茶般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 茉莉花香: 可试着用“茉莉花香”描述这份花香；不需要同时有水果香或酸味。
- 玫瑰花香: 可试着用“玫瑰花香”描述这份花香，看看是否贴近你的感觉。
- 绿茶般的风味: 可把“绿茶”作为参照；如果只感觉像茶，也可以先保留“茶感”。

Owner decision: blank, pending review.

## PT015 · skip

Skip is explicitly stored and leaves earlier scores unchanged

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: SELECTED fruit
2. fruit_region: SKIP 

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT016 · skip_low_information

Four skip responses remain distinguishable from unsure

Fixture: participant flow. Variant A. Questions: 4.

1. direction_A: SKIP 
2. floral_tea_reference: SKIP 
3. roast_smoke_reference: SKIP 
4. browned_sweet_reference: SKIP 

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_INSUFFICIENT_EVIDENCE. Q5 offer: true.


Owner decision: blank, pending review.

## PT017 · c0_weak_prior_override

Explicit sweet support survives a weak negative C0 adjustment

Fixture: participant flow. Variant A. Questions: 1.

1. direction_A: SELECTED sweet_nut_cocoa

Headline: 焦糖般的香气、黑巧克力般的风味、蜂蜜般的香气.

Expanded main: 杏仁般的风味.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 焦糖般的香气: 可把“焦糖香”作为参照；它不表示加了糖，也不等于烟熏味。
- 黑巧克力般的风味: 可把“黑巧克力”作为参照；只有苦味，还不足以描述这种联想。
- 蜂蜜般的香气: 可把“蜂蜜香”作为参照；闻着甜不代表含糖量高，也不一定喝着甜。
- 杏仁般的风味: 可把“杏仁”作为参照，看看是否贴近你的感觉；这个名称不表示添加了杏仁。

Owner decision: blank, pending review.

## PT018 · c0_missing

Missing C0 remains a neutral policy fixture

Fixture: engine policy. Variant A. Questions: 1.

1. direction_A: SELECTED fruit

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT019 · c1_neutral

A very light roast adds no roast evidence

Fixture: engine policy. Variant A. Questions: 1.

1. direction_A: SELECTED fruit

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT020 · c1_neutral

A very dark roast cannot be reverse-inferred from flavor

Fixture: engine policy. Variant A. Questions: 1.

1. direction_A: SELECTED fruit

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT021 · c1_unsure

Roast unsure is null and never an eighth level

Fixture: engine policy. Variant A. Questions: 1.

1. direction_A: SELECTED fruit

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT022 · redundancy

Selecting both fruit examples does not duplicate aliases or citrus concepts

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: SELECTED fruit
2. fruit_region: SELECTED citrus, berry

Headline: 橙子般的风味、蓝莓般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT023 · rights_blocked

Only rights-blocked orange-blossom support must abstain

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: UNSURE 
2. floral_tea_reference: SELECTED citrus_blossom

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_RIGHTS_BLOCKED. Q5 offer: false.


Owner decision: blank, pending review.

## PT024 · rights_mixed

Blocked concepts remain hidden when eligible concepts also have support

Fixture: participant flow. Variant A. Questions: 1.

1. direction_A: SELECTED fruit, floral_tea, sweet_nut_cocoa, roast_spice_ferment

Headline: 焦糖般的香气、蜂蜜般的香气、黑巧克力般的风味.

Expanded main: 茉莉花香、橙子般的风味.

Explore: 蓝莓般的风味、肉桂般的香气、杏仁般的风味.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 焦糖般的香气: 可把“焦糖香”作为参照；它不表示加了糖，也不等于烟熏味。
- 蜂蜜般的香气: 可把“蜂蜜香”作为参照；闻着甜不代表含糖量高，也不一定喝着甜。
- 黑巧克力般的风味: 可把“黑巧克力”作为参照；只有苦味，还不足以描述这种联想。
- 茉莉花香: 可试着用“茉莉花香”描述这份花香；不需要同时有水果香或酸味。
- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。
- 肉桂般的香气: 可把“肉桂香”作为参照，看看是否贴近你的感觉。
- 杏仁般的风味: 可把“杏仁”作为参照，看看是否贴近你的感觉；这个名称不表示添加了杏仁。

Owner decision: blank, pending review.

## PT025 · all_options_selected

Selecting every displayed option is recorded and is not a conflict

Fixture: participant flow. Variant A. Questions: 2.

1. direction_A: SELECTED fruit, floral_tea, sweet_nut_cocoa, roast_spice_ferment
2. floral_tea_reference: SELECTED citrus_blossom, rose_floral, tea, white_floral

Headline: 茉莉花香、玫瑰花香、绿茶般的风味.

Expanded main: 焦糖般的香气、蜂蜜般的香气.

Explore: 黑巧克力般的风味、橙子般的风味、蓝莓般的风味.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 茉莉花香: 可试着用“茉莉花香”描述这份花香；不需要同时有水果香或酸味。
- 玫瑰花香: 可试着用“玫瑰花香”描述这份花香，看看是否贴近你的感觉。
- 绿茶般的风味: 可把“绿茶”作为参照；如果只感觉像茶，也可以先保留“茶感”。
- 焦糖般的香气: 可把“焦糖香”作为参照；它不表示加了糖，也不等于烟熏味。
- 蜂蜜般的香气: 可把“蜂蜜香”作为参照；闻着甜不代表含糖量高，也不一定喝着甜。
- 黑巧克力般的风味: 可把“黑巧克力”作为参照；只有苦味，还不足以描述这种联想。
- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。
- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。

Owner decision: blank, pending review.

## PT026 · q1_mandatory

No sensory response must not yield output

Fixture: engine policy. Variant A. Questions: 0.


Headline: none.

Expanded main: none.

Explore: none.

State: NEEDS_MANDATORY_Q1. Q5 offer: false.


Owner decision: blank, pending review.

## PT027 · redundant_semantic_rejected

Fruit_region and acidity_character share a semantic distinction

Fixture: engine policy. Variant A. Questions: 2.

1. direction_A: SELECTED fruit
2. fruit_region: SELECTED berry

Headline: 蓝莓般的风味、橙子般的风味.

Expanded main: none.

Explore: none.

State: SUPPORTED_PARTIAL_OUTPUT. Q5 offer: false.

- 蓝莓般的风味: 可把“蓝莓”作为参照；如果你只感觉像某种莓果，也可以先保留宽泛说法。
- 橙子般的风味: 可把“橙子”作为参照，看看是否贴近你的感觉；它与橙花香分开描述。

Owner decision: blank, pending review.

## PT028 · q5_without_opt_in_rejected

Fifth-question acceptance is required, even when separation exists

Fixture: engine policy. Variant A. Questions: 4.

1. direction_A: UNSURE 
2. floral_tea_reference: UNSURE 
3. roast_smoke_reference: UNSURE 
4. browned_sweet_reference: UNSURE 

Headline: none.

Expanded main: none.

Explore: none.

State: ABSTAINED_INSUFFICIENT_EVIDENCE. Q5 offer: true.


Owner decision: blank, pending review.
