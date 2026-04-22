import {
    Box,
    Stack
} from "@chakra-ui/react"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import TimelineItem from "./TimelineItem"

export default function TodaysActivityCard({ items }) {
    const visibleItemsCount = 4
    const timelineItemMinHeightPx = 70
    const timelineGapPx = 24
    const timelineViewportHeightPx =
        visibleItemsCount * timelineItemMinHeightPx +
        (visibleItemsCount - 1) * timelineGapPx

    const sortedItems = [...items].sort((b, a) => a.scheduledTime - b.scheduledTime)

    const shouldScroll = sortedItems.length > 4

    return (
        <GlassPanelSection
            title="Today's Activity"
            description="Planned and completed irrigation tasks for today"
        >
            <Box
                h={`${timelineViewportHeightPx}px`}
                overflowY={shouldScroll ? "auto" : "visible"}
                pr={shouldScroll ? "2" : "0"}
            >
                <Box position="relative" pl="28px">

                    {/* Vertical timeline line */}
                    <Box
                        position="absolute"
                        left="12px"
                        top="0"
                        bottom="0"
                        width="2px"
                        bg="rgba(56,178,172,0.12)"
                    />

                    <Stack gap={6}>
                        {sortedItems.map(item => (
                            <TimelineItem key={item.id} item={item} />
                        ))}
                    </Stack>

                </Box>
            </Box>
        </GlassPanelSection>
    )
}
