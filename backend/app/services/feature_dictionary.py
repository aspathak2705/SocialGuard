from typing import Dict, Any, NamedTuple

class FeatureMetadata(NamedTuple):
    display_name: str
    description: str
    is_derived: bool
    unit_or_type: str

FEATURE_DICTIONARY: Dict[str, FeatureMetadata] = {
    "profile_pic": FeatureMetadata(
        display_name="Profile Picture Present",
        description="Indicates whether the account has uploaded an avatar or profile image.",
        is_derived=False,
        unit_or_type="boolean",
    ),
    "nums_length_username": FeatureMetadata(
        display_name="Digit Ratio in Username",
        description="Proportion of numeric digits within the account handle string.",
        is_derived=True,
        unit_or_type="ratio [0.0 - 1.0]",
    ),
    "fullname_words": FeatureMetadata(
        display_name="Full Name Word Count",
        description="Number of space-separated tokens in the profile's full name field.",
        is_derived=True,
        unit_or_type="integer",
    ),
    "nums_length_fullname": FeatureMetadata(
        display_name="Digit Ratio in Full Name",
        description="Proportion of numeric digits within the displayed full name.",
        is_derived=True,
        unit_or_type="ratio [0.0 - 1.0]",
    ),
    "name_equals_username": FeatureMetadata(
        display_name="Name Matches Handle",
        description="Flags whether full name text is identical to the username handle.",
        is_derived=True,
        unit_or_type="boolean",
    ),
    "description_length": FeatureMetadata(
        display_name="Biography Character Length",
        description="Total character count of the account profile biography / description.",
        is_derived=False,
        unit_or_type="integer count",
    ),
    "external_url": FeatureMetadata(
        display_name="External Website Link",
        description="Flags presence of an external link in the bio profile section.",
        is_derived=False,
        unit_or_type="boolean",
    ),
    "private": FeatureMetadata(
        display_name="Private Account Status",
        description="Flags whether profile visibility is restricted to approved followers.",
        is_derived=False,
        unit_or_type="boolean",
    ),
    "posts": FeatureMetadata(
        display_name="Total Media Posts Count",
        description="Observed number of published media posts on the profile.",
        is_derived=False,
        unit_or_type="integer count",
    ),
    "followers": FeatureMetadata(
        display_name="Follower Count",
        description="Total number of accounts following this profile.",
        is_derived=False,
        unit_or_type="integer count",
    ),
    "follows": FeatureMetadata(
        display_name="Following Count",
        description="Total number of other accounts this profile is actively following.",
        is_derived=False,
        unit_or_type="integer count",
    ),
    "follower_following_ratio": FeatureMetadata(
        display_name="Follower-to-Following Ratio",
        description="Ratio of incoming followers compared to outgoing follow connections (followers / (follows + 1)).",
        is_derived=True,
        unit_or_type="ratio",
    ),
    "following_follower_ratio": FeatureMetadata(
        display_name="Following-to-Follower Disparity",
        description="Outward connection pressure ratio (follows / (followers + 1)). High values often characterize automated mass-following bots.",
        is_derived=True,
        unit_or_type="ratio",
    ),
    "total_visible_connections": FeatureMetadata(
        display_name="Total Network Footprint",
        description="Sum of followers and follows representing gross profile network visibility.",
        is_derived=True,
        unit_or_type="integer count",
    ),
    "has_biography": FeatureMetadata(
        display_name="Has Non-Empty Biography",
        description="Flags whether the user wrote any bio description.",
        is_derived=True,
        unit_or_type="boolean",
    ),
    "has_media": FeatureMetadata(
        display_name="Has Published Content",
        description="Flags whether post count is strictly greater than zero.",
        is_derived=True,
        unit_or_type="boolean",
    ),
    "followers_per_media": FeatureMetadata(
        display_name="Followers Per Post",
        description="Content reach efficiency metric (followers / (posts + 1)).",
        is_derived=True,
        unit_or_type="ratio",
    ),
    "following_minus_followers": FeatureMetadata(
        display_name="Net Follow Asymmetry",
        description="Difference between outbound following and inbound followers (follows - followers).",
        is_derived=True,
        unit_or_type="integer",
    ),
    "log_followers": FeatureMetadata(
        display_name="Log-Transformed Followers",
        description="Natural logarithm scale representation of follower count to stabilize long-tail distribution.",
        is_derived=True,
        unit_or_type="log float",
    ),
    "log_follows": FeatureMetadata(
        display_name="Log-Transformed Follows",
        description="Natural logarithm scale representation of following count.",
        is_derived=True,
        unit_or_type="log float",
    ),
    "log_posts": FeatureMetadata(
        display_name="Log-Transformed Posts",
        description="Natural logarithm scale representation of post volume.",
        is_derived=True,
        unit_or_type="log float",
    ),
}


def get_feature_metadata(feature_name: str) -> FeatureMetadata:
    """Returns metadata for named feature or safe fallback."""
    return FEATURE_DICTIONARY.get(
        feature_name,
        FeatureMetadata(
            display_name=feature_name.replace("_", " ").title(),
            description=f"Observed feature attribute '{feature_name}'.",
            is_derived=False,
            unit_or_type="numerical",
        ),
    )
