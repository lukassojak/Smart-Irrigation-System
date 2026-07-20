import React from "react"
import { Box, HStack, Text, Badge, Stack } from "@chakra-ui/react"

function formatNumber(value, fractionDigits = 2) {
    if (value == null || Number.isNaN(Number(value))) return "-"
    return Number(value).toFixed(fractionDigits)
}

export default function WaterAmountGauge({ base = null, target = null, actual = null, thresholdPerc = null, unit = "L", manualRun = false, dynamicEnabled = false }) {
    // Determine scale max with 20% headroom (user request)
    const values = [base, target, actual].filter(v => v != null && !Number.isNaN(Number(v))).map(Number)
    const rawMax = values.length ? Math.max(...values) : 10
    const maxScale = Math.max(rawMax * 1.2, 1)

    const pos = (v) => (v == null || Number.isNaN(Number(v)) ? null : Math.min(100, Math.max(0, (Number(v) / maxScale) * 100)))

    const basePos = pos(base)
    const targetPos = pos(target)
    const actualPos = pos(actual)
    const carryOverThresholdPos = pos(thresholdPerc != null && base != null ? (Number(base) * (Number(thresholdPerc) / 100)) : null)

    // total correction: percent change from base -> target, e.g. 2L -> 6L === +200%
    let correctionPercent = null
    if (base != null && target != null && Number(base) !== 0) {
        correctionPercent = ((Number(target) / Number(base) - 1) * 100)
    }

    const ticks = 11

    const thresholdValue =
        thresholdPerc != null && base != null
            ? Number(base) * (Number(thresholdPerc) / 100)
            : null
    // Build markers and cluster them if too close to avoid overlap
    const markerList = []
    if (basePos != null) markerList.push({ key: 'base', pos: basePos, label: 'Base', value: base, color: 'rgba(126, 126, 126, 0.44)' })
    if (targetPos != null) markerList.push({ key: 'target', pos: targetPos, label: 'Target', value: target, color: 'rgba(49,151,149,0.95)' })
    if (actualPos != null) markerList.push({ key: 'actual', pos: actualPos, label: 'Actual', value: actual, color: 'rgba(37, 139, 223, 0.95)' })
    if (carryOverThresholdPos != null && manualRun === false && dynamicEnabled === true)
        markerList.push({
            key: 'threshold',
            pos: carryOverThresholdPos,
            label: 'Threshold',
            value: thresholdValue,
            color: 'rgba(126, 126, 126, 0.44)'
        })

    markerList.sort((a, b) => a.pos - b.pos)

    // cluster threshold in percent units
    const clusterThreshold = 6
    const clusters = []
    for (const m of markerList) {
        const last = clusters[clusters.length - 1]
        if (!last || m.pos - last[last.length - 1].pos > clusterThreshold) {
            clusters.push([m])
        } else {
            last.push(m)
        }
    }

    const fillPercent = actualPos != null ? Math.max(0, Math.min(100, actualPos)) : 0

    return (
        <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.6)" border="1px solid rgba(56,178,172,0.08)">
            <Stack gap={10}>
                <HStack justify="space-between">
                    <Text fontSize="sm" fontWeight="700">Water amounts</Text>
                    <Text fontSize="sm" color="gray.600">Scale: 0 — {formatNumber(maxScale)} {unit}</Text>
                </HStack>
                <Stack gap={0}>
                    <Box position="relative" w="100%">
                        {/* base bar with light blue linear gradient */}
                        <Box
                            h="14px"
                            borderRadius="full"
                            bg="linear-gradient(270deg, rgba(197,224,255,0.65) 0%, rgba(225,245,255,0.6) 50%, rgba(197,224,255,0.4) 100%)"
                            border="1px solid rgba(66,153,225,0.12)"
                        />

                        {/* filled area up to actual */}
                        <Box
                            position="absolute"
                            left="0"
                            top="0"
                            bottom="0"
                            w={`${fillPercent}%`}
                            borderTopLeftRadius="999px"
                            borderBottomLeftRadius="999px"
                            borderTopRightRadius={fillPercent >= 99 ? '999px' : 0}
                            borderBottomRightRadius={fillPercent >= 99 ? '999px' : 0}
                            bg="linear-gradient(270deg, rgba(66, 153, 225, 0.65), rgba(66, 153, 225, 0.51))"
                            zIndex={1}
                        />

                        {/* minor ticks */}
                        {Array.from({ length: ticks - 2 }).map((_, i) => {
                            const idx = i + 1
                            return (
                                <Box
                                    key={`tick-${idx}`}
                                    position="absolute"
                                    top="50%"
                                    left={`${(idx / (ticks - 1)) * 100}%`}
                                    transform="translate(-50%, -50%)"
                                    h={idx % 5 === 0 ? "14px" : "10px"}
                                    w="2px"
                                    bg="rgba(15,23,42,0.12)"
                                    borderRadius="1px"
                                    zIndex={2}
                                />
                            )
                        })}

                        {/* marker lines centered on the bar */}
                        {markerList.map(m => (
                            <Box
                                key={`marker-line-${m.key}`}
                                position="absolute"
                                left={`${m.pos}%`}
                                top="50%"
                                transform="translate(-50%, -50%)"
                                textAlign="center"
                                zIndex={4}
                            >
                                <Box mx="auto" w="4px" h="22px" bg={m.color} borderRadius="2px" />
                            </Box>
                        ))}

                        {/* clustered labels rendered below the bar, side-by-side for close markers */}
                        {clusters.map((cluster, idx) => {
                            const center = cluster.reduce((s, it) => s + it.pos, 0) / cluster.length
                            return (
                                <Box
                                    key={`cluster-${idx}`}
                                    position="absolute"
                                    left={`${center}%`}
                                    top="calc(100% + 28px)"
                                    transform="translate(-50%, 0)"
                                    zIndex={5}
                                    display="flex"
                                    gap={2}
                                    alignItems="center"
                                >
                                    {cluster.map(item => (
                                        <Box key={`lbl-${item.key}`} bg="rgba(255,255,255,0.95)" px={2} py={1} borderRadius="md" border="1px solid rgba(0,0,0,0.04)">
                                            <Text fontSize="xs" fontWeight="700" color="gray.800">{item.label}</Text>
                                            <Text fontSize="xs" color="gray.600">{formatNumber(item.value)} {unit}</Text>
                                        </Box>
                                    ))}
                                </Box>
                            )
                        })}
                    </Box>
                </Stack>

                <HStack gap={3} wrap="wrap" mt={14}>
                    <Badge colorPalette="gray" variant="subtle">Target: {target != null ? `${formatNumber(target)} ${unit}` : "N/A"}</Badge>
                    <Badge colorPalette="gray" variant="subtle">Actual: {actual != null ? `${formatNumber(actual)} ${unit}` : "N/A"}</Badge>

                    {correctionPercent != null && !manualRun && (
                        <Badge colorPalette={correctionPercent >= 0 ? "teal" : "orange"} variant="solid">
                            Total correction: {correctionPercent >= 0 ? "+" : ""}{Math.round(correctionPercent)}%
                        </Badge>
                    )}
                </HStack>
            </Stack>
        </Box >
    )
}
