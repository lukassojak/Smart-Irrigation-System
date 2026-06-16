import { useEffect, useState } from "react"
import { Link, useParams, useNavigate, useOutletContext } from "react-router-dom"
import {
    Stack,
    Box,
    Heading,
    Text,
    SimpleGrid,
    Image,
    HStack,
    VStack,
} from "@chakra-ui/react"

import PanelSection from "../../../components/layout/PanelSection"
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'
import { HeaderAction } from '../../../components/ui/ActionButtons'
import GPIOHeaderVisualizer from "../components/GPIOHeaderVisualizer"
import { fetchNodeHeader } from "../../../api/nodes.api"


export default function NodeHeaderDetailPage() {
    const { nodeId } = useParams()
    const navigate = useNavigate()
    const { isMobile, openMobileSidebar } = useOutletContext() || {}
    const [pins, setPins] = useState([])
    const [loading, setLoading] = useState(true)

    // In the future, this would fetch actual data from API:
    // useEffect(() => {
    //     fetchNodeGPIOPins(nodeId)
    //         .then(response => setPins(response.data))
    //         .catch(error => console.error("Failed to fetch GPIO pins:", error))
    // }, [nodeId])
    useEffect(() => {
        fetchNodeHeader(nodeId)
            .then(response => {
                const mappedPins = response.data.pins.map(pin => ({
                    boardPinId: pin.board_pin,
                    bcmPinId: pin.bcm,
                    occupiedBy: pin.occupied_by,
                    type:
                        pin.type === "gpio"
                            ? pin.occupied_by
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

                setPins(mappedPins)
            })
            .catch(error => {
                console.error("Failed to fetch GPIO pins:", error)
            })
            .finally(() => setLoading(false))
    }, [nodeId])

    return (
        <>
            <GlassPageHeader
                title={`Node #${nodeId}`}
                subtitle="GPIO Header Configuration"
                actions={
                    <HeaderActions>
                        <HeaderAction
                            as={Link}
                            to={`/configuration/nodes/${nodeId}`}
                        >
                            &larr; Back to Node
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Box p={6}>
                <Stack gap={10}>
                    {/* Pin Statistics */}
                    <PanelSection title="Pin Statistics">
                        <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
                            <Box
                                bg="green.50"
                                borderRadius="md"
                                p={4}
                                borderLeft="4px solid"
                                borderColor="green.500"
                            >
                                <Text fontSize="sm" color="fg.muted">
                                    Available GPIO
                                </Text>
                                <Heading size="lg">
                                    {pins.filter(p => p.type === "gpio_free").length}
                                </Heading>
                            </Box>

                            <Box
                                bg="red.50"
                                borderRadius="md"
                                p={4}
                                borderLeft="4px solid"
                                borderColor="red.500"
                            >
                                <Text fontSize="sm" color="fg.muted">
                                    In Use GPIO
                                </Text>
                                <Heading size="lg">
                                    {pins.filter(p => p.type === "gpio_used").length}
                                </Heading>
                            </Box>

                            <Box
                                bg="gray.50"
                                borderRadius="md"
                                p={4}
                                borderLeft="4px solid"
                                borderColor="gray.500"
                            >
                                <Text fontSize="sm" color="fg.muted">
                                    Reserved
                                </Text>
                                <Heading size="lg">
                                    {pins.filter(p => p.type === "other").length}
                                </Heading>
                            </Box>
                        </SimpleGrid>
                    </PanelSection>

                    {/* Board Image and GPIO Header Layout */}
                    <PanelSection title="GPIO Header Configuration" description="Hover on any pin to view details. Green pins are available, red pins are in use.">
                        <VStack gap={4} align="start">
                            <SimpleGrid columns={{ base: 1, md: 2 }} gap={6} alignItems="center">
                                <GPIOHeaderVisualizer pins={pins} showImage={isMobile} />

                                <Box display={{ base: "none", md: "flex" }}>
                                    <Image
                                        src="/pi_zero_2w_board.webp"
                                        alt="Raspberry Pi Zero 2W Board"
                                        maxW="70%"
                                        h="auto"
                                        borderRadius="md"
                                        transform="rotate(90deg)"
                                    />
                                </Box>
                            </SimpleGrid>

                            {/* Text with link to GPIO pinout guide */}
                            <Text fontSize="sm" color="fg.muted" textAlign="left">
                                <Link to="https://pinout.xyz/" target="_blank" style={{ color: "inherit", textDecoration: "underline" }}>
                                    See GPIO pinout guide
                                </Link>.
                            </Text>
                        </VStack>
                    </PanelSection>
                </Stack>
            </Box>
        </>
    )
}
