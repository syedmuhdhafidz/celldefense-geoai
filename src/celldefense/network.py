"""Synthetic base-station topology used by the RF simulator."""

from collections.abc import Sequence
from dataclasses import dataclass

from celldefense.config import AreaOfInterest, CYBERJAYA_AOI
from celldefense.schema import ALLOWED_RATS


@dataclass(frozen=True, slots=True)
class BaseStation:
    """One fictional base station in the synthetic reference network."""

    cell_id: str
    operator_id: str
    rat: str
    pci: int
    tac: int
    arfcn: int
    latitude: float
    longitude: float
    frequency_mhz: float
    reference_rsrp_at_1m_dbm: float = -30.0
    path_loss_exponent: float = 2.5

    def __post_init__(self) -> None:
        if self.rat not in ALLOWED_RATS:
            raise ValueError(f"Unsupported RAT: {self.rat}")

        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90.")

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180.")

        if not 0 <= self.pci <= 1007:
            raise ValueError("pci must be between 0 and 1007.")

        if self.frequency_mhz <= 0:
            raise ValueError("frequency_mhz must be positive.")

        if self.path_loss_exponent <= 0:
            raise ValueError("path_loss_exponent must be positive.")


SYNTHETIC_BASE_STATIONS = (
    BaseStation(
        cell_id="cell-001",
        operator_id="OP_A",
        rat="LTE",
        pci=101,
        tac=5001,
        arfcn=1650,
        latitude=2.9000,
        longitude=101.6300,
        frequency_mhz=1800.0,
    ),
    BaseStation(
        cell_id="cell-002",
        operator_id="OP_A",
        rat="NR",
        pci=501,
        tac=6001,
        arfcn=635000,
        latitude=2.9000,
        longitude=101.6750,
        frequency_mhz=3500.0,
    ),
    BaseStation(
        cell_id="cell-003",
        operator_id="OP_A",
        rat="LTE",
        pci=102,
        tac=5001,
        arfcn=1650,
        latitude=2.9200,
        longitude=101.6450,
        frequency_mhz=1800.0,
    ),
    BaseStation(
        cell_id="cell-004",
        operator_id="OP_A",
        rat="NR",
        pci=502,
        tac=6001,
        arfcn=635000,
        latitude=2.9200,
        longitude=101.6900,
        frequency_mhz=3500.0,
    ),
    BaseStation(
        cell_id="cell-005",
        operator_id="OP_A",
        rat="LTE",
        pci=103,
        tac=5002,
        arfcn=1800,
        latitude=2.9450,
        longitude=101.6300,
        frequency_mhz=1800.0,
    ),
    BaseStation(
        cell_id="cell-006",
        operator_id="OP_A",
        rat="NR",
        pci=503,
        tac=6002,
        arfcn=640000,
        latitude=2.9450,
        longitude=101.6600,
        frequency_mhz=3500.0,
    ),
    BaseStation(
        cell_id="cell-007",
        operator_id="OP_A",
        rat="LTE",
        pci=104,
        tac=5002,
        arfcn=1800,
        latitude=2.9550,
        longitude=101.6900,
        frequency_mhz=1800.0,
    ),
    BaseStation(
        cell_id="cell-008",
        operator_id="OP_A",
        rat="NR",
        pci=504,
        tac=6002,
        arfcn=640000,
        latitude=2.9650,
        longitude=101.6500,
        frequency_mhz=3500.0,
    ),
)


def validate_network(
    stations: Sequence[BaseStation],
    area_of_interest: AreaOfInterest = CYBERJAYA_AOI,
) -> None:
    """Validate the complete synthetic network topology."""

    if not stations:
        raise ValueError("The synthetic network must contain base stations.")

    cell_ids = [station.cell_id for station in stations]
    if len(cell_ids) != len(set(cell_ids)):
        raise ValueError("Base-station cell_id values must be unique.")

    outside_cells = [
        station.cell_id
        for station in stations
        if not area_of_interest.contains(
            latitude=station.latitude,
            longitude=station.longitude,
        )
    ]
    if outside_cells:
        raise ValueError(
            f"Base stations outside the pilot area: {outside_cells}"
        )