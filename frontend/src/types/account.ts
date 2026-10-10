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
