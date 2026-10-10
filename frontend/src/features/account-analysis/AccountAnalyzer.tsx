import React, { useState } from 'react';
import { validateAccountTarget, ApiServiceError } from '../../services/api';
import type { AccountTarget } from '../../types/account';

export const AccountAnalyzer: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validatedTarget, setValidatedTarget] = useState<AccountTarget | null>(null);
  const [serverMessage, setServerMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();

    // Client-side pre-validation
    if (!trimmed) {
      setError('Please enter an Instagram username or profile URL.');
      setValidatedTarget(null);
      setServerMessage(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    setValidatedTarget(null);
    setServerMessage(null);

    try {
      const response = await validateAccountTarget(trimmed);
      setValidatedTarget(response.data.target);
      setServerMessage(response.data.message);
    } catch (err: unknown) {
      if (err instanceof ApiServiceError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while communicating with the server.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit} noValidate>
        <div className="form-group">
          <label htmlFor="account-target-input" className="form-label">
            Target Account (Username or Profile URL)
          </label>
          <div className="input-container">
            <input
              id="account-target-input"
              type="text"
              className="text-input"
              placeholder="e.g. johndoe or https://www.instagram.com/johndoe/"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isLoading}
              aria-describedby="target-input-hint"
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="submit"
              className="submit-btn"
              disabled={isLoading || !inputValue.trim()}
            >
              {isLoading ? 'Validating...' : 'Analyze'}
            </button>
          </div>
          <p id="target-input-hint" className="form-hint">
            Accepts raw usernames (with or without @) or direct Instagram URLs.
          </p>
        </div>
      </form>

      {/* Error Presentation */}
      {error && (
        <div className="alert alert-error" role="alert">
          <div className="alert-title">Target Validation Failed</div>
          <p>{error}</p>
        </div>
      )}

      {/* Honest Validated Target Presentation (No Fake ML predictions) */}
      {validatedTarget && (
        <div className="alert alert-success" role="status">
          <div className="alert-title">Target Validated Successfully</div>
          <p>{serverMessage}</p>
          <div className="target-details">
            <div>
              <span>Normalized Username:</span> @{validatedTarget.normalized_username}
            </div>
            <div>
              <span>Detected Type:</span> {validatedTarget.input_type}
            </div>
            <div>
              <span>Canonical URL:</span>{' '}
              <a
                href={validatedTarget.canonical_profile_url}
                target="_blank"
                rel="noreferrer"
                style={{ color: 'inherit', textDecoration: 'underline' }}
              >
                {validatedTarget.canonical_profile_url}
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
