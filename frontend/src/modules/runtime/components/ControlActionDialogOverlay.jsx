import {
    Button,
    Dialog,
    Portal,
    Stack,
    Text,
    createOverlay,
} from "@chakra-ui/react"
import { AlertTriangle, CheckCircle2 } from "lucide-react"
import { useEffect } from "react"

export const controlActionDialog = createOverlay((props) => {
    const {
        title,
        description,
        status = "info",
        mode,
        nodeId,
        nodeCount,
        zoneId,
        code,
        retryable,
        correlationId,
        ...rest
    } = props

    const statusColor = {
        success: "green.400",
        error: "red.400",
        info: "teal.400",
    }[status] ?? "teal.400"

    const StatusIcon = status === "success" ? CheckCircle2 : AlertTriangle

    useEffect(() => {
        if (!props.open) {
            return
        }

        const timeoutId = window.setTimeout(() => {
            props.onOpenChange?.({ open: false })
        }, 3000)

        return () => {
            window.clearTimeout(timeoutId)
        }
    }, [props.open, props.onOpenChange])

    return (
        <Dialog.Root {...rest}>
            <Portal>
                <Dialog.Backdrop bg="rgba(15, 23, 42, 0.28)" backdropFilter="blur(6px)" />
                <Dialog.Positioner alignItems="flex-start" pt={{ base: 4, md: 8 }}>
                    <Dialog.Content
                        bg="rgba(255,255,255,0.72)"
                        backdropFilter="blur(18px) saturate(160%)"
                        border="1px solid"
                        borderColor="rgba(56,178,172,0.12)"
                        borderTopWidth="4px"
                        borderTopColor={statusColor}
                        boxShadow="
                            inset 0 1px 0 rgba(255,255,255,0.85),
                            0 16px 40px rgba(15, 23, 42, 0.12)
                        "
                    >
                        {title && (
                            <Dialog.Header borderBottomWidth="1px" borderBottomColor="rgba(56,178,172,0.10)">
                                <Dialog.Title>
                                    <Stack direction="row" align="center" gap={2}>
                                        <StatusIcon size={18} />
                                        <Text color="gray.800">{title}</Text>
                                    </Stack>
                                </Dialog.Title>
                            </Dialog.Header>
                        )}

                        <Dialog.Body>
                            <Stack gap={3}>
                                {description && (
                                    <Dialog.Description color="gray.700">{description}</Dialog.Description>
                                )}

                                <Stack gap={1}>
                                    {zoneId != null && (
                                        <Text fontSize="sm" color="gray.600">
                                            Zone ID: {zoneId}
                                        </Text>
                                    )}
                                    {nodeId && (
                                        <Text fontSize="sm" color="gray.600">
                                            Node ID: {nodeId}
                                        </Text>
                                    )}
                                    {typeof nodeCount === "number" && (
                                        <Text fontSize="sm" color="gray.600">
                                            Nodes affected: {nodeCount}
                                        </Text>
                                    )}
                                    {mode && (
                                        <Text fontSize="sm" color="gray.600">
                                            Mode: {mode}
                                        </Text>
                                    )}
                                    {code && (
                                        <Text fontSize="sm" color="gray.600">
                                            Error code: {code}
                                        </Text>
                                    )}
                                    {retryable != null && (
                                        <Text fontSize="sm" color="gray.600">
                                            Retryable: {retryable ? "yes" : "no"}
                                        </Text>
                                    )}
                                    {correlationId && (
                                        <Text fontSize="sm" color="gray.600">
                                            Correlation ID: {correlationId}
                                        </Text>
                                    )}
                                </Stack>

                                <Button
                                    alignSelf="flex-end"
                                    size="sm"
                                    onClick={() => props.onOpenChange?.({ open: false })}
                                >
                                    Close
                                </Button>
                            </Stack>
                        </Dialog.Body>
                    </Dialog.Content>
                </Dialog.Positioner>
            </Portal>
        </Dialog.Root>
    )
})

export const ControlActionDialogViewport = controlActionDialog.Viewport
