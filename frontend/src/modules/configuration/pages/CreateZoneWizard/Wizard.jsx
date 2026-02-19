import { useRef, useState, useMemo, useEffect } from "react"
import { Link, useParams, useNavigate } from "react-router-dom"
import {
    SimpleGrid,
    HStack,
    Stack,
    Box,
    Heading,
    Text,
    Button,
} from "@chakra-ui/react"

import { createZone } from "../../../../api/nodes.api"

import StepBasicInfo from "./steps/StepBasicInfo"
import StepIrrigationMode from "./steps/StepIrrigationMode"
import StepIrrigationEvenArea from "./steps/StepIrrigationEvenArea"
import StepIrrigationPerPlant from "./steps/StepIrrigationPerPlant"
import StepEmittersEvenArea from "./steps/StepEmittersEvenArea"
import StepEmittersPerPlant from "./steps/StepEmittersPerPlant"
import StepEmittersPerPlantAuto from "./steps/StepEmittersPerPlantAuto"
import StepBehaviorSettings from "./steps/StepBehaviorSettings"
import StepReview from "./steps/StepReview"

import HelpBox from "../../../../components/HelpBox"
import HelpSidebar from "../../../../components/HelpSidebar"

import { wizardHelp } from "../../../../help/WizardHelp"

import GlassPageHeader, { HeaderActions } from '../../../../components/layout/GlassPageHeader'
import { HeaderAction, HeaderActionDanger } from '../../../../components/ui/ActionButtons'

export default function Wizard() {
    const { nodeId } = useParams()
    const navigate = useNavigate()

    const [currentStep, setCurrentStep] = useState(0)
    const [submitError, setSubmitError] = useState(null)

    /* --------------------------------------------
       Zone draft state
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
                            autoOptimize={autoOptimize} // Pass the autoOptimize state
                            onChange={(config) =>
                                setZoneDraft({
                                    ...zoneDraft,
                                    irrigation_configuration: config,
                                })
                            }
                            onAutoOptimizeChange={setAutoOptimize} // Pass the state updater
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
        // For debugging, show zoneDraft in console on next
        console.log("Current zone draft:", zoneDraft)
    }

    const goBack = () => {
        if (currentStep > 0) {
            setCurrentStep((s) => s - 1)
        }
    }

    const handleSubmit = () => {
        createZone(nodeId, zoneDraft)
            .then((res) =>
                navigate(`/configuration/nodes/${nodeId}/zones/${res.data.id}`)
            )
            .catch((error) => {
                console.error("Create zone failed:", error)

                if (error.response) {
                    console.error("Response data:", error.response.data)
                    console.error("Status:", error.response.status)
                }

                setSubmitError(
                    error.response?.data?.message ??
                    JSON.stringify(error.response?.data, null, 2) ??
                    "An unknown error occurred."
                )
            }
            )
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
       Render
    -------------------------------------------- */

    return (
        <>
            <GlassPageHeader
                title="Create New Zone"
                subtitle={`Node ID: ${nodeId}`}
                actions={
                    <HeaderActions>
                        <HeaderAction
                            as={Link}
                            to={`/configuration/nodes/${nodeId}`}
                        >
                            Exit Wizard
                        </HeaderAction>
                    </HeaderActions>
                }
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
                                disabled={currentStep === 0}
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
                                <Button
                                    colorPalette="teal"
                                    onClick={handleSubmit}
                                >
                                    Create Zone
                                </Button>
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

