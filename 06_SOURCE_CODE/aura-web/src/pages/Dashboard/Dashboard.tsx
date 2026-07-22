import styles from "./Dashboard.module.css";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import AIStatusCard from "@/components/dashboard/AIStatusCard";
import QuickActions from "@/components/dashboard/QuickActions";
import RecentTasks from "@/components/dashboard/RecentTasks";
import Notifications from "@/components/dashboard/Notifications";
import AnalyticsCard from "@/components/dashboard/AnalyticsCard";
import TokenUsage from "@/components/dashboard/TokenUsage";
import UsageChart from "@/components/dashboard/UsageChart";
import AgentList from "@/components/dashboard/AgentList";
import SystemHealth from "@/components/dashboard/SystemHealth";
import ResearchCard from "@/components/dashboard/ResearchCard";

const Dashboard = () => {

    return (

        <main className={styles.dashboard}>

            <section className={styles.statsGrid}>

                {/* Stats Cards */}

            </section>

            <section className={styles.analytics}>

                <UsageChart
                    data={[]}
                    chart={<></>}
                />

                <TokenUsage
                    totalTokens={1000000}
                    usedTokens={720000}
                    remainingTokens={280000}
                    estimatedCost="$32.10"
                />

            </section>

            <section className={styles.middle}>

                <AnalyticsCard metrics={[]} />

                <SystemHealth metrics={[]} />

                <ResearchCard
                    title="Research"
                    source="OpenAI"
                    description="AI Research Summary"
                    confidence={94}
                    status="completed"
                    updatedAt="5 mins ago"
                />

            </section>

            <section className={styles.bottom}>

                <AgentList agents={[]} />

                <ActivityFeed activities={[]} />

                <RecentTasks tasks={[]} />

                <Notifications notifications={[]} />

                <AIStatusCard
                    model="GPT-5"
                    status="online"
                    responseTime="340ms"
                    metrics={[]}
                />

                <QuickActions actions={[]} />

            </section>

        </main>

    );

};

export default Dashboard;