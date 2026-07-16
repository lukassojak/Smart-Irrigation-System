from datetime import datetime
from typing import Optional

from smart_irrigation_system.node.core.irrigation_result import IrrigationResult
from smart_irrigation_system.node.core.enums import IrrigationOutcome
from smart_irrigation_system.node.config.global_config import StandardConditions
from smart_irrigation_system.node.weather.global_conditions import GlobalConditions
from smart_irrigation_system.node.config.zone_config import ZoneConfig


def create_flow_overload(
        was_manual_run: bool,
        zone_config: ZoneConfig,
        start_time: datetime,
        target_duration: int,
        target_water_amount: float,
        standard_conditions: StandardConditions,
        actual_conditions: GlobalConditions
    ) -> IrrigationResult:
    """Factory function to create a flow overload irrigation result."""
    return IrrigationResult(
        was_manual_run=was_manual_run,
        circuit_id=zone_config.id,
        success=False,
        outcome=IrrigationOutcome.FAILED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Timeout due to persistent flow overload",
        base_water_amount=zone_config.base_volume_liters,
        standard_conditions_solar=standard_conditions.solar_total,
        standard_conditions_rain=standard_conditions.rain_mm,
        standard_conditions_temp=standard_conditions.temperature_celsius,
        actual_solar=actual_conditions.solar_total,
        actual_rain=actual_conditions.rain_mm,
        actual_temp=actual_conditions.temperature,
        carry_over_applied=False,
        even_area_mode=zone_config.even_area_mode,
        dynamic_interval_enabled=zone_config.frequency_settings.dynamic_interval,
        irrigation_volume_threshold_percent=zone_config.frequency_settings.irrigation_volume_threshold_percent
    )


def create_skipped_due_to_negative_adjustment(
    zone_config: ZoneConfig,
    start_time: datetime,
    target_duration: int,
    target_water_amount: float,
    standard_conditions: StandardConditions,
    actual_conditions: GlobalConditions
) -> IrrigationResult:
    """Factory function to create a skipped due to negative adjustment irrigation result. Only used for automatic irrigation runs."""
    return IrrigationResult(
        was_manual_run=False,
        circuit_id=zone_config.id,
        success=True,
        outcome=IrrigationOutcome.SKIPPED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Skipped due to negative adjustment",
        base_water_amount=zone_config.base_volume_liters,
        standard_conditions_solar=standard_conditions.solar_total,
        standard_conditions_rain=standard_conditions.rain_mm,
        standard_conditions_temp=standard_conditions.temperature_celsius,
        actual_solar=actual_conditions.solar_total,
        actual_rain=actual_conditions.rain_mm,
        actual_temp=actual_conditions.temperature,
        carry_over_applied=False,
        even_area_mode=zone_config.even_area_mode,
        dynamic_interval_enabled=zone_config.frequency_settings.dynamic_interval,
        irrigation_volume_threshold_percent=zone_config.frequency_settings.irrigation_volume_threshold_percent
    )


def create_skipped_due_to_dynamic_interval(
    zone_config: ZoneConfig,
    start_time: datetime,
    target_duration: int,
    target_water_amount: float,
    standard_conditions: StandardConditions,
    actual_conditions: GlobalConditions
) -> IrrigationResult:
    """Factory function to create a skipped due to dynamic interval irrigation result (carry-over). Only used for automatic irrigation runs."""
    return IrrigationResult(
        was_manual_run=False,
        circuit_id=zone_config.id,
        success=True,
        outcome=IrrigationOutcome.SKIPPED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Skipped due to dynamic interval adjustment",
        base_water_amount=zone_config.base_volume_liters,
        standard_conditions_solar=standard_conditions.solar_total,
        standard_conditions_rain=standard_conditions.rain_mm,
        standard_conditions_temp=standard_conditions.temperature_celsius,
        actual_solar=actual_conditions.solar_total,
        actual_rain=actual_conditions.rain_mm,
        actual_temp=actual_conditions.temperature,
        carry_over_applied=True,
        even_area_mode=zone_config.even_area_mode,
        dynamic_interval_enabled=zone_config.frequency_settings.dynamic_interval,
        irrigation_volume_threshold_percent=zone_config.frequency_settings.irrigation_volume_threshold_percent,
    )

def create_failure_invalid_water_amount(
        zone_config: ZoneConfig,
        start_time: datetime,
        target_duration: int,
        target_water_amount: float,
    ) -> IrrigationResult:
    """Factory function to create a failure due to invalid water amount irrigation result. Only used for manual irrigation runs."""
    return IrrigationResult(
        was_manual_run=True,
        circuit_id=zone_config.id,
        success=False,
        outcome=IrrigationOutcome.FAILED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Invalid target water amount. Must be greater than zero",
        base_water_amount=zone_config.base_volume_liters,
        carry_over_applied=False,
        even_area_mode=zone_config.even_area_mode,
        dynamic_interval_enabled=zone_config.frequency_settings.dynamic_interval,
        irrigation_volume_threshold_percent=zone_config.frequency_settings.irrigation_volume_threshold_percent
    )

def create_failure_circuit_not_idle(
        was_manual_run: bool,
        zone_config: ZoneConfig,
        start_time: datetime,
        target_duration: int,
        target_water_amount: float,
        standard_conditions: StandardConditions,
        actual_conditions: GlobalConditions
    ) -> IrrigationResult:
    """Factory function to create a failure due to circuit not being idle irrigation result."""
    return IrrigationResult(
        was_manual_run=was_manual_run,
        circuit_id=zone_config.id,
        success=False,
        outcome=IrrigationOutcome.FAILED,
        start_time=start_time,
        completed_duration=0,
        target_duration=target_duration,
        actual_water_amount=0.0,
        target_water_amount=target_water_amount,
        error="Circuit is not in IDLE state",
        base_water_amount=zone_config.base_volume_liters,
        standard_conditions_solar=standard_conditions.solar_total,
        standard_conditions_rain=standard_conditions.rain_mm,
        standard_conditions_temp=standard_conditions.temperature_celsius,
        actual_solar=actual_conditions.solar_total,
        actual_rain=actual_conditions.rain_mm,
        actual_temp=actual_conditions.temperature,
        carry_over_applied=False,
        even_area_mode=zone_config.even_area_mode,
        dynamic_interval_enabled=zone_config.frequency_settings.dynamic_interval,
        irrigation_volume_threshold_percent=zone_config.frequency_settings.irrigation_volume_threshold_percent
    )

def create_interrupted(
        zone_id: int,
        reason: str,
        start_time: Optional[datetime] = None,
        completed_duration: Optional[int] = None,
        target_duration: Optional[int] = None,
        actual_water_amout: Optional[float] = None,
        target_water_amount: Optional[float] = None,
        standard_conditions: Optional[StandardConditions] = None,
        actual_conditions: Optional[GlobalConditions] = None,
        was_manual_run: Optional[bool] = None,
    ) -> IrrigationResult:
    """Factory function to create an interrupted irrigation result."""
    return IrrigationResult(
        was_manual_run=was_manual_run,
        circuit_id=zone_id,
        success=False,
        outcome=IrrigationOutcome.INTERRUPTED,
        start_time=start_time,
        completed_duration=completed_duration,
        target_duration=target_duration,
        actual_water_amount=actual_water_amout,
        target_water_amount=target_water_amount,
        error=f"{reason}",
        base_water_amount=None,
        standard_conditions_solar=None if standard_conditions is None else standard_conditions.solar_total,
        standard_conditions_rain=None if standard_conditions is None else standard_conditions.rain_mm,
        standard_conditions_temp=None if standard_conditions is None else standard_conditions.temperature_celsius,
        actual_solar=None if actual_conditions is None else actual_conditions.solar_total,
        actual_rain=None if actual_conditions is None else actual_conditions.rain_mm,
        actual_temp=None if actual_conditions is None else actual_conditions.temperature,
        carry_over_applied=False,
        even_area_mode=None,
        dynamic_interval_enabled=None,
        irrigation_volume_threshold_percent=None
    )

def create_general(
        was_manual_run: bool,
        zone_config: ZoneConfig,    # for circuit_id, even_area_mode, base_water_amount, irrigation_volume_threshold_percent, dynamic_interval_enabled
        start_time: datetime,
        completed_duration: int,
        target_duration: int,
        actual_water_amount: float,
        target_water_amount: float,
        success: bool,
        outcome: IrrigationOutcome,
        standard_conditions: StandardConditions,
        actual_conditions: GlobalConditions,
        carry_over_applied: bool,
        error: str = None,
    ) -> IrrigationResult:
    """Factory function to create a general irrigation result."""
    return IrrigationResult(
        was_manual_run=was_manual_run,
        circuit_id=zone_config.id,
        success=success,
        outcome=outcome,
        start_time=start_time,
        completed_duration=completed_duration,
        target_duration=target_duration,
        actual_water_amount=actual_water_amount,
        target_water_amount=target_water_amount,
        error=error,
        base_water_amount=zone_config.base_volume_liters,
        standard_conditions_solar=standard_conditions.solar_total,
        standard_conditions_rain=standard_conditions.rain_mm,
        standard_conditions_temp=standard_conditions.temperature_celsius,
        actual_solar=actual_conditions.solar_total,
        actual_rain=actual_conditions.rain_mm,
        actual_temp=actual_conditions.temperature,
        carry_over_applied=carry_over_applied,
        even_area_mode=zone_config.even_area_mode,
        dynamic_interval_enabled=zone_config.frequency_settings.dynamic_interval,
        irrigation_volume_threshold_percent=zone_config.frequency_settings.irrigation_volume_threshold_percent
    )