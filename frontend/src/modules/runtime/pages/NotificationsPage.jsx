import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import PageNotImplementedWarning from "../../../components/ui/PageNotImplementedWarning"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"

export default function NotificationsPage() {
    return (
        <>
            <GlassPageHeader title="Notifications" />
            <PageContainer>
                <DashboardPageSectionStack>
                    <GlassPanelSection>
                        <PageNotImplementedWarning message="The notifications page is not available yet." />
                    </GlassPanelSection>
                </DashboardPageSectionStack>
            </PageContainer>
        </>
    )
}