import React, { useState } from 'react';
import {
  validateAccountTarget,
  processPipelineData,
  predictAccountInference,
  ApiServiceError,
} from '../../services/api';
import type {
  AccountTarget,
  UnifiedCollectionRun,
  PredictionAssessment,
} from '../../types/account';

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

  // Phase 5 ML Inference States
  const [isPredicting, setIsPredicting] = useState(false);
  const [prediction, setPrediction] = useState<PredictionAssessment | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();

    if (!trimmed) {
      setError('Please enter an Instagram username or profile URL.');
      setValidatedTarget(null);
      setServerMessage(null);
      setPipelineRun(null);
      setPrediction(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    setValidatedTarget(null);
    setServerMessage(null);
    setPipelineRun(null);
    setPipelineError(null);
    setPrediction(null);
    setPredictionError(null);

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

  const handleRunPrediction = async () => {
    if (!validatedTarget) return;

    setIsPredicting(true);
    setPredictionError(null);
    setPrediction(null);

    try {
      const res = await predictAccountInference(validatedTarget.normalized_username);
      setPrediction(res.data);
    } catch (err: unknown) {
      if (err instanceof ApiServiceError) {
        setPredictionError(err.message);
      } else {
        setPredictionError('Unexpected error during model inference execution.');
      }
    } finally {
      setIsPredicting(false);
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
              disabled={isLoading || isProcessing || isPredicting}
              aria-describedby="target-input-hint"
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="submit"
              className="neo-submit-btn"
              disabled={isLoading || isProcessing || isPredicting || !inputValue.trim()}
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

          {/* Action Trigger Buttons */}
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: 'var(--border-thin)', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button
              onClick={handleStartPipeline}
              className="neo-btn-secondary"
              disabled={isProcessing || isPredicting}
              style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}
            >
              {isProcessing ? 'Processing Unified Pipeline...' : 'Run Phase 3 Unified Pipeline →'}
            </button>
            <button
              onClick={handleRunPrediction}
              className="neo-btn-primary"
              disabled={isProcessing || isPredicting}
              style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}
            >
              {isPredicting ? 'Executing Inference & SHAP...' : 'Run Phase 5 AI Inference →'}
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


      {/* Prediction Error */}
      {predictionError && (
        <div className="neo-alert neo-alert-error animate-entrance" role="alert" style={{ marginTop: '1.5rem' }}>
          <div className="neo-alert-title">Inference Execution Error</div>
          <p>{predictionError}</p>
        </div>
      )}

      {/* Phase 5 Model Prediction & Investigation Dashboard */}
      {prediction && (
        <div className="neo-card animate-entrance" style={{ marginTop: '1.5rem', border: '3px solid #000' }}>
          {/* Provisional Banner */}
          <div
            style={{
              backgroundColor: '#fef08a',
              borderBottom: '2px solid #000',
              padding: '0.75rem',
              fontWeight: 700,
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span>⚠️</span>
            <span>{prediction.verification_note}</span>
          </div>

          <div style={{ padding: '1.25rem' }}>
            {/* Header / Assessment Summary */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', borderBottom: 'var(--border-thin)', paddingBottom: '1rem' }}>
              <div>
                <span className="neo-eyebrow">ASSESSMENT REPORT • {prediction.request_id}</span>
                <h3 style={{ margin: '0.25rem 0', fontSize: '1.4rem' }}>
                  Target: @{prediction.target_username}
                </h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Model: {prediction.model_id} • Status: <strong>{prediction.verification_status}</strong> • Time: {prediction.processing_time_ms}ms
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span
                  className="neo-evidence-badge"
                  style={{
                    backgroundColor: prediction.predicted_class === 'fake' ? '#fda4af' : '#bef264',
                    fontSize: '1rem',
                    padding: '0.4rem 0.8rem',
                  }}
                >
                  PREDICTED: {prediction.predicted_class.toUpperCase()}
                </span>
                <div style={{ fontSize: '0.75rem', marginTop: '0.35rem', fontWeight: 600 }}>
                  Probability: {(prediction.fake_probability * 100).toFixed(1)}% ({prediction.score_label})
                </div>
              </div>
            </div>

            {/* Quality & Coverage Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', margin: '1rem 0' }}>
              <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: '#f9fafb' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>FEATURE COVERAGE</div>
                <strong>{Math.round(prediction.feature_coverage_ratio * 100)}%</strong>
              </div>
              <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: '#f9fafb' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>DECISION THRESHOLD</div>
                <strong>{prediction.decision_threshold}</strong>
              </div>
              <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: '#f9fafb' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MISSING FEATURES</div>
                <strong>{prediction.missing_features.length}</strong>
              </div>
              <div style={{ border: 'var(--border-thin)', padding: '0.5rem', backgroundColor: '#f9fafb' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>EXPLANATION METHOD</div>
                <strong style={{ fontSize: '0.75rem' }}>{prediction.explanation.method}</strong>
              </div>
            </div>

            {/* Explainability Panel (Local SHAP) */}
            <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: 'var(--border-thin)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h4 style={{ margin: 0, textTransform: 'uppercase', fontSize: '0.9rem' }}>
                  Local Feature Attributions (SHAP Explanations)
                </h4>
                <span className="neo-evidence-badge neo-badge-purple">
                  {prediction.explanation.status.toUpperCase()}
                </span>
              </div>
              {prediction.explanation.warning && (
                <p style={{ fontSize: '0.75rem', color: '#b45309', margin: '0.25rem 0 0.75rem' }}>
                  {prediction.explanation.warning}
                </p>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {prediction.explanation.contributions.map((c) => (
                  <div
                    key={c.feature_name}
                    style={{
                      border: 'var(--border-thin)',
                      padding: '0.5rem 0.75rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      backgroundColor: c.direction === 'fake' ? '#fff1f2' : '#f0fdf4',
                    }}
                  >
                    <div>
                      <strong style={{ fontSize: '0.85rem' }}>{c.feature_name}</strong>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                        (val: {c.feature_value})
                      </span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '0.85rem',
                          color: c.direction === 'fake' ? '#be123c' : '#15803d',
                        }}
                      >
                        {c.contribution > 0 ? `+${c.contribution}` : c.contribution}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: '0.35rem' }}>
                        → {c.direction}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Evidence & Provenance Explorer */}
            {prediction.evidence.length > 0 && (
              <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: 'var(--border-thin)' }}>
                <h4 style={{ margin: '0 0 0.75rem 0', textTransform: 'uppercase', fontSize: '0.9rem' }}>
                  Observed Evidence & Source Provenance
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
                  {prediction.evidence.map((ev) => (
                    <div
                      key={ev.field_name}
                      style={{
                        border: 'var(--border-thin)',
                        padding: '0.5rem',
                        backgroundColor: '#ffffff',
                        fontSize: '0.8rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <strong>{ev.field_name}</strong>
                        <span className="neo-evidence-badge neo-badge-purple" style={{ fontSize: '0.65rem' }}>
                          {ev.source}
                        </span>
                      </div>
                      <div style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        Observed: {String(ev.observed_value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

