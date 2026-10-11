import json
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.schemas.prediction import ExplanationResult, FeatureContribution, KeyFactor
from app.services.feature_dictionary import FEATURE_DICTIONARY

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Coordinates explainability generation via OpenRouter Nemotron
    with deterministic fallback when LLM is unavailable or disabled.
    """

    @classmethod
    def generate_explanation(
        cls,
        target_username: str,
        predicted_class: str,
        fake_probability: float,
        decision_threshold: float,
        verification_status: str,
        feature_coverage_ratio: float,
        missing_features: List[str],
        features_dict: Dict[str, float],
        contributions: List[FeatureContribution],
        raw_status: str,
        method: str,
        warning_msg: Optional[str] = None,
    ) -> ExplanationResult:
        # Build enriched contributions with display names and dictionary descriptions
        enriched_contribs: List[FeatureContribution] = []
        for c in contributions:
            meta = FEATURE_DICTIONARY.get(c.feature_name)
            enriched_contribs.append(
                FeatureContribution(
                    feature_name=c.feature_name,
                    feature_value=c.feature_value,
                    contribution=c.contribution,
                    direction=c.direction,
                    display_name=meta.display_name if meta else c.feature_name,
                    description=meta.description if meta else "",
                )
            )

        top_drivers = [c.feature_name for c in enriched_contribs[:5]]

        # If SHAP is unavailable
        if raw_status == "unavailable" or not enriched_contribs:
            return ExplanationResult(
                status="unavailable",
                provider="unavailable",
                model_id="None",
                method=method,
                summary=f"Explainability attribution is currently unavailable for @{target_username}.",
                limitations=["Insufficient or malformed observation data to generate local attribution."],
                warning=warning_msg or "Model attribution provider unavailable.",
            )

        # Build deterministic fallback explanation
        deterministic_expl = cls._build_deterministic_explanation(
            target_username=target_username,
            predicted_class=predicted_class,
            fake_probability=fake_probability,
            verification_status=verification_status,
            feature_coverage_ratio=feature_coverage_ratio,
            missing_features=missing_features,
            enriched_contribs=enriched_contribs,
            top_drivers=top_drivers,
            method=method,
            warning_msg=warning_msg,
        )

        # Check if OpenRouter is enabled and configured
        if not settings.OPENROUTER_ENABLED or not settings.OPENROUTER_API_KEY:
            return deterministic_expl

        # Attempt OpenRouter Nemotron structured synthesis
        try:
            llm_res = cls._call_openrouter_nemotron(
                target_username=target_username,
                predicted_class=predicted_class,
                fake_probability=fake_probability,
                verification_status=verification_status,
                enriched_contribs=enriched_contribs[:5],
                missing_features=missing_features,
            )
            if llm_res:
                return ExplanationResult(
                    status="available",
                    provider="openrouter_nemotron",
                    model_id=settings.OPENROUTER_MODEL,
                    method=f"{method} + Nemotron Synthesis",
                    summary=llm_res.get("summary", deterministic_expl.summary),
                    key_factors=[KeyFactor(**kf) for kf in llm_res.get("key_factors", [])] or deterministic_expl.key_factors,
                    conflicting_signals=llm_res.get("conflicting_signals", deterministic_expl.conflicting_signals),
                    limitations=llm_res.get("limitations", deterministic_expl.limitations),
                    review_guidance=llm_res.get("review_guidance", deterministic_expl.review_guidance),
                    contributions=enriched_contribs,
                    top_drivers=top_drivers,
                    warning=warning_msg,
                )
        except Exception as e:
            logger.warning(f"OpenRouter Nemotron call failed, using deterministic fallback: {e}")

        return deterministic_expl

    @classmethod
    def _build_deterministic_explanation(
        cls,
        target_username: str,
        predicted_class: str,
        fake_probability: float,
        verification_status: str,
        feature_coverage_ratio: float,
        missing_features: List[str],
        enriched_contribs: List[FeatureContribution],
        top_drivers: List[str],
        method: str,
        warning_msg: Optional[str],
    ) -> ExplanationResult:
        key_factors: List[KeyFactor] = []
        conflicting: List[str] = []

        fake_alignments = [c for c in enriched_contribs if c.direction == "fake"]
        genuine_alignments = [c for c in enriched_contribs if c.direction == "genuine"]

        if fake_alignments and genuine_alignments:
            conflicting.append(
                f"Account displays both deceptive signals ({fake_alignments[0].display_name}) "
                f"and authentic signals ({genuine_alignments[0].display_name})."
            )

        for c in enriched_contribs[:5]:
            kf_expl = (
                f"{c.display_name} (observed value: {c.feature_value}) contributed {abs(c.contribution):.3f} "
                f"toward a {c.direction} classification."
            )
            key_factors.append(
                KeyFactor(
                    feature_name=c.feature_name,
                    display_name=c.display_name or c.feature_name,
                    direction=c.direction,
                    contribution_value=c.contribution,
                    explanation=kf_expl,
                )
            )

        summary = (
            f"Model predicts @{target_username} as {predicted_class.upper()} "
            f"with an uncalibrated score of {fake_probability * 100:.1f}%. "
            f"The primary driver is '{enriched_contribs[0].display_name}' "
            f"which aligns with {enriched_contribs[0].direction} profile patterns."
        )

        limitations = [
            f"Evaluation is {verification_status}: holdout metrics guided candidate selection on curated Instagram data.",
            f"Observation coverage is {feature_coverage_ratio * 100:.0f}%; {len(missing_features)} core signals unobserved.",
        ]

        review_guidance = [
            "Cross-reference media content authenticity and account engagement quality.",
            "Confirm whether external bio link leads to verified domains.",
        ]

        return ExplanationResult(
            status="fallback",
            provider="deterministic_fallback",
            model_id="Rule-Grounded XAI Engine",
            method=method,
            summary=summary,
            key_factors=key_factors,
            conflicting_signals=conflicting,
            limitations=limitations,
            review_guidance=review_guidance,
            contributions=enriched_contribs,
            top_drivers=top_drivers,
            warning=warning_msg,
        )

    @classmethod
    def _call_openrouter_nemotron(
        cls,
        target_username: str,
        predicted_class: str,
        fake_probability: float,
        verification_status: str,
        enriched_contribs: List[FeatureContribution],
        missing_features: List[str],
    ) -> Optional[Dict[str, Any]]:
        url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://socialguard.local",
            "X-Title": "SocialGuard Investigation",
        }

        factors_payload = [
            {
                "feature_name": c.feature_name,
                "display_name": c.display_name,
                "direction": c.direction,
                "contribution_value": c.contribution,
                "observed_value": c.feature_value,
            }
            for c in enriched_contribs
        ]

        prompt_payload = {
            "target_username": target_username,
            "predicted_class": predicted_class,
            "fake_probability": fake_probability,
            "verification_status": verification_status,
            "missing_features": missing_features,
            "verified_factors": factors_payload,
        }

        system_instruction = (
            "You are an explainable AI investigator assistant for SocialGuard. "
            "Explain the supplied verified model evidence faithfully in neutral, objective language. "
            "Never invent facts, alter numeric probabilities, or change contribution directions. "
            "You MUST respond ONLY with a valid JSON object matching this exact structure:\n"
            "{\n"
            '  "summary": "Concise plain-language synthesis of the assessment.",\n'
            '  "key_factors": [\n'
            '    {\n'
            '      "feature_name": "feature_id",\n'
            '      "display_name": "Name",\n'
            '      "direction": "fake or genuine",\n'
            '      "contribution_value": 0.123,\n'
            '      "explanation": "Short grounded interpretation."\n'
            '    }\n'
            "  ],\n"
            '  "conflicting_signals": ["Descriptions of contradicting signals, if any"],\n'
            '  "limitations": ["Dataset or measurement limitations"],\n'
            '  "review_guidance": ["Next steps for human investigator review"]\n'
            "}"
        )

        user_content = f"Input verified assessment data:\n{json.dumps(prompt_payload, indent=2)}"

        req_body = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "temperature": settings.OPENROUTER_TEMPERATURE,
            "max_tokens": settings.OPENROUTER_MAX_TOKENS,
        }

        with httpx.Client(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
            resp = client.post(url, headers=headers, json=req_body)
            if resp.status_code != 200:
                logger.warning(f"OpenRouter returned status {resp.status_code}: {resp.text}")
                return None
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return None
            content_str = choices[0].get("message", {}).get("content", "").strip()

            # Clean markdown code blocks if present
            if content_str.startswith("```json"):
                content_str = content_str[7:]
            if content_str.startswith("```"):
                content_str = content_str[3:]
            if content_str.endswith("```"):
                content_str = content_str[:-3]

            parsed = json.loads(content_str.strip())
            # Enforce verified contribution values to prevent LLM numerical hallucination
            if "key_factors" in parsed and isinstance(parsed["key_factors"], list):
                for idx, kf in enumerate(parsed["key_factors"]):
                    if idx < len(factors_payload):
                        kf["feature_name"] = factors_payload[idx]["feature_name"]
                        kf["display_name"] = factors_payload[idx]["display_name"]
                        kf["direction"] = factors_payload[idx]["direction"]
                        kf["contribution_value"] = factors_payload[idx]["contribution_value"]

            return parsed
