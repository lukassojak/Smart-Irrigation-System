import {
    Box,
    Heading,
    Text,
    Stack,
    SimpleGrid,
    Badge,
    DataList,
    HStack,
} from "@chakra-ui/react"

import { useState } from "react"

import FrequencyTimeline from "../../../../../components/FrequencyTimeline"
import PanelSection from "../../../../../components/layout/PanelSection"

import { FullCorrectionIndicator } from "../../../../../components/CorrectionIndicator"

export default function StepReview({ data }) {
    const [showRawData, setShowRawData] = useState(false)

    const {
        name,
        relay_pin,
        enabled,
        irrigation_mode,
        irrigation_configuration,
        emitters_configuration,
        frequency_settings,
        local_correction_factors,
    } = data

    const totalZoneFlow =
        irrigation_mode === "even_area"
            ? emitters_configuration?.summary?.reduce(
                (s, e) => s + e.flow_rate_lph * e.count,
                0
            )
            : emitters_configuration?.plants?.reduce(
                (sum, plant) =>
                    sum +
                    plant.emitters.reduce(
                        (s, e) =>
                            s +
                            (e.type === "soaker_hose"
                                ? e.flow_rate_lph
                                : e.flow_rate_lph * e.count),
                        0
                    ),
                0
            )

    return (
        <Stack>

            {/* -------------------------
            Zone summary
        ------------------------- */}
            <PanelSection title="Zone summary">
                <DataList.Root orientation="horizontal">
                    <DataList.Item>
                        <DataList.ItemLabel>Name</DataList.ItemLabel>
                        <DataList.ItemValue>
                            {name || "Unnamed zone"}
                        </DataList.ItemValue>
                    </DataList.Item>

                    <DataList.Item>
                        <DataList.ItemLabel>Relay pin</DataList.ItemLabel>
                        <DataList.ItemValue>
                            <Badge variant="subtle" colorPalette="teal">
                                Pin {relay_pin}
                            </Badge>
                        </DataList.ItemValue>
                    </DataList.Item>

                    <DataList.Item>
                        <DataList.ItemLabel>Status</DataList.ItemLabel>
                        <DataList.ItemValue>
                            {enabled ? (
                                <Badge colorPalette="green" variant="subtle">
                                    Enabled
                                </Badge>
                            ) : (
                                <Badge colorPalette="red" variant="subtle">
                                    Disabled
                                </Badge>
                            )}
                        </DataList.ItemValue>
                    </DataList.Item>
                </DataList.Root>
            </PanelSection>

            {/* -------------------------
            Irrigation strategy
        ------------------------- */}
            <PanelSection title="Irrigation strategy">
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                    <Box>
                        <Text fontSize="xs" color="fg.muted">Mode</Text>
                        <Badge colorPalette="teal" variant="subtle">
                            {irrigation_mode === "even_area"
                                ? "Even area"
                                : "Per plant"}
                        </Badge>
                    </Box>

                    {irrigation_mode === "even_area" && (
                        <>
                            <Box>
                                <Text fontSize="xs" color="fg.muted">Zone area</Text>
                                <Text>
                                    {irrigation_configuration.zone_area_m2} m²
                                </Text>
                            </Box>

                            <Box>
                                <Text fontSize="xs" color="fg.muted">Target depth</Text>
                                <Text>
                                    {irrigation_configuration.target_mm} mm
                                </Text>
                            </Box>
                        </>
                    )}

                    {irrigation_mode === "per_plant" && (
                        <Box>
                            <Text fontSize="xs" color="fg.muted">
                                Base target volume
                            </Text>
                            <Text>
                                {irrigation_configuration.base_target_volume_liters} L
                            </Text>
                        </Box>
                    )}
                </SimpleGrid>
            </PanelSection>

            {/* -------------------------
            Emitters overview
        ------------------------- */}
            <PanelSection title="Emitters overview">

                <Text fontSize="sm" color="fg.muted" mb={3}>
                    Total zone flow
                </Text>

                <Text fontSize="lg" fontWeight="semibold">
                    {totalZoneFlow?.toFixed(1)} l/h
                </Text>
            </PanelSection>

            {/* -------------------------
            Behavior & scheduling
        ------------------------- */}
            <PanelSection title="Behavior & scheduling">

                <FrequencyTimeline settings={frequency_settings} />
            </PanelSection>

            {/* -------------------------
            Corrections
        ------------------------- */}
            <PanelSection title="Corrections overview">
                <HStack>
                    <FullCorrectionIndicator
                        label="Solar"
                        value={local_correction_factors.solar}
                    />
                    <FullCorrectionIndicator
                        label="Rain"
                        value={local_correction_factors.rain}
                    />
                    <FullCorrectionIndicator
                        label="Temp"
                        value={local_correction_factors.temperature}
                    />
                </HStack>
            </PanelSection>

            {/* -------------------------
            Option to show raw data
            ------------------------- */}
            <PanelSection title="Raw configuration data">
                <Text
                    fontSize="sm"
                    color="teal.600"
                    cursor="pointer"
                    textDecoration="underline"
                    onClick={() => setShowRawData(!showRawData)}
                >
                    {showRawData ? "Hide" : "Show"} raw data
                </Text>

                {showRawData && (
                    <Box
                        as="pre"
                        mt={4}
                        p={4}
                        bg="bg.subtle"
                        borderRadius="md"
                        overflowX="auto"
                        fontSize="xs"
                    >
                        {JSON.stringify(data, null, 2)}
                    </Box>
                )}
            </PanelSection>

            {/* -------------------------
            Final hint
        ------------------------- */}
            <Box bg="teal.50" p={4} borderRadius="md">
                <Text fontSize="sm" color="teal.700">
                    Review the configuration carefully. Once the zone is created,
                    it will be evaluated automatically during each irrigation cycle
                    according to the node schedule and weather data.
                </Text>
            </Box>

        </Stack>
    )
}
