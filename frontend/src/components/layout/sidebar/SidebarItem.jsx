import { Box, HStack, Text } from "@chakra-ui/react"
import { NavLink } from "react-router-dom"

export default function SidebarItem({ to, icon: Icon, children, isCollapsed }) {
    return (
        <NavLink to={to} style={{ textDecoration: "none" }}>
            {({ isActive }) => (
                <Box
                    px={isCollapsed ? 2 : 3}
                    py={2}
                    borderRadius="md"
                    transition="all 0.12s ease"
                    bg={isActive ? "rgba(56,178,172,0.08)" : "transparent"}
                    display="flex"
                    justifyContent={isCollapsed ? "center" : "flex-start"}
                    _hover={{
                        bg: "rgba(56,178,172,0.06)"
                    }}
                >
                    <HStack spacing={isCollapsed ? 0 : 3}>
                        {Icon && (
                            <Icon
                                size={18}
                                strokeWidth={2}
                                color={isActive ? "#0F766E" : "#4A5568"}
                            />
                        )}

                        {!isCollapsed && (
                            <Text
                                fontSize="sm"
                                fontWeight={isActive ? "600" : "500"}
                                color={isActive ? "teal.700" : "gray.700"}
                            >
                                {children}
                            </Text>
                        )}
                    </HStack>
                </Box>
            )}
        </NavLink>
    )
}