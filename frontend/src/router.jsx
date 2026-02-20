import { createBrowserRouter } from "react-router-dom"
import { Box } from "@chakra-ui/react"

import MainDashboardPage from "./modules/runtime/pages/MainDashboardPage"
import ManualControlPage from "./modules/runtime/pages/ManualControlPage"
import NodesDashboardPage from "./modules/configuration/pages/DashboardPage"
import NodeDetailPage from "./modules/configuration/pages/NodeDetailPage"
import CreateNodePage from "./modules/configuration/pages/CreateNodePage"
import ZoneDetailPage from "./modules/configuration/pages/ZoneDetailPage"
import Wizard from "./modules/configuration/pages/CreateZoneWizard/Wizard"
import AppLayout from "./components/layout/AppLayout"

import RuntimeNodesPage from "./modules/runtime/pages/RuntimeNodesPage"
import RuntimeNodeDetailPage from "./modules/runtime/pages/RuntimeNodeDetailPage"
import HomePage from "./HomePage"

const router = createBrowserRouter([
    {
        path: "/",
        element: <AppLayout />,
        children: [

            {
                index: true,
                element: <HomePage />
            },

            {
                path: "dashboard",
                element: <MainDashboardPage />,
            },

            {
                path: "configuration",
                children: [
                    {
                        path: "nodes",
                        element: <NodesDashboardPage />,
                    },
                    {
                        path: "nodes/new",
                        element: <CreateNodePage />,
                    },
                    {
                        path: "nodes/:nodeId",
                        element: <NodeDetailPage />,
                    },
                    {
                        path: "nodes/:nodeId/zones/:zoneId",
                        element: <ZoneDetailPage />,
                    },
                    {
                        path: "nodes/:nodeId/zones/new",
                        element: <Wizard />,
                    }
                ]
            },

            {
                path: "manual",
                // placeholder
                element: <ManualControlPage />
            },

            {
                path: "notifications",
                // placeholder
                element: <Box p={6}>
                    <Box fontSize="2xl" fontWeight="bold" mb={4}>
                        Notifications
                    </Box>
                    <Box fontSize="md" color="fg.muted">
                        This is the notifications page placeholder.
                    </Box>
                </Box>
            },

            {
                path: "monitoring",
                // placeholder
                element: <Box p={6}>
                    <Box fontSize="2xl" fontWeight="bold" mb={4}>
                        Monitoring
                    </Box>
                    <Box fontSize="md" color="fg.muted">
                        This is the monitoring page placeholder.
                    </Box>
                </Box>
            },

            {
                path: "statistics",
                // placeholder
                element: <Box p={6}>
                    <Box fontSize="2xl" fontWeight="bold" mb={4}>
                        Statistics
                    </Box>
                    <Box fontSize="md" color="fg.muted">
                        This is the statistics page placeholder.
                    </Box>
                </Box>
            },

            {
                path: "irrigation-history",
                // placeholder
                element: <Box p={6}>
                    <Box fontSize="2xl" fontWeight="bold" mb={4}>
                        Irrigation History
                    </Box>
                    <Box fontSize="md" color="fg.muted">
                        This is the irrigation history page placeholder.
                    </Box>
                </Box>
            },

            {
                path: "weather",
                // placeholder
                element: <Box p={6}>
                    <Box fontSize="2xl" fontWeight="bold" mb={4}>
                        Weather History
                    </Box>
                    <Box fontSize="md" color="fg.muted">
                        This is the weather history page placeholder.
                    </Box>
                </Box>
            },

            {
                path: "settings",
                // placeholder
                element: <Box p={6}>
                    <Box fontSize="2xl" fontWeight="bold" mb={4}>
                        Settings
                    </Box>
                    <Box fontSize="md" color="fg.muted">
                        This is the settings page placeholder.
                    </Box>
                </Box>
            },

            {
                path: "/runtime/nodes",
                element: <RuntimeNodesPage />
            },
            {
                path: "/runtime/nodes/:nodeId",
                element: <RuntimeNodeDetailPage />
            }

        ]
    }
])



export default router;