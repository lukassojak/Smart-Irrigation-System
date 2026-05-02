import { useState, useEffect } from 'react'
import { Link, useParams, useNavigate, useOutletContext } from "react-router-dom"
import { For, SegmentGroup, Switch, Field, Text, Box, Heading, Input, Button, Stack, SimpleGrid, HStack, Badge } from "@chakra-ui/react"
import { fetchNodeById, updateNode, pushNodeConfig } from "../../../api/nodes.api"
import {
    ControlActionDialogViewport,
    openControlActionDialog,
} from "../../../components/ui/ControlActionDialogOverlay"

import HelpSidebar from "../../../components/HelpSidebar"
import HelpBox from "../../../components/HelpBox"
import PanelSection from '../../../components/layout/PanelSection'
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'
import { HeaderAction } from '../../../components/ui/ActionButtons'

import { createNodeHelp, createNodeAdvancedHelp } from "../../../help/createNodeHelp"

const buildErrorDetail = (error, fallbackMessage) => {
    const detail = error?.response?.data?.detail

    if (typeof detail === "string") {
        return {
            message: detail,
            retryable: false,
            code: detail === "Push config timeout" ? "PUSH_TIMEOUT" : undefined,
        }
    }

    if (detail && typeof detail === "object") {
        return {
            ...detail,
            message: detail.message ?? fallbackMessage,
            retryable: Boolean(detail.retryable),
        }
    }

    return {
        message: error?.message ?? fallbackMessage,
        retryable: false,
        code: error?.message === "Push config timeout" ? "PUSH_TIMEOUT" : undefined,
    }
}

const withTimeout = (promise, timeoutMs, timeoutMessage) => new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs)

    promise
        .then((value) => {
            window.clearTimeout(timeoutId)
            resolve(value)
        })
        .catch((error) => {
            window.clearTimeout(timeoutId)
            reject(error)
        })
})

const SUCCESS_REDIRECT_DELAY_MS = 900


export default function EditNodePage() {
    const { nodeId } = useParams()
    const navigate = useNavigate()

    // Node data
    const [loading, setLoading] = useState(true)
    const [name, setName] = useState("")
    const [location, setLocation] = useState("")
    const [hardwareUid, setHardwareUid] = useState("")

    // Automation settings
    const [scheduledHour, setScheduledHour] = useState(18)
    const [scheduledMinute, setScheduledMinute] = useState(0)
    const [scheduledTime, setScheduledTime] = useState("18:00")
    const [automationEnabled, setAutomationEnabled] = useState(true)

    // Batch strategy
    const [concurrentIrrigation, setConcurrentIrrigation] = useState(false)

    // Advanced settings
    const [showAdvanced, setShowAdvanced] = useState(false)
    const [minIrrigationPercent, setMinIrrigationPercent] = useState(20)
    const [maxIrrigationPercent, setMaxIrrigationPercent] = useState(200)
    const [mainValveMaxFlow, setMainValveMaxFlow] = useState(null)
    const [weatherCacheInterval, setWeatherCacheInterval] = useState(30)
    const [weatherCacheExpiry, setWeatherCacheExpiry] = useState(2)
    const [flowControlEnabled, setFlowControlEnabled] = useState(false)
    const [maxConcurrentZones, setMaxConcurrentZones] = useState(null)
    const [maxTotalIrrigationTime, setMaxTotalIrrigationTime] = useState(null)

    const [isSubmitting, setIsSubmitting] = useState(false)

    // Load node data
    useEffect(() => {
        const loadNode = async () => {
            try {
                const response = await fetchNodeById(nodeId)
                const node = response.data

                setName(node.name || "")
                setLocation(node.location || "")
                setHardwareUid(node.hardware_uid || "")

                // Automation settings
                setScheduledHour(node.automation.scheduled_hour || 18)
                setScheduledMinute(node.automation.scheduled_minute || 0)
                setScheduledTime(
                    `${String(node.automation.scheduled_hour || 18).padStart(2, '0')}:${String(node.automation.scheduled_minute || 0).padStart(2, '0')}`
                )
                setAutomationEnabled(node.automation.enabled !== false)

                // Weather settings
                setWeatherCacheInterval(node.automation.weather_cache_interval_minutes || 30)
                setWeatherCacheExpiry(node.automation.weather_cache_expiry_hours || 2)

                // Batch strategy
                setConcurrentIrrigation(node.batch_strategy.concurrent_irrigation || false)
                setFlowControlEnabled(node.batch_strategy.flow_control || false)
                setMaxConcurrentZones(node.batch_strategy.max_concurrent_zones || null)
                setMaxTotalIrrigationTime(node.batch_strategy.max_total_irrigation_time_minutes || null)

                // Irrigation limits
                setMinIrrigationPercent(node.irrigation_limits.min_percent || 20)
                setMaxIrrigationPercent(node.irrigation_limits.max_percent || 200)
                setMainValveMaxFlow(node.irrigation_limits.main_valve_max_flow || null)

                setLoading(false)
            } catch (error) {
                console.error("Failed to load node:", error)
                setLoading(false)
            }
        }

        loadNode()
    }, [nodeId])

    const updateScheduledTime = (time) => {
        setScheduledTime(time)
        const [hour, minute] = time.split(":").map(Number)
        setScheduledHour(hour)
        setScheduledMinute(minute)
    }

    const openControlDialog = (payload) => {
        const id = `edit-node-action-result-${Date.now()}`
        openControlActionDialog(id, payload)
    }

    const handleSubmit = async () => {
        if (isSubmitting) {
            return
        }

        const payload = {
            name,
            location,
            hardware: {
                input_pins: { pins: [] },
                output_pins: { pins: [] },
            },
            irrigation_limits: {
                min_percent: minIrrigationPercent,
                max_percent: maxIrrigationPercent,
                main_valve_max_flow: mainValveMaxFlow,
            },
            automation: {
                enabled: automationEnabled,
                scheduled_hour: scheduledHour,
                scheduled_minute: scheduledMinute,
                weather_cache_interval_minutes: weatherCacheInterval,
                weather_cache_expiry_hours: weatherCacheExpiry,
            },
            batch_strategy: {
                concurrent_irrigation: concurrentIrrigation,
                flow_control: flowControlEnabled,
                max_concurrent_zones: maxConcurrentZones,
                max_total_irrigation_time_minutes: maxTotalIrrigationTime,
            },
            logging: {
                enabled: true,
                log_level: "DEBUG",
            },
        }

        const PUSH_TIMEOUT_MS = 12000

        try {
            setIsSubmitting(true)

            const response = await updateNode(nodeId, payload)

            const pushResponse = await withTimeout(
                pushNodeConfig(nodeId),
                PUSH_TIMEOUT_MS,
                "Push config timeout",
            )

            openControlDialog({
                title: "Node updated",
                description: "Node configuration was updated and pushed successfully.",
                status: "success",
                nodeId: nodeId,
                mode: pushResponse?.data?.mode,
                correlationId: pushResponse?.data?.response?.correlation_id,
            })

            window.setTimeout(() => {
                navigate(`/configuration/nodes/${nodeId}`)
            }, SUCCESS_REDIRECT_DELAY_MS)
        } catch (error) {
            const errorDetail = buildErrorDetail(error, "Failed to update node and push config")
            openControlDialog({
                title: "Update node failed",
                description: errorDetail.message,
                status: "error",
                nodeId: errorDetail.node_id,
                code: errorDetail.code,
                retryable: errorDetail.retryable,
                correlationId: errorDetail.correlation_id,
            })
            console.error("Failed to update node and push config", error)
        } finally {
            setIsSubmitting(false)
        }
    }

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    if (loading) {
        return (
            <Box p={6}>
                <Text color="fg.muted">Loading node…</Text>
            </Box>
        )
    }

    return (
        <>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title={`Edit Node #${nodeId}`}
                subtitle={name || "Unnamed Node"}
                actions={
                    <HeaderActions>
                        <HeaderAction as={Link} to={`/configuration/nodes/${nodeId}`}>
                            Cancel
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />
            <Box p={6}>
                <SimpleGrid columns={{ base: 1, lg: 3 }} gap={6}>
                    <Stack gap={10} gridColumn="span 2">
                        {/* Basic settings */}
                        <Stack gap={6}>
                            <Heading size="md" color="fg" textAlign="left">
                                Primary Settings
                            </Heading>

                            <PanelSection title="Basic Information">
                                <Stack gap={6}>
                                    {hardwareUid && (
                                        <Box
                                            borderRadius="md"
                                            p={4}
                                            bg="rgba(56,178,172,0.06)"
                                            border="1px solid rgba(56,178,172,0.24)"
                                        >
                                            <Stack gap={2}>
                                                <Text fontSize="xs" color="fg.muted" textTransform="uppercase" letterSpacing="0.04em">
                                                    Paired Device
                                                </Text>
                                                <HStack>
                                                    <Text fontSize="sm" color="fg.muted">Hardware UID:</Text>
                                                    <Badge colorPalette="teal">{hardwareUid}</Badge>
                                                </HStack>
                                            </Stack>
                                        </Box>
                                    )}

                                    {/* Name input */}
                                    <Field.Root required>
                                        <Field.Label>Node Name <Field.RequiredIndicator /></Field.Label>
                                        <Input
                                            placeholder="e.g., Backyard Node"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                        />
                                        <Field.HelperText>
                                            Human-readable identifier for this node.
                                        </Field.HelperText>
                                        <Field.ErrorText>
                                            Name is required.
                                        </Field.ErrorText>
                                    </Field.Root>

                                    {/* Location input */}
                                    <Field.Root>
                                        <Field.Label>Location</Field.Label>
                                        <Input
                                            placeholder="e.g., Backyard Garden"
                                            value={location}
                                            onChange={(e) => setLocation(e.target.value)}
                                        />
                                        <Field.HelperText>
                                            Location description for easier identification.
                                        </Field.HelperText>
                                    </Field.Root>

                                </Stack>
                            </PanelSection>

                            <PanelSection title="Automation Settings">
                                <Stack spacing={4} gap={6}>
                                    {/* Scheduled time input */}
                                    <Field.Root>
                                        <Field.Label>Scheduled Time</Field.Label>
                                        <Input
                                            type="time"
                                            value={scheduledTime}
                                            onChange={(e) => updateScheduledTime(e.target.value)}
                                        />
                                        <Field.HelperText>
                                            Daily time to run automated irrigation.
                                        </Field.HelperText>
                                        <Field.ErrorText>
                                            Invalid time.
                                        </Field.ErrorText>
                                    </Field.Root>

                                    {/* Automation enabled input */}
                                    <HStack justify="space-between">
                                        <Field.Root colorPalette="teal">
                                            <Field.Label>Automatic Irrigation</Field.Label>
                                            <Switch.Root
                                                checked={automationEnabled}
                                                onChange={(checked) => setAutomationEnabled(!automationEnabled)}
                                            >
                                                <Switch.HiddenInput />
                                                <Switch.Control>
                                                    <Switch.Thumb />
                                                </Switch.Control>
                                                <Switch.Label>
                                                    {automationEnabled ? "Enabled" : "Disabled"}
                                                </Switch.Label>
                                            </Switch.Root>
                                            <Field.HelperText>
                                                Toggle to enable or disable automatic daily irrigation checks.
                                            </Field.HelperText>
                                        </Field.Root>
                                    </HStack>
                                </Stack>
                            </PanelSection>

                            <PanelSection title="Batch Strategy">
                                <Stack spacing={4} gap={6}>
                                    <Field.Root>
                                        <Field.Label>Irrigation mode</Field.Label>
                                        <SegmentGroup.Root
                                            value={concurrentIrrigation ? "concurrent" : "sequential"}
                                            onValueChange={(details) => {
                                                setConcurrentIrrigation(details.value === "concurrent")
                                            }}
                                            size="md"
                                            colorPalette="teal"
                                            css={{
                                                "--segment-indicator-bg": "colors.white",
                                                "--segment-indicator-shadow": "shadows.md",
                                            }}
                                        >
                                            <SegmentGroup.Indicator />
                                            <For each={["sequential", "concurrent"]}>
                                                {(item) => (
                                                    <SegmentGroup.Item key={item} value={item}>
                                                        <SegmentGroup.ItemText
                                                            _checked={{ color: "colorPalette.fg", fontWeight: "medium" }}
                                                        >
                                                            {item}
                                                        </SegmentGroup.ItemText>
                                                        <SegmentGroup.ItemHiddenInput />
                                                    </SegmentGroup.Item>
                                                )}
                                            </For>
                                        </SegmentGroup.Root>
                                        <Field.HelperText>
                                            Choose how to handle multiple irrigation zones simultaneously.
                                        </Field.HelperText>
                                        <Field.ErrorText>
                                            Invalid selection.
                                        </Field.ErrorText>
                                    </Field.Root>
                                </Stack>
                            </PanelSection>
                        </Stack>

                        {/* Advanced settings, collapsible */}
                        {showAdvanced && (
                            <Stack spacing={6} gap={6}>
                                <Heading size="md" color="fg" textAlign="left">
                                    Advanced Settings
                                </Heading>
                                <PanelSection title="Irrigation Limits">
                                    <Stack spacing={4} gap={6}>
                                        <HStack justify="space-between" align="flex-start">
                                            <Field.Root>
                                                <Field.Label>Minimum Irrigation %</Field.Label>
                                                <Input
                                                    type="number"
                                                    step="5"
                                                    value={minIrrigationPercent}
                                                    onChange={(e) => setMinIrrigationPercent(Number(e.target.value))}
                                                />
                                                <Field.HelperText>
                                                    If the calculated volume will be less than this percentage of the zone's
                                                    base volume, it will be clamped to this minimum.
                                                </Field.HelperText>
                                            </Field.Root>
                                            <Field.Root>
                                                <Field.Label>Maximum Irrigation %</Field.Label>
                                                <Input
                                                    type="number"
                                                    step="5"
                                                    value={maxIrrigationPercent}
                                                    onChange={(e) => setMaxIrrigationPercent(Number(e.target.value))}
                                                />
                                                <Field.HelperText>
                                                    If the calculated volume exceeds this percentage of the zone's base
                                                    volume, it will be clamped to this maximum.
                                                </Field.HelperText>
                                            </Field.Root>
                                        </HStack>
                                        <Field.Root>
                                            <Field.Label>Water Supply Max Flow (L/min)</Field.Label>
                                            <Input
                                                type="number"
                                                step="100"
                                                value={mainValveMaxFlow || ""}
                                                onChange={(e) => {
                                                    const val = e.target.value
                                                    if (val === "") {
                                                        setFlowControlEnabled(false)
                                                    }
                                                    setMainValveMaxFlow(val ? Number(val) : null)
                                                }}
                                                placeholder="Leave blank for no limit"
                                            />
                                            <Field.HelperText>
                                                Maximum flow rate in liters per minute for the water supply of this node.
                                            </Field.HelperText>
                                            <Field.ErrorText>
                                                Invalid flow rate.
                                            </Field.ErrorText>
                                        </Field.Root>
                                    </Stack>
                                </PanelSection>

                                <PanelSection title="Weather Fetching">
                                    <Text fontSize="sm" color="fg.muted" mb={6}>
                                        These settings control how often weather data is fetched and how long it is cached.
                                    </Text>
                                    <Stack spacing={4} gap={6}>
                                        <HStack justify="space-between" align="flex-start">
                                            <Field.Root required>
                                                <Field.Label>Weather Cache Interval <Field.RequiredIndicator /></Field.Label>
                                                <Input
                                                    type="number"
                                                    step="5"
                                                    value={weatherCacheInterval}
                                                    onChange={(e) => setWeatherCacheInterval(Number(e.target.value))}
                                                />
                                                <Field.HelperText>
                                                    Interval in minutes to fetch new weather data.
                                                </Field.HelperText>
                                                <Field.ErrorText>
                                                    Invalid interval.
                                                </Field.ErrorText>
                                            </Field.Root>
                                            <Field.Root required>
                                                <Field.Label>Weather Cache Expiry <Field.RequiredIndicator /></Field.Label>
                                                <Input
                                                    type="number"
                                                    step="1"
                                                    value={weatherCacheExpiry}
                                                    onChange={(e) => setWeatherCacheExpiry(Number(e.target.value))}
                                                />
                                                <Field.HelperText>
                                                    Duration in hours before cached weather data is considered stale.
                                                </Field.HelperText>
                                                <Field.ErrorText>
                                                    Invalid duration.
                                                </Field.ErrorText>
                                            </Field.Root>
                                        </HStack>
                                    </Stack>
                                </PanelSection>

                                <PanelSection title="Flow Control & Batch Strategy">
                                    <Stack spacing={4} gap={6}>
                                        <Field.Root colorPalette="teal">
                                            <Field.Label>Flow Control</Field.Label>
                                            <Switch.Root
                                                checked={flowControlEnabled}
                                                onChange={(checked) => setFlowControlEnabled(!flowControlEnabled)}
                                                disabled={mainValveMaxFlow === null}
                                            >
                                                <Switch.HiddenInput />
                                                <Switch.Control>
                                                    <Switch.Thumb />
                                                </Switch.Control>
                                                <Switch.Label>
                                                    {flowControlEnabled ? "Enabled" : "Disabled"}
                                                </Switch.Label>
                                            </Switch.Root>
                                            <Field.HelperText>
                                                {mainValveMaxFlow === null
                                                    ? "Set a Water Supply Max Flow to enable flow control."
                                                    : "Enable to manage water pressure during concurrent irrigation to stay within water supply limits."
                                                }

                                            </Field.HelperText>
                                        </Field.Root>

                                        <HStack justify="space-between" align="flex-start">
                                            <Field.Root>
                                                <Field.Label>Max Concurrent Zones</Field.Label>
                                                <Input
                                                    type="number"
                                                    step="1"
                                                    value={maxConcurrentZones || ""}
                                                    onChange={(e) => {
                                                        const val = e.target.value
                                                        setMaxConcurrentZones(val ? Number(val) : null)
                                                    }}
                                                    placeholder="Leave blank for no limit"
                                                />
                                                <Field.HelperText>
                                                    Maximum number of zones that can be irrigated simultaneously.
                                                </Field.HelperText>
                                            </Field.Root>
                                            <Field.Root>
                                                <Field.Label>Max Total Irrigation Time</Field.Label>
                                                <Input
                                                    type="number"
                                                    step="30"
                                                    value={maxTotalIrrigationTime || ""}
                                                    onChange={(e) => {
                                                        const val = e.target.value
                                                        setMaxTotalIrrigationTime(val ? Number(val) : null)
                                                    }}
                                                    placeholder="Leave blank for no limit"
                                                />
                                                <Field.HelperText>
                                                    Maximum total irrigation time for one cycle in minutes.
                                                </Field.HelperText>
                                            </Field.Root>
                                        </HStack>
                                    </Stack>
                                </PanelSection>
                            </Stack>
                        )}

                        <HStack spacing={4}>
                            <Button
                                alignSelf="flex-start"
                                variant="outline"
                                colorPalette="teal"
                                onClick={() => setShowAdvanced((v) => !v)}
                            >
                                {showAdvanced ? "Hide advanced settings" : "Show advanced settings"}
                            </Button>

                            <Button
                                alignSelf="flex-start"
                                colorPalette="teal"
                                onClick={handleSubmit}
                                isDisabled={!name.trim() || isSubmitting}
                                loading={isSubmitting}
                            >
                                Save Changes
                            </Button>
                        </HStack>
                    </Stack >

                    <HelpSidebar fullHeight>
                        {createNodeHelp.map(box => (
                            <HelpBox key={box.id} title={box.title}>
                                {box.description}
                            </HelpBox>
                        ))}

                        {showAdvanced &&
                            createNodeAdvancedHelp.map(box => (
                                <HelpBox key={box.id} title={box.title}>
                                    {box.description}
                                </HelpBox>
                            ))}
                    </HelpSidebar>

                </SimpleGrid >

            </Box >
        </>
    )
}
