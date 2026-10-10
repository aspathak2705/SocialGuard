import React from 'react';
import { AccountAnalyzer } from './features/account-analysis/AccountAnalyzer';

export const App: React.FC = () => {
  const scrollToAnalyze = (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById('analyze-section')?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToProcess = (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="neo-page-container">
      {/* 1. Header Navigation */}
      <header className="neo-navbar">
        <div className="neo-brand">
          <h2 style={{ fontSize: '1.5rem', margin: 0, textTransform: 'uppercase' }}>SocialGuard</h2>
          <span className="neo-brand-badge">Phase 1 Foundation</span>
        </div>
        <nav>
          <ul className="neo-nav-links">
            <li>
              <a href="#overview" className="neo-nav-link">Overview</a>
            </li>
            <li>
              <a href="#signals" className="neo-nav-link">Signals</a>
            </li>
            <li>
              <a href="#how-it-works" className="neo-nav-link">How It Works</a>
            </li>
            <li>
              <a href="#metrics" className="neo-nav-link">Metrics</a>
            </li>
          </ul>
        </nav>
        <button onClick={scrollToAnalyze} className="neo-nav-cta">
          Analyze Profile
        </button>
      </header>

      {/* 2. Asymmetric Split Hero */}
      <section className="neo-hero-split" id="overview">
        {/* Left Hero */}
        <div className="neo-hero-left">
          <div>
            <span className="neo-eyebrow">Explainable AI • Multi-Signal Architecture</span>
            <h1 className="neo-hero-headline">
              Look Closer. <br />
              Stay Safer.
            </h1>
            <p className="neo-hero-subtext">
              Multi-signal Instagram account inspection engineered to detect synthetic,
              inauthentic, and bot behaviors using explainable evidence models.
            </p>
            <div className="neo-hero-actions">
              <button onClick={scrollToAnalyze} className="neo-btn-primary">
                Start Investigation →
              </button>
              <button onClick={scrollToProcess} className="neo-btn-secondary">
                How It Works
              </button>
            </div>
          </div>
          <div className="neo-trust-statement">
            <span className="neo-trust-dot"></span>
            Strictly public intelligence inspection • Zero credential harvesting
          </div>
        </div>

        {/* Right Hero: Layered Graphic Preview */}
        <div className="neo-hero-right">
          <div className="neo-preview-stack">
            <div className="neo-preview-backdrop"></div>
            <div className="neo-preview-card">
              <div className="neo-preview-header">
                <span className="neo-preview-tag">Target Preview</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 800 }}>
                  DEMO_SPEC_V1
                </span>
              </div>
              <div className="neo-terminal-status">
                <div className="neo-terminal-title">
                  <span>&gt; COLLECTOR_STATUS</span>
                  <span>STANDBY</span>
                </div>
                <div>Awaiting target input for multi-source verification.</div>
              </div>
              <div className="neo-profile-meta-grid">
                <div className="neo-meta-box">
                  <div className="neo-meta-box-label">Inspection Engine</div>
                  <div className="neo-meta-box-val">Multi-Signal XAI</div>
                </div>
                <div className="neo-meta-box">
                  <div className="neo-meta-box-label">Adapter Pipeline</div>
                  <div className="neo-meta-box-val">Phase 2 Planned</div>
                </div>
                <div className="neo-meta-box">
                  <div className="neo-meta-box-label">Inference Model</div>
                  <div className="neo-meta-box-val">XGBoost + SHAP</div>
                </div>
                <div className="neo-meta-box">
                  <div className="neo-meta-box-label">Persistence</div>
                  <div className="neo-meta-box-val">Stateless (v1)</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Signal Category Strip (6 Items) */}
      <section className="neo-category-strip" id="signals">
        <div className="neo-category-item">
          <div className="neo-category-icon">👤</div>
          <h3 className="neo-category-title">Profile</h3>
          <p className="neo-category-desc">Username patterns, bio structure, verification flags</p>
        </div>
        <div className="neo-category-item">
          <div className="neo-category-icon">⚡</div>
          <h3 className="neo-category-title">Behavior</h3>
          <p className="neo-category-desc">Post cadences, active intervals, bursting behavior</p>
        </div>
        <div className="neo-category-item">
          <div className="neo-category-icon">📸</div>
          <h3 className="neo-category-title">Content</h3>
          <p className="neo-category-desc">Media variance, caption entropy, repost fingerprints</p>
        </div>
        <div className="neo-category-item">
          <div className="neo-category-icon">💬</div>
          <h3 className="neo-category-title">Engagement</h3>
          <p className="neo-category-desc">Follower-to-following anomalies, comment ratios</p>
        </div>
        <div className="neo-category-item">
          <div className="neo-category-icon">🕸️</div>
          <h3 className="neo-category-title">Network</h3>
          <p className="neo-category-desc">Cluster reciprocity, synthetic follow networks</p>
        </div>
        <div className="neo-category-item">
          <div className="neo-category-icon">🔍</div>
          <h3 className="neo-category-title">Evidence</h3>
          <p className="neo-category-desc">Explainable SHAP signals, auditable trail</p>
        </div>
      </section>

      {/* 4. Investigation & Right-Hand Metrics Layout */}
      <section className="neo-investigation-layout" id="metrics">
        {/* Main Content Area */}
        <div className="neo-main-investigation">
          <div className="neo-section-heading-wrap">
            <h2 className="neo-section-title">Active Investigation Panel</h2>
            <div className="neo-live-indicator">
              <span className="neo-trust-dot"></span>
              Phase 1 Live Validation Ready
            </div>
          </div>

          {/* Account Analyzer Module */}
          <AccountAnalyzer />

          {/* Structured Findings & Evidence Cards */}
          <div className="neo-evidence-grid">
            <div className="neo-evidence-card">
              <div className="neo-evidence-card-header">
                <span className="neo-evidence-badge neo-badge-lime">Collector Architecture</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>01</span>
              </div>
              <h4 className="neo-evidence-title">Triple-Adapter Ingestion</h4>
              <p className="neo-evidence-text">
                Future acquisition combines Instaloader metadata, gallery-dl media graphs, and Playwright DOM checks.
              </p>
            </div>

            <div className="neo-evidence-card">
              <div className="neo-evidence-card-header">
                <span className="neo-evidence-badge neo-badge-pink">Fairness & Ethics</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>02</span>
              </div>
              <h4 className="neo-evidence-title">Explainability First</h4>
              <p className="neo-evidence-text">
                Predictions produce calibrated SHAP evidence attribution rather than uninterpretable opaque scores.
              </p>
            </div>

            <div className="neo-evidence-card">
              <div className="neo-evidence-card-header">
                <span className="neo-evidence-badge neo-badge-purple">Safety Guarantee</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>03</span>
              </div>
              <h4 className="neo-evidence-title">No Synthetic Fabrication</h4>
              <p className="neo-evidence-text">
                System explicitly refuses to render fabricated predictions when models or data are uninitialized.
              </p>
            </div>
          </div>
        </div>

        {/* Right-Hand Metrics Sidebar (Lime Green) */}
        <aside className="neo-metrics-sidebar">
          <h3 className="neo-sidebar-title">Foundation Metrics</h3>

          <div className="neo-metric-card">
            <div className="neo-metric-label">Target Format</div>
            <div className="neo-metric-val">100%</div>
            <div className="neo-metric-desc">URL & handle normalization consistency</div>
          </div>

          <div className="neo-metric-card">
            <div className="neo-metric-label">Planned Adapters</div>
            <div className="neo-metric-val">3</div>
            <div className="neo-metric-desc">Instaloader, gallery-dl, Playwright</div>
          </div>

          <div className="neo-metric-card">
            <div className="neo-metric-label">Signal Vectors</div>
            <div className="neo-metric-val">6</div>
            <div className="neo-metric-desc">Multivariate feature channels</div>
          </div>

          <div className="neo-metric-card">
            <div className="neo-metric-label">Persistence Model</div>
            <div className="neo-metric-val">v1</div>
            <div className="neo-metric-desc">Stateless contract verification</div>
          </div>
        </aside>
      </section>

      {/* 5. How It Works: Three-Part Section */}
      <section className="neo-process-section" id="how-it-works">
        {/* Left colored label panel */}
        <div className="neo-process-label-panel">
          <div>
            <span className="neo-process-tag">Methodology</span>
            <h3 className="neo-process-label-title" style={{ marginTop: '1rem' }}>
              How SocialGuard Works
            </h3>
          </div>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-main)' }}>
            Transparent verification pipeline from raw handle to explainable report.
          </p>
        </div>

        {/* Central numbered timeline */}
        <div className="neo-process-timeline">
          <div className="neo-step-item">
            <div className="neo-step-number">01</div>
            <div className="neo-step-content">
              <h4>Submit Target Identifier</h4>
              <p>
                Enter an Instagram handle (@username) or direct profile URL. The system validates syntax and produces a canonical target.
              </p>
            </div>
          </div>

          <div className="neo-step-item">
            <div className="neo-step-number">02</div>
            <div className="neo-step-content">
              <h4>Multi-Signal Acquisition (Phase 2)</h4>
              <p>
                Permitted public metrics and metadata are acquired through three specialized collectors without storing credentials.
              </p>
            </div>
          </div>

          <div className="neo-step-item">
            <div className="neo-step-number">03</div>
            <div className="neo-step-content">
              <h4>Explainable AI Assessment (Phase 4)</h4>
              <p>
                Trained classification models analyze feature signals and return transparent SHAP explanations with auditable limitations.
              </p>
            </div>
          </div>
        </div>

        {/* Right Purple CTA Panel */}
        <div className="neo-process-cta-panel">
          <div>
            <h3 className="neo-cta-title">Ready To Validate Target?</h3>
            <p className="neo-cta-text">
              Try the Phase 1 target validation engine right now. Test URL variations, whitespace handling, and domain security checks.
            </p>
          </div>
          <button onClick={scrollToAnalyze} className="neo-cta-btn">
            Validate An Account Now →
          </button>
        </div>
      </section>

      {/* Notice Box */}
      <div style={{ padding: '1.25rem 2rem', backgroundColor: 'var(--color-offwhite)', borderBottom: 'var(--border-thick)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
        <strong>System Status Notice:</strong> Live account data acquisition and machine-learning inference are scheduled for subsequent project phases. No real account scraping or artificial predictions are performed in this phase.
      </div>

      {/* 6. Footer */}
      <footer className="neo-footer">
        <div className="neo-footer-brand">SocialGuard</div>
        <div className="neo-footer-statement">
          Explainable Multi-Signal Instagram Fake Account Detection • Final-Year B.Tech Capstone Project
        </div>
        <ul className="neo-footer-links">
          <li><a href="#overview">Overview</a></li>
          <li><a href="#signals">Signals</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
        </ul>
      </footer>
    </div>
  );
};

export default App;
