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
  const [error, setError] = useState<string | null>(null);
  const [validatedTarget, setValidatedTarget] = useState<AccountTarget | null>(null);

  // Investigation States
  const [investigationStep, setInvestigationStep] = useState<string | null>(null);
  const [pipelineRun, setPipelineRun] = useState<UnifiedCollectionRun | null>(null);
  const [prediction, setPrediction] = useState<PredictionAssessment | null>(null);
  const [investigationError, setInvestigationError] = useState<string | null>(null);

  const isInvestigating = Boolean(investigationStep);

  const handleInvestigate = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();

    if (!trimmed) {
      setError('Please enter an Instagram username or profile URL.');
      setValidatedTarget(null);
      setPipelineRun(null);
      setPrediction(null);
      return;
    }

    setError(null);
    setValidatedTarget(null);
    setPipelineRun(null);
    setPrediction(null);
    setInvestigationError(null);

    // Step 1: Validating Account
    setInvestigationStep('Validating account...');
    let targetObj: AccountTarget;
    try {
      const valRes = await validateAccountTarget(trimmed);
      targetObj = valRes.data.target;
      setValidatedTarget(targetObj);
    } catch (err: unknown) {
      setInvestigationStep(null);
      if (err instanceof ApiServiceError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while validating target syntax.');
      }
      return;
    }

    // Step 2: Collecting Available Evidence & Normalizing Pipeline
    setInvestigationStep('Collecting available evidence & normalizing observations...');
    let currentRun: UnifiedCollectionRun | null = null;
    try {
      const pipeRes = await processPipelineData(targetObj.original_input);
      currentRun = pipeRes.data;
      setPipelineRun(currentRun);
    } catch (err: unknown) {
      // If collection completely fails, record error and halt
      setInvestigationStep(null);
      if (err instanceof ApiServiceError) {
        setInvestigationError(`Data collection failed: ${err.message}`);
      } else {
        setInvestigationError('Unexpected error during evidence acquisition.');
      }
      return;
    }

    // Step 3: Check Evidence Sufficiency before Model Execution
    // Check if usable observations with core signals exist
    const hasUsableProfileEvidence = currentRun.canonical_observations.some(
      (obs) =>
        obs.posts_count !== undefined ||
        obs.followers_count !== undefined ||
        obs.following_count !== undefined ||
        obs.has_profile_pic !== undefined ||
        obs.biography !== undefined ||
        obs.external_url !== undefined
    );

    if (!hasUsableProfileEvidence || currentRun.canonical_observations.length === 0) {
      setInvestigationStep(null);
      const isBlocked = Object.values(currentRun.source_executions).some(
        (s) => s.status === 'failed' || s.status === 'timed_out' || s.status === 'unavailable'
      );
      setInvestigationError(
        isBlocked
          ? 'Insufficient evidence for a defensible assessment: collectors were blocked, restricted, or returned no profile signals. Account cannot be classified as fake or genuine.'
          : 'Insufficient observation coverage to produce a defensible assessment. Required profile signals were not returned.'
      );
      return;
    }

    // Step 4: Preparing Account Features & Running ML Assessment & SHAP Explanation
    setInvestigationStep('Extracting features, evaluating model, and generating explanations...');
    try {
      const predRes = await predictAccountInference(
        targetObj.normalized_username,
        currentRun.run_id
      );
      setPrediction(predRes.data);
      setInvestigationStep(null);
    } catch (err: unknown) {
      setInvestigationStep(null);
      if (err instanceof ApiServiceError) {
        setInvestigationError(err.message);
      } else {
        setInvestigationError('Unexpected error during model inference and assessment.');
      }
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
      <form onSubmit={handleInvestigate} noValidate>
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
              disabled={isInvestigating}
              aria-describedby="target-input-hint"
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="submit"
              className="neo-submit-btn"
              disabled={isInvestigating || !inputValue.trim()}
            >
              {isInvestigating ? 'Investigating...' : 'INVESTIGATE ACCOUNT'}
            </button>
          </div>
          <p id="target-input-hint" className="neo-form-hint">
            Accepts raw usernames (with or without @) or direct Instagram URLs.
          </p>
        </div>
      </form>

      {/* Progressive Step / Status Banner */}
      {investigationStep && (
        <div className="neo-alert neo-alert-info animate-entrance" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="neo-trust-dot" style={{ animation: 'pulse 1.5s infinite' }}></span>
          <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            STATUS: {investigationStep}
          </span>
        </div>
      )}

      {/* Target Validation Error */}
      {error && (
        <div className="neo-alert neo-alert-error animate-entrance" role="alert" style={{ marginTop: '1rem' }}>
          <div className="neo-alert-title">Target Validation Failed</div>
          <p>{error}</p>
        </div>
      )}

      {/* Target Validated Presentation */}
      {validatedTarget && (
        <div className="neo-alert neo-alert-success animate-entrance" role="status" style={{ marginTop: '1rem' }}>
          <div className="neo-alert-title">Target Validated</div>
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
        </div>
      )}

      {/* Investigation Error */}
      {investigationError && (
        <div className="neo-alert neo-alert-error animate-entrance" role="alert" style={{ marginTop: '1.25rem' }}>
          <div className="neo-alert-title">Investigation Notice</div>
          <p>{investigationError}</p>
        </div>
      )}




      {/* Unified Pipeline Results */}
      {pipelineRun && (
        <div
          className={`neo-alert ${
            pipelineRun.overall_status === 'completed'
              ? 'neo-alert-success'
              : pipelineRun.overall_status === 'partial'
              ? 'neo-alert-info'
              : 'neo-alert-error'
          } animate-entrance`}
          style={{ marginTop: '1.5rem' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div className="neo-alert-title" style={{ margin: 0 }}>
              Collection & Evidence Summary: {pipelineRun.run_id}
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

          {/* Collector Execution Breakdown */}
          {pipelineRun.source_executions && Object.keys(pipelineRun.source_executions).length > 0 && (
            <div style={{ marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: 'var(--border-thin)' }}>
              <strong style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Collector Adapter Diagnostics:</strong>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.5rem', marginTop: '0.35rem' }}>
                {Object.entries(pipelineRun.source_executions).map(([src, statusObj]) => (
                  <div key={src} style={{ border: 'var(--border-thin)', padding: '0.4rem', backgroundColor: 'var(--color-white)', fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong>{src}</strong>
                      <span className={`neo-evidence-badge ${getStatusBadgeClass(statusObj.status)}`} style={{ fontSize: '0.65rem' }}>
                        {statusObj.status.toUpperCase()}
                      </span>
                    </div>
                    {statusObj.error_message && (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.2rem' }}>
                        {statusObj.error_message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

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




      {/* Model Prediction & Investigation Dashboard */}
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

            {/* Explainability Panel (Human-Readable + Local SHAP) */}
            <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: 'var(--border-thin)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h4 style={{ margin: 0, textTransform: 'uppercase', fontSize: '0.9rem' }}>
                  Explainability & Factor Attribution
                </h4>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <span
                    className="neo-evidence-badge"
                    style={{
                      backgroundColor:
                        prediction.explanation.provider === 'openrouter_nemotron'
                          ? 'var(--color-lime)'
                          : prediction.explanation.provider === 'deterministic_fallback'
                          ? 'var(--color-amber)'
                          : '#e5e7eb',
                      fontWeight: 700,
                    }}
                  >
                    {prediction.explanation.provider === 'openrouter_nemotron'
                      ? 'AI-GENERATED EXPLANATION (NEMOTRON)'
                      : prediction.explanation.provider === 'deterministic_fallback'
                      ? 'DETERMINISTIC EXPLANATION'
                      : prediction.explanation.provider === 'evidence_only'
                      ? 'EVIDENCE SUMMARY'
                      : 'EXPLANATION UNAVAILABLE'}
                  </span>
                  <span className="neo-evidence-badge neo-badge-purple">
                    {prediction.explanation.status.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Natural Language Synthesis Box */}
              {prediction.explanation.summary && (
                <div
                  style={{
                    backgroundColor: 'var(--color-offwhite)',
                    border: 'var(--border-thin)',
                    padding: '0.85rem 1rem',
                    marginBottom: '1rem',
                    lineHeight: 1.5,
                  }}
                >
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                    Executive Synthesis
                  </div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>
                    {prediction.explanation.summary}
                  </div>
                </div>
              )}

              {/* Conflicting Signals Alert */}
              {prediction.explanation.conflicting_signals && prediction.explanation.conflicting_signals.length > 0 && (
                <div style={{ backgroundColor: '#fef3c7', border: '1px solid #f59e0b', padding: '0.6rem 0.8rem', marginBottom: '0.75rem', fontSize: '0.8rem' }}>
                  <strong>Contradicting Signals:</strong> {prediction.explanation.conflicting_signals.join(' ')}
                </div>
              )}

              {prediction.explanation.warning && (
                <p style={{ fontSize: '0.75rem', color: '#b45309', margin: '0.25rem 0 0.75rem' }}>
                  {prediction.explanation.warning}
                </p>
              )}

              {/* Verified Feature Attribution Breakdown */}
              <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
                Verified Feature Attributions (Fake vs Genuine Direction)
              </div>
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
                      <strong style={{ fontSize: '0.85rem' }}>{c.display_name || c.feature_name}</strong>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                        ({c.feature_name}: {c.feature_value})
                      </span>
                      {c.description && (
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                          {c.description}
                        </div>
                      )}
                    </div>
                    <div style={{ textAlign: 'right', minWidth: '110px' }}>
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
                        → {c.direction.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Review Guidance & Limitations */}
              {((prediction.explanation.limitations && prediction.explanation.limitations.length > 0) ||
                (prediction.explanation.review_guidance && prediction.explanation.review_guidance.length > 0)) && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem', marginTop: '1rem' }}>
                  {prediction.explanation.limitations && prediction.explanation.limitations.length > 0 && (
                    <div style={{ border: 'var(--border-thin)', padding: '0.6rem 0.8rem', backgroundColor: '#f9fafb', fontSize: '0.75rem' }}>
                      <strong>Assessment Limitations:</strong>
                      <ul style={{ paddingLeft: '1.1rem', marginTop: '0.3rem' }}>
                        {prediction.explanation.limitations.map((lim, idx) => (
                          <li key={idx}>{lim}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {prediction.explanation.review_guidance && prediction.explanation.review_guidance.length > 0 && (
                    <div style={{ border: 'var(--border-thin)', padding: '0.6rem 0.8rem', backgroundColor: '#f9fafb', fontSize: '0.75rem' }}>
                      <strong>Investigator Review Steps:</strong>
                      <ul style={{ paddingLeft: '1.1rem', marginTop: '0.3rem' }}>
                        {prediction.explanation.review_guidance.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
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

