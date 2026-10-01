from decimal import Decimal

import pytest
from pydantic import ValidationError

from APP.core.config import Settings
from APP.schemas.rating import RatingPut, RatingResult


def test_bayesian_average_is_computed_and_internal_fields_are_excluded():
    rating = RatingResult(
        target_type="track",
        target_id=1,
        rating_sum=Decimal("14.5"),
        rating_weight=Decimal("3"),
        ratings_count=2,
        my_rating=4.5,
    )
    assert rating.rating_avg == pytest.approx(164.5 / 53)
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
    assert rating.rating_avg == pytest.approx(159 / 52)


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
        {"rating_weight_green": 0},
        {"rating_weight_experienced": -1},
        {"rating_weight_admin": Decimal("0.0000001")},
        {"rating_weight_moderator": float("inf")},
    ],
)
def test_rating_settings_reject_invalid_policies(settings, changes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(settings.model_dump() | changes))
