import {
    Box,
    Heading,
    Stack,
    Field,
    Input,
    Switch,
    HStack,
    Text,
} from "@chakra-ui/react"

import PanelSection from "../../../../../components/layout/PanelSection"

export default function StepBasicInfo({ data, onChange }) {
    const update = (patch) => {
        onChange({ ...data, ...patch })
    }

    return (
        <PanelSection title="Basic Zone Information">
            <Stack gap={6}>
                {/* Zone name */}
                <Field.Root required>
                    <Field.Label>
                        Zone name <Field.RequiredIndicator />
                    </Field.Label>

                    <Input
                        placeholder="e.g. Front Lawn"
                        value={data.name}
                        onChange={(e) =>
                            update({ name: e.target.value })
                        }
                    />

                    <Field.HelperText>
                        Human-readable name to identify this irrigation zone.
                    </Field.HelperText>
                </Field.Root>

                {/* Relay pin */}
                <Field.Root required>
                    <Field.Label>
                        Relay valve pin <Field.RequiredIndicator />
                    </Field.Label>

                    <Input
                        type="number"
                        min={0}
                        placeholder="e.g. 3"
                        value={data.relay_pin ?? ""}
                        onChange={(e) =>
                            update({
                                relay_pin:
                                    e.target.value === ""
                                        ? null
                                        : Number(e.target.value),
                            })
                        }
                    />

                    <Field.HelperText>
                        Hardware output pin controlling the valve for this zone.
                    </Field.HelperText>
                </Field.Root>

                {/* Enabled switch */}
                <HStack justify="space-between">
                    <Field.Root colorPalette="teal">
                        <Field.Label>Automatic Irrigation</Field.Label>

                        <Switch.Root
                            checked={data.enabled}
                            onCheckedChange={(details) =>
                                update({ enabled: details.checked })
                            }
                        >
                            <Switch.HiddenInput />
                            <Switch.Control>
                                <Switch.Thumb />
                            </Switch.Control>
                            <Switch.Label>
                                {data.enabled ? "Enabled" : "Disabled"}
                            </Switch.Label>
                        </Switch.Root>

                        <Field.HelperText>
                            Enable or disable automatic daily irrigation checks for this zone.
                        </Field.HelperText>
                    </Field.Root>
                </HStack>
            </Stack>
        </PanelSection>
    )
}
