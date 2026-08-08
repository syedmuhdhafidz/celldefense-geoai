import pytest

from celldefense.config import AreaOfInterest, CYBERJAYA_AOI


def test_cyberjaya_coordinate_is_inside_aoi() -> None:
    assert CYBERJAYA_AOI.contains(
        latitude=2.9225,
        longitude=101.6550,
    )


def test_outside_coordinate_is_not_inside_aoi() -> None:
    assert not CYBERJAYA_AOI.contains(
        latitude=3.1390,
        longitude=101.6869,
    )


def test_invalid_aoi_boundaries_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="minimum_latitude must be less",
    ):
        AreaOfInterest(
            name="Invalid area",
            minimum_latitude=3.0,
            maximum_latitude=2.0,
            minimum_longitude=101.0,
            maximum_longitude=102.0,
        )