import { useRef, useState, useMemo, useEffect } from "react"
import { Link, useParams, useNavigate, useOutletContext } from "react-router-dom"
import {
    SimpleGrid,
    HStack,
    Stack,
    Box,
    Heading,
    Text,
    Button,
} from "@chakra-ui/react"

import { updateZone, fetchZoneById, pushNodeConfig, fetchNodeHeader } from "../../../../api/nodes.api"
import {
    ControlActionDialogViewport,
    openControlActionDialog,
} from "../../../../components/ui/ControlActionDialogOverlay"

import StepBasicInfo from "../CreateZoneWizard/steps/StepBasicInfo"
import StepIrrigationMode from "../CreateZoneWizard/steps/StepIrrigationMode"
import StepIrrigationEvenArea from "../CreateZoneWizard/steps/StepIrrigationEvenArea"
import StepIrrigationPerPlant from "../CreateZoneWizard/steps/StepIrrigationPerPlant"
import StepEmittersEvenArea from "../CreateZoneWizard/steps/StepEmittersEvenArea"
import StepEmittersPerPlant from "../CreateZoneWizard/steps/StepEmittersPerPlant"
import StepEmittersPerPlantAuto from "../CreateZoneWizard/steps/StepEmittersPerPlantAuto"
import StepBehaviorSettings from "../CreateZoneWizard/steps/StepBehaviorSettings"
import StepReview from "../CreateZoneWizard/steps/StepReview"

import HelpBox from "../../../../components/HelpBox"
import HelpSidebar from "../../../../components/HelpSidebar"

import { wizardHelp } from "../../../../help/WizardHelp"

import GlassPageHeader, { HeaderActions } from '../../../../components/layout/GlassPageHeader'
import { HeaderAction } from '../../../../components/ui/ActionButtons'

const SUCCESS_REDIRECT_DELAY_MS = 900

export default function EditZoneWizard() {
    const { nodeId, zoneId } = useParams()
    const navigate = useNavigate()

    const [currentStep, setCurrentStep] = useState(0)
    const [submitError, setSubmitError] = useState(null)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const [loadError, setLoadError] = useState(null)
    const [headerPins, setHeaderPins] = useState([])
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const openControlDialog = (payload) => {
        const id = `edit-zone-action-result-${Date.now()}`
        openControlActionDialog(id, payload)
    }

    /* --------------------------------------------
       Zone draft state - initialized from existing zone
    -------------------------------------------- */

    const [zoneDraft, setZoneDraft] = useState({
        name: "",
        relay_pin: null,
        enabled: true,
        irrigation_mode: null,

        irrigation_configuration: null,
        emitters_configuration: null,

        local_correction_factors: {
            solar: 0,
            rain: 0,
            temperature: 0,
        },
        frequency_settings: {
            dynamic_interval: false,
            min_interval_days: 1,
            max_interval_days: 7,
            carry_over_volume: true,
            irrigation_volume_threshold_percent: 20,
        },
        fallback_strategy: {
            on_fresh_weather_data_unavailable: "use_cached_data",
            on_expired_weather_data: "use_cached_data",
            on_missing_weather_data: "use_base_volume",
        },
    })

    /* --------------------------------------------
      Load existing zone data on mount
    -------------------------------------------- */

    useEffect(() => {
        const loadZone = async () => {
            try {
                setIsLoading(true)
                const response = await fetchZoneById(nodeId, zoneId)
                const zone = response.data

                // Initialize zoneDraft with existing data
                setZoneDraft({
                    name: zone.name || "",
                    relay_pin: zone.relay_pin || null,
                    enabled: zone.enabled !== undefined ? zone.enabled : true,
                    irrigation_mode: zone.irrigation_mode || null,
                    irrigation_configuration: zone.irrigation_configuration || null,
                    emitters_configuration: zone.emitters_configuration || null,
                    local_correction_factors: zone.local_correction_factors || {
                        solar: 0,
                        rain: 0,
                        temperature: 0,
                    },
                    frequency_settings: zone.frequency_settings || {
                        dynamic_interval: false,
                        min_interval_days: 1,
                        max_interval_days: 7,
                        carry_over_volume: true,
                        irrigation_volume_threshold_percent: 20,
                    },
                    fallback_strategy: zone.fallback_strategy || {
                        on_fresh_weather_data_unavailable: "use_cached_data",
                        on_expired_weather_data: "use_cached_data",
                        on_missing_weather_data: "use_base_volume",
                    },
                })

                setIsLoading(false)
            } catch (error) {
                console.error("Failed to load zone:", error)
                setLoadError("Failed to load zone details")
                setIsLoading(false)
            }
        }

        loadZone()
    }, [nodeId, zoneId])

    /* --------------------------------------------
        Load GPIO header details for pin selection step
    -------------------------------------------- */

    useEffect(() => {
        fetchNodeHeader(nodeId)
            .then((response) => {
                const mappedPins = response.data.pins.map(pin => ({
                    boardPinId: pin.board_pin,
                    bcmPinId: pin.bcm,
                    occupiedBy: pin.occupied_by,
                    type:
                        pin.type === "gpio"
                            ? pin.occupied_by && pin.occupied_by !== zoneId
                                ? "gpio_used"
                                : "gpio_free"
                            : pin.type,
                    label:
                        pin.type === "gpio"
                            ? `GPIO ${pin.bcm}`
                            : pin.type === "ground"
                                ? "GND"
                                : "POWER"
                }))

                setHeaderPins(mappedPins)
            })
    }, [nodeId])

    /* --------------------------------------------
        AutoOptimize state for per-plant emitter configuration
    -------------------------------------------- */

    const [autoOptimize, setAutoOptimize] = useState(true)

    /* --------------------------------------------
       Steps (DATA-DRIVEN)
    -------------------------------------------- */

    const steps = useMemo(
        () => [
            {
                key: "basic",
                title: "Basic",
                description: "Zone identity & valve",
                isValid: () =>
                    zoneDraft.name.trim() !== "" &&
                    zoneDraft.relay_pin !== null,
                render: () => (
                    <StepBasicInfo
                        data={zoneDraft}
                        onChange={setZoneDraft}
                        headerPins={headerPins}
                    />
                ),
            },
            {
                key: "mode",
                title: "Mode",
                description: "Irrigation strategy",
                isValid: () => zoneDraft.irrigation_mode !== null,
                render: () => (
                    <StepIrrigationMode
                        value={zoneDraft.irrigation_mode}
                        onChange={(mode) =>
                            setZoneDraft({
                                ...zoneDraft,
                                irrigation_mode: mode,

                                // Reset dependent configurations
                                irrigation_configuration: null,
                                emitters_configuration: null,
                            })
                        }
                    />
                ),
            },
            {
                key: "irrigation",
                title: "Irrigation",
                description: "Water targets",
                isValid: () => {
                    if (zoneDraft.irrigation_mode === "even_area") {
                        return (
                            zoneDraft.irrigation_configuration?.zone_area_m2 &&
                            zoneDraft.irrigation_configuration?.target_mm
                        )
                    }

                    if (zoneDraft.irrigation_mode === "per_plant") {
                        if (autoOptimize) return true

                        return !!zoneDraft.irrigation_configuration?.base_target_volume_liters
                    }

                    return false
                },
                render: () =>
                    zoneDraft.irrigation_mode === "even_area" ? (
                        <StepIrrigationEvenArea
                            data={zoneDraft.irrigation_configuration || {}}
                            onChange={(config) =>
                                setZoneDraft({
                                    ...zoneDraft,
                                    irrigation_configuration: config,
                                })
                            }
                        />
                    ) : (
                        <StepIrrigationPerPlant
                            data={zoneDraft.irrigation_configuration || {}}
                            autoOptimize={autoOptimize}
                            onChange={(config) =>
                                setZoneDraft({
                                    ...zoneDraft,
                                    irrigation_configuration: config,
                                })
                            }
                            onAutoOptimizeChange={setAutoOptimize}
                        />
                    ),
            },
            {
                key: "emitters",
                title: "Emitters",
                description: "Hardware layout",
                isValid: () =>
                    zoneDraft.irrigation_mode === "even_area"
                        ? zoneDraft.emitters_configuration?.summary?.length > 0
                        : zoneDraft.emitters_configuration?.plants?.length > 0,
                render: () =>
                    zoneDraft.irrigation_mode === "even_area" ? (
                        <StepEmittersEvenArea
                            data={zoneDraft.emitters_configuration || {}}
                            onChange={(config) =>
                                setZoneDraft({
                                    ...zoneDraft,
                                    emitters_configuration: config,
                                })
                            }
                        />
                    ) : autoOptimize ? (
                        <StepEmittersPerPlantAuto
                            data={zoneDraft.emitters_configuration || {}}
                            onChange={(config) =>
                                setZoneDraft(prev => ({
                                    ...prev,
                                    emitters_configuration: config,
                                }))
                            }
                            onIrrigationChange={(config) =>
                                setZoneDraft(prev => ({
                                    ...prev,
                                    irrigation_configuration: {
                                        ...prev.irrigation_configuration,
                                        ...config,
                                    },
                                }))
                            }
                        />
                    ) : (
                        <StepEmittersPerPlant
                            data={zoneDraft.emitters_configuration || {}}
                            baseTargetVolumeLiters={
                                zoneDraft.irrigation_configuration?.base_target_volume_liters || 0
                            }
                            onChange={(config) =>
                                setZoneDraft({
                                    ...zoneDraft,
                                    emitters_configuration: config,
                                })
                            }
                        />
                    ),
            },
            {
                key: "behavior",
                title: "Behavior",
                description: "Frequency & corrections",
                isValid: () => true,
                render: () => (
                    <StepBehaviorSettings
                        data={{
                            local_correction_factors:
                                zoneDraft.local_correction_factors,
                            frequency_settings:
                                zoneDraft.frequency_settings,
                            fallback_strategy:
                                zoneDraft.fallback_strategy,
                        }}
                        onChange={(updated) =>
                            setZoneDraft({
                                ...zoneDraft,
                                ...updated,
                            })
                        }
                    />
                ),
            },
            {
                key: "review",
                title: "Review",
                description: "Final check",
                isValid: () => true,
                render: () => <StepReview data={zoneDraft} />,
            },
        ],
        [zoneDraft, autoOptimize]
    )

    const activeStep = steps[currentStep]

    /* --------------------------------------------
       Navigation
    -------------------------------------------- */

    const goNext = () => {
        if (currentStep < steps.length - 1) {
            setCurrentStep((s) => s + 1)
        }
        console.log("Current zone draft:", zoneDraft)
    }

    const goBack = () => {
        if (currentStep > 0) {
            setCurrentStep((s) => s - 1)
        }
    }

    const getErrorMessage = (error) => {
        const detail = error.response?.data?.detail
        if (typeof detail === "string") return detail
        if (detail?.message) return detail.message
        return (
            error.response?.data?.message ??
            JSON.stringify(error.response?.data, null, 2) ??
            "An unknown error occurred."
        )
    }

    const submitZone = async (pushAfterUpdate = false) => {
        setIsSubmitting(true)
        setSubmitError(null)

        try {
            await updateZone(nodeId, zoneId, zoneDraft)

            if (pushAfterUpdate) {
                try {
                    const pushResponse = await pushNodeConfig(nodeId)
                    openControlDialog({
                        title: "Zone updated",
                        description: "Zone was updated and node configuration was pushed successfully.",
                        status: "success",
                        zoneId,
                        nodeId,
                        mode: pushResponse?.data?.mode,
                        correlationId: pushResponse?.data?.response?.correlation_id,
                    })
                } catch (pushError) {
                    console.error("Push config failed after zone update:", pushError)

                    openControlDialog({
                        title: "Zone updated, push failed",
                        description: getErrorMessage(pushError),
                        status: "error",
                        zoneId,
                        nodeId,
                    })

                    window.setTimeout(() => {
                        navigate(`/configuration/nodes/${nodeId}/zones/${zoneId}`)
                    }, SUCCESS_REDIRECT_DELAY_MS)
                    return
                }
            } else {
                openControlDialog({
                    title: "Zone updated",
                    description: "Zone was updated successfully.",
                    status: "success",
                    zoneId,
                    nodeId,
                })
            }

            window.setTimeout(() => {
                navigate(`/configuration/nodes/${nodeId}/zones/${zoneId}`)
            }, SUCCESS_REDIRECT_DELAY_MS)
        } catch (error) {
            console.error("Update zone failed:", error)

            if (error.response) {
                console.error("Response data:", error.response.data)
                console.error("Status:", error.response.status)
            }

            setSubmitError(getErrorMessage(error))
        } finally {
            setIsSubmitting(false)
        }
    }

    /* --------------------------------------------
       Sidebar scroll logic
    -------------------------------------------- */

    const helpBoxRefs = useRef({})

    useEffect(() => {
        const ref = helpBoxRefs.current[activeStep.key]
        if (ref) {
            ref.scrollIntoView({
                behavior: "smooth",
                block: "start",
            })
        }
    }, [activeStep.key])

    /* --------------------------------------------
        New step scroll to top
    -------------------------------------------- */

    useEffect(() => {
        window.scrollTo({ top: 0, behavior: "smooth" })
    }, [currentStep])

    /* --------------------------------------------
       Render - Loading state
    -------------------------------------------- */

    if (isLoading) {
        return (
            <Box p={4}>
                <Text>Loading zone details...</Text>
            </Box>
        )
    }

    if (loadError) {
        return (
            <Box p={4}>
                <Text color="red.700">{loadError}</Text>
            </Box>
        )
    }

    /* --------------------------------------------
       Render - Main
    -------------------------------------------- */

    return (
        <>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title={`Edit Zone #${zoneId}`}
                subtitle={`Node ID: ${nodeId}`}
                actions={
                    <HeaderActions>
                        <HeaderAction
                            as={Link}
                            to={`/configuration/nodes/${nodeId}/zones/${zoneId}`}
                        >
                            Exit Wizard
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            >
            </GlassPageHeader>

            <Box p={6} textAlign="left">
                {/* Step indicator */}
                <HStack mb={4} spacing={2}>
                    {steps.map((step, index) => (
                        <Box
                            key={step.key}
                            px={3}
                            py={1}
                            borderRadius="full"
                            fontSize="sm"
                            transition="all 0.15s ease"
                            bg={index === currentStep ? "teal.100" : "bg.subtle"}
                            color={index === currentStep ? "teal.700" : "fg.muted"}
                            fontWeight={index === currentStep ? "semibold" : "normal"}
                            transform={index === currentStep ? "scale(1.05)" : "scale(1)"}
                        >
                            {index + 1}. {step.title}
                        </Box>
                    ))}
                </HStack>

                <SimpleGrid columns={{ base: 1, lg: 3 }} gap={6}>
                    {/* Main column */}
                    <Stack gap={6} gridColumn="span 2">
                        <Box
                            key={activeStep.key}
                            animation="fadeSlideIn 0.25s ease-out"
                        >
                            {activeStep.render()}
                        </Box>

                        {submitError && activeStep.key === "review" && (
                            <Box p={3} bg="red.50" borderRadius="md">
                                <Text fontSize="sm" color="red.700">
                                    {submitError}
                                </Text>
                            </Box>
                        )}

                        <HStack>
                            <Button
                                variant="outline"
                                colorPalette="teal"
                                onClick={goBack}
                                disabled={currentStep === 0 || isSubmitting}
                            >
                                Back
                            </Button>

                            {activeStep.key !== "review" ? (
                                <Button
                                    variant="outline"
                                    colorPalette="teal"
                                    onClick={goNext}
                                    disabled={!activeStep.isValid()}
                                >
                                    Next
                                </Button>
                            ) : (
                                <HStack>
                                    <Button
                                        colorPalette="teal"
                                        onClick={() => submitZone(false)}
                                        disabled={isSubmitting}
                                    >
                                        Update Zone
                                    </Button>
                                    <Button
                                        loading={isSubmitting}
                                        loadingText="Updating ..."
                                        colorPalette="teal"
                                        onClick={() => submitZone(true)}
                                        disabled={isSubmitting}
                                    >
                                        Update Zone &amp; Push
                                    </Button>
                                </HStack>
                            )}
                        </HStack>
                    </Stack>

                    {/* Sidebar */}
                    <HelpSidebar
                        sticky
                        stickyTop="80px"
                        maxHeight="calc(100vh - 120px)"
                    >
                        {wizardHelp.map(box => (
                            <HelpBox
                                key={box.step}
                                title={box.title}
                                active={box.step === activeStep.key}
                                boxRef={el => {
                                    helpBoxRefs.current[box.step] = el
                                }}
                            >
                                {box.description}
                            </HelpBox>
                        ))}
                    </HelpSidebar>

                </SimpleGrid>
            </Box>
        </>
    )
}
