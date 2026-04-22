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
                <Dialog.Backdrop />
                <Dialog.Positioner alignItems="flex-start" pt={{ base: 4, md: 8 }}>
                    <Dialog.Content borderTopWidth="4px" borderTopColor={statusColor}>
                        {title && (
                            <Dialog.Header>
                                <Dialog.Title>
                                    <Stack direction="row" align="center" gap={2}>
                                        <StatusIcon size={18} />
                                        <Text>{title}</Text>
                                    </Stack>
                                </Dialog.Title>
                            </Dialog.Header>
                        )}

                        <Dialog.Body>
                            <Stack gap={3}>
                                {description && (
                                    <Dialog.Description>{description}</Dialog.Description>
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
