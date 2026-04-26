import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate, useOutletContext } from 'react-router-dom'
import { SimpleGrid, DataList, Badge, HStack, Stack, Box, Text } from '@chakra-ui/react'
import { fetchZoneById, deleteZone } from '../../../api/nodes.api'

import FrequencyTimeline from '../../../components/FrequencyTimeline'
import { FullCorrectionIndicator } from '../../../components/CorrectionIndicator'

import HelpSidebar from "../../../components/HelpSidebar"
import HelpBox from "../../../components/HelpBox"
import PanelSection from '../../../components/layout/PanelSection'
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'
import { HeaderAction, HeaderActionDanger } from '../../../components/ui/ActionButtons'
import DataUnavailableWarning from '../../../components/ui/DataUnavailableWarning'
import EmitterOverviewCard from '../components/EmitterOverviewCard'
import PerPlantAllocationCard from '../components/PerPlantAllocationCard'

import { zoneDetailHelp } from "../../../help/zoneDetailHelp"


export default function ZoneDetailPage() {
    const { nodeId, zoneId } = useParams();
    const navigate = useNavigate();
    const [zone, setZone] = useState(null);
    const [zoneError, setZoneError] = useState(false)
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    useEffect(() => {
        setZoneError(false)
        fetchZoneById(nodeId, zoneId)
            .then((response) => {
                setZone(response.data)
            })
            .catch((error) => {
                console.error('Failed to fetch zone:', error)
                setZoneError(true)
            })
    }, [nodeId, zoneId])

    if (!zone) {
        return (
            <Box p={4} >
                {zoneError ? (
                    <DataUnavailableWarning message="Zone details are unavailable. Server may be disconnected." />
                ) : (
                    <Text>Loading zone details...</Text>
                )}
            </Box>
        )
    }

    const evenAreaEmitters = zone.emitters_configuration?.summary || []
    const totalEvenAreaFlow = evenAreaEmitters.reduce(
        (sum, emitter) =>
            sum +
            (emitter.type === "soaker_hose"
                ? emitter.flow_rate_lph || 0
                : (emitter.flow_rate_lph || 0) * (emitter.count || 0)),
        0
    )

    const perPlantZoneBaseVolumeLiters =
        zone.irrigation_configuration?.base_target_volume_liters ?? 0

    return (
        <>
            <GlassPageHeader
                title={`Zone #${zone.id}`}
                subtitle={zone.name || "Unnamed Zone"}
                actions={
                    <HeaderActions>
                        <HeaderActionDanger
                            onClick={() => {
                                if (!confirm("Are you sure?")) return
                                deleteZone(nodeId, zone.id)
                                    .then(() => navigate("/configuration/nodes/" + nodeId))
                            }}
                        >
                            Delete zone
                        </HeaderActionDanger>

                        <HeaderAction
                            as={Link}
                            to={`/configuration/nodes/${nodeId}`}
                        >
                            ← Back to Node #{nodeId}
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            >
                <HStack>
                    <Link to={`/nodes/${nodeId}`}>
                        <Text fontSize="xs" color="gray.500">
                            Node #{nodeId}
                        </Text>
                    </Link>

                    <Text fontSize="xs" color="gray.400">
                        →
                    </Text>

                    <Text fontSize="xs" color="gray.500">
                        Zone #{zone.id}
                    </Text>
                </HStack>
            </GlassPageHeader>


            <Box p={6}>
                {/* Zone summary */}
                <Stack gap={10}>
                    <PanelSection title="Zone Summary">
                        <DataList.Root orientation="horizontal">
                            <DataList.Item key="ID">
                                <DataList.ItemLabel>ID</DataList.ItemLabel>
                                <DataList.ItemValue>{zone.id}</DataList.ItemValue>
                            </DataList.Item>
                            <DataList.Item>
                                <DataList.ItemLabel>Name</DataList.ItemLabel>
                                <DataList.ItemValue>{zone.name || "Unnamed Zone"}</DataList.ItemValue>
                            </DataList.Item>
                            <DataList.Item>
                                <DataList.ItemLabel>Relay Valve Pin</DataList.ItemLabel>
                                <DataList.ItemValue>
                                    <Badge colorPalette="teal" variant="subtle">
                                        Pin {zone.relay_pin}
                                    </Badge>
                                </DataList.ItemValue>
                            </DataList.Item>
                            <DataList.Item>
                                <DataList.ItemLabel>Auto irrigation</DataList.ItemLabel>
                                <DataList.ItemValue>
                                    {zone.enabled ? (
                                        <Badge colorPalette="green" variant="subtle">Enabled</Badge>
                                    ) : (
                                        <Badge colorPalette="red" variant="subtle">Disabled</Badge>
                                    )}
                                </DataList.ItemValue>
                            </DataList.Item>
                        </DataList.Root>
                    </PanelSection>

                    {/* Two-column layout for data + help boxes */}
                    <SimpleGrid columns={{ base: 1, lg: 3 }} gap={6}>
                        <Stack gap={10} gridColumn="span 2">
                            {/* Main data boxes */}
                            <PanelSection title="Irrigation Configuration">
                                {zone.irrigation_mode === "even_area" && (
                                    <DataList.Root orientation="horizontal">
                                        <DataList.Item>
                                            <DataList.ItemLabel>Mode</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                <Badge colorPalette="teal" variant="subtle">
                                                    Even Area
                                                </Badge>
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>
                                                Zone area
                                            </DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                {zone.irrigation_configuration.zone_area_m2} m²
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>
                                                Base target
                                            </DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                {zone.irrigation_configuration.target_mm} mm
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>
                                                Base total zone target volume
                                            </DataList.ItemLabel>
                                            {/* Calculate liters from mm and area */}
                                            <DataList.ItemValue>
                                                {(
                                                    zone.irrigation_configuration.target_mm *
                                                    zone.irrigation_configuration.zone_area_m2
                                                ).toFixed(1)} L
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                    </DataList.Root>
                                )}

                                {zone.irrigation_mode === "per_plant" && (
                                    <DataList.Root orientation="horizontal">
                                        <DataList.Item>
                                            <DataList.ItemLabel>Mode</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                <Badge colorPalette="teal" variant="subtle">
                                                    Per Plant
                                                </Badge>
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>
                                                Base total zone target volume
                                            </DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                {(zone.irrigation_configuration.base_target_volume_liters).toFixed(1)} L
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                    </DataList.Root>
                                )}
                            </PanelSection>

                            {/* Behavior & Scheduling - frequency settings & fallback strategies */}
                            <PanelSection title="Behavior & Scheduling">
                                {/* Top: two-column overview */}
                                <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                                    {/* Frequency settings */}
                                    <Box>
                                        <Text fontSize="sm" fontWeight="semibold" mb={3}>
                                            Frequency Settings
                                        </Text>

                                        <DataList.Root orientation="horizontal">
                                            <DataList.Item>
                                                <DataList.ItemLabel>Dynamic interval</DataList.ItemLabel>
                                                <DataList.ItemValue>
                                                    {zone.frequency_settings.dynamic_interval ? (
                                                        <Badge colorPalette="green" variant="subtle">Enabled</Badge>
                                                    ) : (
                                                        <Badge variant="subtle">Disabled</Badge>
                                                    )}
                                                </DataList.ItemValue>
                                            </DataList.Item>

                                            <DataList.Item>
                                                <DataList.ItemLabel>{zone.frequency_settings.dynamic_interval ? "Min interval" : "Fixed interval"}</DataList.ItemLabel>
                                                <DataList.ItemValue>
                                                    {zone.frequency_settings.min_interval_days} days
                                                </DataList.ItemValue>
                                            </DataList.Item>

                                            {zone.frequency_settings.dynamic_interval && (
                                                <DataList.Item>
                                                    <DataList.ItemLabel>Max interval</DataList.ItemLabel>
                                                    <DataList.ItemValue>
                                                        {zone.frequency_settings.max_interval_days} days
                                                    </DataList.ItemValue>
                                                </DataList.Item>
                                            )}
                                        </DataList.Root>
                                    </Box>

                                    {/* Fallback strategy */}
                                    <Box>
                                        <Text fontSize="sm" fontWeight="semibold" mb={3}>
                                            Fallback Strategy
                                        </Text>

                                        <DataList.Root orientation="horizontal">
                                            <DataList.Item>
                                                <DataList.ItemLabel>No fresh data</DataList.ItemLabel>
                                                <DataList.ItemValue>
                                                    <Badge variant="outline">
                                                        {zone.fallback_strategy.on_fresh_weather_data_unavailable}
                                                    </Badge>
                                                </DataList.ItemValue>
                                            </DataList.Item>

                                            <DataList.Item>
                                                <DataList.ItemLabel>Expired data</DataList.ItemLabel>
                                                <DataList.ItemValue>
                                                    <Badge variant="outline">
                                                        {zone.fallback_strategy.on_expired_weather_data}
                                                    </Badge>
                                                </DataList.ItemValue>
                                            </DataList.Item>

                                            <DataList.Item>
                                                <DataList.ItemLabel>Missing weather data</DataList.ItemLabel>
                                                <DataList.ItemValue>
                                                    <Badge variant="outline">
                                                        {zone.fallback_strategy.on_missing_weather_data}
                                                    </Badge>
                                                </DataList.ItemValue>
                                            </DataList.Item>
                                        </DataList.Root>
                                    </Box>
                                </SimpleGrid>


                                {/* show divider & timeline if dynamic interval is enabled */}
                                {zone.frequency_settings.dynamic_interval && (
                                    <>
                                        <Box my={6} borderBottom="1px solid" borderColor="border.muted" />
                                        <FrequencyTimeline settings={zone.frequency_settings} />
                                    </>
                                )}

                            </PanelSection>

                            {/* Corrections & Adjustments */}
                            <PanelSection title="Corrections & Adjustments">
                                <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                                    {/* Indicators */}
                                    <HStack>
                                        <FullCorrectionIndicator
                                            label="Solar"
                                            value={zone.local_correction_factors.solar}
                                        />
                                        <FullCorrectionIndicator
                                            label="Rain"
                                            value={zone.local_correction_factors.rain}
                                        />
                                        <FullCorrectionIndicator
                                            label="Temperature"
                                            value={zone.local_correction_factors.temperature}
                                        />
                                    </HStack>

                                    {/* Legend */}
                                    <Box>
                                        <Text fontSize="sm" fontWeight="semibold" mb={2}>
                                            Adjustment Impact
                                        </Text>
                                        <Text fontSize="sm" color="fg.muted">
                                            Correction factors dynamically increase or decrease the calculated
                                            irrigation volume based on environmental conditions.
                                        </Text>
                                        <Text fontSize="xs" color="fg.subtle" mt={2}>
                                            Left = reduce • Center = neutral • Right = amplify
                                        </Text>
                                    </Box>
                                </SimpleGrid>
                            </PanelSection>

                            {/* Emitters overview */}
                            <PanelSection title="Emitters Overview">
                                {zone.irrigation_mode === "even_area" && (
                                    <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={4}>
                                        {evenAreaEmitters.map((emitter, index) => (
                                            <EmitterOverviewCard
                                                key={index}
                                                emitter={emitter}
                                                totalFlow={totalEvenAreaFlow}
                                            />
                                        ))}
                                    </SimpleGrid>
                                )}

                                {zone.irrigation_mode === "per_plant" && (
                                    <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={4}>
                                        {(() => {
                                            const plants = zone.emitters_configuration?.plants || []
                                            const getEmitterFlow = (emitter) =>
                                                emitter.type === "soaker_hose"
                                                    ? emitter.flow_rate_lph || 0
                                                    : (emitter.flow_rate_lph || 0) * (emitter.count || 0)

                                            const totalPlantFlow = plants.reduce(
                                                (sum, plant) =>
                                                    sum +
                                                    (plant.emitters || []).reduce(
                                                        (plantSum, emitter) => plantSum + getEmitterFlow(emitter),
                                                        0
                                                    ),
                                                0
                                            )

                                            return plants.map((plant, plantIndex) => {
                                                const plantFlow = (plant.emitters || []).reduce(
                                                    (sum, emitter) => sum + getEmitterFlow(emitter),
                                                    0
                                                )

                                                const baseVolumeLiters =
                                                    totalPlantFlow > 0
                                                        ? (plantFlow / totalPlantFlow) * perPlantZoneBaseVolumeLiters
                                                        : 0

                                                return (
                                                    <PerPlantAllocationCard
                                                        key={plantIndex}
                                                        plantName={plant.name || `Plant #${plantIndex + 1}`}
                                                        baseVolumeLiters={baseVolumeLiters}
                                                        assignedDrippers={(plant.emitters || []).map((emitter) => ({
                                                            count: emitter.count,
                                                            flow_rate_lph: emitter.flow_rate_lph,
                                                        }))}
                                                    />
                                                )
                                            })
                                        })()}
                                    </SimpleGrid>
                                )}

                            </PanelSection>
                        </Stack>

                        {/* Help sidebar */}
                        <HelpSidebar
                            sticky
                            stickyTop="80px"
                            maxHeight="calc(100vh - 120px)"
                        >
                            {zoneDetailHelp.map(box => (
                                <HelpBox key={box.id} title={box.title}>
                                    {box.description}
                                </HelpBox>
                            ))}

                            {zone.frequency_settings.dynamic_interval && (
                                <HelpBox title="Frequency & Scheduling">
                                    {/* původní JSX obsahu */}
                                </HelpBox>
                            )}
                        </HelpSidebar>
                    </SimpleGrid>
                </Stack>
            </Box>
        </>
    )
}