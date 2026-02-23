import { Box, useBreakpointValue } from "@chakra-ui/react"
import { Outlet } from "react-router-dom"
import Sidebar from "./sidebar/Sidebar"
import MobileSidebar from "./sidebar/MobileSidebar"
import { useState } from "react"


export default function AppLayout() {

    const [isCollapsed, setIsCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)

    const isMobile = useBreakpointValue({ base: true, lg: false })

    return (
        <Box display="flex">
            {!isMobile && (
                <Sidebar
                    isCollapsed={isCollapsed}
                    onToggle={() => setIsCollapsed(!isCollapsed)}
                />
            )}

            {isMobile && (
                <MobileSidebar
                    isOpen={mobileOpen}
                    onClose={() => setMobileOpen(false)}
                />
            )}

            <Box
                ml={!isMobile ? (isCollapsed ? "72px" : "260px") : 0}
                flex="1"
                minH="100vh"
                transition="margin 0.2s ease"
            >
                <Outlet
                    context={{
                        isMobile,
                        openMobileSidebar: () => setMobileOpen(true)
                    }}
                />
            </Box>
        </Box>
    )
}