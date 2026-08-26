# Round 3J Regional User-Evidence Audit

Recorded: 2026-08-26

The six blocking regional candidate frames are audited and satisfy their source-frame thresholds. This is a candidate and rights/access audit only: no source was admitted, no user content was scraped, no post or comment was inspected or copied, no training-eligible evidence unit was created, and no prepared request was sent.

The original 17-candidate register, outcome ledger, four acquisition batches, and `CONDITION_B_MET_STOP_ACQUISITION` result remain unchanged. That stop result remains valid inside the original frame; only its global-exhaustion implication is superseded.

The `false` regional-completion values in the expected-state and stop-decision artifacts are the immutable pre-audit baseline committed before regional research. Actual post-audit observations are recorded separately in `db/data/round3j/regional_user_evidence_audit_result.tsv`; the baseline is not rewritten after seeing results.

## Machine receipt

```makefile
ORIGINAL_CANDIDATE_FRAME_COUNT=17
ORIGINAL_STOP_RULE_PRESERVED=true
ORIGINAL_STOP_RULE_GLOBAL_EFFECT_SUPERSEDED=true

CORE_REGION_COUNT=4
SECONDARY_REGION_COUNT=2

MAINLAND_CHINA_CANDIDATE_COUNT=8
MAINLAND_CHINA_SOURCE_FAMILY_COUNT=8
MAINLAND_CHINA_ADMITTED_SOURCE_COUNT=0

TAIWAN_CANDIDATE_COUNT=7
TAIWAN_SOURCE_FAMILY_COUNT=6
TAIWAN_ADMITTED_SOURCE_COUNT=0

AU_NZ_CANDIDATE_COUNT=7
AU_NZ_SOURCE_FAMILY_COUNT=5
AU_NZ_ADMITTED_SOURCE_COUNT=0

US_CANADA_CANDIDATE_COUNT=9
US_CANADA_SOURCE_FAMILY_COUNT=8
US_CANADA_ADMITTED_SOURCE_COUNT=0

JAPAN_CANDIDATE_COUNT=6
JAPAN_SOURCE_FAMILY_COUNT=6
JAPAN_ADMITTED_SOURCE_COUNT=0

SOUTH_KOREA_CANDIDATE_COUNT=6
SOUTH_KOREA_SOURCE_FAMILY_COUNT=6
SOUTH_KOREA_ADMITTED_SOURCE_COUNT=0

FORUM_OR_COMMUNITY_CANDIDATE_COUNT=13
AUTHORIZED_FORUM_SOURCE_COUNT=0
FORUM_PERMISSION_REQUEST_COUNT=13
BLOCKED_FORUM_SOURCE_COUNT=2

REGIONAL_SOURCE_FRAME_COMPLETE=true
REGIONAL_REPRESENTATIVENESS_CLAIM=false
GLOBAL_ACQUISITION_COMPLETE=false
```

## Regional frame results

### Mainland China

- Candidate count: 8
- Audited independent source-family count: 8
- Structured preference or sensory candidate count: 2
- Community candidate count: 3
- Industry or professional-language candidate count: 3
- Rights/access decision completeness: 1.0000
- Admitted source count: 0
- Candidate-family concentration: largest 0.1250; top three 0.3750; effective 8.0000
- Candidate-level modes: A=PRESENT; B=PRESENT; C=PRESENT; D=PRESENT
- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING

### Taiwan

- Candidate count: 7
- Audited independent source-family count: 6
- Structured preference or sensory candidate count: 4
- Community candidate count: 2
- Industry or professional-language candidate count: 2
- Rights/access decision completeness: 1.0000
- Admitted source count: 0
- Candidate-family concentration: largest 0.2857; top three 0.5714; effective 5.4444
- Candidate-level modes: A=PRESENT; B=PRESENT; C=PRESENT; D=PRESENT
- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING

### Australia / New Zealand

- Candidate count: 7
- Audited independent source-family count: 5
- Structured preference or sensory candidate count: 4
- Community candidate count: 1
- Industry or professional-language candidate count: 3
- Rights/access decision completeness: 1.0000
- Admitted source count: 0
- Candidate-family concentration: largest 0.2857; top three 0.7143; effective 4.4545
- Candidate-level modes: A=PRESENT; B=PRESENT; C=PRESENT; D=PRESENT
- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING

### United States / Canada

- Candidate count: 9
- Audited independent source-family count: 8
- Structured preference or sensory candidate count: 5
- Community candidate count: 3
- Industry or professional-language candidate count: 5
- Rights/access decision completeness: 1.0000
- Admitted source count: 0
- Candidate-family concentration: largest 0.2222; top three 0.4444; effective 7.3636
- Candidate-level modes: A=PRESENT; B=PRESENT; C=PRESENT; D=PRESENT
- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING

### Japan

- Candidate count: 6
- Audited independent source-family count: 6
- Structured preference or sensory candidate count: 3
- Community candidate count: 1
- Industry or professional-language candidate count: 2
- Rights/access decision completeness: 1.0000
- Admitted source count: 0
- Candidate-family concentration: largest 0.1667; top three 0.5000; effective 6.0000
- Candidate-level modes: A=PRESENT; B=PRESENT; C=PRESENT; D=PRESENT
- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING

### South Korea

- Candidate count: 6
- Audited independent source-family count: 6
- Structured preference or sensory candidate count: 2
- Community candidate count: 3
- Industry or professional-language candidate count: 2
- Rights/access decision completeness: 1.0000
- Admitted source count: 0
- Candidate-family concentration: largest 0.1667; top three 0.5000; effective 6.0000
- Candidate-level modes: A=PRESENT; B=PRESENT; C=PRESENT; D=PRESENT
- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING

### Latin America (nonblocking)

- Candidate count: 3
- Audited independent source-family count: 3
- Structured preference or sensory candidate count: 3
- Community candidate count: 0
- Industry or professional-language candidate count: 2
- Rights/access decision completeness: 1.0000
- Admitted source count: 0
- Candidate-family concentration: largest 0.3333; top three 1.0000; effective 3.0000
- Candidate-level modes: A=MISSING; B=PRESENT; C=PRESENT; D=PRESENT
- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING

## Candidate register

Each item below is an audited named candidate, not an admitted source or training unit.

### 法压式冲泡对海南罗布斯塔咖啡感官品质的影响

- Candidate: `candidate.r3j.regional.cn-cau-catas-french-press-2025`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: B, C
- Source family: `family.cn.cau-catas-french-press-study`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.spkx.net.cn/CN/10.7506/spkx1002-6630-20231222-185
- Rights evidence: https://www.spkx.net.cn/CN/10.7506/spkx1002-6630-20231222-185
- Limitation: Small specialist convenience panel; not population preference evidence.

### 原产地形象、价值感知与消费决策：云南咖啡产业的实证研究

- Candidate: `candidate.r3j.regional.cn-ynau-yunnan-origin-purchase-2026`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: NONE (purchase/consumption behavior kept separate)
- Source family: `family.cn.ynau-yunnan-consumer-study`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://xb.ynau.edu.cn/jwk_sk/cn/article/doi/10.12371/j.ynau(s).202512008
- Rights evidence: https://xb.ynau.edu.cn/jwk_sk/cn/article/doi/10.12371/j.ynau(s).202512008
- Limitation: Purchase intention is not sensory liking or descriptor mapping.

### DB 46/T 642—2024 中粒种咖啡（罗布斯塔） 生咖啡

- Candidate: `candidate.r3j.regional.cn-hainan-db46-robusta-standard-2024`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: D
- Source family: `family.cn.hainan-amr-db46-standard`
- Rights/access decision: `METADATA_ONLY`
- Community decision: `NOT_APPLICABLE`
- Official source: https://amr.hainan.gov.cn/zw/tztg/202409/P020240926630634846777.pdf
- Rights evidence: https://amr.hainan.gov.cn/zw/tztg/202409/P020240926630634846777.pdf
- Limitation: The standard defines professional method and vocabulary; it is not an observed sensory dataset.

### 《咖啡 感官分析 术语》（征求意见稿）编制说明

- Candidate: `candidate.r3j.regional.cn-sac-tc566-coffee-terms-draft-2025`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: D
- Source family: `family.cn.sac-tc566-coffee-vocabulary`
- Rights/access decision: `METADATA_ONLY`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.cnis.ac.cn/bydt/bzyjzq/gbyjzq/202511/P020251128532335843841.pdf
- Rights evidence: https://www.cnis.ac.cn/bydt/bzyjzq/gbyjzq/202511/P020251128532335843841.pdf
- Limitation: Terminology proposal is not consumer language, liking data, or a sensory-outcome sample.

### 云南省消费者协会发布比较试验结果 30款咖啡豆指标安全可靠

- Candidate: `candidate.r3j.regional.cn-yunnan-30-bean-comparison-2025`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: C, D
- Source family: `family.cn.yunnan-consumers-association-coffee-test`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://amr.yn.gov.cn/info/1688/55297.htm
- Rights evidence: https://amr.yn.gov.cn/info/1688/55297.htm
- Limitation: No consumer liking responses; the public page does not expose reusable sample-level results.

### Xiaohongshu coffee-note regional-language official API/permission route

- Candidate: `candidate.r3j.regional.cn-xiaohongshu-coffee-permission-route`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: A
- Source family: `family.cn.xiaohongshu-platform`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://openaccount.xiaohongshu.com/docs/scope
- Rights evidence: https://openaccount.xiaohongshu.com/docs/scope
- Limitation: Language tag describes the requested source text only and does not infer user nationality, residence, or market.

### Douban coffee review/community written-permission route

- Candidate: `candidate.r3j.regional.cn-douban-coffee-permission-route`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: A
- Source family: `family.cn.douban-platform`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://www.douban.com/about/legal
- Rights evidence: https://www.douban.com/about/legal
- Limitation: No posts or comments were accessed; platform context does not prove an author's market or location.

### Weibo coffee-language official API and research-permission route

- Candidate: `candidate.r3j.regional.cn-weibo-coffee-api-permission-route`
- Frame / market / language: `MAINLAND_CHINA` / `MAINLAND_CHINA` / `zh-Hans-CN` (`Hans`)
- Modes: A
- Source family: `family.cn.weibo-platform`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://open.weibo.com/cli/index
- Rights evidence: https://open.weibo.com/cli/index
- Limitation: No posts or comments were accessed; language alone cannot establish a user's nationality or market.

### 以不同分析方法評估與比較臺灣各產地咖啡感官特性之研究

- Candidate: `candidate.r3j.regional.tw-nkuht-multi-method-sensory-2019`
- Frame / market / language: `TAIWAN` / `TAIWAN` / `zh-Hant-TW` (`Hant`)
- Modes: B, C
- Source family: `family.tw.nkuht-sensory-study`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi?o=dnclcdr&s=id%3D%22107NKHC0255003%22.&searchmode=basic
- Rights evidence: https://ndltd.ncl.edu.tw/gs32/nclcdr/Operating/2-1-3.html
- Limitation: Convenience student and expert panels are not population-representative.

### 台灣消費者對精品咖啡偏好之研究

- Candidate: `candidate.r3j.regional.tw-nchu-specialty-choice-preference-2023`
- Frame / market / language: `TAIWAN` / `TAIWAN` / `zh-Hant-TW` (`Hant`)
- Modes: B
- Source family: `family.tw.nchu-specialty-preference-study`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi/login?o=dnclcdr&s=id%3D%22111NCHU5411004%22.&searchmode=basic
- Rights evidence: https://ndltd.ncl.edu.tw/gs32/nclcdr/Operating/2-1-3.html
- Limitation: Measures product-attribute choice and willingness-to-pay, not descriptor mapping.

### 消費者對咖啡觀感之探討

- Candidate: `candidate.r3j.regional.tw-uknn-coffee-perception-survey-2020`
- Frame / market / language: `TAIWAN` / `TAIWAN` / `zh-Hant-TW` (`Hant`)
- Modes: B
- Source family: `family.tw.uknn-consumer-perception-study`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi/login?o=dnclcdr&s=id%3D%22108LU000252001%22.&searchmode=basic
- Rights evidence: https://ndltd.ncl.edu.tw/gs32/nclcdr/Operating/2-1-3.html
- Limitation: Web/paper convenience sample; stated preference is not controlled sensory response.

### 臺灣咖啡風味輪介紹

- Candidate: `candidate.r3j.regional.tw-tbrs-coffee-flavor-wheel`
- Frame / market / language: `TAIWAN` / `TAIWAN` / `zh-Hant-TW` (`Hant`)
- Modes: D
- Source family: `family.tw.tbrs-tcags`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.tbrs.gov.tw/ws.php?id=5444
- Rights evidence: https://www.tbrs.gov.tw/ws.php?id=3889
- Limitation: Professional vocabulary is not consumer preference evidence; conflicting rights notices block admission.

### 2024第一屆臺灣咖啡分類分級評鑑賽詳細結果及報告書

- Candidate: `candidate.r3j.regional.tw-tbrs-tcags-2024-results`
- Frame / market / language: `TAIWAN` / `TAIWAN` / `zh-Hant-TW` (`Hant`)
- Modes: C, D
- Source family: `family.tw.tbrs-tcags`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.tbrs.gov.tw/ws.php?id=5445
- Rights evidence: https://www.tbrs.gov.tw/ws.php?id=3889
- Limitation: One competition year; not a consumer-liking sample or regional population estimate.

### Dcard coffee-community platform-permission route

- Candidate: `candidate.r3j.regional.tw-dcard-coffee-permission-route`
- Frame / market / language: `TAIWAN` / `TAIWAN` / `zh-Hant-TW` (`Hant`)
- Modes: A
- Source family: `family.tw.dcard-platform`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://www.dcard.tw/terms
- Rights evidence: https://www.dcard.tw/terms
- Limitation: Anonymous visibility is neither reusable permission nor evidence of user nationality or location.

### PTT coffee-community SYSOP/platform-permission route

- Candidate: `candidate.r3j.regional.tw-ptt-coffee-permission-route`
- Frame / market / language: `TAIWAN` / `TAIWAN` / `zh-Hant-TW` (`Hant`)
- Modes: A
- Source family: `family.tw.ptt-platform`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://www.ptt.cc/man/PttLaw/D8FB/M.1473340560.A.653.html
- Rights evidence: https://www.ptt.cc/man/PttLaw/D8FB/M.1473340560.A.653.html
- Limitation: Taiwan service context does not prove an individual user's nationality, residence, or market.

### Defining terroir of Australian coffee to increase demand and investment

- Candidate: `candidate.r3j.regional.aunz-agrifutures-terroir-report`
- Frame / market / language: `AU_NZ` / `AUSTRALIA` / `en-AU` (`Latn`)
- Modes: C, D
- Source family: `family.aunz.agrifutures-scu-terroir`
- Rights/access decision: `RESEARCH_ONLY_NONCOMMERCIAL`
- Community decision: `NOT_APPLICABLE`
- Official source: https://agrifutures.com.au/product/defining-terroir-of-australian-coffee-to-increase-demand-and-investment/
- Rights evidence: https://agrifutures.com.au/legal/
- Limitation: Professional-panel evidence is neither Australian population preference nor universal vocabulary.

### Sensory and Consumer Evaluation of Soy Milk in Coffee

- Candidate: `candidate.r3j.regional.aunz-deakin-soy-milk-coffee`
- Frame / market / language: `AU_NZ` / `AUSTRALIA` / `en-AU` (`Latn`)
- Modes: B, C
- Source family: `family.aunz.deakin-cafs`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.advancedfoodsciences.com.au/current_studies/sensory-and-consumer-evaluation-of-soy-milk-in-coffee/
- Rights evidence: https://www.advancedfoodsciences.com.au/current_studies/sensory-and-consumer-evaluation-of-soy-milk-in-coffee/
- Limitation: Recruitment page gives no achieved sample size, collection dates, reusable dataset, or model-use rights.

### Identifying aroma-active compounds in coffee-flavored dairy beverages

- Candidate: `candidate.r3j.regional.aunz-deakin-aroma-dairy-2022`
- Frame / market / language: `AU_NZ` / `AUSTRALIA` / `en-AU` (`Latn`)
- Modes: B, C
- Source family: `family.aunz.deakin-cafs`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://doi.org/10.1111/1750-3841.16071
- Rights evidence: https://dro.deakin.edu.au/articles/journal_contribution/Identifying_aroma-active_compounds_in_coffee-flavored_dairy_beverages/20618184
- Limitation: Published results do not make raw responses reusable; this is not an independent family from the other Deakin candidate.

### r/AustralianCoffee community sensory-language permission route

- Candidate: `candidate.r3j.regional.aunz-reddit-australiancoffee-route`
- Frame / market / language: `AU_NZ` / `AUSTRALIA` / `en-AU` (`Latn`)
- Modes: A
- Source family: `family.global.reddit`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://www.reddit.com/r/AustralianCoffee/
- Rights evidence: https://redditinc.com/policies/data-api-terms
- Limitation: No API request was sent; public visibility does not authorize collection, reuse, or model training.

### NZ Regional Championship: Sensory Scoresheet

- Candidate: `candidate.r3j.regional.aunz-nzsca-regional-scoresheet`
- Frame / market / language: `AU_NZ` / `NEW_ZEALAND` / `en-NZ` (`Latn`)
- Modes: D
- Source family: `family.aunz.nzsca`
- Rights/access decision: `METADATA_ONLY`
- Community decision: `NOT_APPLICABLE`
- Official source: https://nzsca.org/wp-content/uploads/2023/12/NZBC-Sensory-Scoresheet-Master.pdf
- Rights evidence: https://nzsca.org/2018/02/05/nzscg-milk-wizard-auckland-rules-and-regulations/
- Limitation: Do not reproduce the scoresheet or treat competition scales as consumer preference or universal sensory scores.

### Effects of customers' café experience on perceptions of value for money, satisfaction, and loyalty intentions: a case of the Auckland café industry

- Candidate: `candidate.r3j.regional.aunz-aut-auckland-cafe-experience-2017`
- Frame / market / language: `AU_NZ` / `NEW_ZEALAND` / `en-NZ` (`Latn`)
- Modes: B
- Source family: `family.aunz.aut-auckland-cafe-study`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://hdl.handle.net/10292/11241
- Rights evidence: https://tuwhera.aut.ac.nz/research-repository
- Limitation: Coffee quality is an experience attribute; the study is neither controlled sensory evidence nor representative of New Zealand.

### Those that Judge

- Candidate: `candidate.r3j.regional.aunz-nzsca-those-that-judge`
- Frame / market / language: `AU_NZ` / `NEW_ZEALAND` / `en-NZ` (`Latn`)
- Modes: D
- Source family: `family.aunz.nzsca`
- Rights/access decision: `METADATA_ONLY`
- Community decision: `NOT_APPLICABLE`
- Official source: https://nzsca.org/2020/07/29/those-that-judge/
- Rights evidence: https://nzsca.org/2018/02/05/nzscg-milk-wizard-auckland-rules-and-regulations/
- Limitation: Preserve flat white, long black, and batch brew source-locally without claiming uniqueness, universality, or representativeness.

### Consumer preference data for black coffee

- Candidate: `candidate.r3j.regional.us-ucd-black-coffee-dryad-2023`
- Frame / market / language: `US_CANADA` / `UNITED_STATES` / `en-US` (`Latn`)
- Modes: B, C
- Source family: `family.us.uc-davis-dryad-black-coffee`
- Rights/access decision: `CLEARED_OPEN_LICENSE`
- Community decision: `NOT_APPLICABLE`
- Official source: https://datadryad.org/dataset/doi%3A10.25338/B8993H
- Rights evidence: https://datadryad.org/terms
- Limitation: No download or admission occurred; the convenience study is not representative of the United States.

### Spring 2026 National Coffee Data Trends

- Candidate: `candidate.r3j.regional.us-nca-ncdt-spring-2026`
- Frame / market / language: `US_CANADA` / `UNITED_STATES` / `en-US` (`Latn`)
- Modes: B, D
- Source family: `family.us.national-coffee-association`
- Rights/access decision: `BLOCKED_MODEL_USE`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.ncausa.org/Market-Research/National-Coffee-Data-Trends
- Rights evidence: https://www.ncausa.org/NCA-Membership-Terms-of-Service
- Limitation: Public metadata only; proprietary survey content and response data are not admitted.

### World Coffee Research Sensory Lexicon 2.0

- Candidate: `candidate.r3j.regional.us-wcr-sensory-lexicon-v2`
- Frame / market / language: `US_CANADA` / `UNITED_STATES` / `en-US` (`Latn`)
- Modes: D
- Source family: `family.us.wcr-kansas-state-sensory-center`
- Rights/access decision: `BLOCKED_COPYRIGHT`
- Community decision: `NOT_APPLICABLE`
- Official source: https://worldcoffeeresearch.org/resources/sensory-lexicon
- Rights evidence: https://worldcoffeeresearch.org/read-more/news/174-world-coffee-research-sensory-lexicon
- Limitation: Do not copy vocabulary definitions, forms, layout, or reference materials into the project corpus.

### Reddit coffee-community official API and permission route

- Candidate: `candidate.r3j.regional.us-reddit-coffee-permission-route`
- Frame / market / language: `US_CANADA` / `UNITED_STATES` / `und` (`Latn`)
- Modes: A
- Source family: `family.global.reddit`
- Rights/access decision: `BLOCKED_MODEL_USE`
- Community decision: `BLOCKED_MODEL_USE`
- Official source: https://support.reddithelp.com/hc/en-us/articles/14945211791892-Reddit-Developer-Interfaces
- Rights evidence: https://redditinc.com/policies/data-api-terms
- Limitation: No post/comment content was inspected or collected; item language remains undetermined.

### CoffeeGeek consumer reviews and retired forum archive permission route

- Candidate: `candidate.r3j.regional.ca-coffeegeek-archive-permission-route`
- Frame / market / language: `US_CANADA` / `CANADA` / `und` (`Latn`)
- Modes: A, D
- Source family: `family.ca.coffeegeek-m-prince`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://coffeegeek.com/about/
- Rights evidence: https://coffeegeek.com/about/terms/
- Limitation: Global users are not a Canadian population; item language and author market remain undetermined.

### Winter 2025 Canadian Coffee Drinking Trends

- Candidate: `candidate.r3j.regional.ca-cac-ccdt-winter-2025`
- Frame / market / language: `US_CANADA` / `CANADA` / `en-CA` (`Latn`)
- Modes: B, D
- Source family: `family.ca.coffee-association-of-canada`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://coffeeassoc.com/coffee-consumption-remained-strong-in-canada-in-2025-despite-rising-prices/
- Rights evidence: https://coffeeassoc.com/fr/conditions-dutilisation/
- Limitation: The public summary provides no reusable response data or complete sample frame.

### One-way Degassing Valve Behavior & Function in The Acceptability of Stored Coffee

- Candidate: `candidate.r3j.regional.ca-guelph-cowell-thesis-2018`
- Frame / market / language: `US_CANADA` / `CANADA` / `en-CA` (`Latn`)
- Modes: B, C
- Source family: `family.ca.university-of-guelph-studies`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: http://hdl.handle.net/10214/14340
- Rights evidence: https://atrium.lib.uoguelph.ca/bitstream/10214/14340/4/Cowell_Jessey_201809_Msc.pdf
- Limitation: Institutional convenience study; not a Canadian population preference estimate.

### An assessment of consumer preference for fair trade coffee in Toronto and Vancouver

- Candidate: `candidate.r3j.regional.ca-fairtrade-toronto-vancouver-2010`
- Frame / market / language: `US_CANADA` / `CANADA` / `en-CA` (`Latn`)
- Modes: B
- Source family: `family.ca.university-of-guelph-studies`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://onlinelibrary.wiley.com/doi/abs/10.1002/agr.20217
- Rights evidence: https://onlinelibrary.wiley.com/doi/abs/10.1002/agr.20217
- Limitation: Purchase and label preference has no sensory fields and is not descriptor mapping.

### Home-Barista Coffees and Brewing forums permission route

- Candidate: `candidate.r3j.regional.usca-home-barista-permission-route`
- Frame / market / language: `US_CANADA` / `UNITED_STATES` / `und` (`Latn`)
- Modes: A, D
- Source family: `family.us.home-barista`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://www.home-barista.com/forums/index.php
- Rights evidence: https://www.home-barista.com/contribute
- Limitation: Locale and market cannot be inferred from English; no posts or comments were inspected.

### Questionnaire-based survey of coffee consumption in Japan

- Candidate: `candidate.r3j.regional.jp-mendeley-sato-consumption-v1`
- Frame / market / language: `JAPAN` / `JAPAN` / `en` (`Latn`)
- Modes: NONE (purchase/consumption behavior kept separate)
- Source family: `family.jp.toyo-sato-consumption-survey`
- Rights/access decision: `CLEARED_OPEN_LICENSE`
- Community decision: `NOT_APPLICABLE`
- Official source: https://doi.org/10.17632/5sjfp2334f.1
- Rights evidence: https://data.mendeley.com/datasets/5sjfp2334f/1
- Limitation: English public metadata does not supply ja-JP sensory wording, preference, or descriptors; no file was acquired.

### A milk coffee flavor lexicon developed based on the perceptions of Japanese consumers and its application to check-all-that-apply questions

- Candidate: `candidate.r3j.regional.jp-milk-coffee-flavor-lexicon-2023`
- Frame / market / language: `JAPAN` / `JAPAN` / `ja-JP` (`Jpan`)
- Modes: B, C
- Source family: `family.jp.morinaga-tsukuba-milk-coffee`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://doi.org/10.3136/fstr.FSTR-D-22-00176
- Rights evidence: https://www.jstage.jst.go.jp/article/fstr/29/3/29_FSTR-D-22-00176/_html/-char/ja
- Limitation: The copyrighted 53-term lexicon is a source-specific research output, not a general Japanese standard.

### 働く世代に好まれるコーヒーの開発

- Candidate: `candidate.r3j.regional.jp-konan-working-generation-coffee`
- Frame / market / language: `JAPAN` / `JAPAN` / `ja-JP` (`Jpan`)
- Modes: B, C
- Source family: `family.jp.konan-womens-working-coffee`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.jstage.jst.go.jp/article/kasei/70/0/70_138/_article/-char/ja/
- Rights evidence: https://www.jstage.jst.go.jp/article/kasei/70/0/70_138/_article/-char/ja/
- Limitation: A single university-employee sample in Hyogo cannot represent working-age Japan.

### コーヒー需要動向調査2024年度 第22回調査

- Candidate: `candidate.r3j.regional.jp-ajca-demand-survey-2024`
- Frame / market / language: `JAPAN` / `JAPAN` / `ja-JP` (`Jpan`)
- Modes: B, D
- Source family: `family.jp.ajca-demand-survey`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://coffee.ajca.or.jp/data/survey/
- Rights evidence: https://coffee.ajca.or.jp/data/survey/
- Limitation: Industry summary lacks raw responses; preference ratings cannot become descriptor mapping without sensory fields.

### Sensory Evaluation of Coffee

- Candidate: `candidate.r3j.regional.jp-jcqa-sensory-evaluation`
- Frame / market / language: `JAPAN` / `JAPAN` / `ja-JP` (`Jpan`)
- Modes: D
- Source family: `family.jp.jcqa-ishimitsu-professional`
- Rights/access decision: `METADATA_ONLY`
- Community decision: `NOT_APPLICABLE`
- Official source: https://doi.org/10.2171/jao.38.368
- Rights evidence: https://www.jstage.jst.go.jp/article/jao/38/5/38_5_368/_article/-char/en
- Limitation: Professional method review is neither controlled consumer outcome nor a reusable qualification form.

### Tabelog coffee and café review permission route

- Candidate: `candidate.r3j.regional.jp-tabelog-coffee-reviews-route`
- Frame / market / language: `JAPAN` / `JAPAN` / `ja-JP` (`Jpan`)
- Modes: A
- Source family: `family.jp.kakaku-tabelog`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://tabelog.com/
- Rights evidence: https://tabelog.com/en/help/rules
- Limitation: No ordinary review was collected, inspected, or quoted; public visibility does not authorize model use.

### 물의 종류와 온도를 달리하여 추출한 커피의 품질 특성 및 소비자 기호도 연구

- Candidate: `candidate.r3j.regional.kr-water-temperature-acceptance-2022`
- Frame / market / language: `SOUTH_KOREA` / `SOUTH_KOREA` / `ko-KR` (`Kore`)
- Modes: B, C
- Source family: `family.kr.culinary-society-coway-snu-water-study`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002897843
- Rights evidence: https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002897843
- Limitation: No reusable response-level dataset or model-use licence is public; not a national preference sample.

### 2024 커피 - 가공식품 세분시장 현황 보고서

- Candidate: `candidate.r3j.regional.kr-atfis-coffee-report-2024`
- Frame / market / language: `SOUTH_KOREA` / `SOUTH_KOREA` / `ko-KR` (`Kore`)
- Modes: B, D
- Source family: `family.kr.at-fis-coffee-report`
- Rights/access decision: `METADATA_ONLY`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.atfis.or.kr/home/board/FB0024.do?act=read&bcaId=0&bpoId=4958&pageIndex=1&subSkinYn=N
- Rights evidence: https://www.atfis.or.kr/home/board/FB0024.do?act=read&bcaId=0&bpoId=4958&pageIndex=1&subSkinYn=N
- Limitation: Consumer/market survey and industry vocabulary are present, but no reusable response-level data is admitted.

### NAVER Café coffee sensory-language official Search API permission route

- Candidate: `candidate.r3j.regional.kr-naver-cafe-permission-route`
- Frame / market / language: `SOUTH_KOREA` / `SOUTH_KOREA` / `ko-KR` (`Kore`)
- Modes: A
- Source family: `family.kr.naver-cafe`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://developers.naver.com/docs/serviceapi/search/cafearticle/cafearticle.md
- Rights evidence: https://developers.naver.com/products/terms/
- Limitation: No café article was collected; platform context and Korean language do not prove an author's residence or nationality.

### Daum Café coffee sensory-language official Search API permission route

- Candidate: `candidate.r3j.regional.kr-daum-cafe-permission-route`
- Frame / market / language: `SOUTH_KOREA` / `SOUTH_KOREA` / `ko-KR` (`Kore`)
- Modes: A
- Source family: `family.kr.daum-cafe-kakao`
- Rights/access decision: `DATA_REQUEST_PREPARED`
- Community decision: `DATA_REQUEST_PREPARED`
- Official source: https://developers.kakao.com/docs/ko/daum-search/dev-guide
- Rights evidence: https://www.kakao.com/policy/terms?lang=ko&type=ts
- Limitation: No café article was collected; platform context and Korean language do not prove an author's residence or nationality.

### 커피향미평가사 표준교육과정

- Candidate: `candidate.r3j.regional.kr-kca-flavor-evaluator-curriculum`
- Frame / market / language: `SOUTH_KOREA` / `SOUTH_KOREA` / `ko-KR` (`Kore`)
- Modes: D
- Source family: `family.kr.korea-coffee-association`
- Rights/access decision: `METADATA_ONLY`
- Community decision: `NOT_APPLICABLE`
- Official source: https://www.kca-coffee.org/cms/FrCon/index.do?MENU_ID=2210
- Rights evidence: https://www.kca-coffee.org/cms/FrCon/index.do?MENU_ID=570
- Limitation: Professional terminology is not consumer preference or controlled sensory outcome evidence.

### DCInside coffee-gallery permission route

- Candidate: `candidate.r3j.regional.kr-dcinside-coffee-permission-route`
- Frame / market / language: `SOUTH_KOREA` / `SOUTH_KOREA` / `ko-KR` (`Kore`)
- Modes: A
- Source family: `family.kr.dcinside`
- Rights/access decision: `BLOCKED_AUTOMATION`
- Community decision: `BLOCKED_AUTOMATION`
- Official source: https://en.dcinside.com/
- Rights evidence: https://nstatic.dcinside.com/dc/m/policy/policy.html
- Limitation: No gallery content was inspected; a prepared contact route does not override the current automation/model-use block.

### Qualidade de cafés especiais: uma avaliação sensorial feita com consumidores utilizando a técnica MFACT

- Candidate: `candidate.r3j.regional.latam-br-mfact-consumer-sensory-2017`
- Frame / market / language: `LATIN_AMERICA_NONBLOCKING` / `LATIN_AMERICA_NONBLOCKING` / `pt-BR` (`Latn`)
- Modes: B, C
- Source family: `family.latam.ufc-ufla-mfact-consumer-study`
- Rights/access decision: `CLEARED_OPEN_LICENSE`
- Community decision: `NOT_APPLICABLE`
- Official source: https://periodicos.ufc.br/revistacienciaagronomica/article/view/84692
- Rights evidence: https://repositorio.ufla.br/items/1eacbdda-bd41-444c-abb6-2d2b0700b2e7
- Limitation: Published aggregate tables only; do not infer representative Brazilian preferences or reuse third-party protocol/form text.

### Into the minds of coffee consumers: perception, preference, and impact of information in the sensory analysis of specialty coffee

- Candidate: `candidate.r3j.regional.latam-br-ufla-consumer-cata-2021`
- Frame / market / language: `LATIN_AMERICA_NONBLOCKING` / `LATIN_AMERICA_NONBLOCKING` / `en` (`Latn`)
- Modes: B, C, D
- Source family: `family.latam.scielo-figshare-ufla-consumer-study`
- Rights/access decision: `CLEARED_OPEN_LICENSE`
- Community decision: `NOT_APPLICABLE`
- Official source: https://scielo.figshare.com/articles/dataset/Into_the_minds_of_coffee_consumers_perception_preference_and_impact_of_information_in_the_sensory_analysis_of_specialty_coffee/14318575
- Rights evidence: https://scielo.figshare.com/articles/dataset/Into_the_minds_of_coffee_consumers_perception_preference_and_impact_of_information_in_the_sensory_analysis_of_specialty_coffee/14318575
- Limitation: Public artifact language is English; questionnaire language is not established, so this is not pt-BR language coverage without file-level verification.

### Fourier Transform Near Infrared spectra and sensory scores in green and roasted specialty coffee for machine learning-based quality monitoring

- Candidate: `candidate.r3j.regional.latam-co-cesurcafe-ftnir-v4`
- Frame / market / language: `LATIN_AMERICA_NONBLOCKING` / `LATIN_AMERICA_NONBLOCKING` / `en` (`Latn`)
- Modes: C, D
- Source family: `family.latam.mendeley-cesurcafe-colombia`
- Rights/access decision: `CLEARED_OPEN_LICENSE`
- Community decision: `NOT_APPLICABLE`
- Official source: https://data.mendeley.com/datasets/nz2fr76trm/4
- Rights evidence: https://data.mendeley.com/datasets/nz2fr76trm/4
- Limitation: Controlled professional outcomes only; English labels are not es-CO language coverage, and overall quality score is not descriptor mapping.

## Coverage and concentration interpretation

All six admitted regional coverage measures are zero because no source or evidence unit was admitted in this audit. Published sample sizes remain source-reported, not-acquired metadata and never enter regional coverage totals. Concentration over admitted evidence is therefore `NOT_COMPUTABLE_ZERO_UNITS`; the separately reported candidate-family concentration does not establish representativeness.

Combined frames retain atomic markets and language tags. `zh-Hans-CN` and `zh-Hant-TW`, and `en-AU`, `en-NZ`, `en-US`, and `en-CA`, remain distinct. `und` is used where an uninspected community item cannot responsibly be assigned a dialect. No nationality, residence, or market is inferred from language alone.

## Stop decision

`ALL_CORE_REGIONAL_SOURCE_FRAMES_COMPLETE=true` and `ALL_SECONDARY_REGIONAL_SOURCE_FRAMES_AUDITED=true`. These are now satisfied prerequisites, not an automatic global stop. `GLOBAL_ACQUISITION_COMPLETE=false` because admission, effective-unit, training-eligibility, and representativeness gaps remain. No region invoked the two-consecutive-no-gain rule: each first regional batch produced candidate-frame material gain and reset its region-local counter to zero.

## Request boundary

There are 33 complete prepared dossiers, including 13 forum/community permission routes. Every one is recorded as unsent. Sending any request requires separate explicit user authorization.
