export type TargetInputType = 'username' | 'profile_url';

export interface AccountTarget {
  original_input: string;
  normalized_username: string;
  canonical_profile_url: string;
  input_type: TargetInputType;
}

export interface AccountValidateResponseData {
  is_valid: boolean;
  target: AccountTarget;
  message: string;
}

export type CollectorSource = 'instaloader' | 'gallery-dl' | 'playwright';

export type DataSourceExecutionStatus =
  | 'pending'
  | 'running'
  | 'success'
  | 'partial'
  | 'failed'
  | 'skipped'
  | 'unavailable'
  | 'timed_out';

export interface DataSourceStatus {
  source: CollectorSource;
  status: DataSourceExecutionStatus;
  duration_ms?: number;
  capabilities_attempted?: string[];
  collected_field_names: string[];
  missing_field_names: string[];
  error_code?: string;
  error_message?: string;
  retryable?: boolean;
  collection_timestamp?: string;
}

export interface AccountObservation {
  account_id?: string;
  username: string;
  full_name?: string;
  biography?: string;
  is_private?: boolean;
  is_verified?: boolean;
  posts_count?: number;
  followers_count?: number;
  following_count?: number;
  has_profile_pic?: boolean;
  external_url?: string;
  observation_timestamp: string;
  source_provenance: CollectorSource;
  completeness_score?: number;
}

export type OverallCollectionStatus =
  | 'not_started'
  | 'in_progress'
  | 'completed'
  | 'partial'
  | 'failed'
  | 'timed_out';

export interface CollectionResult {
  request_id: string;
  target: AccountTarget;
  overall_status: OverallCollectionStatus;
  sources: Record<CollectorSource, DataSourceStatus>;
  observations: AccountObservation[];
  missing_data_summary: string[];
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

// Phase 3 Pipeline Types
export type ObservationType = 'profile' | 'media' | 'post' | 'browser_dom';
export type FieldAvailabilityStatus = 'observed' | 'not_returned' | 'unavailable' | 'not_applicable' | 'invalid';

export interface FieldValueMetadata {
  field_name: string;
  status: FieldAvailabilityStatus;
  raw_value?: unknown;
  detail?: string;
}

export interface CanonicalObservation {
  observation_id: string;
  observation_type: ObservationType;
  target_username: string;
  source: CollectorSource;
  source_record_id?: string;
  observation_timestamp: string;
  normalization_timestamp: string;
  account_id?: string;
  full_name?: string;
  biography?: string;
  is_private?: boolean;
  is_verified?: boolean;
  posts_count?: number;
  followers_count?: number;
  following_count?: number;
  has_profile_pic?: boolean;
  external_url?: string;
  field_metadata: Record<string, FieldValueMetadata>;
  validation_warnings: string[];
  is_duplicate: boolean;
  duplicate_of?: string;
}

export interface DataQualitySummary {
  raw_records_received: number;
  valid_normalized_records: number;
  invalid_records_rejected: number;
  duplicate_records_detected: number;
  retained_records: number;
  completeness_score?: number;
  source_breakdown: Partial<Record<CollectorSource, Record<string, number>>>;
  warnings: string[];
}

export interface UnifiedCollectionRun {
  run_id: string;
  target: AccountTarget;
  overall_status: OverallCollectionStatus;
  pipeline_version: string;
  created_at: string;
  completed_at?: string;
  source_executions: Partial<Record<CollectorSource, DataSourceStatus>>;
  canonical_observations: CanonicalObservation[];
  quality_summary: DataQualitySummary;
  missing_data_summary: string[];
  errors: string[];
}

export interface ApiSuccessResponse<T> {
  success: true;
  timestamp: string;
  data: T;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiErrorResponse {
  success: false;
  timestamp: string;
  error: ApiErrorDetail;
}

export type AccountValidateResponse = ApiSuccessResponse<AccountValidateResponseData>;
export type AccountAcquisitionResponse = ApiSuccessResponse<CollectionResult>;
export type PipelineProcessResponse = ApiSuccessResponse<UnifiedCollectionRun>;

// Phase 5 Prediction & Explainability Types
export interface FeatureContribution {
  feature_name: string;
  feature_value: number;
  contribution: number;
  direction: 'fake' | 'genuine';
  display_name?: string;
  description?: string;
}

export interface KeyFactor {
  feature_name: string;
  display_name: string;
  direction: string;
  contribution_value: number;
  explanation: string;
}

export interface ExplanationResult {
  status: 'available' | 'fallback' | 'evidence_only' | 'unavailable';
  provider: 'openrouter_nemotron' | 'deterministic_fallback' | 'evidence_only' | 'unavailable';
  model_id: string;
  method: string;
  summary: string;
  key_factors?: KeyFactor[];
  conflicting_signals?: string[];
  limitations?: string[];
  review_guidance?: string[];
  contributions: FeatureContribution[];
  top_drivers: string[];
  warning?: string;
}


export interface EvidenceItem {
  field_name: string;
  observed_value: unknown;
  source: string;
  observation_id?: string;
  timestamp?: string;
}

export interface PredictionAssessment {
  request_id: string;
  target_username: string;
  predicted_class: 'fake' | 'genuine';
  fake_probability: number;
  score_label: string;
  decision_threshold: number;
  model_id: string;
  pipeline_version: string;
  verification_status: 'PROVISIONAL' | 'APPROVED';
  verification_note: string;
  feature_coverage_ratio: number;
  missing_features: string[];
  extracted_features: Record<string, number>;
  evidence: EvidenceItem[];
  explanation: ExplanationResult;
  warnings: string[];
  created_at: string;
  processing_time_ms: number;
}

export type PredictionResponse = ApiSuccessResponse<PredictionAssessment>;

