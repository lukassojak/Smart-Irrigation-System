import { useState } from "react"

import {
    Box,
    Heading,
    Text,
    SimpleGrid,
    Stack,
    Switch,
    Field,
    RadioGroup,
    HStack,
} from "@chakra-ui/react"

import PanelSection from "../../../../../components/layout/PanelSection"

import { a } from "framer-motion/client"

import { LandPlot, Sprout } from "lucide-react"

function ModeCard({ icon: Icon, title, description, bullets, active, onClick }) {
    return (
        <Box
            onClick={onClick}
            cursor="pointer"
            bg={active ? "teal.50" : "bg.panel"}
            borderWidth="2px"
            borderColor={active ? "teal.400" : "border"}
            borderRadius="md"
            p={4}
            transition="all 0.15s ease"
            _hover={{
                borderColor: "teal.300",
                bg: "teal.50",
            }}
        >
            <Stack textAlign="left">
                <Box fontSize="2xl">
                    <Icon size={28} color="#319795" />
                </Box>

                <Heading size="sm">
                    {title}
                </Heading>

                <Text fontSize="sm" color="fg.muted">
                    {description}
                </Text>

                <Stack mt={2}>
                    {bullets.map((b, i) => (
                        <Text key={i} fontSize="sm">
                            • {b}
                        </Text>
                    ))}
                </Stack>
            </Stack>
        </Box>
    )
}

export default function StepIrrigationMode({ value, onChange }) {
    const [autoOptimize, setAutoOptimize] = useState(true)

    return (
        <PanelSection
            title="Irrigation Strategy"
            description="Choose how the base irrigation volume for this zone is calculated.
                This decision affects all following configuration steps."
        >
            <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                <ModeCard
                    icon={LandPlot}
                    title="Even Area"
                    description="Uniform irrigation over the entire zone area."
                    bullets={[
                        "Lawns and garden beds",
                        "Even emitter distribution",
                        "Volume calculated from area & depth",
                    ]}
                    active={value === "even_area"}
                    onClick={() => onChange("even_area")}
                />

                <ModeCard
                    icon={Sprout}
                    title="Per Plant"
                    description="Individual irrigation for separate plants."
                    bullets={[
                        "Pots, trees, mixed crops",
                        "Different emitters per plant",
                        "Base volume distributed per plant",
                    ]}
                    active={value === "per_plant"}
                    onClick={() => onChange("per_plant")}
                />
            </SimpleGrid>
        </PanelSection>
    )
}
