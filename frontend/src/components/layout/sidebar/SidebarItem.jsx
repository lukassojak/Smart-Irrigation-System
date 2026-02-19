// components/layout/sidebar/SidebarItem.jsx

import { Box, HStack, Text } from "@chakra-ui/react"
import { NavLink } from "react-router-dom"

export default function SidebarItem({ to, icon: Icon, children }) {
    return (
        <NavLink to={to} style={{ textDecoration: "none" }}>
            {({ isActive }) => (
                <Box
                    px={3}
                    py={2}
                    borderRadius="md"
                    transition="background 0.12s ease"
                    bg={isActive ? "rgba(56,178,172,0.08)" : "transparent"}
                    _hover={{
                        bg: "rgba(56,178,172,0.06)"
                    }}
                >
                    <HStack spacing={3}>
                        {Icon && (
                            <Icon
                                size={16}
                                strokeWidth={2}
                                color={isActive ? "#0F766E" : "#4A5568"}
                            />
                        )}

                        <Text
                            fontSize="sm"
                            fontWeight={isActive ? "600" : "500"}
                            color={isActive ? "teal.700" : "gray.700"}
                        >
                            {children}
                        </Text>
                    </HStack>
                </Box>
            )}
        </NavLink>
    )
}
