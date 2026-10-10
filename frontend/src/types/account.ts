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
