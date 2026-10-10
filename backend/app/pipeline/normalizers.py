import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Tuple
from app.schemas.collection import AccountObservation, CollectorSource
from app.schemas.pipeline import (
    CanonicalObservation,
    ObservationType,
    FieldAvailabilityStatus,
    FieldValueMetadata,
)


class BaseNormalizer:
    """Base normalizer converting raw collector observations into canonical observations."""

    @staticmethod
    def _create_field_meta(name: str, val: any) -> FieldValueMetadata:
        if val is not None:
            return FieldValueMetadata(
                field_name=name,
                status=FieldAvailabilityStatus.OBSERVED,
                raw_value=val,
            )
        return FieldValueMetadata(
            field_name=name,
            status=FieldAvailabilityStatus.NOT_RETURNED,
            detail="Field absent in raw collector output",
        )

    def normalize(self, raw_obs: AccountObservation) -> Tuple[CanonicalObservation, List[str]]:
        raise NotImplementedError


class InstaloaderNormalizer(BaseNormalizer):
    def normalize(self, raw: AccountObservation) -> Tuple[CanonicalObservation, List[str]]:
        warnings: List[str] = []
        obs_id = f"obs-insta-{uuid.uuid4().hex[:10]}"

        # Validate non-negative numbers
        posts = raw.posts_count if (raw.posts_count is not None and raw.posts_count >= 0) else None
        if raw.posts_count is not None and raw.posts_count < 0:
            warnings.append(f"Invalid negative posts_count {raw.posts_count} encountered; set to None.")

        followers = raw.followers_count if (raw.followers_count is not None and raw.followers_count >= 0) else None
        if raw.followers_count is not None and raw.followers_count < 0:
            warnings.append(f"Invalid negative followers_count {raw.followers_count} encountered; set to None.")

        following = raw.following_count if (raw.following_count is not None and raw.following_count >= 0) else None
        if raw.following_count is not None and raw.following_count < 0:
            warnings.append(f"Invalid negative following_count {raw.following_count} encountered; set to None.")

        meta_dict = {
            "account_id": self._create_field_meta("account_id", raw.account_id),
            "full_name": self._create_field_meta("full_name", raw.full_name),
            "biography": self._create_field_meta("biography", raw.biography),
            "is_private": self._create_field_meta("is_private", raw.is_private),
            "is_verified": self._create_field_meta("is_verified", raw.is_verified),
            "posts_count": self._create_field_meta("posts_count", posts),
            "followers_count": self._create_field_meta("followers_count", followers),
            "following_count": self._create_field_meta("following_count", following),
            "has_profile_pic": self._create_field_meta("has_profile_pic", raw.has_profile_pic),
            "external_url": self._create_field_meta("external_url", raw.external_url),
        }

        canonical = CanonicalObservation(
            observation_id=obs_id,
            observation_type=ObservationType.PROFILE,
            target_username=raw.username,
            source=CollectorSource.INSTALOADER,
            source_record_id=raw.account_id,
            observation_timestamp=raw.observation_timestamp,
            normalization_timestamp=datetime.now(timezone.utc),
            account_id=raw.account_id,
            full_name=raw.full_name,
            biography=raw.biography,
            is_private=raw.is_private,
            is_verified=raw.is_verified,
            posts_count=posts,
            followers_count=followers,
            following_count=following,
            has_profile_pic=raw.has_profile_pic,
            external_url=raw.external_url,
            field_metadata=meta_dict,
            validation_warnings=warnings,
        )
        return canonical, warnings


class GalleryDlNormalizer(BaseNormalizer):
    def normalize(self, raw: AccountObservation) -> Tuple[CanonicalObservation, List[str]]:
        warnings: List[str] = []
        obs_id = f"obs-gdl-{uuid.uuid4().hex[:10]}"

        meta_dict = {
            "media_structure": self._create_field_meta("media_structure", raw.raw_metadata_sample),
        }

        canonical = CanonicalObservation(
            observation_id=obs_id,
            observation_type=ObservationType.MEDIA,
            target_username=raw.username,
            source=CollectorSource.GALLERY_DL,
            source_record_id=None,
            observation_timestamp=raw.observation_timestamp,
            normalization_timestamp=datetime.now(timezone.utc),
            field_metadata=meta_dict,
            validation_warnings=warnings,
        )
        return canonical, warnings


class PlaywrightNormalizer(BaseNormalizer):
    def normalize(self, raw: AccountObservation) -> Tuple[CanonicalObservation, List[str]]:
        warnings: List[str] = []
        obs_id = f"obs-pw-{uuid.uuid4().hex[:10]}"

        meta_dict = {
            "browser_dom": self._create_field_meta("browser_dom", raw.raw_metadata_sample),
        }

        canonical = CanonicalObservation(
            observation_id=obs_id,
            observation_type=ObservationType.BROWSER_DOM,
            target_username=raw.username,
            source=CollectorSource.PLAYWRIGHT,
            observation_timestamp=raw.observation_timestamp,
            normalization_timestamp=datetime.now(timezone.utc),
            field_metadata=meta_dict,
            validation_warnings=warnings,
        )
        return canonical, warnings
