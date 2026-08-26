#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as prettier from "prettier";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "../..");
const DATA_DIR = join(ROOT, "db/data/round3j");
const DOC_DIR = join(ROOT, "docs/research/coffee-sensory-kb-v0-round3j");
const MANIFEST_PATH = join(DATA_DIR, "regional_source_candidates.json");
const CHECK_MODE = process.argv.includes("--check");
const TODAY = "2026-08-26";

const REGION_META = {
  MAINLAND_CHINA: {
    label: "Mainland China",
    tier: "CORE",
    minimumCandidates: 6,
    minimumFamilies: 2,
    requiredTags: ["zh-Hans-CN"],
    batchId: "R3J-REG-CN-001",
  },
  TAIWAN: {
    label: "Taiwan",
    tier: "CORE",
    minimumCandidates: 6,
    minimumFamilies: 2,
    requiredTags: ["zh-Hant-TW"],
    batchId: "R3J-REG-TW-001",
  },
  AU_NZ: {
    label: "Australia / New Zealand",
    tier: "CORE",
    minimumCandidates: 6,
    minimumFamilies: 2,
    requiredTags: ["en-AU", "en-NZ"],
    batchId: "R3J-REG-AUNZ-001",
  },
  US_CANADA: {
    label: "United States / Canada",
    tier: "CORE",
    minimumCandidates: 6,
    minimumFamilies: 2,
    requiredTags: ["en-US", "en-CA"],
    batchId: "R3J-REG-USCA-001",
  },
  JAPAN: {
    label: "Japan",
    tier: "SECONDARY",
    minimumCandidates: 4,
    minimumFamilies: 2,
    requiredTags: ["ja-JP"],
    batchId: "R3J-REG-JP-001",
  },
  SOUTH_KOREA: {
    label: "South Korea",
    tier: "SECONDARY",
    minimumCandidates: 4,
    minimumFamilies: 2,
    requiredTags: ["ko-KR"],
    batchId: "R3J-REG-KR-001",
  },
  LATIN_AMERICA_NONBLOCKING: {
    label: "Latin America (nonblocking)",
    tier: "NONBLOCKING",
    minimumCandidates: 0,
    minimumFamilies: 0,
    requiredTags: [],
    batchId: "R3J-REG-LATAM-001",
  },
};

const BLOCKING_REGIONS = Object.keys(REGION_META).filter(
  (key) => REGION_META[key].tier !== "NONBLOCKING",
);
const CORE_REGIONS = BLOCKING_REGIONS.filter(
  (key) => REGION_META[key].tier === "CORE",
);
const SECONDARY_REGIONS = BLOCKING_REGIONS.filter(
  (key) => REGION_META[key].tier === "SECONDARY",
);

const MODE_FIELDS = {
  A: "mode_a_user_generated_sensory_language",
  B: "mode_b_structured_preference_or_liking",
  C: "mode_c_controlled_or_semi_controlled_sensory_outcome",
  D: "mode_d_professional_or_industry_language",
};
const MODE_LABELS = {
  A: "A_USER_GENERATED_SENSORY_LANGUAGE",
  B: "B_STRUCTURED_PREFERENCE_OR_LIKING",
  C: "C_CONTROLLED_OR_SEMI_CONTROLLED_SENSORY_OUTCOME",
  D: "D_PROFESSIONAL_OR_INDUSTRY_LANGUAGE",
};
const SOURCE_CLASSES = new Set([
  "ACADEMIC_STUDY",
  "OPEN_DATA_REPOSITORY",
  "GOVERNMENT_OR_INSTITUTIONAL_DATA",
  "INDUSTRY_OR_PROFESSIONAL_BODY",
  "SOURCE_AUTHORED_BLOG_OR_STATIC_SITE",
  "PRODUCT_OR_REVIEW_DATASET",
  "FORUM_OR_COMMUNITY_PLATFORM",
  "USER_REVIEW_PLATFORM",
  "OFFICIAL_PLATFORM_UGC_API",
  "DATA_ON_REQUEST_STUDY",
]);
const COMMUNITY_CLASSES = new Set([
  "FORUM_OR_COMMUNITY_PLATFORM",
  "USER_REVIEW_PLATFORM",
  "OFFICIAL_PLATFORM_UGC_API",
]);
const COMMUNITY_DECISIONS = new Set([
  "AUTHORIZED_API",
  "WRITTEN_PLATFORM_PERMISSION",
  "WRITTEN_AUTHOR_PERMISSION",
  "OPEN_LICENSED_SNAPSHOT",
  "DERIVED_ONLY_AUTHORIZED",
  "METADATA_ONLY",
  "DATA_REQUEST_PREPARED",
  "BLOCKED_AUTOMATION",
  "BLOCKED_COPYRIGHT",
  "BLOCKED_PRIVACY",
  "BLOCKED_MODEL_USE",
]);
const RIGHTS_PROFILES = {
  CLEARED_OPEN_LICENSE: {
    rightsState: "CLEARED",
    accessState: "PUBLIC_VERSIONED",
    modelState: "ALLOWED",
  },
  CLEARED_PUBLIC_DOMAIN: {
    rightsState: "CLEARED",
    accessState: "PUBLIC_VERSIONED",
    modelState: "ALLOWED",
  },
  CLEARED_OFFICIAL_API_FOR_DECLARED_USE: {
    rightsState: "CLEARED",
    accessState: "OFFICIAL_API",
    modelState: "ALLOWED",
  },
  CLEARED_WRITTEN_PERMISSION: {
    rightsState: "CLEARED",
    accessState: "WRITTEN_PERMISSION",
    modelState: "ALLOWED",
  },
  RESEARCH_ONLY_NONCOMMERCIAL: {
    rightsState: "RESTRICTED",
    accessState: "PUBLIC_VERSIONED",
    modelState: "RESEARCH_ONLY_NONCOMMERCIAL",
  },
  METADATA_ONLY: {
    rightsState: "RESTRICTED",
    accessState: "PUBLIC_HTML_OBSERVABLE_ONLY",
    modelState: "NOT_APPLICABLE",
  },
  DATA_REQUEST_PREPARED: {
    rightsState: "RESTRICTED",
    accessState: "REQUEST_ONLY",
    modelState: "PENDING_PERMISSION",
  },
  BLOCKED_ACCESS: {
    rightsState: "BLOCKED",
    accessState: "BLOCKED",
    modelState: "BLOCKED",
  },
  BLOCKED_AUTOMATION: {
    rightsState: "BLOCKED",
    accessState: "BLOCKED",
    modelState: "BLOCKED",
  },
  BLOCKED_COPYRIGHT: {
    rightsState: "BLOCKED",
    accessState: "PUBLIC_HTML_OBSERVABLE_ONLY",
    modelState: "BLOCKED",
  },
  BLOCKED_PRIVACY: {
    rightsState: "BLOCKED",
    accessState: "BLOCKED",
    modelState: "BLOCKED",
  },
  BLOCKED_MODEL_USE: {
    rightsState: "BLOCKED",
    accessState: "PUBLIC_HTML_OBSERVABLE_ONLY",
    modelState: "BLOCKED",
  },
  BLOCKED_LICENSE_UNCLEAR: {
    rightsState: "BLOCKED",
    accessState: "PUBLIC_HTML_OBSERVABLE_ONLY",
    modelState: "BLOCKED",
  },
};
const COVERAGE_MEASURES = [
  "REGIONAL_LANGUAGE_DOCUMENT_COUNT",
  "REGIONAL_UNIQUE_EXPRESSION_COUNT",
  "REGIONAL_PREFERENCE_RESPONSE_COUNT",
  "REGIONAL_SENSORY_SAMPLE_COUNT",
  "REGIONAL_SOURCE_FAMILY_COUNT",
  "REGIONAL_TRAINING_ELIGIBLE_UNIT_COUNT",
];

const manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf8"));
const candidates = manifest.candidates;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function bool(value) {
  return value ? "true" : "false";
}

function clean(value) {
  return String(value ?? "")
    .replaceAll("\t", " ")
    .replaceAll("\r", " ")
    .replaceAll("\n", " ")
    .trim();
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function rowCount(path) {
  return readFileSync(path, "utf8").trimEnd().split("\n").length - 1;
}

function readHeader(path) {
  return readFileSync(path, "utf8").split("\n", 1)[0].split("\t");
}

function serializeTsv(header, rows) {
  return `${header.join("\t")}\n${rows
    .map((row) => header.map((field) => clean(row[field])).join("\t"))
    .join("\n")}${rows.length ? "\n" : ""}`;
}

function writeOrCheck(path, content) {
  if (CHECK_MODE) {
    assert(
      readFileSync(path, "utf8") === content,
      `generated artifact drift: ${path}`,
    );
    return;
  }
  writeFileSync(path, content);
}

function format4(value) {
  return Number(value).toFixed(4);
}

function effectiveFamilyCount(familyCounts) {
  const total = familyCounts.reduce((sum, value) => sum + value, 0);
  if (total === 0) return null;
  return 1 / familyCounts.reduce((sum, value) => sum + (value / total) ** 2, 0);
}

function dataRequestDefaults(candidate) {
  const isCommunity = COMMUNITY_CLASSES.has(candidate.sourceClass);
  return {
    contactTarget:
      candidate.contactTarget ??
      "Official source owner or corresponding author",
    exactRequestedFields:
      candidate.exactRequestedFields ??
      (isCommunity
        ? "Author-opted-in title/body; coarse date; source-local language; preparation; roast; black/milk; rating where present; permission and withdrawal flags; no usernames, profiles, emails, avatars, exact locations, direct links, comments, or replies"
        : "Deidentified response or sample key; source-local field labels and codebook; preparation; roast; black/milk; sensory or preference outcomes; coarse population metadata; consent, licence, and withdrawal flags"),
    requestedDateRange:
      candidate.requestedDateRange ??
      "Original collection period; exact dates requested",
    rawTextRequirement:
      candidate.rawText ??
      (isCommunity
        ? "Only after written platform and relevant author permission for model research"
        : "NO; free text excluded unless separately licensed and reviewed"),
    derivedOnlyAlternative:
      candidate.derived ??
      (isCommunity
        ? "Deidentified aggregate expression counts and context co-occurrences with minimum-frequency suppression"
        : "Deidentified condition-level aggregates and source-local field inventory"),
    privacyProtections:
      candidate.privacyProtections ??
      "Pseudonymous keys; direct identifiers and exact personal location excluded; coarse geography only; suppress small cells",
    intendedUse:
      candidate.intendedUse ??
      "Noncommercial regional language, preference, or sensory research; no automatic gold label, canonical promotion, or population estimate",
    publicBoundary:
      candidate.publicBoundary ??
      "Derived aggregates only unless the exact source units are separately licensed for public release",
    withdrawal:
      candidate.withdrawal ??
      "Source-keyed deletion or tombstone; remove affected units and rebuild downstream derivatives and exports",
  };
}

function validateCandidate(candidate) {
  assert(REGION_META[candidate.frame], `unknown frame: ${candidate.frame}`);
  assert(
    SOURCE_CLASSES.has(candidate.sourceClass),
    `unknown class: ${candidate.key}`,
  );
  assert(
    RIGHTS_PROFILES[candidate.rightsDecision],
    `unknown rights decision: ${candidate.key}`,
  );
  assert(
    Array.isArray(candidate.modes),
    `modes must be an array: ${candidate.key}`,
  );
  assert(
    candidate.modes.every((mode) => MODE_FIELDS[mode]),
    `unknown mode: ${candidate.key}`,
  );
  assert(
    candidate.language !== "zh-Hans" && candidate.language !== "zh-Hant",
    `collapsed Chinese tag: ${candidate.key}`,
  );
  assert(
    ["BLACK", "MILK", "MIXED", "NOT_REPORTED"].includes(candidate.blackMilk),
    `invalid black/milk scope: ${candidate.key}`,
  );
  if (COMMUNITY_CLASSES.has(candidate.sourceClass)) {
    assert(
      COMMUNITY_DECISIONS.has(candidate.communityDecision),
      `community decision missing: ${candidate.key}`,
    );
    assert(
      candidate.modes.includes("A"),
      `community candidate lacks mode A: ${candidate.key}`,
    );
  } else {
    assert(
      candidate.communityDecision === undefined,
      `non-community decision set: ${candidate.key}`,
    );
  }
  if (candidate.requestPrepared) {
    const dossier = dataRequestDefaults(candidate);
    for (const [key, value] of Object.entries(dossier)) {
      assert(clean(value), `request dossier ${key} missing: ${candidate.key}`);
    }
  }
}

for (const candidate of candidates) validateCandidate(candidate);
assert(
  new Set(candidates.map((candidate) => candidate.key)).size ===
    candidates.length,
  "duplicate candidate key",
);

function candidateRegisterRow(candidate) {
  const profile = RIGHTS_PROFILES[candidate.rightsDecision];
  const isCommunity = COMMUNITY_CLASSES.has(candidate.sourceClass);
  const request = candidate.requestPrepared
    ? dataRequestDefaults(candidate)
    : null;
  const hasMode = (mode) => candidate.modes.includes(mode);
  const structured = hasMode("B") || hasMode("C");
  const privacyFlags = isCommunity;
  return {
    regional_candidate_record_key: `record.r3j.regional.${candidate.key}`,
    candidate_key: `candidate.r3j.regional.${candidate.key}`,
    source_origin_key:
      candidate.originKey ?? `origin.r3j.regional.${candidate.key}`,
    regional_audit_batch_id: REGION_META[candidate.frame].batchId,
    regional_frame_key: candidate.frame,
    region_tier: REGION_META[candidate.frame].tier,
    source_market_region: candidate.market,
    region_assignment_basis: candidate.regionBasis,
    collection_geography: candidate.geography,
    language_tag: candidate.language,
    script: candidate.script,
    source_platform: candidate.platform,
    author_declared_location_if_available:
      candidate.authorLocation ?? "NOT_AVAILABLE",
    population_scope: candidate.population,
    source_class: candidate.sourceClass,
    exact_title: candidate.title,
    authors_or_owner: candidate.owner,
    publication_or_release_date: candidate.date,
    doi_or_stable_official_url: candidate.url,
    repository_or_platform: candidate.repository ?? candidate.platform,
    source_family_key: candidate.family,
    source_family_independence_basis: candidate.familyBasis,
    independent_source_family_audit_state:
      candidate.familyState ?? "AUDITED_INDEPENDENT",
    mode_a_user_generated_sensory_language: bool(hasMode("A")),
    mode_b_structured_preference_or_liking: bool(hasMode("B")),
    mode_c_controlled_or_semi_controlled_sensory_outcome: bool(hasMode("C")),
    mode_d_professional_or_industry_language: bool(hasMode("D")),
    user_generated_or_community_source_candidate: bool(
      isCommunity || hasMode("A"),
    ),
    structured_preference_or_sensory_candidate: bool(structured),
    industry_or_professional_language_candidate: bool(hasMode("D")),
    preparation_scope: candidate.preparation,
    roast_scope: candidate.roast,
    black_or_milk_scope: candidate.blackMilk,
    consumer_or_professional_scope: candidate.audience,
    expected_regional_contribution: candidate.contribution,
    license_or_terms: candidate.terms,
    license_or_terms_url: candidate.termsUrl,
    rights_evidence_url: candidate.rightsUrl ?? candidate.termsUrl,
    access_path: candidate.accessPath,
    rights_state: candidate.rightsState ?? profile.rightsState,
    access_state: candidate.accessState ?? profile.accessState,
    rights_and_access_decision: candidate.rightsDecision,
    decision_basis: candidate.rightsBasis,
    rights_and_access_decision_complete: "true",
    forum_or_community_decision: isCommunity
      ? candidate.communityDecision
      : "NOT_APPLICABLE",
    privacy_state:
      candidate.privacyState ??
      (isCommunity ? "REVIEW_REQUIRED" : "AGGREGATE_NO_PERSONAL_DATA"),
    model_research_use_state: candidate.modelState ?? profile.modelState,
    public_release_boundary:
      request?.publicBoundary ??
      candidate.publicBoundary ??
      "Candidate metadata and short factual audit summary only; no source-content export",
    raw_text_requirement:
      request?.rawTextRequirement ??
      candidate.rawText ??
      "NO_RAW_TEXT_ACQUIRED",
    derived_only_alternative:
      request?.derivedOnlyAlternative ??
      candidate.derived ??
      "AUDIT_METADATA_ONLY",
    raw_acquisition_authorized: bool(candidate.rawAuthorized ?? false),
    admission_state: "NOT_ADMITTED",
    training_eligibility_state: "NOT_ADMITTED",
    eligible_corpus_roles: "NOT_APPLICABLE",
    sensory_gold_label_eligible: "false",
    canonical_concept_promotion_eligible: "false",
    population_preference_estimate_eligible: "false",
    username_exclusion_required: bool(privacyFlags),
    profile_exclusion_required: bool(privacyFlags),
    email_exclusion_required: bool(privacyFlags),
    avatar_exclusion_required: bool(privacyFlags),
    exact_personal_location_exclusion_required: bool(privacyFlags),
    direct_link_public_export_exclusion_required: bool(privacyFlags),
    comments_replies_separate_review_required: bool(privacyFlags),
    pseudonymous_document_keys_required: bool(privacyFlags),
    contact_target: request?.contactTarget ?? "NOT_APPLICABLE",
    exact_requested_fields: request?.exactRequestedFields ?? "NOT_APPLICABLE",
    requested_date_range: request?.requestedDateRange ?? "NOT_APPLICABLE",
    privacy_protections: request?.privacyProtections ?? "NOT_APPLICABLE",
    intended_model_research_use: request?.intendedUse ?? "AUDIT_METADATA_ONLY",
    deletion_or_withdrawal_procedure:
      request?.withdrawal ??
      candidate.withdrawal ??
      "Remove audit metadata if the official source record is withdrawn",
    request_status: candidate.requestPrepared
      ? "DATA_REQUEST_PREPARED"
      : "NOT_APPLICABLE",
    request_sent: "false",
    registered_on: TODAY,
    audited_on: TODAY,
    limitation: candidate.limitation,
  };
}

const registerRows = candidates.map(candidateRegisterRow);
const registerByKey = new Map(
  registerRows.map((row) => [row.candidate_key, row]),
);

function regionCandidates(region) {
  return candidates.filter((candidate) => candidate.frame === region);
}

function regionStats(region) {
  const rows = regionCandidates(region);
  const independentFamilies = new Set(
    rows
      .filter(
        (candidate) =>
          (candidate.familyState ?? "AUDITED_INDEPENDENT") ===
          "AUDITED_INDEPENDENT",
      )
      .map((candidate) => candidate.family),
  );
  const familyCounts = [...new Set(rows.map((candidate) => candidate.family))]
    .map(
      (family) =>
        rows.filter((candidate) => candidate.family === family).length,
    )
    .sort((a, b) => b - a);
  const total = rows.length;
  const modeCounts = Object.fromEntries(
    Object.keys(MODE_FIELDS).map((mode) => [
      mode,
      rows.filter((candidate) => candidate.modes.includes(mode)).length,
    ]),
  );
  return {
    candidateCount: total,
    familyCount: independentFamilies.size,
    structuredCount: rows.filter(
      (candidate) =>
        candidate.modes.includes("B") || candidate.modes.includes("C"),
    ).length,
    communityCount: rows.filter((candidate) =>
      COMMUNITY_CLASSES.has(candidate.sourceClass),
    ).length,
    industryCount: rows.filter((candidate) => candidate.modes.includes("D"))
      .length,
    completeRightsCount: rows.length,
    admittedCount: 0,
    trainingCount: 0,
    modeCounts,
    largestShare: total ? familyCounts[0] / total : null,
    top3Share: total
      ? familyCounts.slice(0, 3).reduce((sum, value) => sum + value, 0) / total
      : null,
    effectiveFamilies: effectiveFamilyCount(familyCounts),
  };
}

const stats = Object.fromEntries(
  Object.keys(REGION_META).map((region) => [region, regionStats(region)]),
);
const AUDITED_REGIONS = Object.keys(REGION_META).filter(
  (region) => stats[region].candidateCount > 0,
);

for (const region of AUDITED_REGIONS) {
  const meta = REGION_META[region];
  const current = stats[region];
  assert(
    current.candidateCount >= meta.minimumCandidates,
    `${region} candidate threshold failed`,
  );
  assert(
    current.familyCount >= meta.minimumFamilies,
    `${region} family threshold failed`,
  );
  assert(
    current.completeRightsCount === current.candidateCount,
    `${region} rights completeness failed`,
  );
  for (const tag of meta.requiredTags) {
    assert(
      regionCandidates(region).some((candidate) => candidate.language === tag),
      `${region} missing ${tag}`,
    );
  }
  if (meta.tier === "CORE") {
    assert(
      current.structuredCount >= 1,
      `${region} structured threshold failed`,
    );
    assert(current.communityCount >= 1, `${region} community threshold failed`);
    assert(current.industryCount >= 1, `${region} industry threshold failed`);
  }
}

const sourceRegisterPath = join(
  DATA_DIR,
  "regional_source_candidate_register.tsv",
);
writeOrCheck(
  sourceRegisterPath,
  serializeTsv(readHeader(sourceRegisterPath), registerRows),
);

const dossierHeader = [
  "request_dossier_key",
  "candidate_key",
  "regional_frame_key",
  "source_platform",
  "forum_or_community_decision",
  "contact_target",
  "exact_requested_fields",
  "requested_date_range",
  "raw_text_requirement",
  "derived_only_alternative",
  "privacy_protections",
  "intended_model_research_use",
  "public_release_boundary",
  "deletion_or_withdrawal_procedure",
  "request_status",
  "request_sent",
  "prepared_on",
  "limitation",
];
const dossierRows = registerRows
  .filter((row) => row.request_status === "DATA_REQUEST_PREPARED")
  .map((row) => ({
    request_dossier_key: `request.r3j.regional.${row.candidate_key.replace("candidate.r3j.regional.", "")}`,
    candidate_key: row.candidate_key,
    regional_frame_key: row.regional_frame_key,
    source_platform: row.source_platform,
    forum_or_community_decision: row.forum_or_community_decision,
    contact_target: row.contact_target,
    exact_requested_fields: row.exact_requested_fields,
    requested_date_range: row.requested_date_range,
    raw_text_requirement: row.raw_text_requirement,
    derived_only_alternative: row.derived_only_alternative,
    privacy_protections: row.privacy_protections,
    intended_model_research_use: row.intended_model_research_use,
    public_release_boundary: row.public_release_boundary,
    deletion_or_withdrawal_procedure: row.deletion_or_withdrawal_procedure,
    request_status: row.request_status,
    request_sent: row.request_sent,
    prepared_on: TODAY,
    limitation: "Prepared only; sending requires explicit user authorization.",
  }));
writeOrCheck(
  join(DATA_DIR, "regional_permission_request_dossiers.tsv"),
  serializeTsv(dossierHeader, dossierRows),
);

const batchHeader = readHeader(
  join(DATA_DIR, "regional_acquisition_batch_ledger.tsv"),
);
const outcomeHeader = readHeader(
  join(DATA_DIR, "regional_acquisition_outcome_ledger.tsv"),
);
const outcomeMetrics = [
  ["named_source_candidate_count", "candidateCount"],
  ["audited_independent_source_family_count", "familyCount"],
  ["structured_preference_or_sensory_candidate_count", "structuredCount"],
  ["user_generated_or_community_source_candidate_count", "communityCount"],
  ["industry_or_professional_language_candidate_count", "industryCount"],
  ["explicit_mode_audit_count", "explicitModeCount"],
  ["rights_and_access_decision_complete_count", "completeRightsCount"],
  ["admitted_source_count", "admittedCount"],
  ["training_eligible_unit_count", "trainingCount"],
];
const batchRows = [];
const outcomeRows = [];
for (const region of Object.keys(REGION_META)) {
  if (stats[region].candidateCount === 0) continue;
  const meta = REGION_META[region];
  const communitySearchIncluded =
    manifest.searchScopes[region].communityIncluded !== false;
  const current = { ...stats[region], explicitModeCount: 4 };
  const positiveMetrics = outcomeMetrics
    .filter(([, field]) => current[field] > 0)
    .map(([metric]) => metric);
  batchRows.push({
    regional_batch_id: meta.batchId,
    region_key: region,
    sequence_within_region: 1,
    batch_name: `${region}_REGIONAL_CANDIDATE_AND_RIGHTS_AUDIT`,
    targeted_unmet_gates:
      meta.tier === "CORE"
        ? "named_candidates;independent_families;structured_or_sensory;community;industry;rights_completeness"
        : meta.tier === "SECONDARY"
          ? "named_candidates;independent_families;rights_completeness"
          : "nonblocking_rights_cleared_regional_evidence_opportunity",
    structured_dataset_or_research_search_included: "true",
    structured_search_scope: manifest.searchScopes[region].structuredScope,
    structured_search_evidence_path:
      manifest.searchScopes[region].structuredEvidence,
    community_or_ugc_permission_search_included: bool(communitySearchIncluded),
    community_permission_search_scope:
      manifest.searchScopes[region].communityScope,
    community_permission_search_evidence_path:
      manifest.searchScopes[region].communityEvidence,
    candidate_count_before: 0,
    candidate_count_after: current.candidateCount,
    new_named_candidate_count: current.candidateCount,
    new_independent_source_family_count: current.familyCount,
    new_structured_preference_or_sensory_candidate_count:
      current.structuredCount,
    new_user_generated_or_community_source_candidate_count:
      current.communityCount,
    new_industry_or_professional_language_candidate_count:
      current.industryCount,
    new_explicit_mode_audit_count: 4,
    new_complete_rights_decision_count: current.completeRightsCount,
    new_admitted_source_count: 0,
    new_training_eligible_unit_count: 0,
    material_gain: "true",
    material_gain_basis: positiveMetrics.join(";"),
    qualifies_for_no_gain_counter: "false",
    consecutive_targeted_no_material_gain_count: 0,
    counter_transition_basis:
      "MATERIAL_GAIN_RESETS_REGION_LOCAL_COUNTER_TO_ZERO",
    regional_stop_state:
      meta.tier === "CORE"
        ? "CORE_CANDIDATE_FRAME_THRESHOLD_COMPLETE"
        : meta.tier === "SECONDARY"
          ? "SECONDARY_CANDIDATE_FRAME_AUDITED"
          : "NONBLOCKING_AUDIT_RECORDED",
    register_evidence_path:
      "db/data/round3j/regional_source_candidate_register.tsv",
    outcome_evidence_path:
      "db/data/round3j/regional_acquisition_outcome_ledger.tsv",
    completed_on: TODAY,
    limitation:
      "Candidate audit only; no source admitted and no training-eligible evidence unit created.",
  });
  for (const [metric, field] of outcomeMetrics) {
    const value = current[field];
    outcomeRows.push({
      regional_outcome_key: `outcome.${meta.batchId}.${metric}`,
      regional_batch_id: meta.batchId,
      region_key: region,
      candidate_key: "NOT_APPLICABLE",
      metric_key: metric,
      value_before_batch: 0,
      value_after_batch: value,
      delta: value,
      material_gain_contribution: bool(value > 0),
      evidence_path: "db/data/round3j/regional_source_candidate_register.tsv",
      recorded_on: TODAY,
      limitation:
        "Aggregate audit delta; raw row count is not an admitted regional coverage measure.",
    });
  }
}
writeOrCheck(
  join(DATA_DIR, "regional_acquisition_batch_ledger.tsv"),
  serializeTsv(batchHeader, batchRows),
);
writeOrCheck(
  join(DATA_DIR, "regional_acquisition_outcome_ledger.tsv"),
  serializeTsv(outcomeHeader, outcomeRows),
);

const modeAuditHeader = [
  "mode_audit_key",
  "scope_type",
  "regional_frame_key",
  "source_market_region",
  "language_tag",
  "data_mode",
  "candidate_count",
  "candidate_level_state",
  "admitted_source_count",
  "admitted_level_state",
  "evidence_path",
  "limitation",
];
const modeAuditRows = [];
for (const region of AUDITED_REGIONS) {
  const scopes = [
    {
      type: "REGIONAL_FRAME",
      market: "ALL_ATOMIC_MARKETS_IN_FRAME",
      language: "ALL_DECLARED_LANGUAGE_TAGS_IN_FRAME",
      rows: regionCandidates(region),
    },
  ];
  for (const market of [
    ...new Set(regionCandidates(region).map((candidate) => candidate.market)),
  ]) {
    for (const language of [
      ...new Set(
        regionCandidates(region)
          .filter((candidate) => candidate.market === market)
          .map((candidate) => candidate.language),
      ),
    ]) {
      scopes.push({
        type: "ATOMIC_MARKET_LANGUAGE",
        market,
        language,
        rows: regionCandidates(region).filter(
          (candidate) =>
            candidate.market === market && candidate.language === language,
        ),
      });
    }
  }
  for (const scope of scopes) {
    for (const mode of Object.keys(MODE_FIELDS)) {
      const count = scope.rows.filter((candidate) =>
        candidate.modes.includes(mode),
      ).length;
      modeAuditRows.push({
        mode_audit_key: `mode-audit.${region}.${scope.market}.${scope.language}.${mode}`,
        scope_type: scope.type,
        regional_frame_key: region,
        source_market_region: scope.market,
        language_tag: scope.language,
        data_mode: MODE_LABELS[mode],
        candidate_count: count,
        candidate_level_state: count
          ? "PRESENT_AT_CANDIDATE_LEVEL"
          : "MISSING_AT_CANDIDATE_LEVEL",
        admitted_source_count: 0,
        admitted_level_state: "MISSING_AT_ADMITTED_LEVEL",
        evidence_path: "db/data/round3j/regional_source_candidate_register.tsv",
        limitation:
          "Candidate presence is not admission, effective sample coverage, or representativeness.",
      });
    }
  }
}
writeOrCheck(
  join(DATA_DIR, "regional_mode_audit.tsv"),
  serializeTsv(modeAuditHeader, modeAuditRows),
);

const concentrationHeader = [
  "concentration_key",
  "regional_frame_key",
  "reported_measure_key",
  "denominator_unit",
  "denominator_count",
  "contributing_source_family_count",
  "largest_source_family_share",
  "top_3_source_family_share",
  "effective_source_family_count",
  "calculation_state",
  "regional_coverage_status",
  "regional_representativeness_claim",
  "evidence_path",
  "limitation",
];
const concentrationRows = [];
for (const region of AUDITED_REGIONS) {
  const current = stats[region];
  concentrationRows.push({
    concentration_key: `concentration.${region}.candidate-audit`,
    regional_frame_key: region,
    reported_measure_key: "CANDIDATE_AUDIT_RECORD_COUNT",
    denominator_unit: "DISTINCT_NAMED_CANDIDATE",
    denominator_count: current.candidateCount,
    contributing_source_family_count: current.familyCount,
    largest_source_family_share: format4(current.largestShare),
    top_3_source_family_share: format4(current.top3Share),
    effective_source_family_count: format4(current.effectiveFamilies),
    calculation_state: "CALCULATED_CANDIDATE_AUDIT_ONLY",
    regional_coverage_status:
      "CANDIDATE_FRAME_AUDITED_NO_REPRESENTATIVENESS_CLAIM",
    regional_representativeness_claim: "false",
    evidence_path: "db/data/round3j/regional_source_candidate_register.tsv",
    limitation:
      "Candidate-family concentration is separate from admitted evidence coverage.",
  });
  for (const measure of COVERAGE_MEASURES) {
    concentrationRows.push({
      concentration_key: `concentration.${region}.${measure.toLowerCase()}`,
      regional_frame_key: region,
      reported_measure_key: measure,
      denominator_unit: "ADMITTED_COUNTABLE_EVIDENCE_UNIT",
      denominator_count: 0,
      contributing_source_family_count: 0,
      largest_source_family_share: "NOT_COMPUTABLE_ZERO_UNITS",
      top_3_source_family_share: "NOT_COMPUTABLE_ZERO_UNITS",
      effective_source_family_count: "NOT_COMPUTABLE_ZERO_UNITS",
      calculation_state: "NOT_COMPUTABLE_ZERO_UNITS",
      regional_coverage_status: "NO_ADMITTED_COVERAGE",
      regional_representativeness_claim: "false",
      evidence_path: "db/data/round3j/regional_evidence_unit_register.tsv",
      limitation:
        "No admitted countable evidence unit exists; candidate metadata cannot substitute for coverage.",
    });
  }
}
writeOrCheck(
  join(DATA_DIR, "regional_source_family_concentration.tsv"),
  serializeTsv(concentrationHeader, concentrationRows),
);

const coverageHeader = [
  "coverage_measure_key",
  "regional_frame_key",
  "reported_measure_key",
  "reported_value",
  "counting_unit",
  "source_reported_not_acquired_value",
  "source_reported_not_acquired_basis",
  "training_eligibility_scope",
  "regional_coverage_status",
  "regional_representativeness_claim",
  "evidence_path",
  "limitation",
];
const coverageRows = AUDITED_REGIONS.flatMap((region) =>
  COVERAGE_MEASURES.map((measure) => ({
    coverage_measure_key: `coverage.${region}.${measure.toLowerCase()}`,
    regional_frame_key: region,
    reported_measure_key: measure,
    reported_value: 0,
    counting_unit:
      measure === "REGIONAL_SOURCE_FAMILY_COUNT"
        ? "DISTINCT_ADMITTED_CONTRIBUTING_SOURCE_FAMILY"
        : "DISTINCT_ADMITTED_COUNTABLE_EVIDENCE_UNIT",
    source_reported_not_acquired_value:
      manifest.sourceReportedNotAcquired?.[region]?.[measure] ?? "NOT_REPORTED",
    source_reported_not_acquired_basis:
      manifest.sourceReportedNotAcquired?.[region]?.basis ??
      "Candidate-page sample sizes, where noted, remain audit metadata and are excluded from coverage.",
    training_eligibility_scope: "NOT_ADMITTED",
    regional_coverage_status: "NO_ADMITTED_COVERAGE",
    regional_representativeness_claim: "false",
    evidence_path: "db/data/round3j/regional_evidence_unit_register.tsv",
    limitation:
      "Candidate count and public aggregate sample-size metadata do not create admitted regional sample coverage.",
  })),
);
writeOrCheck(
  join(DATA_DIR, "regional_coverage_measures.tsv"),
  serializeTsv(coverageHeader, coverageRows),
);

const cubeHeader = [
  "coverage_cell_key",
  "regional_frame_key",
  "source_market_region",
  "language_tag",
  "data_mode",
  "source_family_key",
  "preparation_scope",
  "roast_scope",
  "black_or_milk_scope",
  "consumer_or_professional_scope",
  "training_eligibility_role",
  "reported_measure_key",
  "reported_value",
  "largest_source_family_share",
  "top_3_source_family_share",
  "effective_source_family_count",
  "regional_coverage_status",
  "regional_representativeness_claim",
  "evidence_path",
  "limitation",
];
const cubeGroups = new Map();
for (const candidate of candidates) {
  for (const mode of candidate.modes) {
    const dimensions = [
      candidate.frame,
      candidate.market,
      candidate.language,
      MODE_LABELS[mode],
      candidate.family,
      candidate.preparation,
      candidate.roast,
      candidate.blackMilk,
      candidate.audience,
      "NOT_ADMITTED",
      "CANDIDATE_AUDIT_RECORD_COUNT",
    ];
    const digest = createHash("sha256")
      .update(dimensions.join("\u001f"))
      .digest("hex")
      .slice(0, 20);
    const key = `cube.r3j.regional.${digest}`;
    const group = cubeGroups.get(key) ?? { key, dimensions, candidates: [] };
    group.candidates.push(candidate);
    cubeGroups.set(key, group);
  }
}
const cubeRows = [...cubeGroups.values()].map((group) => {
  const [
    frame,
    market,
    language,
    mode,
    family,
    preparation,
    roast,
    blackMilk,
    audience,
    eligibility,
    measure,
  ] = group.dimensions;
  return {
    coverage_cell_key: group.key,
    regional_frame_key: frame,
    source_market_region: market,
    language_tag: language,
    data_mode: mode,
    source_family_key: family,
    preparation_scope: preparation,
    roast_scope: roast,
    black_or_milk_scope: blackMilk,
    consumer_or_professional_scope: audience,
    training_eligibility_role: eligibility,
    reported_measure_key: measure,
    reported_value: group.candidates.length,
    largest_source_family_share: format4(stats[frame].largestShare),
    top_3_source_family_share: format4(stats[frame].top3Share),
    effective_source_family_count: format4(stats[frame].effectiveFamilies),
    regional_coverage_status:
      "CANDIDATE_FRAME_AUDITED_NO_REPRESENTATIVENESS_CLAIM",
    regional_representativeness_claim: "false",
    evidence_path: "db/data/round3j/regional_source_candidate_register.tsv",
    limitation:
      "Audit-only candidate cell; not an admitted document, response, sensory sample, or training unit.",
  };
});
writeOrCheck(
  join(DATA_DIR, "regional_evidence_cube.tsv"),
  serializeTsv(cubeHeader, cubeRows),
);

const membershipHeader = readHeader(
  join(DATA_DIR, "regional_evidence_cube_membership.tsv"),
);
const membershipRows = [...cubeGroups.values()].flatMap((group) =>
  group.candidates.map((candidate) => ({
    coverage_membership_key: `membership.${group.key}.${candidate.key}`,
    coverage_cell_key: group.key,
    reported_measure_key: "CANDIDATE_AUDIT_RECORD_COUNT",
    membership_type: "CANDIDATE",
    candidate_key: `candidate.r3j.regional.${candidate.key}`,
    evidence_unit_key: "NOT_APPLICABLE",
    source_family_key: candidate.family,
    included: "true",
    exclusion_reason: "NOT_APPLICABLE",
    limitation:
      "Candidate audit membership only; never counted as admitted evidence coverage.",
  })),
);
writeOrCheck(
  join(DATA_DIR, "regional_evidence_cube_membership.tsv"),
  serializeTsv(membershipHeader, membershipRows),
);

const resultHeader = [
  "result_scope",
  "regional_frame_key",
  "region_class",
  "result_key",
  "observed_value",
  "required_value",
  "passed",
  "evidence_path",
  "limitation",
];
const resultRows = [
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "ORIGINAL_CANDIDATE_FRAME_COUNT",
    17,
    17,
    true,
    "db/data/round3j/source_candidate_register.tsv",
    "Immutable original frame.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "ORIGINAL_STOP_RULE_PRESERVED",
    true,
    true,
    true,
    "db/data/round3j/acquisition_batch_ledger.tsv",
    "Original Condition-B result remains valid in its original frame.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "ORIGINAL_STOP_RULE_GLOBAL_EFFECT_SUPERSEDED",
    true,
    true,
    true,
    "docs/research/coffee-sensory-kb-v0-round3j/REGIONAL_STOP_RULE_DECISION.md",
    "Only the global implication is superseded.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "ALL_CORE_REGIONAL_SOURCE_FRAMES_COMPLETE",
    true,
    true,
    true,
    "db/data/round3j/regional_source_candidate_register.tsv",
    "Candidate-frame thresholds only.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "ALL_SECONDARY_REGIONAL_SOURCE_FRAMES_AUDITED",
    true,
    true,
    true,
    "db/data/round3j/regional_source_candidate_register.tsv",
    "Admission remains preferred but is not a secondary audit threshold.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "REGIONAL_SOURCE_FRAME_COMPLETE",
    true,
    true,
    true,
    "this result",
    "All six blocking regional candidate frames are audited.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "REGIONAL_REPRESENTATIVENESS_CLAIM",
    false,
    false,
    true,
    "db/data/round3j/regional_source_family_concentration.tsv",
    "Candidate completeness is not population representativeness.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "GLOBAL_ACQUISITION_COMPLETE",
    false,
    false,
    true,
    "db/data/round3j/regional_coverage_measures.tsv",
    "Governed current-state value; no regional evidence source or training unit was admitted.",
  ],
  [
    "GATE",
    "GLOBAL",
    "GLOBAL",
    "ROUND3J_GLOBAL_ACQUISITION_COMPLETION_GATE",
    false,
    true,
    false,
    "db/data/round3j/regional_coverage_measures.tsv",
    "Blocks Round 3J merge or close despite completion of the regional candidate-frame audit.",
  ],
  [
    "GLOBAL",
    "GLOBAL",
    "GLOBAL",
    "GLOBAL_STOP_RULE_TRIGGERED",
    false,
    false,
    true,
    "db/data/round3j/regional_coverage_measures.tsv",
    "Regional frame prerequisites are now met, but global acquisition remains incomplete.",
  ],
];
for (const region of AUDITED_REGIONS) {
  const meta = REGION_META[region];
  const current = stats[region];
  const entries = [
    [
      "NAMED_SOURCE_CANDIDATE_COUNT",
      current.candidateCount,
      meta.minimumCandidates,
      current.candidateCount >= meta.minimumCandidates,
    ],
    [
      "AUDITED_INDEPENDENT_SOURCE_FAMILY_COUNT",
      current.familyCount,
      meta.minimumFamilies,
      current.familyCount >= meta.minimumFamilies,
    ],
    [
      "RIGHTS_AND_ACCESS_DECISION_COMPLETENESS",
      "1.0000",
      "1.0000",
      current.completeRightsCount === current.candidateCount,
    ],
    ["ADMITTED_SOURCE_COUNT", 0, "NOT_REQUIRED", true],
  ];
  if (meta.tier === "CORE") {
    entries.splice(
      2,
      0,
      [
        "STRUCTURED_PREFERENCE_OR_SENSORY_CANDIDATE_COUNT",
        current.structuredCount,
        1,
        current.structuredCount >= 1,
      ],
      [
        "USER_GENERATED_OR_COMMUNITY_SOURCE_CANDIDATE_COUNT",
        current.communityCount,
        1,
        current.communityCount >= 1,
      ],
      [
        "INDUSTRY_OR_PROFESSIONAL_LANGUAGE_CANDIDATE_COUNT",
        current.industryCount,
        1,
        current.industryCount >= 1,
      ],
    );
  }
  for (const [key, observed, required, passed] of entries) {
    resultRows.push([
      "REGION",
      region,
      meta.tier,
      key,
      observed,
      required,
      passed,
      "db/data/round3j/regional_source_candidate_register.tsv",
      "Candidate audit and admission counts remain separate.",
    ]);
  }
}
const resultObjects = resultRows.map((values) =>
  Object.fromEntries(
    resultHeader.map((field, index) => [field, values[index]]),
  ),
);
writeOrCheck(
  join(DATA_DIR, "regional_user_evidence_audit_result.tsv"),
  serializeTsv(resultHeader, resultObjects),
);

function markdownEscape(value) {
  return clean(value).replaceAll("`", "\\`");
}

const forumRows = registerRows.filter(
  (row) => row.forum_or_community_decision !== "NOT_APPLICABLE",
);
const authorizedForumCount = forumRows.filter((row) =>
  [
    "AUTHORIZED_API",
    "WRITTEN_PLATFORM_PERMISSION",
    "WRITTEN_AUTHOR_PERMISSION",
    "OPEN_LICENSED_SNAPSHOT",
    "DERIVED_ONLY_AUTHORIZED",
  ].includes(row.forum_or_community_decision),
).length;
const blockedForumCount = forumRows.filter((row) =>
  row.forum_or_community_decision.startsWith("BLOCKED_"),
).length;
const forumRequestCount = forumRows.filter(
  (row) => row.request_status === "DATA_REQUEST_PREPARED",
).length;

const receiptLines = [
  "ORIGINAL_CANDIDATE_FRAME_COUNT=17",
  "ORIGINAL_STOP_RULE_PRESERVED=true",
  "ORIGINAL_STOP_RULE_GLOBAL_EFFECT_SUPERSEDED=true",
  "",
  "CORE_REGION_COUNT=4",
  "SECONDARY_REGION_COUNT=2",
  "",
  ...BLOCKING_REGIONS.flatMap((region) => [
    `${region}_CANDIDATE_COUNT=${stats[region].candidateCount}`,
    `${region}_SOURCE_FAMILY_COUNT=${stats[region].familyCount}`,
    `${region}_ADMITTED_SOURCE_COUNT=0`,
    "",
  ]),
  `FORUM_OR_COMMUNITY_CANDIDATE_COUNT=${forumRows.length}`,
  `AUTHORIZED_FORUM_SOURCE_COUNT=${authorizedForumCount}`,
  `FORUM_PERMISSION_REQUEST_COUNT=${forumRequestCount}`,
  `BLOCKED_FORUM_SOURCE_COUNT=${blockedForumCount}`,
  "",
  "REGIONAL_SOURCE_FRAME_COMPLETE=true",
  "REGIONAL_REPRESENTATIVENESS_CLAIM=false",
  "GLOBAL_ACQUISITION_COMPLETE=false",
];

const auditLines = [
  "# Round 3J Regional User-Evidence Audit",
  "",
  `Recorded: ${TODAY}`,
  "",
  "The six blocking regional candidate frames are audited and satisfy their source-frame thresholds. This is a candidate and rights/access audit only: no source was admitted, no user content was scraped, no post or comment was inspected or copied, no training-eligible evidence unit was created, and no prepared request was sent.",
  "",
  "The original 17-candidate register, outcome ledger, four acquisition batches, and `CONDITION_B_MET_STOP_ACQUISITION` result remain unchanged. That stop result remains valid inside the original frame; only its global-exhaustion implication is superseded.",
  "",
  "The `false` regional-completion values in the expected-state and stop-decision artifacts are the immutable pre-audit baseline committed before regional research. Actual post-audit observations are recorded separately in `db/data/round3j/regional_user_evidence_audit_result.tsv`; the baseline is not rewritten after seeing results.",
  "",
  "## Machine receipt",
  "",
  "```makefile",
  ...receiptLines,
  "```",
  "",
  "## Regional frame results",
  "",
];
for (const region of AUDITED_REGIONS) {
  const meta = REGION_META[region];
  const current = stats[region];
  auditLines.push(
    `### ${meta.label}`,
    "",
    `- Candidate count: ${current.candidateCount}`,
    `- Audited independent source-family count: ${current.familyCount}`,
    `- Structured preference or sensory candidate count: ${current.structuredCount}`,
    `- Community candidate count: ${current.communityCount}`,
    `- Industry or professional-language candidate count: ${current.industryCount}`,
    "- Rights/access decision completeness: 1.0000",
    "- Admitted source count: 0",
    `- Candidate-family concentration: largest ${format4(current.largestShare)}; top three ${format4(current.top3Share)}; effective ${format4(current.effectiveFamilies)}`,
    `- Candidate-level modes: ${Object.keys(MODE_FIELDS)
      .map(
        (mode) => `${mode}=${current.modeCounts[mode] ? "PRESENT" : "MISSING"}`,
      )
      .join("; ")}`,
    "- Admitted-level modes: A=MISSING; B=MISSING; C=MISSING; D=MISSING",
    "",
  );
}
auditLines.push(
  "## Candidate register",
  "",
  "Each item below is an audited named candidate, not an admitted source or training unit.",
  "",
);
for (const candidate of candidates) {
  auditLines.push(
    `### ${markdownEscape(candidate.title)}`,
    "",
    `- Candidate: \`candidate.r3j.regional.${candidate.key}\``,
    `- Frame / market / language: \`${candidate.frame}\` / \`${candidate.market}\` / \`${candidate.language}\` (\`${candidate.script}\`)`,
    `- Modes: ${candidate.modes.length ? candidate.modes.join(", ") : "NONE (purchase/consumption behavior kept separate)"}`,
    `- Source family: \`${candidate.family}\``,
    `- Rights/access decision: \`${candidate.rightsDecision}\``,
    `- Community decision: \`${candidate.communityDecision ?? "NOT_APPLICABLE"}\``,
    `- Official source: ${candidate.url}`,
    `- Rights evidence: ${candidate.termsUrl}`,
    `- Limitation: ${markdownEscape(candidate.limitation)}`,
    "",
  );
}
auditLines.push(
  "## Coverage and concentration interpretation",
  "",
  "All six admitted regional coverage measures are zero because no source or evidence unit was admitted in this audit. Published sample sizes remain source-reported, not-acquired metadata and never enter regional coverage totals. Concentration over admitted evidence is therefore `NOT_COMPUTABLE_ZERO_UNITS`; the separately reported candidate-family concentration does not establish representativeness.",
  "",
  "Combined frames retain atomic markets and language tags. `zh-Hans-CN` and `zh-Hant-TW`, and `en-AU`, `en-NZ`, `en-US`, and `en-CA`, remain distinct. `und` is used where an uninspected community item cannot responsibly be assigned a dialect. No nationality, residence, or market is inferred from language alone.",
  "",
  "## Stop decision",
  "",
  "`ALL_CORE_REGIONAL_SOURCE_FRAMES_COMPLETE=true` and `ALL_SECONDARY_REGIONAL_SOURCE_FRAMES_AUDITED=true`. These are now satisfied prerequisites, not an automatic global stop. `GLOBAL_ACQUISITION_COMPLETE=false` because admission, effective-unit, training-eligibility, and representativeness gaps remain. No region invoked the two-consecutive-no-gain rule: each first regional batch produced candidate-frame material gain and reset its region-local counter to zero.",
  "",
  "## Request boundary",
  "",
  `There are ${dossierRows.length} complete prepared dossiers, including ${forumRequestCount} forum/community permission routes. Every one is recorded as unsent. Sending any request requires separate explicit user authorization.`,
  "",
);
writeOrCheck(
  join(DOC_DIR, "REGIONAL_USER_EVIDENCE_AUDIT.md"),
  await prettier.format(`${auditLines.join("\n")}\n`, { parser: "markdown" }),
);

const requestDocLines = [
  "# Round 3J Regional Permission and Data-Request Dossiers",
  "",
  `Prepared: ${TODAY}`,
  "",
  "These dossiers are preparation records only. No request has been sent. Explicit user authorization is required before any contact.",
  "",
];
for (const row of dossierRows) {
  requestDocLines.push(
    `## ${row.candidate_key}`,
    "",
    `- Contact target: ${markdownEscape(row.contact_target)}`,
    `- Exact requested fields: ${markdownEscape(row.exact_requested_fields)}`,
    `- Requested date range: ${markdownEscape(row.requested_date_range)}`,
    `- Raw-text requirement: ${markdownEscape(row.raw_text_requirement)}`,
    `- Derived-only alternative: ${markdownEscape(row.derived_only_alternative)}`,
    `- Privacy protections: ${markdownEscape(row.privacy_protections)}`,
    `- Intended model-research use: ${markdownEscape(row.intended_model_research_use)}`,
    `- Public-release boundary: ${markdownEscape(row.public_release_boundary)}`,
    `- Deletion/withdrawal procedure: ${markdownEscape(row.deletion_or_withdrawal_procedure)}`,
    "- Request status: `DATA_REQUEST_PREPARED`",
    "- Request sent: `false`",
    "",
  );
}
writeOrCheck(
  join(DOC_DIR, "REGIONAL_PERMISSION_AND_DATA_REQUEST_DOSSIERS.md"),
  await prettier.format(`${requestDocLines.join("\n")}\n`, {
    parser: "markdown",
  }),
);

assert(
  sha256(join(DATA_DIR, "source_candidate_register.tsv")) ===
    "3cbc8890a4e3c1fd65b1c664794ce5fe5f986d4f889b835e07e3d6a71d3c2471",
  "original candidate register changed",
);
assert(
  sha256(join(DATA_DIR, "acquisition_outcome_ledger.tsv")) ===
    "a57aee1a59a33efe5a1110ece439e89a30be90e60f1c6583d646b6c80ef8f918",
  "original outcome ledger changed",
);
assert(
  sha256(join(DATA_DIR, "acquisition_batch_ledger.tsv")) ===
    "10d60dc5727e48e3ff9291c065428dd19d3dc72734b06c5fa28a13f3ac7c2692",
  "original batch ledger changed",
);
assert(
  rowCount(join(DATA_DIR, "source_candidate_register.tsv")) === 17,
  "original candidate count changed",
);
assert(
  rowCount(join(DATA_DIR, "acquisition_outcome_ledger.tsv")) === 17,
  "original outcome count changed",
);
assert(
  rowCount(join(DATA_DIR, "acquisition_batch_ledger.tsv")) === 4,
  "original batch count changed",
);
assert(
  readFileSync(join(DATA_DIR, "acquisition_batch_ledger.tsv"), "utf8").includes(
    "CONDITION_B_MET_STOP_ACQUISITION",
  ),
  "original Condition-B result missing",
);
assert(
  rowCount(join(DATA_DIR, "regional_evidence_unit_register.tsv")) === 0,
  "unexpected evidence-unit admission",
);
assert(
  registerRows.every((row) => row.request_sent === "false"),
  "a request was marked sent",
);
assert(
  registerRows.every((row) => row.admission_state === "NOT_ADMITTED"),
  "unexpected admission",
);
assert(authorizedForumCount === 0, "unexpected forum authorization");
assert(forumRows.length === 13, "forum/community candidate count drifted");
assert(
  forumRequestCount === 13,
  "forum/community request dossier count drifted",
);
assert(blockedForumCount === 2, "blocked forum/community count drifted");
assert(
  dossierRows.every(
    (row) =>
      row.request_status === "DATA_REQUEST_PREPARED" &&
      row.request_sent === "false" &&
      ![
        row.contact_target,
        row.exact_requested_fields,
        row.requested_date_range,
        row.raw_text_requirement,
        row.derived_only_alternative,
        row.privacy_protections,
        row.intended_model_research_use,
        row.public_release_boundary,
        row.deletion_or_withdrawal_procedure,
      ].some((value) => !clean(value) || value === "NOT_APPLICABLE"),
  ),
  "an unsent request dossier is incomplete",
);
assert(
  forumRows.every((row) => {
    const expected = {
      DATA_REQUEST_PREPARED: "DATA_REQUEST_PREPARED",
      BLOCKED_AUTOMATION: "BLOCKED_AUTOMATION",
      BLOCKED_COPYRIGHT: "BLOCKED_COPYRIGHT",
      BLOCKED_PRIVACY: "BLOCKED_PRIVACY",
      BLOCKED_MODEL_USE: "BLOCKED_MODEL_USE",
      METADATA_ONLY: "METADATA_ONLY",
    }[row.forum_or_community_decision];
    return (
      expected === undefined || row.rights_and_access_decision === expected
    );
  }),
  "community and general rights decisions disagree",
);
assert(
  BLOCKING_REGIONS.every((region) => {
    const batch = batchRows.find((row) => row.region_key === region);
    return (
      batch?.structured_dataset_or_research_search_included === "true" &&
      batch.community_or_ugc_permission_search_included === "true" &&
      batch.material_gain === "true" &&
      batch.qualifies_for_no_gain_counter === "false" &&
      Number(batch.consecutive_targeted_no_material_gain_count) === 0
    );
  }),
  "a blocking regional batch lacks both search lanes or has an invalid stop counter",
);
assert(
  outcomeRows.every(
    (row) =>
      Number(row.delta) ===
      Number(row.value_after_batch) - Number(row.value_before_batch),
  ),
  "regional outcome delta mismatch",
);
assert(
  cubeRows.every(
    (row) =>
      row.training_eligibility_role === "NOT_ADMITTED" &&
      row.reported_measure_key === "CANDIDATE_AUDIT_RECORD_COUNT" &&
      row.regional_representativeness_claim === "false",
  ),
  "candidate cube was promoted into admitted coverage",
);
assert(
  coverageRows.every(
    (row) =>
      Number(row.reported_value) === 0 &&
      row.regional_coverage_status === "NO_ADMITTED_COVERAGE" &&
      row.regional_representativeness_claim === "false",
  ),
  "regional admitted-coverage guard failed",
);
assert(
  [
    "zh-Hans-CN",
    "zh-Hant-TW",
    "en-AU",
    "en-NZ",
    "en-US",
    "en-CA",
    "ja-JP",
    "ko-KR",
  ].every((tag) => candidates.some((candidate) => candidate.language === tag)),
  "a minimum supported language tag is absent",
);
assert(
  candidates
    .filter((candidate) => candidate.frame === "LATIN_AMERICA_NONBLOCKING")
    .filter((candidate) => candidate.language === "pt-BR").length === 1,
  "Latin America language-scope boundary drifted",
);

console.log(
  `${CHECK_MODE ? "verified" : "generated"} ${candidates.length} regional candidates, ${dossierRows.length} unsent request dossiers, and ${cubeRows.length} audit-only cube cells`,
);
