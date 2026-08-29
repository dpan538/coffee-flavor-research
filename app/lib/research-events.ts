export const COLLECTION_MODE = "NO_REMOTE_COLLECTION" as const;
export const STORAGE_MODE = "LOCAL_ONLY_OR_NO_OP" as const;
export const EVENT_CONTRACT_VERSION = "round4a-first-party-event-v1";
const LOCAL_EVENT_KEY = "coffee-flavor-atlas:round4a:synthetic-events";

export type CompletionState = "STARTED" | "COMPLETED" | "ABANDONED";
export type WithdrawalState = "ACTIVE" | "WITHDRAWN" | "DELETED";

export interface LocalResearchEvent {
  pseudonymous_participant_id: string;
  pseudonymous_session_id: string;
  consent_version: string;
  model_use_consent: boolean;
  C0: string;
  C1: number;
  question_id: string;
  question_version: string;
  question_order: number;
  answer: string | null;
  answer_latency_ms: number;
  candidate_set_version: string;
  candidate_rank: number | null;
  candidate_selected: boolean;
  candidate_rejected: boolean;
  none_of_these_selected: boolean;
  confidence: string | null;
  completion_state: CompletionState;
  withdrawal_state: WithdrawalState;
  fixture_mode: "SYNTHETIC_UI_PREVIEW";
}

function storageAvailable(): boolean {
  return (
    typeof window !== "undefined" && typeof window.localStorage !== "undefined"
  );
}

export function previewSyntheticEvent(
  partial: Partial<LocalResearchEvent> = {},
): LocalResearchEvent {
  return {
    pseudonymous_participant_id: "synthetic-participant-preview",
    pseudonymous_session_id: "synthetic-session-preview",
    consent_version: "round4a-preview-consent-v1",
    model_use_consent: false,
    C0: "filter",
    C1: 4,
    question_id: "Q1",
    question_version: "round4a-q-v1",
    question_order: 1,
    answer: null,
    answer_latency_ms: 0,
    candidate_set_version: "round4a-objective-m-deterministic-v1",
    candidate_rank: null,
    candidate_selected: false,
    candidate_rejected: false,
    none_of_these_selected: false,
    confidence: null,
    completion_state: "STARTED",
    withdrawal_state: "ACTIVE",
    fixture_mode: "SYNTHETIC_UI_PREVIEW",
    ...partial,
  };
}

export function saveSyntheticPreview(event: LocalResearchEvent): void {
  if (!storageAvailable()) return;
  const current = readSyntheticPreviews();
  window.localStorage.setItem(
    LOCAL_EVENT_KEY,
    JSON.stringify([...current, event]),
  );
}

export function readSyntheticPreviews(): LocalResearchEvent[] {
  if (!storageAvailable()) return [];
  const value = window.localStorage.getItem(LOCAL_EVENT_KEY);
  if (!value) return [];
  try {
    const rows: unknown = JSON.parse(value);
    return Array.isArray(rows) ? (rows as LocalResearchEvent[]) : [];
  } catch {
    return [];
  }
}

export function exportSyntheticPreview(): string {
  return JSON.stringify(
    {
      contract_version: EVENT_CONTRACT_VERSION,
      collection_mode: COLLECTION_MODE,
      storage_mode: STORAGE_MODE,
      empirical_data: false,
      events: readSyntheticPreviews(),
    },
    null,
    2,
  );
}

export function withdrawAndDeleteLocalPreviews(): number {
  if (!storageAvailable()) return 0;
  const count = readSyntheticPreviews().length;
  window.localStorage.removeItem(LOCAL_EVENT_KEY);
  return count;
}
