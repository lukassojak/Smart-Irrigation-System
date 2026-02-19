import {
    Box,
    Heading,
    Text,
    Field,
    Input,
    SimpleGrid,
    Stack,
    Separator,
} from "@chakra-ui/react"

import PanelSection from "../../../../../components/layout/PanelSection"

export default function StepIrrigationEvenArea({ data, onChange }) {
    const zoneArea = data.zone_area_m2 || ""
    const targetMm = data.target_mm || ""

    const totalLiters =
        zoneArea && targetMm
            ? (zoneArea * targetMm).toFixed(1)
            : null

    return (
        <PanelSection
            title="Even Area Irrigation"
            description="In this mode, the entire zone is irrigated evenly.
                The system calculates the required water volume from the
                zone area and the target water depth."
        >

            <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                {/* Zone area */}
                <Field.Root required>
                    <Field.Label>
                        Zone area (m²) <Field.RequiredIndicator />
                    </Field.Label>
                    <Input
                        type="number"
                        min={0}
                        step="1"
                        placeholder="e.g. 8"
                        value={zoneArea}
                        onChange={(e) =>
                            onChange({
                                ...data,
                                zone_area_m2: Number(e.target.value),
                            })
                        }
                    />
                    <Field.HelperText>
                        Total irrigated surface of this zone.
                    </Field.HelperText>
                </Field.Root>

                {/* Target depth */}
                <Field.Root required>
                    <Field.Label>
                        Target water depth (mm) <Field.RequiredIndicator />
                    </Field.Label>
                    <Input
                        type="number"
                        min={0}
                        step="1"
                        placeholder="e.g. 20"
                        value={targetMm}
                        onChange={(e) =>
                            onChange({
                                ...data,
                                target_mm: Number(e.target.value),
                            })
                        }
                    />
                    <Field.HelperText>
                        Desired base water depth applied per irrigation cycle.
                    </Field.HelperText>
                </Field.Root>
            </SimpleGrid>

            <Separator my={6} />

            {/* Calculated result */}
            <Stack>
                <Text fontSize="sm" color="fg.muted">
                    Calculated base irrigation volume
                </Text>

                <Text fontSize="lg" fontWeight="semibold">
                    {totalLiters
                        ? `${totalLiters} liters`
                        : "—"}
                </Text>

                <Text fontSize="xs" color="fg.subtle">
                    Calculated as: area × depth (1 mm = 1 liter per m²)
                </Text>
            </Stack>
        </PanelSection>
    )
}
