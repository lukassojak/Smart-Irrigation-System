from pytest import fixture

from smart_irrigation_system.server.configuration.schemas.optimization import (
    PerPlantOptimizationRequest,
    PerPlantOptimizationResponse,
    DripperAllocation,
    PlantOptimizationResult
)
from configuration.optimization.per_plant_optimizer import PerPlantOptimizer

@fixture
def one_plant_request():
    request = PerPlantOptimizationRequest(
        plants=[
            {
                "plant_id": "plant_1",
                "target_volume_liters": 10,
                "tolerance_percent": 10,
                "max_emitter_quantity": 5
            }
        ],
        available_drippers=[
            {
                "dripper_id": "dripper_a",
                "flow_rate_lph": 2,
                "count": None
            },
            {
                "dripper_id": "dripper_b",
                "flow_rate_lph": 5,
                "count": None
            }
        ]
    )

    return request

@fixture
def two_plants_request():
    request = PerPlantOptimizationRequest(
        plants=[
            {
                "plant_id": "plant_1",
                "target_volume_liters": 10,
                "tolerance_percent": 10,
                "max_emitter_quantity": 5
            },
            {
                "plant_id": "plant_2",
                "target_volume_liters": 20,
                "tolerance_percent": 20,
                "max_emitter_quantity": 10
            }
        ],
        available_drippers=[
            {
                "dripper_id": "dripper_a",
                "flow_rate_lph": 2,
                "count": None
            },
            {
                "dripper_id": "dripper_b",
                "flow_rate_lph": 5,
                "count": None
            }
        ]
    )

    return request


# --------- tests for PerPlantOptimizer ---------

def test_per_plant_optimizer_one_plant(one_plant_request):
    optimizer = PerPlantOptimizer(one_plant_request)

    result = optimizer.optimize()

    assert isinstance(result, PerPlantOptimizationResponse)
    assert len(result.plants) == 1
    assert result.plants[0].plant_id == "plant_1"
    assert result.plants[0].actual_volume_liters >= 9  and result.plants[0].actual_volume_liters <= 11  # target ±10%
    assert len(result.plants[0].assigned_drippers) > 0
    assert result.total_drippers_used > 0
    assert result.total_flow_lph > 0
    assert result.base_irrigation_time_seconds > 0
    assert len(result.drippers_used_detail) > 0
    assert result.total_base_volume_liters >= 9 and result.total_base_volume_liters <= 11

    computed_total_volume = result.total_flow_lph * (result.base_irrigation_time_seconds / 3600)
    assert abs(computed_total_volume - result.total_base_volume_liters) < 0.01


def test_per_plant_optimizer_two_plants(two_plants_request):
    optimizer = PerPlantOptimizer(two_plants_request)

    result = optimizer.optimize()

    assert isinstance(result, PerPlantOptimizationResponse)
    assert len(result.plants) == 2

    plant_1_result = next((p for p in result.plants if p.plant_id == "plant_1"), None)
    plant_2_result = next((p for p in result.plants if p.plant_id == "plant_2"), None)

    assert plant_1_result is not None
    assert plant_2_result is not None

    assert plant_1_result.actual_volume_liters >= 9 and plant_1_result.actual_volume_liters <= 11  # target ±10%
    assert plant_2_result.actual_volume_liters >= 16 and plant_2_result.actual_volume_liters <= 24  # target ±20%

    assert len(plant_1_result.assigned_drippers) > 0
    assert len(plant_2_result.assigned_drippers) > 0

    assert result.total_drippers_used > 0
    assert result.total_flow_lph > 0
    assert result.base_irrigation_time_seconds > 0
    assert len(result.drippers_used_detail) > 0
    assert result.total_base_volume_liters >= 25 and result.total_base_volume_liters <= 35

    computed_total_volume = result.total_flow_lph * (result.base_irrigation_time_seconds / 3600)
    assert abs(computed_total_volume - result.total_base_volume_liters) < 0.01


def test_per_plant_optimizer_exact_match():
    request = PerPlantOptimizationRequest(
        plants=[{
            "plant_id": "p1",
            "target_volume_liters": 10,
            "tolerance_percent": 0,
            "max_emitter_quantity": 10
        }],
        available_drippers=[
            {"dripper_id": "small", "flow_rate_lph": 2, "count": None},
            {"dripper_id": "big", "flow_rate_lph": 5, "count": None}
        ]
    )

    optimizer = PerPlantOptimizer(request)
    result = optimizer.optimize()

    assert result.total_drippers_used == 1
    assert result.plants[0].assigned_drippers[0].dripper_id == "big"
    assert result.plants[0].actual_volume_liters == 10
    assert result.total_flow_lph == 5
    assert result.base_irrigation_time_seconds == 7200  # 2 hours to deliver 10 liters at 5 lph


def test_respects_global_dripper_availability():
    request = PerPlantOptimizationRequest(
        plants=[
            {
                "plant_id": "p1",
                "target_volume_liters": 10,
                "tolerance_percent": 0,
                "max_emitter_quantity": 5
            },
            {
                "plant_id": "p2",
                "target_volume_liters": 10,
                "tolerance_percent": 0,
                "max_emitter_quantity": 5
            }
        ],
        available_drippers=[
            {"dripper_id": "big", "flow_rate_lph": 5, "count": 1},  # jen 1 kus
            {"dripper_id": "small", "flow_rate_lph": 2, "count": None}
        ]
    )

    optimizer = PerPlantOptimizer(request)
    result = optimizer.optimize()

    # big dripper může být použit max 1×
    big_used = next(
        (d.count for d in result.drippers_used_detail if d.dripper_id == "big"),
        0
    )

    assert big_used <= 1


def test_respects_max_emitter_quantity():
    request = PerPlantOptimizationRequest(
        plants=[
            {
                "plant_id": "p1",
                "target_volume_liters": 10,
                "tolerance_percent": 10,
                "max_emitter_quantity": 2  # velmi omezeno
            }
        ],
        available_drippers=[
            {"dripper_id": "d1", "flow_rate_lph": 2, "count": None}
        ]
    )

    optimizer = PerPlantOptimizer(request)
    result = optimizer.optimize()

    total_emitters_for_plant = sum(
        alloc.count for alloc in result.plants[0].assigned_drippers
    )

    assert total_emitters_for_plant <= 2


def test_volume_time_flow_consistency():
    request = PerPlantOptimizationRequest(
        plants=[
            {
                "plant_id": "p1",
                "target_volume_liters": 12,
                "tolerance_percent": 10,
                "max_emitter_quantity": 5
            }
        ],
        available_drippers=[
            {"dripper_id": "d1", "flow_rate_lph": 3, "count": None}
        ]
    )

    optimizer = PerPlantOptimizer(request)
    result = optimizer.optimize()

    computed_volume = result.total_flow_lph * (
        result.base_irrigation_time_seconds / 3600
    )

    assert abs(computed_volume - result.total_base_volume_liters) < 0.01


