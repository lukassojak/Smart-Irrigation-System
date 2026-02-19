// InteractiveCard.jsx
import { Link } from "react-router-dom"
import BaseCard from "./BaseCard"

export default function InteractiveCard({
    to,
    children,
    variant = "edge",
    ...props
}) {
    return (
        <BaseCard
            as={Link}
            to={to}
            variant={variant}
            cursor="pointer"
            _hover={{
                transform: "translateY(-2px)"
            }}
            {...props}
        >
            {children}
        </BaseCard>
    )
}
