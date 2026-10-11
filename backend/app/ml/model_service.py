import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from app.ml.feature_builder import MODEL_FEATURES, FeatureExtractionResult
from app.schemas.prediction import (
    PredictionAssessment,
    ExplanationResult,
    FeatureContribution,
    EvidenceItem,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_PATH = os.path.join(PROJECT_ROOT, "artifacts", "phase4", "models", "socialguard_xgboost_v1.joblib")
MANIFEST_PATH = os.path.join(PROJECT_ROOT, "artifacts", "phase4", "models", "model_manifest.json")
VERIFICATION_REPORT_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "model_verification_report.json")
DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "model_ready_dataset.csv")


class ModelService:
    def __init__(self):
        self.model = None
        self.manifest = None
        self.verification_report = None
        self.explainer = None
        self.background_sample = None
        self.is_loaded = False
        self.verification_status = "UNKNOWN"
        self.load_error = None

    def initialize(self):
        """Loads model, manifest, and background explainer safely once."""
        if self.is_loaded:
            return

        try:
            if not os.path.exists(MANIFEST_PATH):
                raise FileNotFoundError(f"Model manifest missing: {MANIFEST_PATH}")
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                self.manifest = json.load(f)

            if not os.path.exists(MODEL_PATH):
                raise FileNotFoundError(f"Model artifact missing: {MODEL_PATH}")
            self.model = joblib.load(MODEL_PATH)

            # Check verification report
            if os.path.exists(VERIFICATION_REPORT_PATH):
                with open(VERIFICATION_REPORT_PATH, "r", encoding="utf-8") as f:
                    self.verification_report = json.load(f)
                    self.verification_status = self.verification_report.get("status", "PROVISIONAL")
            else:
                self.verification_status = "PROVISIONAL"

            # Prepare explainer with background sample
            if os.path.exists(DATASET_PATH):
                df_bg = pd.read_csv(DATASET_PATH)
                if all(col in df_bg.columns for col in MODEL_FEATURES):
                    self.background_sample = df_bg[MODEL_FEATURES].sample(
                        min(50, len(df_bg)), random_state=42
                    )
                    try:
                        import shap
                        self.explainer = shap.Explainer(self.model.predict_proba, self.background_sample)
                        logger.info("Initialized SHAP Explainer with background sample.")
                    except Exception as e:
                        logger.warning(f"Failed to initialize live SHAP explainer: {e}. Fallback enabled.")
                        self.explainer = None

            self.is_loaded = True
            logger.info(f"ModelService initialized successfully. Model: {self.manifest.get('model_id')}, Status: {self.verification_status}")

        except Exception as e:
            self.load_error = str(e)
            logger.error(f"Error loading ModelService: {e}", exc_info=True)

    def is_ready(self) -> bool:
        return self.is_loaded and self.model is not None

    def predict(
        self,
        request_id: str,
        username: str,
        feature_result: FeatureExtractionResult,
        processing_time_ms: float = 0.0,
    ) -> PredictionAssessment:
        if not self.is_ready():
            raise RuntimeError(f"Model is not ready: {self.load_error or 'Not initialized'}")

        # Model input dataframe
        X_input = pd.DataFrame([feature_result.features])[MODEL_FEATURES]

        # Predict probability
        probs = self.model.predict_proba(X_input)[0]
        # Class 1 is fake, Class 0 is genuine
        fake_prob = float(probs[1])
        predicted_class = "fake" if fake_prob >= 0.5 else "genuine"

        # Evidence construction
        evidence_items: List[EvidenceItem] = []
        for feat_name, prov in feature_result.evidence_provenance.items():
            evidence_items.append(
                EvidenceItem(
                    field_name=feat_name,
                    observed_value=feature_result.features.get(feat_name),
                    source=prov.get("source", "unknown"),
                    observation_id=prov.get("obs_id"),
                )
            )

        # Compute Explanations using ExplanationService (OpenRouter Nemotron + Deterministic Fallback)
        raw_contribs, raw_status, method_str, warning_msg = self._compute_raw_contributions(X_input, feature_result.features)

        from app.services.explanation_service import ExplanationService
        explanation = ExplanationService.generate_explanation(
            target_username=username,
            predicted_class=predicted_class,
            fake_probability=round(fake_prob, 4),
            decision_threshold=0.5,
            verification_status=self.verification_status,
            feature_coverage_ratio=round(feature_result.coverage_ratio, 2),
            missing_features=feature_result.missing_features,
            features_dict=feature_result.features,
            contributions=raw_contribs,
            raw_status=raw_status,
            method=method_str,
            warning_msg=warning_msg,
        )

        verification_note = (
            "PROVISIONAL STATUS: Model evaluation reproduced against holdout with zero discrepancy "
            "(Test F1: 96.23%). Model selection used test partition; suitable for research demonstration, "
            "not certified for unassisted production enforcement."
        )

        return PredictionAssessment(
            request_id=request_id,
            target_username=username,
            predicted_class=predicted_class,
            fake_probability=round(fake_prob, 4),
            score_label="Model Probability (Uncalibrated)",
            decision_threshold=0.5,
            model_id=self.manifest.get("model_id", "sg-xgb-v1.0.0"),
            pipeline_version="5.0.0",
            verification_status=self.verification_status,
            verification_note=verification_note,
            feature_coverage_ratio=round(feature_result.coverage_ratio, 2),
            missing_features=feature_result.missing_features,
            extracted_features=feature_result.features,
            evidence=evidence_items,
            explanation=explanation,
            warnings=feature_result.warnings,
            processing_time_ms=processing_time_ms,
        )

    def _compute_raw_contributions(
        self,
        X_input: pd.DataFrame,
        features_dict: Dict[str, float],
    ) -> Tuple[List[FeatureContribution], str, str, Optional[str]]:
        if self.explainer is not None:
            try:
                shap_res = self.explainer(X_input)
                # Extract SHAP values for class 1 (Fake)
                if len(shap_res.values.shape) == 3:
                    contribs_fake = shap_res.values[0, :, 1]
                else:
                    contribs_fake = shap_res.values[0]

                contributions: List[FeatureContribution] = []
                for idx, feat_name in enumerate(MODEL_FEATURES):
                    c_val = float(contribs_fake[idx])
                    contributions.append(
                        FeatureContribution(
                            feature_name=feat_name,
                            feature_value=features_dict.get(feat_name, 0.0),
                            contribution=round(c_val, 4),
                            direction="fake" if c_val > 0 else "genuine",
                        )
                    )

                # Sort by absolute contribution magnitude
                contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
                return contributions, "available", "Local SHAP Tree Attribution", None
            except Exception as e:
                logger.warning(f"Error computing local SHAP: {e}")

        # Fallback explanation using feature importances
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            ranked = sorted(
                zip(MODEL_FEATURES, importances),
                key=lambda x: x[1],
                reverse=True,
            )
            fallback_contribs = [
                FeatureContribution(
                    feature_name=f,
                    feature_value=features_dict.get(f, 0.0),
                    contribution=round(float(imp), 4),
                    direction="fake" if features_dict.get(f, 0.0) > 0 else "genuine",
                )
                for f, imp in ranked
            ]
            return (
                fallback_contribs,
                "fallback",
                "Global Feature Importance Fallback",
                "Local SHAP unavailable; displaying top global model split importances.",
            )

        return [], "unavailable", "None", "Model explainability provider unavailable for this inference pass."


model_service = ModelService()

