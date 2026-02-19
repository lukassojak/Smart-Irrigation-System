import { useEffect, useState } from "react"
import { Link, useParams, useNavigate } from "react-router-dom"
import {
    Button,
    Stack,
    Box,
    Heading,
    Text,
    HStack,
    SimpleGrid,
    DataList,
    Badge
} from "@chakra-ui/react"

import { fetchNodeById, deleteNode } from "../../../api/nodes.api"

import { LimitedCorrectionIndicator } from "../../../components/CorrectionIndicator"
import PanelSection from "../../../components/layout/PanelSection"
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'
import { HeaderAction, HeaderActionDanger } from '../../../components/ui/ActionButtons'
import ZoneCard from "../../../components/ui/cards/ZoneCard"



export default function NodeDetailPage() {
    const { nodeId } = useParams()
    const navigate = useNavigate()
    const [node, setNode] = useState(null)

    useEffect(() => {
        fetchNodeById(nodeId)
            .then((response) => setNode(response.data))
            .catch((error) => console.error("Failed to fetch node:", error))
    }, [nodeId])

    if (!node) {
        return (
            <Box p={6}>
                <Text color="fg.muted">Loading node…</Text>
            </Box>
        )
    }

    return (
        <>
            <GlassPageHeader
                title={`Node #${node.id}`}
                subtitle={node.name || "Unnamed Node"}
                actions={
                    <HeaderActions>
                        <HeaderActionDanger
                            onClick={() => {
                                if (!confirm("Are you sure you want to delete this node and all its zones?")) return
                                deleteNode(node.id)
                                    .then(() => navigate("/configuration/"))
                                    .catch(() => alert("Failed to delete node"))
                            }}
                        >
                            Delete node
                        </HeaderActionDanger>
                        <HeaderAction
                            as={Link}
                            to={`/configuration/nodes/${node.id}/zones/new`}
                        >
                            Create new zone
                        </HeaderAction>
                        <HeaderAction
                            as={Link}
                            to="/configuration/nodes"
                        >
                            &larr; Back
                        </HeaderAction>
                    </HeaderActions>
                }
            />
            <Box p={6}>
                <Stack gap={10} mb={6}>
                    {/* Node summary */}
                    <PanelSection title="Node Summary">
                        <Stack>
                            <HStack>
                                <Text fontSize="sm" color="fg.muted">
                                    Node ID
                                </Text>
                                <Text fontSize="sm">{node.id}</Text>
                            </HStack>
                            <HStack>
                                {node.location && (
                                    <>
                                        <Text fontSize="sm" color="fg.muted">
                                            Location
                                        </Text>
                                        <Text fontSize="sm">{node.location}</Text>
                                    </>
                                )}
                            </HStack>
                            <HStack>
                                <Text fontSize="sm" color="fg.muted">
                                    Last updated
                                </Text>
                                <Text fontSize="sm">{new Date(node.last_updated).toLocaleString() || "N/A"}</Text>
                            </HStack>
                        </Stack>
                    </PanelSection>

                    <PanelSection title="Configuration Overview">
                        <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                            <DataList.Root orientation="horizontal">
                                <DataList.Item>
                                    <DataList.ItemLabel>Automation</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {/* Use badge colors for enabled/disabled */}
                                        {node.automation.enabled ? (
                                            <Badge colorPalette="green">Enabled</Badge>
                                        ) : (
                                            <Badge colorPalette="red">Disabled</Badge>
                                        )}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Scheduled Time</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {node.automation.enabled
                                            ? `${String(node.automation.scheduled_hour).padStart(2, '0')}:${String(node.automation.scheduled_minute).padStart(2, '0')}`
                                            : "N/A"}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Batch Strategy</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {node.batch_strategy.concurrent_irrigation
                                            ? "Concurrent irrigation"
                                            : "Sequential irrigation"}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Flow Control</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {node.batch_strategy.flow_control ? "Enabled" : "Disabled"}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                {/*
                        <DataList.Item>
                            <DataList.ItemLabel>Input Pins</DataList.ItemLabel>
                            <DataList.ItemValue>{node.hardware.input_pins.length}</DataList.ItemValue>
                        </DataList.Item>
                        <DataList.Item>
                            <DataList.ItemLabel>Output Pins</DataList.ItemLabel>
                            <DataList.ItemValue>{node.hardware.output_pins.length}</DataList.ItemValue>
                        </DataList.Item>
                        */}
                            </DataList.Root>
                        </SimpleGrid>
                    </PanelSection>
                </Stack>

                {/* Zones */}
                <Box>
                    <Heading size="md" mb={4} color="fg">
                        Zones
                    </Heading>

                    {/* Info text */}
                    <Text mb={4} fontSize="sm" color="fg.muted">
                        {node.zones.length} configured zone{node.zones.length !== 1 && "s"}
                    </Text>

                    {node.zones.length === 0 && (
                        <Box
                            bg="bg.subtle"
                            borderWidth="1px"
                            borderColor="border.subtle"
                            borderRadius="md"
                            p={4}
                        >
                            <Text color="fg.muted">
                                Node has no zones defined.
                            </Text>
                        </Box>
                    )}

                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                        {node.zones.map((zone) => (
                            <ZoneCard
                                key={zone.id}
                                nodeId={node.id}
                                zone={zone}
                            />
                        ))}
                    </SimpleGrid>
                </Box>
            </Box>
        </>
    )
}
