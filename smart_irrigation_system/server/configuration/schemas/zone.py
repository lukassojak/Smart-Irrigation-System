from pydantic import BaseModel, ConfigDict, model_validator

from smart_irrigation_system.server.configuration.schemas.irrigation import (
    LocalCorrectionFactors,
    FrequencySettings,
    FallbackStrategy,
    IrrigationConfigurationEvenArea,
    IrrigationConfigurationPerPlant
)

from smart_irrigation_system.server.configuration.schemas.emitters import (
    EmittersConfigurationEvenArea,
    EmittersConfigurationPerPlant
)

from smart_irrigation_system.server.configuration.domain.domain import IrrigationMode


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    relay_pin: int
    enabled: bool
    irrigation_mode: IrrigationMode
    local_correction_factors: LocalCorrectionFactors
    frequency_settings: FrequencySettings
    fallback_strategy: FallbackStrategy
    irrigation_configuration: IrrigationConfigurationEvenArea | IrrigationConfigurationPerPlant
    emitters_configuration: EmittersConfigurationEvenArea | EmittersConfigurationPerPlant


class ZoneCreate(BaseModel):
    name: str
    relay_pin: int
    enabled: bool
    irrigation_mode: IrrigationMode
    local_correction_factors: LocalCorrectionFactors
    frequency_settings: FrequencySettings
    fallback_strategy: FallbackStrategy
    irrigation_configuration: IrrigationConfigurationEvenArea | IrrigationConfigurationPerPlant
    emitters_configuration: EmittersConfigurationEvenArea | EmittersConfigurationPerPlant

    @model_validator(mode="after")
    def check_configuration_consistency(cls, model):
        if model.irrigation_mode == IrrigationMode.EVEN_AREA:
            if not isinstance(model.irrigation_configuration, IrrigationConfigurationEvenArea):
                raise ValueError("Irrigation configuration must be of type Even Area for EVEN_AREA mode.")
            if not isinstance(model.emitters_configuration, EmittersConfigurationEvenArea):
                raise ValueError("Emitters configuration must be of type Even Area for EVEN_AREA mode.")
        elif model.irrigation_mode == IrrigationMode.PER_PLANT:
            if not isinstance(model.irrigation_configuration, IrrigationConfigurationPerPlant):
                raise ValueError("Irrigation configuration must be of type Per Plant for PER_PLANT mode.")
            if not isinstance(model.emitters_configuration, EmittersConfigurationPerPlant):
                raise ValueError("Emitters configuration must be of type Per Plant for PER_PLANT mode.")
        return model


class ZoneUpdate(BaseModel):
    name: str | None = None
    relay_pin: int | None = None
    enabled: bool | None = None
    local_correction_factors: LocalCorrectionFactors | None = None
    frequency_settings: FrequencySettings | None = None
    fallback_strategy: FallbackStrategy | None = None
    irrigation_configuration: IrrigationConfigurationEvenArea | IrrigationConfigurationPerPlant | None = None
    emitters_configuration: EmittersConfigurationEvenArea | EmittersConfigurationPerPlant | None = None


class ZoneListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    relay_pin: int
    enabled: bool