import {
    Box,
    Heading,
    Text,
    Field,
    Input,
    Stack,
    HStack,
    Button,
    Badge,
    SimpleGrid,
    Progress,
    Separator,
} from "@chakra-ui/react"

import PanelSection from "../../../../../components/layout/PanelSection"

const EMITTER_PRESETS = [
    { type: "dripper", label: "Dripper", icon: "💧" },
    { type: "soaker_hose", label: "Soaker hose", icon: "〰️" },
    { type: "micro_spray", label: "Micro spray", icon: "🌫️" },
]

export default function StepEmittersEvenArea({ data, onChange }) {
    const emitters = data.summary || []

    const updateEmitter = (index, updated) => {
        const next = [...emitters]
        next[index] = updated
        onChange({ summary: next })
    }

    const addEmitter = (type) => {
        onChange({
            summary: [
                ...emitters,
                {
                    type,
                    flow_rate_lph: type === "dripper" ? 2 : 10,
                    count: 1,
                },
            ],
        })
    }

    const removeEmitter = (index) => {
        onChange({
            summary: emitters.filter((_, i) => i !== index),
        })
    }

    const totalFlow = emitters.reduce(
        (sum, e) =>
            sum +
            (e.type === "soaker_hose"
                ? e.flow_rate_lph || 0
                : (e.flow_rate_lph || 0) * (e.count || 0)),
        0
    )

    return (
        <PanelSection
            title="Emitters configuration"
            description="Define the emitters used across this zone. The system assumes these emitters are distributed evenly over the irrigated area."
        >
            {/* Add emitter buttons */}
            <HStack mb={6}>
                {EMITTER_PRESETS.map((preset) => (
                    <Button
                        key={preset.type}
                        variant="outline"
                        onClick={() => addEmitter(preset.type)}
                    >
                        {preset.icon} Add {preset.label}
                    </Button>
                ))}
            </HStack>

            {/* Emitters grid */}
            <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                {emitters.map((emitter, index) => {
                    const flow =
                        emitter.type === "soaker_hose"
                            ? emitter.flow_rate_lph || 0
                            : (emitter.flow_rate_lph || 0) * (emitter.count || 0)

                    const share =
                        totalFlow > 0 ? Math.round((flow / totalFlow) * 100) : 0

                    return (
                        <PanelSection key={index}>
                            {/* Header */}
                            <HStack justify="space-between" mb={3}>
                                <HStack>
                                    <Box fontSize="xl">
                                        {emitter.type === "dripper" && "💧"}
                                        {emitter.type === "soaker_hose" && "〰️"}
                                        {emitter.type === "micro_spray" && "🌫️"}
                                    </Box>
                                    <Badge variant="subtle">
                                        {emitter.type}
                                    </Badge>
                                </HStack>

                                <Button
                                    size="sm"
                                    variant="ghost"
                                    colorPalette="red"
                                    onClick={() => removeEmitter(index)}
                                >
                                    Remove
                                </Button>
                            </HStack>

                            <Stack>
                                <HStack>
                                    <Field.Root>
                                        <Field.Label>Flow rate (l/h)</Field.Label>
                                        <Input
                                            type="number"
                                            step="0.5"
                                            value={emitter.flow_rate_lph}
                                            onChange={(e) =>
                                                updateEmitter(index, {
                                                    ...emitter,
                                                    flow_rate_lph: Number(e.target.value),
                                                })
                                            }
                                        />
                                    </Field.Root>

                                    {emitter.type !== "soaker_hose" && (
                                        <Field.Root>
                                            <Field.Label>Count</Field.Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={emitter.count}
                                                onChange={(e) =>
                                                    updateEmitter(index, {
                                                        ...emitter,
                                                        count: Number(e.target.value),
                                                    })
                                                }
                                            />
                                        </Field.Root>
                                    )}
                                </HStack>

                                <Box>
                                    <Text fontSize="xs" color="fg.muted" mb={1}>
                                        Share of zone flow
                                    </Text>
                                    <Progress.Root
                                        value={share}
                                        size="sm"
                                        colorPalette="teal"
                                    >
                                        <Progress.Track>
                                            <Progress.Range />
                                        </Progress.Track>
                                    </Progress.Root>
                                    <Text fontSize="xs" color="fg.subtle" mt={1}>
                                        {flow.toFixed(1)} l/h ({share}%)
                                    </Text>
                                </Box>
                            </Stack>
                        </PanelSection>
                    )
                })}
            </SimpleGrid>

            <Separator my={6} />

            {/* Total flow */}
            <Stack>
                <Text fontSize="sm" color="fg.muted">
                    Total zone flow
                </Text>
                <Text fontSize="lg" fontWeight="semibold">
                    {totalFlow.toFixed(1)} l/h
                </Text>
                <Text fontSize="xs" color="fg.subtle">
                    Sum of all emitter flows in this zone
                </Text>
            </Stack>
        </PanelSection>
    )
}
