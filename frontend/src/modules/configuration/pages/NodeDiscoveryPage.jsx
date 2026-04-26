import { useMemo, useState } from "react"
import {
    Box,
    Stack,
    Heading,
    Text,
    Button,
    SimpleGrid,
    HStack,
    Badge,
    Progress,
    Spinner,
} from "@chakra-ui/react"
import { Link, useNavigate, useOutletContext } from "react-router-dom"
import { RadioTower, Router, Cpu, Search, Link2 } from "lucide-react"

import GlassPageHeader, { HeaderActions } from "../../../components/layout/GlassPageHeader"
import { HeaderAction } from "../../../components/ui/ActionButtons"
import PanelSection from "../../../components/layout/PanelSection"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"
import { discoverNodes, pairDiscoveredNode } from "../../../api/runtime.api"


const MIN_DISCOVERY_LOADING_TIME = 3000


function formatLastSeen(value) {
    if (!value) return "Unknown"
    return value.toLocaleString()
}


export default function NodeDiscoveryPage() {
    const navigate = useNavigate()
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const [devices, setDevices] = useState([])
    const [selectedHardwareUid, setSelectedHardwareUid] = useState("")
    const [isDiscovering, setIsDiscovering] = useState(false)
    const [discoveryError, setDiscoveryError] = useState("")

    const [isPairing, setIsPairing] = useState(false)
    const [pairingProgress, setPairingProgress] = useState(0)
    const [pairingError, setPairingError] = useState("")
    const [pairedDevice, setPairedDevice] = useState(null)

    const selectedDevice = useMemo(
        () => devices.find((device) => device.hardwareUid === selectedHardwareUid) || null,
        [devices, selectedHardwareUid],
    )

    const handleDiscover = async () => {
        const startTime = Date.now()
        setIsDiscovering(true)
        setDiscoveryError("")
        setPairingError("")
        setPairedDevice(null)
        setPairingProgress(0)

        try {
            const discoveredDevices = await discoverNodes()

            const elapsed = Date.now() - startTime
            const remaining = MIN_DISCOVERY_LOADING_TIME - elapsed
            if (remaining > 0) {
                await new Promise((resolve) => setTimeout(resolve, remaining))
            }

            setDevices(discoveredDevices)
            if (discoveredDevices.length > 0) {
                setSelectedHardwareUid(discoveredDevices[0].hardwareUid)
            } else {
                setSelectedHardwareUid("")
            }
        } catch (error) {
            console.error("Failed to discover nodes:", error)
            setDiscoveryError("Discovery data is unavailable. Make sure the server is running and try again.")
            setDevices([])
            setSelectedHardwareUid("")
        } finally {
            setIsDiscovering(false)
        }
    }

    const handlePair = async () => {
        if (!selectedDevice) return

        setIsPairing(true)
        setPairingError("")
        setPairedDevice(null)
        setPairingProgress(5)

        const progressInterval = setInterval(() => {
            setPairingProgress((prev) => (prev >= 88 ? prev : prev + 8))
        }, 180)

        try {
            const [result] = await Promise.all([
                pairDiscoveredNode({
                    hardwareUid: selectedDevice.hardwareUid,
                    minWaitSeconds: 2,
                    timeoutSeconds: 8,
                }),
                new Promise((resolve) => setTimeout(resolve, 2000)),
            ])

            setPairingProgress(100)
            setPairedDevice({
                ...selectedDevice,
                lastSeenAt: result.lastSeenAt,
            })
        } catch (error) {
            console.error("Pairing failed:", error)
            const detail = error?.response?.data?.detail
            setPairingError(typeof detail === "string" ? detail : "Pairing failed. Please try again.")
            setPairingProgress(0)
        } finally {
            clearInterval(progressInterval)
            setIsPairing(false)
        }
    }

    const handleConfigure = () => {
        if (!pairedDevice) return
        navigate("/configuration/nodes/new", {
            state: {
                hardwareUid: pairedDevice.hardwareUid,
                discoveredNode: {
                    serialNumber: pairedDevice.serialNumber,
                    hostname: pairedDevice.hostname,
                },
            },
        })
    }

    return (
        <>
            <GlassPageHeader
                title="Node Discovery"
                subtitle="Discover a physical node, pair it, then continue with configuration"
                actions={
                    <HeaderActions>
                        <HeaderAction as={Link} to="/configuration/nodes">
                            Back to dashboard
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Box p={6}>
                <Stack gap={6}>
                    <PanelSection>
                        <Stack gap={5}>
                            <HStack justify="space-between" align="center" wrap="wrap">
                                <HStack gap={3}>
                                    <Box
                                        w="42px"
                                        h="42px"
                                        borderRadius="md"
                                        bg="rgba(56,178,172,0.08)"
                                        display="flex"
                                        alignItems="center"
                                        justifyContent="center"
                                    >
                                        <Search size={20} color="#319795" />
                                    </Box>
                                    <Stack gap={0}>
                                        <Heading size="sm">Step 1: Discover devices</Heading>
                                        <Text fontSize="sm" color="fg.muted">
                                            Refresh the live discovery list and pick one node to pair.
                                        </Text>
                                    </Stack>
                                </HStack>

                                <Button
                                    colorPalette="teal"
                                    onClick={handleDiscover}
                                    loading={isDiscovering}
                                >
                                    Discover new nodes
                                </Button>
                            </HStack>

                            {discoveryError && <DataUnavailableWarning message={discoveryError} />}

                            {isDiscovering && (
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
                                        <Text fontSize="md" fontWeight="medium" color="teal.700">
                                            Scanning for new nodes...
                                        </Text>
                                    </Stack>
                                </Box>
                            )}

                            {!isDiscovering && !discoveryError && devices.length === 0 && (
                                <Box
                                    borderRadius="lg"
                                    p={5}
                                    bg="rgba(255,255,255,0.72)"
                                    border="1px dashed rgba(56,178,172,0.26)"
                                >
                                    <Text color="fg.muted">
                                        No nodes are currently visible. Start a node and click "Discover new nodes".
                                    </Text>
                                </Box>
                            )}

                            {!isDiscovering && devices.length > 0 && (
                                <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={4}>
                                    {devices.map((device) => {
                                        const isSelected = device.hardwareUid === selectedHardwareUid
                                        return (
                                            <Box
                                                key={device.hardwareUid}
                                                onClick={() => setSelectedHardwareUid(device.hardwareUid)}
                                                cursor="pointer"
                                                borderRadius="xl"
                                                p={5}
                                                bg={isSelected ? "rgba(56,178,172,0.10)" : "rgba(255,255,255,0.80)"}
                                                border={isSelected ? "1px solid rgba(56,178,172,0.5)" : "1px solid rgba(56,178,172,0.12)"}
                                                backdropFilter="blur(12px) saturate(170%)"
                                                boxShadow={isSelected ? "0 10px 22px rgba(15,23,42,0.10)" : "0 6px 18px rgba(15,23,42,0.06)"}
                                                transition="all 0.16s ease"
                                                _hover={{
                                                    transform: "translateY(-2px)",
                                                    boxShadow: "0 12px 26px rgba(15,23,42,0.12)",
                                                }}
                                            >
                                                <Stack gap={3}>
                                                    <HStack justify="space-between" align="start">
                                                        <Box
                                                            w="44px"
                                                            h="44px"
                                                            borderRadius="lg"
                                                            bg="rgba(56,178,172,0.14)"
                                                            display="flex"
                                                            alignItems="center"
                                                            justifyContent="center"
                                                        >
                                                            <Router size={22} color="#2C7A7B" />
                                                        </Box>
                                                        {isSelected && <Badge colorPalette="teal">Selected</Badge>}
                                                    </HStack>

                                                    <Stack gap={1}>
                                                        <Text fontSize="sm" color="fg.muted">Hardware UID</Text>
                                                        <Text fontSize="sm" fontWeight="600">{device.hardwareUid}</Text>
                                                    </Stack>

                                                    <Stack gap={0}>
                                                        <Text fontSize="xs" color="fg.muted">Serial number</Text>
                                                        <Text fontSize="sm">{device.serialNumber || "Unavailable"}</Text>
                                                    </Stack>

                                                    <Stack gap={0}>
                                                        <Text fontSize="xs" color="fg.muted">Hostname</Text>
                                                        <Text fontSize="sm">{device.hostname || "Unavailable"}</Text>
                                                    </Stack>

                                                    <Stack gap={0}>
                                                        <Text fontSize="xs" color="fg.muted">Last seen</Text>
                                                        <Text fontSize="sm">{formatLastSeen(device.lastSeenAt)}</Text>
                                                    </Stack>
                                                </Stack>
                                            </Box>
                                        )
                                    })}
                                </SimpleGrid>
                            )}
                        </Stack>
                    </PanelSection>

                    <PanelSection>
                        <Stack gap={5}>
                            <HStack gap={3}>
                                <Box
                                    w="42px"
                                    h="42px"
                                    borderRadius="md"
                                    bg="rgba(56,178,172,0.08)"
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="center"
                                >
                                    <Link2 size={20} color="#319795" />
                                </Box>
                                <Stack gap={0}>
                                    <Heading size="sm">Step 2: Pair and continue</Heading>
                                    <Text fontSize="sm" color="fg.muted">
                                        Pair the selected node, then continue to the configuration page.
                                    </Text>
                                </Stack>
                            </HStack>

                            {(isPairing || pairingProgress > 0) && (
                                <Stack gap={2}>
                                    <Progress.Root value={pairingProgress} colorPalette="teal" size="sm" borderRadius="md">
                                        <Progress.Track>
                                            <Progress.Range />
                                        </Progress.Track>
                                    </Progress.Root>
                                    <Text fontSize="xs" color="fg.muted">
                                        {isPairing ? "Waiting for node response..." : pairedDevice ? "Pairing successful." : "Pairing progress."}
                                    </Text>
                                </Stack>
                            )}

                            {pairingError && <DataUnavailableWarning message={pairingError} />}

                            {pairedDevice && (
                                <Box
                                    borderRadius="lg"
                                    p={4}
                                    bg="rgba(56,178,172,0.06)"
                                    border="1px solid rgba(56,178,172,0.26)"
                                >
                                    <Text fontSize="sm" color="teal.800" fontWeight="600">
                                        Node {pairedDevice.hardwareUid} is ready. Continue with "Configure node".
                                    </Text>
                                </Box>
                            )}

                            <HStack wrap="wrap" gap={3}>
                                <Button
                                    colorPalette="teal"
                                    variant="solid"
                                    onClick={handlePair}
                                    loading={isPairing}
                                    disabled={!selectedDevice || isDiscovering || pairedDevice}
                                >
                                    Pair
                                </Button>
                                <Button
                                    colorPalette="teal"
                                    variant="outline"
                                    onClick={handleConfigure}
                                    disabled={!pairedDevice || isPairing}
                                >
                                    Configure node
                                </Button>
                                {selectedDevice && (
                                    <HStack gap={2} align="center">
                                        <Text fontSize="xs" color="fg.muted">
                                            Selected:
                                        </Text>
                                        <Badge colorPalette="teal" px={2} py={1}>
                                            {selectedDevice.hardwareUid}
                                        </Badge>
                                    </HStack>
                                )}
                            </HStack>
                        </Stack>
                    </PanelSection>
                </Stack>
            </Box>
        </>
    )
}
