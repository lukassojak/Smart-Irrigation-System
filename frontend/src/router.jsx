import { createBrowserRouter } from "react-router-dom"
import { Box } from "@chakra-ui/react"

import MainDashboardPage from "./modules/runtime/pages/MainDashboardPage"
import ManualControlPage from "./modules/runtime/pages/ManualControlPage"
import NodesDashboardPage from "./modules/configuration/pages/DashboardPage"
import NodeDiscoveryPage from "./modules/configuration/pages/NodeDiscoveryPage"
import NodeDetailPage from "./modules/configuration/pages/NodeDetailPage"
import NodeHeaderDetailPage from "./modules/configuration/pages/NodeHeaderDetailPage"
import CreateNodePage from "./modules/configuration/pages/CreateNodePage"
import EditNodePage from "./modules/configuration/pages/EditNodePage"
import ZoneDetailPage from "./modules/configuration/pages/ZoneDetailPage"
import GlobalSettingsPage from "./modules/configuration/pages/GlobalSettingsPage"
import Wizard from "./modules/configuration/pages/CreateZoneWizard/Wizard"
import EditZoneWizard from "./modules/configuration/pages/EditZoneWizard/EditZoneWizard"
import AppLayout from "./components/layout/AppLayout"

import RuntimeNodesPage from "./modules/runtime/pages/RuntimeNodesPage"
import RuntimeNodeDetailPage from "./modules/runtime/pages/RuntimeNodeDetailPage"
import StatisticsPage from "./modules/runtime/pages/StatisticsPage"
import IrrigationHistoryPage from "./modules/history/pages/IrrigationHistoryPage"
import IrrigationRecordDetailPage from "./modules/history/pages/IrrigationRecordDetailPage"
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
                        path: "nodes/discovery",
                        element: <NodeDiscoveryPage />,
                    },
                    {
                        path: "nodes/new",
                        element: <CreateNodePage />,
                    },
                    {
                        path: "nodes/:nodeId/edit",
                        element: <EditNodePage />,
                    },
                    {
                        path: "nodes/:nodeId/zones/new",
                        element: <Wizard />,
                    },
                    {
                        path: "nodes/:nodeId/zones/:zoneId/edit",
                        element: <EditZoneWizard />,
                    },
                    {
                        path: "nodes/:nodeId/zones/:zoneId",
                        element: <ZoneDetailPage />,
                    },
                    {
                        path: "nodes/:nodeId/header",
                        element: <NodeHeaderDetailPage />,
                    },
                    {
                        path: "nodes/:nodeId",
                        element: <NodeDetailPage />,
                    },
                    {
                        path: "settings",
                        element: <GlobalSettingsPage />,
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
                element: <StatisticsPage />
            },

            {
                path: "irrigation-history",
                element: <IrrigationHistoryPage />
            },
            {
                path: "irrigation-history/:nodeId/:circuitId/:startTime",
                element: <IrrigationRecordDetailPage />,
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