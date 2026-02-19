import { useState } from "react"

import {
    Box,
    Heading,
    Text,
    Field,
    Input,
    Stack,
    Separator,
    RadioCard,
    HStack,
    SimpleGrid,
} from "@chakra-ui/react"

import PanelSection from "../../../../../components/layout/PanelSection"

export default function StepIrrigationPerPlant({ data, autoOptimize, onChange, onAutoOptimizeChange }) {
    const baseVolume = data.base_target_volume_liters || ""

    const handleAutoOptimizeChange = (value) => {
        const isAuto = value === "automatic"
        onAutoOptimizeChange(isAuto) // Notify parent component about the change
    }

    return (
        <Stack gap={6}>
            <PanelSection title="Per-Plant irrigation"
                description="In this mode, irrigation is based on individual plants rather than total area."
            >
                <Field.Root colorPalette="teal" gap={4}>
                    <Field.Label>Emitter Configuration Method</Field.Label>
                    <RadioCard.Root
                        value={autoOptimize ? "automatic" : "manual"}
                        onValueChange={(e) => handleAutoOptimizeChange(e.value)}
                    >
                        <SimpleGrid columns={{ base: 1, md: 2 }} gap={8} >
                            <RadioCard.Item value="automatic">
                                <RadioCard.ItemHiddenInput />
                                <RadioCard.ItemControl>
                                    <RadioCard.ItemIndicator />
                                    {/* Set item text with icon and descriptive name */}
                                    <RadioCard.ItemText>
                                        <HStack gap={1}>
                                            <Box fontSize="lg">⚡</Box>
                                            <Text>Automatic optimization</Text>
                                        </HStack>
                                    </RadioCard.ItemText>
                                </RadioCard.ItemControl>
                            </RadioCard.Item>
                            <RadioCard.Item value="manual">
                                <RadioCard.ItemHiddenInput />
                                <RadioCard.ItemControl>
                                    <RadioCard.ItemIndicator />
                                    <RadioCard.ItemText>
                                        <HStack gap={1}>
                                            <Box fontSize="lg">🛠️</Box>
                                            <Text>Manual configuration</Text>
                                        </HStack>
                                    </RadioCard.ItemText>
                                </RadioCard.ItemControl>
                            </RadioCard.Item>
                        </SimpleGrid>
                    </RadioCard.Root>
                    <Field.HelperText>
                        Choose whether you want to manually assign emitters to each plant or let the system automatically generate an optimized configuration.
                    </Field.HelperText>
                    {autoOptimize ? (
                        <Box bg="teal.50" p={4} borderRadius="md">
                            <Text fontSize="sm" color="teal.700">
                                The <strong>automatic mode</strong> is ideal for quick and easy setup. The system will calculate the optimal number and placement of emitters for each plant based on their water requirements. It ensures efficient water distribution and emitter usage.
                            </Text>
                        </Box>
                    ) : (
                        <Box bg="teal.50" p={4} borderRadius="md">
                            <Text fontSize="sm" color="teal.700">
                                In <strong>manual mode</strong>, you can assign specific emitters to each plant, giving you full control over the irrigation setup. This is useful when the zone's emitters are already installed or you want to use a specific configuration.
                            </Text>
                        </Box>
                    )}
                </Field.Root>
            </PanelSection>


            {!autoOptimize && (
                <PanelSection title="Base Target Volume"
                    description="Set the total amount of water available for this zone per irrigation cycle. This volume will be distributed among the plants based on their individual requirements."
                >
                    <Field.Root required>
                        <Field.Label>
                            Base target zone volume (liters)
                        </Field.Label>
                        <Input
                            type="number"
                            min={0}
                            step="1"
                            placeholder="e.g. 40"
                            value={baseVolume}
                            onChange={(e) =>
                                onChange({
                                    ...data,
                                    base_target_volume_liters: Number(e.target.value),
                                })
                            }
                        />
                        <Field.HelperText>
                            Total amount of water available for this zone per irrigation cycle.
                        </Field.HelperText>
                    </Field.Root>
                </PanelSection>
            )}

            {autoOptimize ? (
                <PanelSection title="What happens next?" description="In the next step, you will define individual plants and their water requirements. The system will automatically calculate the optimal emitter configuration for each plant." />
            ) : (
                <PanelSection title="What happens next?" description="In the next step, you will define individual plants and their emitters. The system will use the base volume set above to calculate how much water each plant receives." />
            )}
        </Stack>
    )
}
