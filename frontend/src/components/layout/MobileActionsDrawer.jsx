import React from "react"
import {
    Drawer,
    Portal,
    VStack,
    HStack,
    Box,
    Button,
    Text,
} from "@chakra-ui/react"
import { MoreVertical } from "lucide-react"

import {
    HeaderAction,
    HeaderActionDanger,
} from "../ui/ActionButtons"


function flattenChildren(children) {
    return React.Children.toArray(children).flatMap((child) => {
        if (!React.isValidElement(child)) {
            return []
        }

        if (child.type === React.Fragment) {
            return flattenChildren(child.props.children)
        }

        return child
    })
}


export default function MobileActionsDrawer({
    actions,
}) {
    const [open, setOpen] = React.useState(false)
    const parsedActions = flattenChildren(
        actions?.props?.children,
    )

    if (parsedActions.length === 0) {
        return null
    }

    return (
        <Drawer.Root
            placement="bottom"
            open={open}
            onOpenChange={(e) => setOpen(e.open)}
        >
            <Drawer.Trigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    p={2}
                    minW="unset"
                    borderRadius="lg"
                    _hover={{
                        bg: "rgba(255,255,255,0.08)",
                    }}
                >
                    <MoreVertical size={24} />
                </Button>
            </Drawer.Trigger>

            <Portal>
                <Drawer.Backdrop
                    bg="rgba(15,23,42,0.32)"
                    backdropFilter="blur(8px)"
                />

                <Drawer.Positioner>
                    <Drawer.Content
                        borderTopRadius="2xl"
                        bg="rgba(255,255,255,0.72)"
                        backdropFilter="blur(18px) saturate(160%)"
                        border="1px solid rgba(56,178,172,0.10)"
                        boxShadow="
                            inset 0 1px 0 rgba(255,255,255,0.85),
                            0 -16px 40px rgba(15,23,42,0.16)
                        "
                        pb="max(env(safe-area-inset-bottom), 16px)"
                        maxH="70vh"
                    >
                        {/* iOS handle */}
                        <Box
                            display="flex"
                            justifyContent="center"
                            pt={3}
                            pb={2}
                        >
                            <Box
                                w="42px"
                                h="4px"
                                borderRadius="full"
                                bg="gray.300"
                            />
                        </Box>

                        <Drawer.Header px={6} pb={2}>
                            <Text
                                fontSize="sm"
                                fontWeight="600"
                                color="fg.muted"
                            >
                                Actions
                            </Text>
                        </Drawer.Header>

                        <Drawer.Body
                            px={4}
                            pb={6}
                            overflowY="auto"
                        >
                            <VStack
                                align="stretch"
                                gap={2}
                                w="100%"
                            >
                                {parsedActions.map((action, index) => {
                                    const isDanger =
                                        action.type === HeaderActionDanger

                                    const {
                                        children,
                                        onClick,
                                        disabled,
                                        loading,
                                        as,
                                        to,
                                        href,
                                        ...rest
                                    } = action.props

                                    return (
                                        <Button
                                            h="52px"
                                            justifyContent="flex-start"
                                            borderRadius="xl"
                                            variant="ghost"
                                            fontWeight="500"
                                            colorPalette={
                                                isDanger
                                                    ? "red"
                                                    : "gray"
                                            }
                                            loading={loading}
                                            disabled={disabled}
                                            onClick={(e) => {
                                                onClick?.(e)
                                                setOpen(false)
                                            }}
                                            as={as}
                                            to={to}
                                            href={href}
                                            _hover={{
                                                bg: isDanger
                                                    ? "rgba(229,62,62,0.08)"
                                                    : "rgba(56,178,172,0.08)",
                                            }}
                                            _active={{
                                                transform: "scale(0.98)",
                                            }}
                                            {...rest}
                                        >
                                            <HStack
                                                justify="space-between"
                                                w="100%"
                                            >
                                                <Box>
                                                    {children}
                                                </Box>
                                            </HStack>
                                        </Button>
                                    )
                                })}
                            </VStack>
                        </Drawer.Body>
                    </Drawer.Content>
                </Drawer.Positioner>
            </Portal>
        </Drawer.Root>
    )
}