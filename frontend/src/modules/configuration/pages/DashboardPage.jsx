import { useEffect, useState } from "react"
import {
    Box,
    Heading,
    Text,
    Button,
    Stack,
    HStack,
    SimpleGrid,
} from "@chakra-ui/react"
import { Link } from "react-router-dom"
import { fetchNodes } from "../../../api/nodes.api"
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'
import { HeaderAction } from '../../../components/ui/ActionButtons'
import NodeCard from "../../../components/ui/cards/NodeCard"


export default function NodesDashboardPage() {
    const [nodes, setNodes] = useState([])

    useEffect(() => {
        fetchNodes()
            .then((response) => setNodes(response.data))
            .catch((error) => console.error("Error fetching nodes:", error))
    }, [])

    return (
        <>
            <GlassPageHeader
                title="Dashboard"
                subtitle="Manage your nodes and their zones"
                actions={
                    <HeaderActions>
                        <HeaderAction as={Link} to="/configuration/settings">
                            Settings
                        </HeaderAction>
                        <HeaderAction as={Link} to="/configuration/nodes/new">
                            Add Node
                        </HeaderAction>
                    </HeaderActions>
                }
            />
            <Box p={6}>
                {/* Info text */}
                <Text mb={4} fontSize="sm" color="fg.muted">
                    {nodes.length} configured node{nodes.length !== 1 && "s"}
                </Text>

                {/* Empty state */}
                {nodes.length === 0 && (
                    <Box
                        bg="bg.subtle"
                        borderWidth="1px"
                        borderColor="border.subtle"
                        borderRadius="md"
                        p={6}
                    >
                        <Text color="fg.muted">
                            No nodes found. Create your first node to get started.
                        </Text>
                    </Box>
                )}

                {/* Nodes grid */}
                <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                    {nodes.map((node) => (
                        <NodeCard
                            key={node.id}
                            node={node}
                        />
                    ))}
                </SimpleGrid>
            </Box>
        </>
    )
}
