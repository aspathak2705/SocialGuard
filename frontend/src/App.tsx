import React from 'react';
import { AccountAnalyzer } from './features/account-analysis/AccountAnalyzer';

export const App: React.FC = () => {
  return (
    <main className="app-container">
      <header className="header">
        <div className="brand-badge">Phase 1 Foundation</div>
        <h1>SocialGuard</h1>
        <p>
          Explainable Multi-Signal Instagram Fake Account Detection System.
          Input an account below to verify target syntax and prepare for multi-source inspection.
        </p>
      </header>

      <AccountAnalyzer />

      <section className="notice-box">
        <h4>System Status Notice</h4>
        <p>
          Live account data acquisition (Instaloader, gallery-dl, Playwright) and machine-learning
          inference (XGBoost, SHAP explainability) are scheduled for subsequent project phases.
          No real account scraping or artificial predictions are performed in this phase.
        </p>
      </section>
    </main>
  );
};

export default App;
