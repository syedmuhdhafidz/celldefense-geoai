"""Project-wide geographic and simulation configuration."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AreaOfInterest:
    """Rectangular geographic boundary expressed in WGS 84 coordinates."""

    name: str
    minimum_latitude: float
    maximum_latitude: float
    minimum_longitude: float
    maximum_longitude: float
    coordinate_reference_system: str = "EPSG:4326"

    def __post_init__(self) -> None:
        if not -90.0 <= self.minimum_latitude <= 90.0:
            raise ValueError("minimum_latitude must be between -90 and 90.")

        if not -90.0 <= self.maximum_latitude <= 90.0:
            raise ValueError("maximum_latitude must be between -90 and 90.")

        if not -180.0 <= self.minimum_longitude <= 180.0:
            raise ValueError(
                "minimum_longitude must be between -180 and 180."
            )

        if not -180.0 <= self.maximum_longitude <= 180.0:
            raise ValueError(
                "maximum_longitude must be between -180 and 180."
            )

        if self.minimum_latitude >= self.maximum_latitude:
            raise ValueError(
                "minimum_latitude must be less than maximum_latitude."
            )

        if self.minimum_longitude >= self.maximum_longitude:
            raise ValueError(
                "minimum_longitude must be less than maximum_longitude."
            )

    def contains(self, latitude: float, longitude: float) -> bool:
        """Return whether a coordinate is inside or on the AOI boundary."""

        return (
            self.minimum_latitude
            <= latitude
            <= self.maximum_latitude
            and self.minimum_longitude
            <= longitude
            <= self.maximum_longitude
        )


CYBERJAYA_AOI = AreaOfInterest(
    name="Cyberjaya, Sepang, Selangor",
    minimum_latitude=2.8900,
    maximum_latitude=2.9700,
    minimum_longitude=101.6200,
    maximum_longitude=101.7000,
)

DEFAULT_RANDOM_SEED = 2026
DEFAULT_SAMPLE_INTERVAL_SECONDS = 1
DEFAULT_GRID_SIZE_METRES = 50
DEFAULT_TIME_WINDOW_MINUTES = 5