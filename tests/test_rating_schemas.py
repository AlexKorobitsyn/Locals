from decimal import Decimal

import pytest
from pydantic import ValidationError

from APP.core.config import Settings
from APP.schemas.rating import RatingPut, RatingResult


def test_weighted_average_is_computed_and_internal_fields_are_excluded():
    rating = RatingResult(
        target_type="track",
        target_id=1,
        rating_sum=Decimal("14.5"),
        rating_weight=Decimal("3"),
        ratings_count=2,
        my_rating=4.5,
    )
    assert rating.rating_avg == pytest.approx(14.5 / 3)
    data = rating.model_dump(mode="json")
    assert set(data) == {
        "target_type",
        "target_id",
        "rating_avg",
        "ratings_count",
        "my_rating",
    }
    assert RatingResult(target_type="album", target_id=1).rating_avg is None
    rating.rating_sum = Decimal("9")
    rating.rating_weight = Decimal("2")
    assert rating.rating_avg == pytest.approx(4.5)


@pytest.mark.parametrize("count,weight", [(1, 1), (3, 4), (100, 200)])
def test_unanimous_fives_stay_five_regardless_of_volume_or_weights(count, weight):
    rating = RatingResult(
        target_type="album",
        target_id=1,
        rating_sum=Decimal(5 * weight),
        rating_weight=Decimal(weight),
        ratings_count=count,
    )
    assert rating.rating_avg == 5


@pytest.mark.parametrize("value", [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
def test_all_allowed_rating_steps(value):
    assert RatingPut(target_type="artist", target_id=1, value=value).value == Decimal(
        str(value)
    )


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf"), 4.50000001]
)
def test_rating_rejects_nonfinite_and_imprecise_steps(value):
    with pytest.raises(ValidationError):
        RatingPut(target_type="artist", target_id=1, value=value)


@pytest.mark.parametrize(
    "changes",
    [
        {"rating_prior_strength": 0},
        {"rating_prior_mean": 0},
        {"rating_prior_mean": 6},
        {"rating_level_weights": [1, 1.2]},
        {"rating_level_weights": [0, 1.2, 1.4, 1.7, 2, 2.3, 2.6, 3, 3.5]},
        {"rating_level_weights": [1, 1.2, 1.2, 1.7, 2, 2.3, 2.6, 3, 3.5]},
        {"rating_level_weights": [1, 1.2, 1.4, 1.7, 2, 2.3, 2.6, 3, float("inf")]},
        {"rating_weight_moderator": 3.5},
        {"rating_weight_admin": Decimal("0.0000001")},
        {"rating_weight_moderator": float("inf")},
    ],
)
def test_rating_settings_reject_invalid_policies(settings, changes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(settings.model_dump() | changes))
