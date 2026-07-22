import { Outlet } from "react-router-dom";

import Sidebar from "../../components/layout/Sidebar";
import Topbar from "../../components/layout/Topbar";

import styles from "./DashboardLayout.module.css";

const DashboardLayout = () => {

    return (

        <div className={styles.layout}>

            <Sidebar />

            <div className={styles.content}>

                <Topbar />

                <main className={styles.page}>

                    <Outlet />

                </main>

            </div>

        </div>

    );

};

export default DashboardLayout;