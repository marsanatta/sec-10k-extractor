export type Status = "present" | "legitimately_absent" | "extraction_failure";
export type Band = "high" | "medium" | "low" | "unscored";

export interface Confidence {
  band: Band;
  score: number | null;
  signals: string[];
}

export interface Provenance {
  extractors: string[];
  checks_passed: string[];
  checks_failed: string[];
}

export interface Item {
  item_id: string;
  part: string;
  item: string;
  title: string;
  text: string;
  char_range: [number, number] | null;
  status: Status;
  confidence: Confidence;
  provenance: Provenance;
}

export interface FilingMeta {
  cik: string;
  accession: string;
  company: string;
  form: string;
  filing_date: string;
  fiscal_year: number | null;
  format_era: string;
  primary_document: string | null;
  source_url: string | null;
  smaller_reporting: boolean | null;
}

export interface Summary {
  needs_review: boolean;
  coverage_fraction: number;
  items_present: number;
  items_legitimately_absent: number;
  items_extraction_failure: number;
  structural_ok?: boolean;
  round_trip_ok?: boolean;
  coverage_plausible?: boolean;
  item8_markers: boolean | null;
  item8_xbrl_found: number;
  item8_xbrl_checked: number;
  boundary_disagreements: string[];
  boundary_checked?: number;
  low_confidence_items: number;
  medium_confidence_items: number;
  title_mismatches?: number;
  escalation_candidates: string[];
  escalation_provider: string;
  escalation_performed: boolean;
  escalation_calls: number;
  escalation_applied: number;
  escalation_items_moved: string[];
  escalation_input_tokens: number;
  escalation_output_tokens: number;
  format_era: string;
}

export interface ExtractionResult {
  meta: FilingMeta;
  items: Item[];
  canonical_text_len: number;
  summary: Summary;
  canonical_text: string;
}

export interface DemoEntry {
  id: string;
  label: string;
  accession?: string;
  ticker?: string;
  fiscal_year?: number;
  note: string;
  group: "good" | "limitation";
  detail: string;
}

export interface ExtractRequest {
  ticker?: string;
  fiscal_year?: number;
  accession?: string;
  model?: string;
  escalate?: boolean;
}

export interface ModelInfo {
  id: string;
  name: string;
}
