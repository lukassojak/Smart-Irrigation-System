import {
    Box,
    Grid,
    Stack,
    Text,
    Badge,
    HStack
} from "@chakra-ui/react"

import {
    Server,
    Wifi,
    EthernetPort,
    Activity,
    AlertTriangle
} from "lucide-react"

import { useNavigate } from "react-router-dom"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import RuntimeNodeCard from "../components/RuntimeNodeCard"

export default function RuntimeNodesPage() {

    const navigate = useNavigate()

    // --- Fake Runtime Data ---
    const nodes = [
        {
            id: "node-1",
            name: "Garden Main Controller",
            online: true,
            connection: "wifi", // wifi | ethernet
            signal: -55, // dBm
            zonesCount: 6,
            controllerStatus: "running", // running | idle | error
            warnings: 0,
            errors: 0
        },
        {
            id: "node-2",
            name: "Greenhouse Node",
            online: true,
            connection: "ethernet",
            signal: null,
            zonesCount: 4,
            controllerStatus: "running",
            warnings: 1,
            errors: 0
        },
        {
            id: "node-3",
            name: "Orchard Node",
            online: false,
            connection: "wifi",
            signal: -82,
            zonesCount: 5,
            controllerStatus: "offline",
            warnings: 0,
            errors: 1
        }
    ]

    const onlineCount = nodes.filter(n => n.online).length

    return (
        <Box>

            <GlassPageHeader
                title="Runtime Nodes"
                subtitle="Live status of irrigation nodes"
            />

            <Stack gap={8} p={8}>

                <GlassPanelSection
                    title="Nodes Overview"
                    description={`${onlineCount} / ${nodes.length} nodes online`}
                >
                    <Grid
                        templateColumns={{
                            base: "1fr",
                            md: "1fr 1fr",
                            xl: "1fr 1fr 1fr"
                        }}
                        gap={6}
                    >
                        {nodes.map(node => (
                            <RuntimeNodeCard
                                key={node.id}
                                node={node}
                                onClick={() => navigate(`/runtime/nodes/${node.id}`)}
                            />
                        ))}
                    </Grid>
                </GlassPanelSection>

            </Stack>

        </Box>
    )
}
