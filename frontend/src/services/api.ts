import type {
  AccountValidateResponse,
  AccountAcquisitionResponse,
  ApiErrorResponse,
} from '../types/account';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
const REQUEST_TIMEOUT_MS = 25000;

export class ApiServiceError extends Error {
  code: string;
  details?: unknown;

  constructor(message: string, code: string = 'CLIENT_ERROR', details?: unknown) {
    super(message);
    this.name = 'ApiServiceError';
    this.code = code;
    this.details = details;
  }
}

export async function validateAccountTarget(input: string): Promise<AccountValidateResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const response = await fetch(`${API_BASE_URL}/accounts/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      if (data && 'error' in data) {
        const errResp = data as ApiErrorResponse;
        throw new ApiServiceError(
          errResp.error.message || 'Validation failed.',
          errResp.error.code || `HTTP_${response.status}`,
          errResp.error.details
        );
      }
      throw new ApiServiceError(
        `Server returned error ${response.status}: ${response.statusText}`,
        `HTTP_${response.status}`
      );
    }

    return data as AccountValidateResponse;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof ApiServiceError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiServiceError('Validation request timed out.', 'TIMEOUT_ERROR');
    }
    throw new ApiServiceError(
      'Unable to connect to SocialGuard backend server. Please verify backend service is running on port 8000.',
      'NETWORK_ERROR'
    );
  }
}

export async function collectAccountData(input: string): Promise<AccountAcquisitionResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}/acquisition/collect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      if (data && 'error' in data) {
        const errResp = data as ApiErrorResponse;
        throw new ApiServiceError(
          errResp.error.message || 'Data collection failed.',
          errResp.error.code || `HTTP_${response.status}`,
          errResp.error.details
        );
      }
      throw new ApiServiceError(
        `Server returned error ${response.status}: ${response.statusText}`,
        `HTTP_${response.status}`
      );
    }

    return data as AccountAcquisitionResponse;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof ApiServiceError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiServiceError('Data collection request timed out.', 'TIMEOUT_ERROR');
    }
    throw new ApiServiceError(
      'Unable to communicate with SocialGuard acquisition service.',
      'NETWORK_ERROR'
    );
  }
}
