from typing import List, Tuple
from app.schemas.pipeline import CanonicalObservation


class DeduplicationEngine:
    """
    Deterministic deduplication based on observation type, target username, and source identity.
    Preserves original observations and flags duplicates rather than deleting data.
    """

    @staticmethod
    def deduplicate(
        observations: List[CanonicalObservation],
    ) -> Tuple[List[CanonicalObservation], int]:
        seen_keys = {}
        duplicate_count = 0
        processed: List[CanonicalObservation] = []

        for obs in observations:
            # Create composite key: observation_type + target_username + source (or account_id if available)
            if obs.account_id:
                key = f"{obs.observation_type}:{obs.target_username}:{obs.account_id}"
            else:
                key = f"{obs.observation_type}:{obs.target_username}:{obs.source}"

            if key in seen_keys:
                duplicate_count += 1
                obs.is_duplicate = True
                obs.duplicate_of = seen_keys[key]
                obs.validation_warnings.append(f"Duplicate observation detected of {seen_keys[key]}")
            else:
                seen_keys[key] = obs.observation_id

            processed.append(obs)

        return processed, duplicate_count
