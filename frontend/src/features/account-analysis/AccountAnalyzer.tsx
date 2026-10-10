import React, { useState } from 'react';
import { validateAccountTarget, processPipelineData, ApiServiceError } from '../../services/api';
import type { AccountTarget, UnifiedCollectionRun } from '../../types/account';

export const AccountAnalyzer: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validatedTarget, setValidatedTarget] = useState<AccountTarget | null>(null);
  const [serverMessage, setServerMessage] = useState<string | null>(null);

  // Phase 3 Unified Pipeline States
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineRun, setPipelineRun] = useState<UnifiedCollectionRun | null>(null);
  const [pipelineError, setPipelineError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();

    if (!trimmed) {
      setError('Please enter an Instagram username or profile URL.');
      setValidatedTarget(null);
      setServerMessage(null);
      setPipelineRun(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    setValidatedTarget(null);
    setServerMessage(null);
    setPipelineRun(null);
    setPipelineError(null);

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

  const handleStartPipeline = async () => {
    if (!validatedTarget) return;

    setIsProcessing(true);
    setPipelineError(null);
    setPipelineRun(null);

    try {
      const res = await processPipelineData(validatedTarget.original_input);
      setPipelineRun(res.data);
    } catch (err: unknown) {
      if (err instanceof ApiServiceError) {
        setPipelineError(err.message);
      } else {
        setPipelineError('Unexpected error occurred during pipeline execution.');
      }
    } finally {
      setIsProcessing(false);
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
              disabled={isLoading || isProcessing}
              aria-describedby="target-input-hint"
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="submit"
              className="neo-submit-btn"
              disabled={isLoading || isProcessing || !inputValue.trim()}
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

          {/* Phase 3 Pipeline Trigger */}
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: 'var(--border-thin)' }}>
            <button
              onClick={handleStartPipeline}
              className="neo-btn-primary"
              disabled={isProcessing}
              style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}
            >
              {isProcessing ? 'Processing Unified Pipeline...' : 'Run Phase 3 Unified Pipeline →'}
            </button>
          </div>
        </div>
      )}

      {/* Pipeline Error */}
      {pipelineError && (
        <div className="neo-alert neo-alert-error animate-entrance" role="alert">
          <div className="neo-alert-title">Pipeline Notice</div>
          <p>{pipelineError}</p>
        </div>
      )}

      {/* Phase 3 Unified Pipeline Results */}
      {pipelineRun && (
        <div className="neo-alert neo-alert-success animate-entrance" style={{ marginTop: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div className="neo-alert-title" style={{ margin: 0 }}>
              Pipeline Run: {pipelineRun.run_id} (v{pipelineRun.pipeline_version})
            </div>
            <span className={`neo-evidence-badge ${getStatusBadgeClass(pipelineRun.overall_status)}`}>
              STATUS: {pipelineRun.overall_status.toUpperCase()}
            </span>
          </div>

          {/* Data Quality Overview */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', margin: '0.75rem 0' }}>
            <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: 'var(--color-white)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RAW RECEIVED</div>
              <strong>{pipelineRun.quality_summary.raw_records_received}</strong>
            </div>
            <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: 'var(--color-white)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>NORMALIZED</div>
              <strong>{pipelineRun.quality_summary.valid_normalized_records}</strong>
            </div>
            <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: 'var(--color-white)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>DUPLICATES</div>
              <strong>{pipelineRun.quality_summary.duplicate_records_detected}</strong>
            </div>
            <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: 'var(--color-white)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RETAINED</div>
              <strong>{pipelineRun.quality_summary.retained_records}</strong>
            </div>
            {pipelineRun.quality_summary.completeness_score !== undefined && (
              <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: 'var(--color-white)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>COMPLETENESS</div>
                <strong>{Math.round((pipelineRun.quality_summary.completeness_score || 0) * 100)}%</strong>
              </div>
            )}
          </div>

          {/* Source Execution Outcomes */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginTop: '0.75rem' }}>
            {Object.entries(pipelineRun.source_executions).map(([src, status]) => (
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
                  <div>Collected Fields: {status.collected_field_names.length}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Canonical Observations Explorer */}
          {pipelineRun.canonical_observations.length > 0 && (
            <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: 'var(--border-thin)' }}>
              <strong style={{ fontSize: '0.8rem', textTransform: 'uppercase' }}>Canonical Observations (Traceable):</strong>
              <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {pipelineRun.canonical_observations.map((obs) => (
                  <div key={obs.observation_id} style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: 'var(--color-white)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span><strong>{obs.observation_type.toUpperCase()}</strong> ({obs.observation_id})</span>
                      <span className="neo-evidence-badge neo-badge-purple">{obs.source}</span>
                    </div>
                    <div style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                      Provenance: {obs.source} • Timestamp: {new Date(obs.observation_timestamp).toLocaleTimeString()}
                      {obs.posts_count !== undefined && ` • Posts: ${obs.posts_count}`}
                      {obs.followers_count !== undefined && ` • Followers: ${obs.followers_count}`}
                    </div>
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
