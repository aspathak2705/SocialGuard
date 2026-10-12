import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.pipeline import CanonicalObservation, UnifiedCollectionRun


# Exact 21 features in authoritative model order
MODEL_FEATURES: List[str] = [
    "profile_pic",
    "nums_length_username",
    "fullname_words",
    "nums_length_fullname",
    "name_equals_username",
    "description_length",
    "external_url",
    "private",
    "posts",
    "followers",
    "follows",
    "follower_following_ratio",
    "following_follower_ratio",
    "total_visible_connections",
    "has_biography",
    "has_media",
    "followers_per_media",
    "following_minus_followers",
    "log_followers",
    "log_follows",
    "log_posts",
]


class FeatureExtractionResult:
    def __init__(
        self,
        features: Dict[str, float],
        feature_vector: List[float],
        coverage_ratio: float,
        missing_features: List[str],
        warnings: List[str],
        evidence_provenance: Dict[str, Dict[str, Any]],
    ):
        self.features = features
        self.feature_vector = feature_vector
        self.coverage_ratio = coverage_ratio
        self.missing_features = missing_features
        self.warnings = warnings
        self.evidence_provenance = evidence_provenance


def extract_features_from_observations(
    username: str,
    observations: List[CanonicalObservation],
) -> FeatureExtractionResult:
    """
    Extracts the authoritative 21 ML features from normalized canonical observations.
    Maintains provenance tracing for every extracted field.
    """
    warnings: List[str] = []
    missing_features: List[str] = []
    provenance: Dict[str, Dict[str, Any]] = {}

    # Aggregate fields across observations prioritizing non-null values
    full_name: Optional[str] = None
    biography: Optional[str] = None
    is_private: Optional[bool] = None
    posts_count: Optional[int] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    has_profile_pic: Optional[bool] = None
    external_url: Optional[str] = None

    for obs in observations:
        if full_name is None and obs.full_name is not None:
            full_name = obs.full_name
            provenance["full_name"] = {"source": obs.source, "obs_id": obs.observation_id}
        if biography is None and obs.biography is not None:
            biography = obs.biography
            provenance["biography"] = {"source": obs.source, "obs_id": obs.observation_id}
        if is_private is None and obs.is_private is not None:
            is_private = obs.is_private
            provenance["is_private"] = {"source": obs.source, "obs_id": obs.observation_id}
        if posts_count is None and obs.posts_count is not None:
            posts_count = obs.posts_count
            provenance["posts_count"] = {"source": obs.source, "obs_id": obs.observation_id}
        if followers_count is None and obs.followers_count is not None:
            followers_count = obs.followers_count
            provenance["followers_count"] = {"source": obs.source, "obs_id": obs.observation_id}
        if following_count is None and obs.following_count is not None:
            following_count = obs.following_count
            provenance["following_count"] = {"source": obs.source, "obs_id": obs.observation_id}
        if has_profile_pic is None and obs.has_profile_pic is not None:
            has_profile_pic = obs.has_profile_pic
            provenance["has_profile_pic"] = {"source": obs.source, "obs_id": obs.observation_id}
        if external_url is None and obs.external_url is not None:
            external_url = obs.external_url
            provenance["external_url"] = {"source": obs.source, "obs_id": obs.observation_id}

    # Record missing core signals
    if posts_count is None:
        missing_features.append("posts")
        warnings.append("Post count unavailable from collectors; defaulting to 0.")
    if followers_count is None:
        missing_features.append("followers")
        warnings.append("Follower count unavailable from collectors; defaulting to 0.")
    if following_count is None:
        missing_features.append("follows")
        warnings.append("Following count unavailable from collectors; defaulting to 0.")
    if has_profile_pic is None:
        missing_features.append("profile_pic")
    if biography is None:
        missing_features.append("biography")
    if external_url is None:
        missing_features.append("external_url")
    if is_private is None:
        missing_features.append("private")

    # Calculate username properties
    clean_username = username.strip().lower()
    uname_len = max(len(clean_username), 1)
    uname_digits = sum(c.isdigit() for c in clean_username)
    nums_length_username = uname_digits / uname_len

    # Calculate full name properties
    fname = (full_name or "").strip()
    fname_words = len(fname.split()) if fname else 0
    fname_len = max(len(fname), 1) if fname else 1
    fname_digits = sum(c.isdigit() for c in fname)
    nums_length_fullname = (fname_digits / fname_len) if fname else 0.0
    name_equals_username = 1.0 if clean_username == fname.lower() and clean_username != "" else 0.0

    # Profile & bio flags
    profile_pic = 1.0 if (has_profile_pic is True or (has_profile_pic is None and len(observations) > 0)) else 0.0
    desc_length = float(len(biography or ""))
    has_ext_url = 1.0 if (external_url and len(external_url) > 0) else 0.0
    private_flag = 1.0 if (is_private is True) else 0.0

    # Counts
    p = float(posts_count or 0)
    f_ers = float(followers_count or 0)
    f_ing = float(following_count or 0)

    # Derived Ratios and Behaviors
    follower_following_ratio = f_ers / (f_ing + 1.0)
    following_follower_ratio = f_ing / (f_ers + 1.0)
    total_visible_connections = f_ers + f_ing
    has_biography = 1.0 if desc_length > 0 else 0.0
    has_media = 1.0 if p > 0 else 0.0
    followers_per_media = f_ers / (p + 1.0)
    following_minus_followers = f_ing - f_ers

    # Log transforms
    log_followers = float(np.log1p(max(f_ers, 0.0)))
    log_follows = float(np.log1p(max(f_ing, 0.0)))
    log_posts = float(np.log1p(max(p, 0.0)))

    features: Dict[str, float] = {
        "profile_pic": profile_pic,
        "nums_length_username": nums_length_username,
        "fullname_words": float(fname_words),
        "nums_length_fullname": nums_length_fullname,
        "name_equals_username": name_equals_username,
        "description_length": desc_length,
        "external_url": has_ext_url,
        "private": private_flag,
        "posts": p,
        "followers": f_ers,
        "follows": f_ing,
        "follower_following_ratio": follower_following_ratio,
        "following_follower_ratio": following_follower_ratio,
        "total_visible_connections": total_visible_connections,
        "has_biography": has_biography,
        "has_media": has_media,
        "followers_per_media": followers_per_media,
        "following_minus_followers": following_minus_followers,
        "log_followers": log_followers,
        "log_follows": log_follows,
        "log_posts": log_posts,
    }

    # Total 7 raw observable features: posts, followers, follows, profile_pic, biography, external_url, private
    core_raw_features = ["posts", "followers", "follows", "profile_pic", "biography", "external_url", "private"]
    missing_core = [f for f in missing_features if f in core_raw_features]
    coverage_ratio = 1.0 - (len(missing_core) / len(core_raw_features))

    feature_vector = [features[col] for col in MODEL_FEATURES]

    return FeatureExtractionResult(
        features=features,
        feature_vector=feature_vector,
        coverage_ratio=coverage_ratio,
        missing_features=missing_features,
        warnings=warnings,
        evidence_provenance=provenance,
    )
