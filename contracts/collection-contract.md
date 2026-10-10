# Collection & Observation Contracts (Planned for Phase 2+)

## 1. Overview
Defines future data acquisition contracts across the three planned collectors:
1. `instaloader` (Metadata, public stats, profile picture metadata)
2. `gallery-dl` (Media structures, post timestamps, caption metadata)
3. `playwright` (Rendered DOM verification, public follower list sampling if permitted)

## 2. Core Entities

### A. DataSourceStatus
- `source`: `"instaloader"` | `"gallery-dl"` | `"playwright"`
- `status`: `"pending"` | `"not_implemented"` | `"success"` | `"partial"` | `"failed"` | `"skipped"`
- `collected_field_names`: string[]
- `missing_field_names`: string[]
- `error_code`: Optional string code (e.g. `RATE_LIMITED`, `ACCOUNT_PRIVATE`, `NOT_FOUND`)
- `collection_timestamp`: UTC datetime ISO-8601

### B. AccountObservation
- `account_id`: Optional string (Instagram internal numeric ID if acquired)
- `username`: string
- `full_name`: Optional string
- `biography`: Optional string
- `is_private`: Optional boolean
- `is_verified`: Optional boolean
- `posts_count`: Optional integer
- `followers_count`: Optional integer
- `following_count`: Optional integer
- `has_profile_pic`: Optional boolean
- `external_url`: Optional string
- `observation_timestamp`: UTC datetime ISO-8601
- `source_provenance`: Collector source identifier
- `completeness_score`: Float between 0.0 and 1.0

### C. CollectionResult
- `request_id`: UUID string
- `target`: AccountTarget
- `overall_status`: `"not_started"` | `"in_progress"` | `"completed"` | `"partial"` | `"failed"`
- `sources`: Mapping of CollectorSource to DataSourceStatus
- `observations`: AccountObservation[]
- `missing_data_summary`: string[]
- `error_message`: Optional user-facing string
- `created_at`: UTC datetime ISO-8601

## 3. Future Machine-Learning Prediction Contract (Planned for Phase 4)

*NOTE: Do not implement in Phase 1 or 2. Strictly a forward specification.*

```typescript
interface FuturePredictionResult {
  model_version: string;             // e.g. "sg-xgb-v1.0.0"
  classification: "genuine" | "suspicious" | "bot_generated" | "insufficient_data";
  risk_score: number;                // 0.0 to 100.0 scale (defined semantic threshold)
  probability_score?: number;        // Only when formally calibrated (Brier score evaluated)
  confidence_level: "high" | "medium" | "low";
  feature_availability: {
    total_features_expected: number;
    total_features_present: number;
    missing_critical_signals: string[];
  };
  explanation: {
    shap_summary_available: boolean;
    top_contributing_signals: Array<{
      feature: string;
      value: number | string | boolean;
      impact: "increases_risk" | "decreases_risk";
      weight: number;
    }>;
  };
  limitations: string[];            // e.g. ["Profile private: media and engagement signals unavailable"]
  analysis_timestamp: string;       // ISO 8601 UTC
}
```
