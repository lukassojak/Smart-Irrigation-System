import { useEffect, useState } from "react"
import { Link, useOutletContext, useNavigate } from "react-router-dom"
import {
    Box,
    Field,
    Input,
    Stack,
    Switch,
    Text,
    SimpleGrid,
    Button,
} from "@chakra-ui/react"

import { fetchGlobalConfig, updateGlobalConfig } from "../../../api/globalConfig.api"
import PanelSection from "../../../components/layout/PanelSection"
import GlassPageHeader, { HeaderActions } from "../../../components/layout/GlassPageHeader"
import { HeaderAction, PanelButton } from "../../../components/ui/ActionButtons"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"


export default function GlobalSettingsPage() {
    const navigate = useNavigate()
    const [config, setConfig] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const loadConfig = async () => {
        setIsLoading(true)
        try {
            const response = await fetchGlobalConfig()
            setConfig(response.data)
        } catch (error) {
            console.error("Failed to fetch global config", error)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        loadConfig()
    }, [])

    const updateSection = (section, key, value) => {
        setConfig((prev) => ({
            ...prev,
            [section]: {
                ...prev[section],
                [key]: value,
            },
        }))
    }

    const handleSave = async () => {
        if (!config) {
            return
        }

        setIsSaving(true)
        try {
            const payload = {
                standard_conditions: config.standard_conditions,
                correction_factors: config.correction_factors,
                weather_api: config.weather_api,
            }
            const response = await updateGlobalConfig(payload)
            setConfig(response.data)
            alert("Global configuration saved.")
        } catch (error) {
            console.error("Failed to update global config", error)
            alert("Failed to save global configuration.")
        } finally {
            setIsSaving(false)
            navigate(`/configuration/nodes`)
        }
    }

    return (
        <>
            <GlassPageHeader
                title="System Configuration"
                subtitle="Shared weather and correction settings for all nodes"
                actions={
                    <HeaderActions>
                        <HeaderAction as={Link} to="/configuration/nodes">
                            Back to Dashboard
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Box p={6}>
                {isLoading && (
                    <Text color="fg.muted">Loading global configuration...</Text>
                )}

                {!isLoading && !config && (
                    <DataUnavailableWarning message="Global configuration is unavailable." />
                )}

                {!isLoading && config && (
                    <Stack gap={6}>
                        <Box
                            borderRadius="md"
                            p={4}
                            bg="rgba(56,178,172,0.05)"
                            border="1px solid rgba(56,178,172,0.12)"
                        >
                            <Stack gap={2}>
                                <Text fontSize="sm" fontWeight="600" color="teal.700">
                                    How these values are used
                                </Text>
                                <Text fontSize="sm" color="fg.muted">
                                    Standard Conditions are your reference weather values. They represent a normal day where watering runs at the base plan (100%).
                                </Text>
                                <Text fontSize="sm" color="fg.muted">
                                    Correction Factors define how strongly each weather difference changes watering volume. Positive values increase watering when weather is above the baseline, negative values decrease it.
                                </Text>
                                <Text fontSize="xs" color="fg.subtle">
                                    Example: rain factor -0.2 means each extra 1 mm of rain lowers watering by about 20%.
                                </Text>
                            </Stack>
                        </Box>

                        <PanelSection
                            title="Standard Conditions"
                            description="Default baseline weather values used across all nodes."
                        >
                            <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                                <Field.Root>
                                    <Field.Label>Solar Total</Field.Label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={config.standard_conditions.solar_total}
                                        onChange={(e) =>
                                            updateSection(
                                                "standard_conditions",
                                                "solar_total",
                                                Number(e.target.value || 0),
                                            )
                                        }
                                    />
                                </Field.Root>

                                <Field.Root>
                                    <Field.Label>Rain (mm)</Field.Label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={config.standard_conditions.rain_mm}
                                        onChange={(e) =>
                                            updateSection(
                                                "standard_conditions",
                                                "rain_mm",
                                                Number(e.target.value || 0),
                                            )
                                        }
                                    />
                                </Field.Root>

                                <Field.Root>
                                    <Field.Label>Temperature (C)</Field.Label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={config.standard_conditions.temperature_celsius}
                                        onChange={(e) =>
                                            updateSection(
                                                "standard_conditions",
                                                "temperature_celsius",
                                                Number(e.target.value || 0),
                                            )
                                        }
                                    />
                                </Field.Root>
                            </SimpleGrid>
                        </PanelSection>

                        <PanelSection
                            title="Global Correction Factors"
                            description="Multipliers used for weather-based irrigation corrections on all nodes."
                        >
                            <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                                <Field.Root>
                                    <Field.Label>Solar Factor</Field.Label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={config.correction_factors.solar}
                                        onChange={(e) =>
                                            updateSection(
                                                "correction_factors",
                                                "solar",
                                                Number(e.target.value || 0),
                                            )
                                        }
                                    />
                                </Field.Root>

                                <Field.Root>
                                    <Field.Label>Rain Factor</Field.Label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={config.correction_factors.rain}
                                        onChange={(e) =>
                                            updateSection(
                                                "correction_factors",
                                                "rain",
                                                Number(e.target.value || 0),
                                            )
                                        }
                                    />
                                </Field.Root>

                                <Field.Root>
                                    <Field.Label>Temperature Factor</Field.Label>
                                    <Input
                                        type="number"
                                        step="0.1"
                                        value={config.correction_factors.temperature}
                                        onChange={(e) =>
                                            updateSection(
                                                "correction_factors",
                                                "temperature",
                                                Number(e.target.value || 0),
                                            )
                                        }
                                    />
                                </Field.Root>
                            </SimpleGrid>
                        </PanelSection>

                        <PanelSection
                            title="Weather API"
                            description="Shared Ecowitt endpoint and credential settings used in runtime exports."
                        >
                            <Stack gap={4}>
                                <Field.Root colorPalette="teal">
                                    <Field.Label>Weather API Enabled</Field.Label>
                                    <Switch.Root
                                        checked={config.weather_api.api_enabled}
                                        onCheckedChange={(details) =>
                                            updateSection("weather_api", "api_enabled", details.checked)
                                        }
                                    >
                                        <Switch.HiddenInput />
                                        <Switch.Control>
                                            <Switch.Thumb />
                                        </Switch.Control>
                                        <Switch.Label>
                                            {config.weather_api.api_enabled ? "Enabled" : "Disabled"}
                                        </Switch.Label>
                                    </Switch.Root>
                                </Field.Root>

                                <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                                    <Field.Root>
                                        <Field.Label>Realtime URL</Field.Label>
                                        <Input
                                            value={config.weather_api.realtime_url || ""}
                                            onChange={(e) =>
                                                updateSection("weather_api", "realtime_url", e.target.value)
                                            }
                                        />
                                    </Field.Root>

                                    <Field.Root>
                                        <Field.Label>History URL</Field.Label>
                                        <Input
                                            value={config.weather_api.history_url || ""}
                                            onChange={(e) =>
                                                updateSection("weather_api", "history_url", e.target.value)
                                            }
                                        />
                                    </Field.Root>

                                    <Field.Root>
                                        <Field.Label>API Key</Field.Label>
                                        <Input
                                            value={config.weather_api.api_key || ""}
                                            onChange={(e) =>
                                                updateSection("weather_api", "api_key", e.target.value)
                                            }
                                        />
                                    </Field.Root>

                                    <Field.Root>
                                        <Field.Label>Application Key</Field.Label>
                                        <Input
                                            value={config.weather_api.application_key || ""}
                                            onChange={(e) =>
                                                updateSection("weather_api", "application_key", e.target.value)
                                            }
                                        />
                                    </Field.Root>

                                    <Field.Root>
                                        <Field.Label>Device MAC</Field.Label>
                                        <Input
                                            value={config.weather_api.device_mac || ""}
                                            onChange={(e) =>
                                                updateSection("weather_api", "device_mac", e.target.value)
                                            }
                                        />
                                    </Field.Root>
                                </SimpleGrid>
                            </Stack>
                        </PanelSection>

                        <Box>
                            <Button
                                alignSelf="flex-start"
                                colorPalette="teal"
                                onClick={handleSave}
                                loading={isSaving}>
                                Save System Configuration
                            </Button>
                        </Box>
                    </Stack>
                )}
            </Box>
        </>
    )
}
