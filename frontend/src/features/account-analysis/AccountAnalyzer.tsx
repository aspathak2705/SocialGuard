import React, { useState } from 'react';
import { validateAccountTarget, collectAccountData, ApiServiceError } from '../../services/api';
import type { AccountTarget, CollectionResult } from '../../types/account';

export const AccountAnalyzer: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validatedTarget, setValidatedTarget] = useState<AccountTarget | null>(null);
  const [serverMessage, setServerMessage] = useState<string | null>(null);

  // Phase 2 Acquisition States
  const [isCollecting, setIsCollecting] = useState(false);
  const [collectionResult, setCollectionResult] = useState<CollectionResult | null>(null);
  const [collectionError, setCollectionError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();

    if (!trimmed) {
      setError('Please enter an Instagram username or profile URL.');
      setValidatedTarget(null);
      setServerMessage(null);
      setCollectionResult(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    setValidatedTarget(null);
    setServerMessage(null);
    setCollectionResult(null);
    setCollectionError(null);

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

  const handleStartAcquisition = async () => {
    if (!validatedTarget) return;

    setIsCollecting(true);
    setCollectionError(null);
    setCollectionResult(null);

    try {
      const res = await collectAccountData(validatedTarget.original_input);
      setCollectionResult(res.data);
    } catch (err: unknown) {
      if (err instanceof ApiServiceError) {
        setCollectionError(err.message);
      } else {
        setCollectionError('Unexpected error occurred during data acquisition.');
      }
    } finally {
      setIsCollecting(false);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'success':
      case 'completed':
        return 'neo-badge-lime';
      case 'partial':
        return 'neo-badge-amber';
      case 'failed':
      case 'timed_out':
        return 'neo-badge-pink';
      default:
        return 'neo-badge-purple';
    }
  };

  return (
    <div className="neo-card" id="analyze-section">
      <form onSubmit={handleSubmit} noValidate>
        <div className="neo-form-group">
          <label htmlFor="account-target-input" className="neo-form-label">
            Target Account (Username or Profile URL)
          </label>
          <div className="neo-input-container">
            <input
              id="account-target-input"
              type="text"
              className="neo-text-input"
              placeholder="e.g. johndoe or https://www.instagram.com/johndoe/"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isLoading || isCollecting}
              aria-describedby="target-input-hint"
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="submit"
              className="neo-submit-btn"
              disabled={isLoading || isCollecting || !inputValue.trim()}
            >
              {isLoading ? 'Validating...' : 'Analyze'}
            </button>
          </div>
          <p id="target-input-hint" className="neo-form-hint">
            Accepts raw usernames (with or without @) or direct Instagram URLs.
          </p>
        </div>
      </form>

      {/* Error Presentation */}
      {error && (
        <div className="neo-alert neo-alert-error" role="alert">
          <div className="neo-alert-title">Target Validation Failed</div>
          <p>{error}</p>
        </div>
      )}

      {/* Target Validated Presentation */}
      {validatedTarget && (
        <div className="neo-alert neo-alert-success animate-entrance" role="status">
          <div className="neo-alert-title">Target Validated Successfully</div>
          <p>{serverMessage}</p>
          <div className="neo-target-details">
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

          {/* Phase 2: Action to trigger multi-adapter acquisition */}
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: 'var(--border-thin)' }}>
            <button
              onClick={handleStartAcquisition}
              className="neo-btn-primary"
              disabled={isCollecting}
              style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}
            >
              {isCollecting ? 'Acquiring Multi-Source Data...' : 'Run Phase 2 Data Acquisition →'}
            </button>
          </div>
        </div>
      )}

      {/* Collection Error */}
      {collectionError && (
        <div className="neo-alert neo-alert-error animate-entrance" role="alert">
          <div className="neo-alert-title">Data Acquisition Notice</div>
          <p>{collectionError}</p>
        </div>
      )}

      {/* Phase 2 Acquisition Results */}
      {collectionResult && (
        <div className="neo-alert neo-alert-success animate-entrance" style={{ marginTop: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div className="neo-alert-title" style={{ margin: 0 }}>
              Acquisition Job: {collectionResult.request_id}
            </div>
            <span className={`neo-evidence-badge ${getStatusBadgeClass(collectionResult.overall_status)}`}>
              STATUS: {collectionResult.overall_status.toUpperCase()}
            </span>
          </div>

          <p style={{ fontSize: '0.82rem', marginBottom: '1rem' }}>
            Data collected from configured adapters. Partial outcomes preserved without fabricating missing observations.
          </p>

          {/* Per-collector outcomes */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginTop: '0.75rem' }}>
            {Object.entries(collectionResult.sources).map(([src, status]) => (
              <div key={src} style={{ border: 'var(--border-thin)', padding: '0.75rem', backgroundColor: 'var(--color-white)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <strong style={{ fontSize: '0.85rem', textTransform: 'uppercase' }}>{src}</strong>
                  <span className={`neo-evidence-badge ${getStatusBadgeClass(status.status)}`}>
                    {status.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <div>Duration: {status.duration_ms ? `${status.duration_ms}ms` : 'N/A'}</div>
                  {status.error_code && <div style={{ color: '#dc2626' }}>Code: {status.error_code}</div>}
                  <div>Collected: {status.collected_field_names.length} fields</div>
                </div>
              </div>
            ))}
          </div>

          {/* Observations Summary */}
          {collectionResult.observations.length > 0 && (
            <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: 'var(--border-thin)' }}>
              <strong style={{ fontSize: '0.8rem', textTransform: 'uppercase' }}>Observations Acquired:</strong>
              <div style={{ fontSize: '0.8rem', marginTop: '0.35rem' }}>
                {collectionResult.observations.map((obs, idx) => (
                  <div key={idx} style={{ marginBottom: '0.35rem' }}>
                    • Source <strong>{obs.source_provenance}</strong>: Completeness score{' '}
                    <strong>{obs.completeness_score !== undefined ? `${Math.round((obs.completeness_score || 0) * 100)}%` : 'N/A'}</strong>
                    {obs.posts_count !== undefined && ` | Posts: ${obs.posts_count}`}
                    {obs.followers_count !== undefined && ` | Followers: ${obs.followers_count}`}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
