import { useState, useEffect, useRef } from "react"
import {
    Box,
    Text,
    VStack,
    HStack,
    Button,
    Input,
    NumberInput,
    SimpleGrid,
    Badge,
    Stack,
    Separator,
    Spinner,
    Alert,
} from "@chakra-ui/react"

import PanelSection from "../../../../../components/layout/PanelSection"
import { optimizePerPlant } from "../../../../../api/nodes.api"

const MIN_LOADING_TIME = 3000 // Minimum loading time in milliseconds to ensure the user sees the loading state
const DRIPPER_PRESETS = [1.2, 2, 4, 8]
const THINKING_STEPS = [
    "Exploring combinations...",
    "Evaluating constraints...",
    "Searching for optimal allocation...",
    "Optimizing irrigation time...",
    "Finalizing solution..."
]

export default function StepEmittersPerPlantAuto({ data, onChange, onIrrigationChange }) {
    const [plants, setPlants] = useState([])
    const [drippers, setDrippers] = useState([])
    const [proposal, setProposal] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [isLocked, setIsLocked] = useState(false)     // Locking mechanism to prevent changes after proposal generation
    const [isAccepted, setIsAccepted] = useState(false) // Flag to indicate if the proposal has been accepted, which would also lock changes
    const proposalRef = useRef(null)

    const [thinkingStepIndex, setThinkingStepIndex] = useState(0)
    const [visibleThinkingStep, setVisibleThinkingStep] = useState(null)
    const [isFading, setIsFading] = useState(false)

    // If mounting with existing data, reset the emitter configuration to ensure a fresh start
    useEffect(() => {
        onChange({
            ...data,
            plants: [],
        })
    }, [])

    useEffect(() => {
        if (!loading) return

        setIsFading(true)

        const fadeTimeout = setTimeout(() => {
            setVisibleThinkingStep(THINKING_STEPS[thinkingStepIndex])
            setIsFading(false)
        }, 300) // fade-out duration

        return () => clearTimeout(fadeTimeout)
    }, [thinkingStepIndex, loading])


    useEffect(() => {
        if (proposal && proposalRef.current) {
            proposalRef.current.scrollIntoView({
                behavior: "smooth",
                block: "start",
            })
        }
    }, [proposal])

    /* ======================================================
       PLANTS
    ====================================================== */

    const addPlant = () => {
        setPlants([
            ...plants,
            {
                plant_id: "",
                target_volume_liters: 0.1,
                tolerance_percent: 10,
                max_emitter_quantity: 3,
            },
        ])
    }

    const removePlant = (index) => {
        setPlants(plants.filter((_, i) => i !== index))
    }

    /* ======================================================
       DRIPPERS
    ====================================================== */

    const addDripperPreset = (flow) => {
        if (drippers.some(d => d.flow_rate_lph === flow)) {
            return
        }
        setDrippers([
            ...drippers,
            {
                dripper_id: `dripper-${flow}`,
                flow_rate_lph: flow,
                count: null,
            },
        ])
    }

    const addCustomDripper = () => {
        setDrippers([
            ...drippers,
            {
                dripper_id: `dripper-${drippers.length + 1}`,
                flow_rate_lph: 0,
                count: null,
                isCustom: true, // Mark this dripper as custom
            },
        ])
    }

    const removeDripper = (index) => {
        setDrippers(drippers.filter((_, i) => i !== index))
    }

    /* ======================================================
       OPTIMIZATION
    ====================================================== */

    const handleGenerate = async () => {
        const startTime = Date.now()

        setLoading(true)
        setThinkingStepIndex(0)
        setVisibleThinkingStep(THINKING_STEPS[0])

        const interval = setInterval(() => {
            setThinkingStepIndex((prev) =>
                prev < THINKING_STEPS.length - 1 ? prev + 1 : prev
            )
        }, 4000)

        setError(null)
        setProposal(null)
        setIsLocked(true)   // lock the configuration to prevent changes while optimization is in progress

        try {
            const response = await optimizePerPlant({
                plants,
                available_drippers: drippers,
            })

            // minimum loading time enforcement
            const elapsed = Date.now() - startTime
            const remaining = MIN_LOADING_TIME - elapsed

            if (remaining > 0) {
                await new Promise(resolve => setTimeout(resolve, remaining))
            }

            setProposal(response.data)

        } catch (err) {
            setIsLocked(false)   // unlock if optimization fails, allowing user to make adjustments

            if (err.response?.status === 400) {
                setError(err.response.data?.detail ?? "Invalid configuration.")
            } else {
                setError("Server error or timeout. Please try again.")
            }
        } finally {
            setLoading(false)
            clearInterval(interval)
        }
    }


    return (
        <Stack gap={10}>

            {/* ======================================================
                PLANTS
            ====================================================== */}

            {!isLocked ? (
                <PanelSection
                    title="🌿 Target volumes per plant"
                    description="Define how much water each plant should receive per irrigation cycle."
                >
                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>

                        {plants.map((plant, index) => (
                            <Box
                                key={index}
                                p={5}
                                borderRadius="xl"
                                borderWidth="1px"
                                borderColor="border.subtle"
                                bg="bg.panel"
                                boxShadow="sm"
                                transition="all 0.15s"
                                _hover={{
                                    borderColor: "teal.300",
                                    boxShadow: "md",
                                }}
                            >
                                <Stack gap={4}>

                                    <HStack justify="space-between">
                                        <Text fontWeight="medium">
                                            🌱 {plant.plant_id || "Unnamed plant"}
                                        </Text>
                                        <Button
                                            size="xs"
                                            variant="ghost"
                                            colorPalette="red"
                                            onClick={() => removePlant(index)}
                                        >
                                            Remove
                                        </Button>
                                    </HStack>

                                    <Stack>
                                        <Text fontSize="xs" color="fg.muted">
                                            Plant name
                                        </Text>
                                        <Input
                                            placeholder="e.g. Oleander"
                                            value={plant.plant_id}
                                            onChange={(e) => {
                                                const updated = [...plants]
                                                updated[index].plant_id = e.target.value
                                                setPlants(updated)
                                            }}
                                        />
                                    </Stack>

                                    <HStack>
                                        <Stack width="100%">
                                            <Text fontSize="xs" color="fg.muted">
                                                Target volume (L)
                                            </Text>
                                            <NumberInput.Root
                                                value={String(plant.target_volume_liters)}
                                                min={0.01}
                                                step={0.1}
                                                onValueChange={(details) => {
                                                    const updated = [...plants]
                                                    updated[index].target_volume_liters =
                                                        parseFloat(details.value) || 0.1
                                                    setPlants(updated)
                                                }}
                                            >
                                                <NumberInput.Control />
                                                <NumberInput.Input />
                                            </NumberInput.Root>
                                        </Stack>

                                        <Stack width="100%">
                                            <Text fontSize="xs" color="fg.muted">
                                                Tolerance (%)
                                            </Text>
                                            <NumberInput.Root
                                                value={String(plant.tolerance_percent)}
                                                min={0}
                                                max={50}
                                                step={1}
                                                onValueChange={(details) => {
                                                    const updated = [...plants]
                                                    updated[index].tolerance_percent =
                                                        parseFloat(details.value) || 0
                                                    setPlants(updated)
                                                }}
                                            >
                                                <NumberInput.Control />
                                                <NumberInput.Input />
                                            </NumberInput.Root>
                                        </Stack>
                                    </HStack>

                                    <Badge colorPalette="grey" alignSelf="start">
                                        Max emitters: {plant.max_emitter_quantity}
                                    </Badge>

                                </Stack>
                            </Box>
                        ))}

                    </SimpleGrid>

                    <Button mt={6} variant="outline" onClick={addPlant}>
                        + Add plant
                    </Button>
                </PanelSection>
            ) : (
                <PanelSection
                    title="🌱 Target volumes per plant"
                >
                    <Text fontSize="sm" color="fg.muted">
                        Editing is temporarily disabled. Discard the proposal to modify plants.
                    </Text>
                </PanelSection>
            )}

            {/* ======================================================
                DRIPPERS
            ====================================================== */}
            {!isLocked ? (
                <PanelSection
                    title="💧 Available drippers"
                    description="Select available emitter types for this zone."
                >
                    <HStack mb={6} wrap="wrap">
                        {DRIPPER_PRESETS.map(flow => (
                            <Button
                                key={flow}
                                size="sm"
                                variant="outline"
                                onClick={() => addDripperPreset(flow)}
                            >
                                <HStack>
                                    <Text fontSize="sm" color="teal.700">
                                        +
                                    </Text>
                                    <Badge colorPalette="teal">
                                        {flow} L/h
                                    </Badge>
                                </HStack>
                            </Button>
                        ))}

                        <Button
                            size="sm"
                            variant="ghost"
                            colorPalette="teal"
                            onClick={addCustomDripper}
                        >
                            + Custom
                        </Button>
                    </HStack>

                    <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>

                        {drippers.map((d, index) => (
                            <Box
                                key={index}
                                p={4}
                                borderRadius="lg"
                                borderWidth="1px"
                                borderColor="border.subtle"
                                bg="bg.panel"
                                boxShadow="sm"
                            >
                                <Stack gap={3}>

                                    <HStack justify="space-between">
                                        <Badge colorPalette="teal">
                                            {d.flow_rate_lph || "Custom"} L/h
                                        </Badge>
                                        <Button
                                            size="xs"
                                            variant="ghost"
                                            colorPalette="red"
                                            onClick={() => removeDripper(index)}
                                        >
                                            Remove
                                        </Button>
                                    </HStack>
                                    <HStack>
                                        <Stack>
                                            <Text fontSize="xs" color="fg.muted">
                                                Flow rate (L/h)
                                            </Text>
                                            <NumberInput.Root
                                                value={String(d.flow_rate_lph)}
                                                min={0}
                                                step={0.1}
                                                onValueChange={(details) => {
                                                    const updated = [...drippers]
                                                    updated[index].flow_rate_lph =
                                                        parseFloat(details.value) || 0
                                                    setDrippers(updated)
                                                }}
                                                disabled={!d.isCustom} // Only allow editing flow rate for custom drippers
                                            >
                                                <NumberInput.Control />
                                                <NumberInput.Input />
                                            </NumberInput.Root>
                                        </Stack>

                                        <Stack>
                                            <Text fontSize="xs" color="fg.muted">
                                                Quantity (optional)
                                            </Text>
                                            <NumberInput.Root
                                                value={d.count !== null ? String(d.count) : ""}
                                                min={0}
                                                step={1}
                                                onValueChange={(details) => {
                                                    const updated = [...drippers]
                                                    updated[index].count =
                                                        details.value === ""
                                                            ? null
                                                            : parseInt(details.value)
                                                    setDrippers(updated)
                                                }}
                                            >
                                                <NumberInput.Control />
                                                <NumberInput.Input placeholder="Unlimited" />
                                            </NumberInput.Root>
                                        </Stack>
                                    </HStack>

                                </Stack>
                            </Box>
                        ))}

                    </SimpleGrid>
                </PanelSection>
            ) : (
                <PanelSection
                    title="💧 Available drippers"
                >
                    <Text fontSize="sm" color="fg.muted">
                        Editing is temporarily disabled. Discard the proposal to modify drippers.
                    </Text>
                </PanelSection>
            )}

            {/* ======================================================
                GENERATE CTA
            ====================================================== */}
            {!proposal && !isAccepted && (
                <PanelSection>
                    {!loading && (
                        <HStack justify="space-between">
                            <Stack>
                                <Text fontWeight="semibold">
                                    Ready to optimize?
                                </Text>
                                {plants.length === 0 || drippers.length === 0 ? (
                                    <Text fontSize="sm" color="fg.muted">
                                        Please add at least one plant and one dripper to generate a proposal.
                                    </Text>
                                ) : (
                                    <Text fontSize="sm" color="fg.muted">
                                        The system will calculate the most efficient emitter allocation.
                                    </Text>
                                )}
                            </Stack>

                            <Button
                                colorPalette="teal"
                                size="lg"
                                onClick={handleGenerate}
                                disabled={loading || plants.length === 0 || drippers.length === 0} // Disable if loading or if there are no plants or drippers defined
                            >
                                Generate proposal
                            </Button>
                        </HStack>
                    )}

                    {error && (
                        <Alert.Root status="error" mt={4} borderRadius="md">
                            <Alert.Indicator />
                            <Alert.Title>Optimization failed</Alert.Title>
                            <Alert.Description>{error}</Alert.Description>
                        </Alert.Root>
                    )}

                    {loading && (
                        <Box
                            p={6}
                            borderRadius="xl"
                            bg="teal.50"
                            borderWidth="1px"
                            borderColor="teal.200"
                            boxShadow="sm"
                            transition="all 0.3s ease"
                        >
                            <Stack align="center" gap={4}>
                                <Spinner color="teal.500" size="lg" />

                                <Text
                                    fontSize="md"
                                    fontWeight="medium"
                                    color="teal.700"
                                    opacity={isFading ? 0 : 1}
                                    transition="opacity 0.25s ease"
                                >
                                    {visibleThinkingStep}
                                </Text>

                            </Stack>
                        </Box>
                    )}
                </PanelSection>
            )}

            {proposal && !isAccepted && (
                <Box ref={proposalRef}>
                    <PanelSection>
                        <HStack justify="space-between">
                            <Stack>
                                <Text fontWeight="semibold">
                                    Accept this configuration?
                                </Text>
                                <Text fontSize="sm" color="fg.muted">
                                    Accepting will apply this configuration to the zone.
                                </Text>
                            </Stack>

                            <HStack>
                                <Button
                                    variant="outline"
                                    colorPalette="red"
                                    onClick={() => {
                                        setProposal(null)
                                        setIsLocked(false)
                                    }}
                                >
                                    Discard
                                </Button>

                                <Button
                                    colorPalette="teal"
                                    onClick={() => {
                                        setIsAccepted(true)
                                        const mappedPlants = proposal.plants.map((plant) => ({
                                            id: crypto.randomUUID(),
                                            name: plant.plant_id,
                                            emitters: plant.assigned_drippers.map((d) => ({
                                                type: "dripper",
                                                flow_rate_lph: d.flow_rate_lph,
                                                count: d.count,
                                            })),
                                        }))

                                        console.log("Mapped plants:", mappedPlants)
                                        onChange({
                                            ...data,
                                            plants: mappedPlants,
                                        })
                                        onIrrigationChange({
                                            base_target_volume_liters:
                                                proposal.total_base_volume_liters,
                                        })
                                    }}
                                >
                                    Accept
                                </Button>
                            </HStack>
                        </HStack>
                    </PanelSection>
                </Box>
            )}

            {/* ======================================================
                PROPOSAL
            ====================================================== */}

            {proposal && (
                <PanelSection
                    title="✨ Optimization result"
                    description="Automatically calculated optimal emitter allocation."
                    borderColor={isAccepted ? "green.400" : "border"} // Dynamically set the border color
                >

                    {/* ================= OVERVIEW ================= */}

                    <Box
                        p={6}
                        borderRadius="xl"
                        bg="teal.50"
                        borderWidth="1px"
                        borderColor="teal.200"
                        boxShadow="sm"
                    >
                        <SimpleGrid columns={{ base: 2, md: 4 }} gap={6}>

                            <Box>
                                <Text fontSize="sm" color="fg.muted">
                                    Base volume
                                </Text>
                                <Text fontSize="xl" fontWeight="bold" color="teal.700">
                                    {proposal.total_base_volume_liters.toFixed(1)} L
                                </Text>
                            </Box>

                            <Box>
                                <Text fontSize="sm" color="fg.muted">
                                    Total zone flow
                                </Text>
                                <Text fontSize="xl" fontWeight="bold" color="teal.700">
                                    {proposal.total_flow_lph.toFixed(1)} L/h
                                </Text>
                            </Box>

                            <Box>
                                <Text fontSize="sm" color="fg.muted">
                                    Base irrigation time
                                </Text>
                                <Text fontSize="xl" fontWeight="bold" color="teal.700">
                                    {proposal.base_irrigation_time_seconds.toFixed(0)} s
                                </Text>
                            </Box>

                            <Box>
                                <Text fontSize="sm" color="fg.muted">
                                    Drippers used
                                </Text>
                                <Text fontSize="xl" fontWeight="bold" color="teal.700">
                                    {proposal.total_drippers_used}
                                </Text>
                            </Box>

                        </SimpleGrid>
                    </Box>

                    <Separator my={8} />

                    {/* ================= PER PLANT BREAKDOWN ================= */}

                    <Stack gap={6}>

                        <Text fontWeight="semibold">
                            Per plant allocation
                        </Text>

                        <SimpleGrid columns={{ base: 1, md: 2 }} gap={5}>

                            {proposal.plants.map((plant, index) => {

                                const originalPlant = plants.find(
                                    p => p.plant_id === plant.plant_id
                                )

                                const target = originalPlant?.target_volume_liters ?? 0
                                const actual = plant.actual_volume_liters

                                const diffPercent =
                                    target > 0
                                        ? ((actual - target) / target) * 100
                                        : 0

                                return (
                                    <Box
                                        key={index}
                                        p={5}
                                        borderRadius="xl"
                                        borderWidth="1px"
                                        borderColor="border.subtle"
                                        bg="bg.panel"
                                        boxShadow="sm"
                                    >
                                        <Stack gap={4}>

                                            {/* Header */}
                                            <Text fontWeight="medium">
                                                🌱 {plant.plant_id}
                                            </Text>

                                            {/* Target vs Actual */}
                                            <SimpleGrid columns={2} gap={4} alignItems="baseline">
                                                <Stack>
                                                    <Text fontSize="sm" color="fg.muted">
                                                        Target volume
                                                    </Text>
                                                    <Text fontSize="lg" color="fg.subtle" fontWeight="semibold">
                                                        {target.toFixed(2)} L
                                                    </Text>
                                                </Stack>
                                                <Stack>
                                                    <Text fontSize="sm" color="fg.muted" mt={2}>
                                                        Actual volume
                                                    </Text>
                                                    <HStack>
                                                        <Text fontSize="lg" fontWeight="semibold">
                                                            {actual.toFixed(2)} L
                                                        </Text>
                                                        <Badge
                                                            colorPalette={
                                                                diffPercent === 0
                                                                    ? "gray"
                                                                    : "orange"
                                                            }
                                                        >
                                                            {diffPercent > 0 ? "+" : ""}
                                                            {diffPercent.toFixed(0)}%
                                                        </Badge>
                                                    </HStack>
                                                </Stack>
                                            </SimpleGrid>

                                            {/* Drippers */}
                                            <Stack>
                                                <Text fontSize="sm" color="fg.muted">
                                                    Assigned drippers
                                                </Text>
                                                <HStack wrap="wrap" gap={4}>
                                                    {plant.assigned_drippers.map((d, i) => (
                                                        <HStack gap={1} key={i}>
                                                            <Text fontSize="sm" color="fg.muted">
                                                                {d.count}×
                                                            </Text>
                                                            <Badge
                                                                key={i}
                                                                colorPalette="teal"
                                                                variant="subtle"
                                                            >
                                                                {d.flow_rate_lph} L/h
                                                            </Badge>
                                                        </HStack>
                                                    ))}
                                                </HStack>
                                            </Stack>

                                        </Stack>
                                    </Box>
                                )
                            })}

                        </SimpleGrid>
                    </Stack>

                    <Separator my={8} />

                    {/* ================= GLOBAL DRIPPER SUMMARY ================= */}

                    <Stack gap={3}>
                        <Text fontWeight="semibold">
                            Dripper usage summary
                        </Text>

                        <SimpleGrid columns={{ base: 3, md: 4 }} gap={4}>
                            {proposal.drippers_used_detail.map((d, index) => (
                                <Box
                                    key={index}
                                    p={4}
                                    borderRadius="xl"
                                    borderWidth="1px"
                                    borderColor="border.subtle"
                                    bg="bg.panel"
                                    boxShadow="sm"
                                    textAlign="center"
                                >
                                    <Stack align="center" gap={2}>
                                        <Text fontWeight="bold" fontSize="lg">
                                            {d.count}×
                                        </Text>

                                        <Badge colorPalette="teal" variant="subtle" fontSize="sm">
                                            {d.flow_rate_lph} L/h
                                        </Badge>
                                    </Stack>
                                </Box>
                            ))}
                        </SimpleGrid>
                    </Stack>

                </PanelSection>
            )}

            {isAccepted && (
                <Box
                    p={5}
                    bg="green.50"
                    borderColor="green.200"
                >
                    <Text fontWeight="semibold" color="green.700">
                        Configuration accepted
                    </Text>
                    <Text fontSize="sm" color="green.600">
                        The optimized configuration is now applied to this zone.
                    </Text>
                </Box>
            )}


        </Stack>
    )
}
