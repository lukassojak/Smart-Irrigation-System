import {
    For,
    Box,
    Heading,
    Text,
    Stack,
    SimpleGrid,
    Field,
    Badge,
    Switch,
    NumberInput,
    Slider,
    SegmentGroup,
    HStack,
} from "@chakra-ui/react"

import FrequencyTimeline from "../../../../../components/FrequencyTimeline"

import PanelSection from "../../../../../components/layout/PanelSection"

export default function StepBehaviorSettings({ data, onChange }) {
    const {
        local_correction_factors,
        frequency_settings,
        fallback_strategy,
    } = data

    const updateFrequency = (partial) => {
        onChange({
            frequency_settings: {
                ...frequency_settings,
                ...partial,
            },
        })
    }

    const updateCorrections = (partial) => {
        onChange({
            local_correction_factors: {
                ...local_correction_factors,
                ...partial,
            },
        })
    }

    const updateFallback = (partial) => {
        onChange({
            fallback_strategy: {
                ...fallback_strategy,
                ...partial,
            },
        })
    }

    {/* Define items - all fallback strategies for different scenarios */ }
    const fullFallbackItems = [
        {
            label: "Use cached data",
            value: "use_cached_data",
        },
        {
            label: "Use base volume",
            value: "use_base_volume",
        },
        {
            label: "Use half of base volume",
            value: "use_half_base_volume",
        },
        {
            label: "Skip irrigation",
            value: "skip_irrigation",
        },
    ]

    {/* Define items - limited fallback strategies for missing weather data */ }
    const limitedFallbackItems = [
        {
            label: "Use base volume",
            value: "use_base_volume",
        },
        {
            label: "Use half of base volume",
            value: "use_half_base_volume",
        },
        {
            label: "Skip irrigation",
            value: "skip_irrigation",
        },
    ]

    return (
        <Stack gap={10}>
            {/* ======================================================
                SECTION: Frequency & Scheduling
            ====================================================== */}
            <PanelSection
                title="Frequency & Scheduling"
                description="Define how often this zone is allowed to irrigate and how strictly the system follows the schedule."
            >
                <Stack gap={6}>
                    {/* Dynamic interval switch */}
                    <Field.Root colorPalette="teal">
                        <Field.Label>Dynamic irrigation interval</Field.Label>
                        <Switch.Root
                            checked={frequency_settings.dynamic_interval}
                            onCheckedChange={(e) =>
                                updateFrequency({ dynamic_interval: e.checked })
                            }
                        >
                            <Switch.HiddenInput />
                            <Switch.Control>
                                <Switch.Thumb />
                            </Switch.Control>
                            <Switch.Label>
                                {frequency_settings.dynamic_interval
                                    ? "Enabled"
                                    : "Disabled"}
                            </Switch.Label>
                        </Switch.Root>

                        <Field.HelperText>
                            When enabled, the system dynamically decides the
                            irrigation day based on weather conditions and
                            calculated water demand.
                        </Field.HelperText>
                    </Field.Root>

                    {/* Dynamic vs fixed interval */}
                    {frequency_settings.dynamic_interval ? (

                        <Box>
                            <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                                <Field.Root>
                                    <Field.Label>
                                        Minimum interval (days)
                                    </Field.Label>
                                    <NumberInput.Root
                                        value={String(
                                            frequency_settings.min_interval_days
                                        )}
                                        min={1}
                                        max={
                                            frequency_settings.max_interval_days
                                        }
                                        onValueChange={(e) =>
                                            updateFrequency({
                                                min_interval_days: Number(e.value),
                                            })
                                        }
                                    >
                                        <NumberInput.Control />
                                        <NumberInput.Input />
                                    </NumberInput.Root>
                                    <Field.HelperText>
                                        Earliest possible day the zone may irrigate.
                                    </Field.HelperText>
                                </Field.Root>
                                <Field.Root>
                                    <Field.Label>
                                        Maximum interval (days)
                                    </Field.Label>
                                    <NumberInput.Root
                                        value={String(
                                            frequency_settings.max_interval_days
                                        )}
                                        min={
                                            frequency_settings.min_interval_days
                                        }
                                        max={29}
                                        onValueChange={(e) =>
                                            updateFrequency({
                                                max_interval_days: Number(e.value),
                                            })
                                        }
                                    >
                                        <NumberInput.Control />
                                        <NumberInput.Input />
                                    </NumberInput.Root>
                                    <Field.HelperText>
                                        Latest day irrigation will be forced if
                                        skipped before.
                                    </Field.HelperText>
                                </Field.Root>
                            </SimpleGrid>

                            {frequency_settings.min_interval_days === frequency_settings.max_interval_days && (
                                <Text fontSize="sm" color="fg.warning" mt={2}>
                                    Minimum and maximum intervals are equal. This effectively disables dynamic scheduling.
                                </Text>
                            )}
                        </Box>
                    ) : (
                        <Field.Root>
                            <Field.Label>Fixed interval (days)</Field.Label>
                            <NumberInput.Root
                                value={String(
                                    frequency_settings.min_interval_days
                                )}
                                min={1}
                                max={29}
                                onValueChange={(e) =>
                                    updateFrequency({
                                        min_interval_days: Number(e.value),
                                    })
                                }
                            >
                                <NumberInput.Control />
                                <NumberInput.Input />
                            </NumberInput.Root>
                            <Field.HelperText>
                                Irrigation will run strictly every N days.
                            </Field.HelperText>
                        </Field.Root>
                    )}

                    {/* Carry-over & threshold */}
                    {frequency_settings.dynamic_interval && (
                        <>
                            <Field.Root colorPalette="teal">
                                <Field.Label>
                                    Carry-over skipped volume
                                </Field.Label>
                                <Switch.Root
                                    checked={
                                        frequency_settings.carry_over_volume
                                    }
                                    onCheckedChange={(e) =>
                                        updateFrequency({
                                            carry_over_volume: e.checked,
                                        })
                                    }
                                >
                                    <Switch.HiddenInput />
                                    <Switch.Control>
                                        <Switch.Thumb />
                                    </Switch.Control>
                                    <Switch.Label>
                                        {frequency_settings.carry_over_volume
                                            ? "Enabled"
                                            : "Disabled"}
                                    </Switch.Label>
                                </Switch.Root>
                                <Field.HelperText>
                                    Accumulate skipped irrigation volume and add
                                    it to the next cycle.
                                </Field.HelperText>
                            </Field.Root>

                            <Field.Root>
                                <Slider.Root
                                    width="100%"
                                    maxW="400px"
                                    value={[
                                        frequency_settings.irrigation_volume_threshold_percent,
                                    ]}
                                    min={5}
                                    max={95}
                                    step={5}
                                    colorPalette="teal"
                                    onValueChange={(e) =>
                                        updateFrequency({
                                            irrigation_volume_threshold_percent:
                                                e.value[0],
                                        })
                                    }
                                >
                                    <HStack justify="space-between" mb={2}>
                                        <Field.Label>
                                            Irrigation volume threshold (%)
                                        </Field.Label>
                                        <Slider.ValueText />
                                    </HStack>
                                    <Slider.Control>
                                        <Slider.Track>
                                            <Slider.Range />
                                        </Slider.Track>
                                        <Slider.Thumbs />
                                    </Slider.Control>
                                </Slider.Root>

                                <Field.HelperText>
                                    Skip irrigation if calculated volume is too
                                    small to be meaningful.
                                </Field.HelperText>
                            </Field.Root>
                        </>
                    )}

                    {/* Timeline */}
                    {frequency_settings.dynamic_interval && (
                        <FrequencyTimeline
                            settings={frequency_settings}
                        />
                    )}
                </Stack>
            </PanelSection>

            {/* ======================================================
                SECTION: Local Weather Corrections
            ====================================================== */}
            <PanelSection
                title="Local Weather Corrections"
                description="Fine-tune how strongly different weather conditions affect irrigation volume for this zone."
            >
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={6}>
                    {[
                        { key: "solar", label: "Solar" },
                        { key: "rain", label: "Rain" },
                        { key: "temperature", label: "Temperature" },
                    ].map(({ key, label }) => (
                        <Field.Root key={key}>
                            <Field.Label>{label}</Field.Label>

                            <Slider.Root
                                width="100%"
                                maxW="300px"
                                min={-1}
                                max={1}
                                step={0.05}
                                value={[local_correction_factors[key]]}
                                onValueChange={(e) =>
                                    updateCorrections({
                                        [key]: e.value[0],
                                    })
                                }
                            >
                                <Slider.Control>
                                    <Slider.Track bg="gray.200">
                                        <Slider.Range bg="transparent" />
                                    </Slider.Track>
                                    <Slider.Thumbs borderColor="teal.600" />
                                </Slider.Control>
                            </Slider.Root>

                            <HStack justify="space-between" width="100%" maxW="300px" mt={2}>
                                <Text fontSize="xs" color="fg.subtle">Reduce</Text>
                                <Text fontSize="sm" fontWeight="medium">
                                    {local_correction_factors[key].toFixed(2)}
                                </Text>
                                <Text fontSize="xs" color="fg.subtle">Amplify</Text>
                            </HStack>
                        </Field.Root>
                    ))}
                </SimpleGrid>
            </PanelSection>

            {/* ======================================================
                SECTION: Weather Data Fallback Strategy
            ====================================================== */}
            <PanelSection
                title="Weather Data Fallback Strategy"
                description="Define how the system should behave if weather data is missing or outdated."
            >
                <Stack>
                    {[
                        {
                            key: "on_fresh_weather_data_unavailable",
                            label: "Fresh weather data unavailable",
                            description: "The system cannot fetch up-to-date weather data, but cached data is still valid.",
                            items: fullFallbackItems,
                        },
                        {
                            key: "on_expired_weather_data",
                            label: "Expired weather data",
                            description: "The system cannot fetch up-to-date weather data, and cached data is outdated, but still available.",
                            items: fullFallbackItems,
                        },
                        {
                            key: "on_missing_weather_data",
                            label: "Missing weather data",
                            description: "The system has no weather data available at all.",
                            items: limitedFallbackItems,
                        },
                    ].map(({ key, label, description, items }) => (
                        <Box
                            key={key}
                            p={4}
                            bg="bg.muted"
                            borderRadius="md"
                            borderWidth="1px"
                            borderColor="border.subtle"
                        >
                            <Text
                                fontSize="sm"
                                fontWeight="medium"
                                mb={2}
                            >
                                {label}
                            </Text>
                            <Text
                                fontSize="xs"
                                color="fg.muted"
                                mb={4}
                            >
                                {description}
                            </Text>

                            <SegmentGroup.Root
                                value={fallback_strategy[key]}
                                onValueChange={(e) =>
                                    updateFallback({
                                        [key]: e.value,
                                    })
                                }
                                colorPalette="teal"
                                css={{
                                    "--segment-indicator-bg": "colors.white",
                                    "--segment-indicator-shadow": "shadows.md",
                                }}
                            >
                                <SegmentGroup.Indicator />
                                <For each={items.map((item) => item.value)}>
                                    {(itemValue) => (
                                        <SegmentGroup.Item key={itemValue} value={itemValue}>
                                            <SegmentGroup.ItemText
                                                _checked={{
                                                    color: "colorPalette.fg",
                                                    fontWeight: "medium",
                                                }}
                                            >
                                                {items.find((item) => item.value === itemValue).label}
                                            </SegmentGroup.ItemText>
                                            <SegmentGroup.ItemHiddenInput />
                                        </SegmentGroup.Item>
                                    )}
                                </For>
                            </SegmentGroup.Root>
                        </Box>
                    ))}
                </Stack>
            </PanelSection>
        </Stack>
    )
}
