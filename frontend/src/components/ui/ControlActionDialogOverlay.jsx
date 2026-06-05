import {
    Button,
    Dialog,
    Group,
    HStack,
    IconButton,
    Menu,
    Portal,
    Stack,
    Text,
    createOverlay,
} from "@chakra-ui/react"
import { AlertTriangle, CheckCircle2, ChevronDown } from "lucide-react"
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
        isConfirmation = false,
        confirmLabel = "Confirm",
        confirmMenuItems = [],
        cancelLabel = "Cancel",
        closeLabel = "Close",
        overlayId,
        ...rest
    } = props

    const statusColor = {
        success: "green.400",
        error: "red.400",
        info: "teal.400",
    }[status] ?? "teal.400"

    const StatusIcon = status === "success" ? CheckCircle2 : AlertTriangle

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

                                {isConfirmation ? (
                                    <HStack justify="flex-end" gap={2}>
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => controlActionDialog.close(overlayId, false)}
                                        >
                                            {cancelLabel}
                                        </Button>

                                        {confirmMenuItems.length > 0 ? (
                                            <Menu.Root positioning={{ placement: "bottom-end" }}>
                                                <Group attached>
                                                    <Button
                                                        size="sm"
                                                        colorPalette={status === "error" ? "red" : "teal"}
                                                        onClick={() => controlActionDialog.close(overlayId, true)}
                                                    >
                                                        {confirmLabel}
                                                    </Button>

                                                    <Menu.Trigger asChild>
                                                        <IconButton
                                                            size="sm"
                                                            colorPalette={status === "error" ? "red" : "teal"}
                                                            aria-label={`${confirmLabel} options`}
                                                        >
                                                            <ChevronDown size={16} />
                                                        </IconButton>
                                                    </Menu.Trigger>
                                                </Group>

                                                <Menu.Positioner>
                                                    <Menu.Content>
                                                        {confirmMenuItems.map((item) => (
                                                            <Menu.Item
                                                                key={item.value}
                                                                value={item.value}
                                                                onClick={() => controlActionDialog.close(overlayId, item.value)}
                                                            >
                                                                {item.label}
                                                            </Menu.Item>
                                                        ))}
                                                    </Menu.Content>
                                                </Menu.Positioner>
                                            </Menu.Root>
                                        ) : (
                                            <Button
                                                size="sm"
                                                colorPalette={status === "error" ? "red" : "teal"}
                                                onClick={() => controlActionDialog.close(overlayId, true)}
                                            >
                                                {confirmLabel}
                                            </Button>
                                        )}
                                    </HStack>
                                ) : (
                                    <Button
                                        alignSelf="flex-end"
                                        size="sm"
                                        onClick={() => props.onOpenChange?.({ open: false })}
                                    >
                                        {closeLabel}
                                    </Button>
                                )}
                            </Stack>
                        </Dialog.Body>
                    </Dialog.Content>
                </Dialog.Positioner>
            </Portal>
        </Dialog.Root>
    )
})

export const ControlActionDialogViewport = controlActionDialog.Viewport

export function OverlayCleanup() {
    useEffect(() => {
        return () => {
            controlActionDialog.removeAll()
        }
    }, [])

    return null
}

const CONTROL_ACTION_DIALOG_AUTO_CLOSE_MS = 3000

export const openControlActionDialog = (id, payload) => {
    controlActionDialog.open(id, { ...payload, overlayId: id })

    window.setTimeout(() => {
        try {
            controlActionDialog.close(id)
        } catch {
            // The dialog may have already been closed or removed.
        }
    }, CONTROL_ACTION_DIALOG_AUTO_CLOSE_MS)
}

export const openControlActionConfirmDialog = async (id, payload) => {
    const result = await controlActionDialog.open(id, {
        ...payload,
        overlayId: id,
        isConfirmation: true,
    })

    return result
}