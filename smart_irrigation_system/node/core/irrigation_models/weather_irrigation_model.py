# smart_irrigation_system/node/core/irrigation_models/weather_irrigation_model.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from smart_irrigation_system.node.config.global_config import GlobalConfig
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions
from smart_irrigation_system.node.core.correction_factors import CorrectionFactors
from smart_irrigation_system.node.utils.logger import get_logger


logger = get_logger("WeatherIrrigationModel")


@dataclass
class WeatherModelResult:
    """
    Result of the weather-based irrigation model. Contains full context of the computation.

    This includes:
    - base_volume:       base volume before adjustments
    - total_adjustment:  total adjustment factor from weather model
    - adjusted_volume:   volume after applying total_adjustment
    - min_volume:        lower bound according to irrigation_limits (min_percent)
    - max_volume:        upper bound according to irrigation_limits (max_percent)
    - final_volume:      final volume after clamping to min/max bounds
    - should_skip:       whether irrigation should be skipped entirely
    """
    base_volume: float
    total_adjustment: float
    adjusted_volume: float
    min_volume: float
    max_volume: float
    final_volume: float
    should_skip: bool


# =====================================================================
# Public API
# =====================================================================

def compute_weather_adjusted_volume(
    base_volume: float,
    global_config: GlobalConfig,
    global_conditions: GlobalConditions,
    local_factors: CorrectionFactors,
) -> WeatherModelResult:
    """
    Compute the weather-adjusted irrigation volume for a single circuit.

    This function:
    - calculates deltas between current and standard weather conditions,
    - applies global + local correction factors,
    - computes total_adjustment and adjusted volume,
    - uses min/max bounds from `global_config.irrigation_limits`,
    - decides whether irrigation should be skipped when total_adjustment <= -1.
    """
    if base_volume < 0:
        logger.warning(
            "Received negative base_volume %.3f in weather model, treating as 0.0.",
            base_volume,
        )
        base_volume = 0.0

    # 1) Compute total adjustment (and its components) from weather deltas
    total_adjustment, solar_adj, rain_adj, temp_adj = _compute_total_adjustment(
        global_config=global_config,
        global_conditions=global_conditions,
        local_factors=local_factors,
    )

    logger.debug(
        "Weather adjustments - Solar: %.5f, Rain: %.5f, Temperature: %.5f, Total: %.5f",
        solar_adj,
        rain_adj,
        temp_adj,
        total_adjustment,
    )

    # 2) Raw adjusted volume (rounded to 3 decimals)
    adjusted_volume = _apply_adjustment(base_volume, total_adjustment)

    logger.debug(
        "Base target water amount: %.3f L, adjusted by total factor %.5f -> %.3f L",
        base_volume,
        1.0 + total_adjustment,
        adjusted_volume,
    )

    # 3) Decide whether to skip irrigation entirely
    should_skip = _should_skip_irrigation(total_adjustment)
    if should_skip:
        logger.info(
            "No irrigation needed based on weather model. "
            "Total adjustment %.5f <= -1.0 (100%% reduction or more).",
            total_adjustment,
        )

    # 4) Bounds (min/max percent) and clamping – only if we actually irrigate
    min_volume, max_volume = _compute_bounds(base_volume, global_config)

    if not should_skip:
        final_volume = _clamp_volume(adjusted_volume, min_volume, max_volume)
        if final_volume != adjusted_volume:
            logger.info(
                "Adjusted water amount %.3f L out of bounds (%.3f L, %.3f L). "
                "Clamped to %.3f L.",
                adjusted_volume,
                min_volume,
                max_volume,
                final_volume,
            )
    else:
        # When skipping irrigation, resulting volume is 0.0
        final_volume = 0.0

    return WeatherModelResult(
        base_volume=base_volume,
        total_adjustment=total_adjustment,
        adjusted_volume=adjusted_volume,
        min_volume=min_volume,
        max_volume=max_volume,
        final_volume=final_volume,
        should_skip=should_skip,
    )


# =====================================================================
# Helpers
# =====================================================================

def _compute_total_adjustment(
    global_config: GlobalConfig,
    global_conditions: GlobalConditions,
    local_factors: CorrectionFactors,
) -> Tuple[float, float, float, float]:
    """
    Compute total adjustment based on deviations from standard conditions.
    """
    standard_conditions = global_config.standard_conditions

    # Weather deltas
    delta_solar = global_conditions.solar_total - standard_conditions.solar_total
    delta_rain = global_conditions.rain_mm - standard_conditions.rain_mm
    delta_temperature = (
        global_conditions.temperature - standard_conditions.temperature_celsius
    )

    g_c = global_config.correction_factors
    l_c = local_factors

    # Combined factors
    solar_factor = g_c.solar + l_c.factors.get("solar", 0.0)
    rain_factor = g_c.rain + l_c.factors.get("rain", 0.0)
    temperature_factor = g_c.temperature + l_c.factors.get("temperature", 0.0)

    solar_adjustment = delta_solar * solar_factor
    rain_adjustment = delta_rain * rain_factor
    temperature_adjustment = delta_temperature * temperature_factor

    total_adjustment = solar_adjustment + rain_adjustment + temperature_adjustment

    return total_adjustment, solar_adjustment, rain_adjustment, temperature_adjustment


def _apply_adjustment(base_volume: float, total_adjustment: float) -> float:
    """
    Apply total adjustment to base_volume and round to 3 decimals.
    """
    adjusted = base_volume * (1.0 + total_adjustment)
    return round(adjusted, 3)


def _should_skip_irrigation(total_adjustment: float) -> bool:
    """
    Decide whether to skip irrigation entirely based on total_adjustment.
    """
    return total_adjustment <= -1.0


def _compute_bounds(
    base_volume: float, global_config: GlobalConfig
) -> Tuple[float, float]:
    """
    Compute minimum and maximum allowed water amount based on irrigation_limits.
    """
    limits = global_config.irrigation_limits
    min_volume = (limits.min_percent / 100.0) * base_volume
    max_volume = (limits.max_percent / 100.0) * base_volume
    return min_volume, max_volume


def _clamp_volume(volume: float, min_volume: float, max_volume: float) -> float:
    """
    Clamp volume into <min_volume, max_volume> interval.
    """
    if min_volume > max_volume:
        # Guard against misconfigured limits
        logger.error(
            "Invalid irrigation limits: min_volume (%.3f) > max_volume (%.3f). "
            "Falling back to unclamped volume.",
            min_volume,
            max_volume,
        )
        return volume

    if min_volume <= volume <= max_volume:
        return volume

    return max(min_volume, min(volume, max_volume))
