// components/layout/AppLayout.jsx

import { Box } from "@chakra-ui/react"
import { Outlet } from "react-router-dom"
import Sidebar from "./sidebar/Sidebar"

export default function AppLayout() {
    return (
        <Box display="flex">
            <Sidebar />

            <Box
                ml="260px"
                flex="1"
                minH="100vh"
            >
                <Outlet />
            </Box>
        </Box>
    )
}
