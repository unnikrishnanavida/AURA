import { ArrowLeft, Compass, Home } from "lucide-react";
import { useNavigate } from "react-router-dom";

import styles from "./NotFound.module.css";

import type { NotFoundProps } from "./NotFound.types";

const NotFound = ({ className }: NotFoundProps) => {

    const navigate = useNavigate();

    return (

        <main
            className={`${styles.page} ${className ?? ""}`}
        >

            <section className={styles.card}>

                {/* ================= ILLUSTRATION ================= */}

                <div className={styles.illustration}>

                    <Compass size={96} strokeWidth={1.5} />

                </div>

                {/* ================= ERROR CODE ================= */}

                <div className={styles.code}>
                    404
                </div>

                {/* ================= TITLE ================= */}

                <h1 className={styles.title}>
                    Page Not Found
                </h1>

                {/* ================= DESCRIPTION ================= */}

                <p className={styles.description}>

                    The page you're looking for doesn't exist,
                    may have been moved, or the URL may be
                    incorrect.

                    <br />

                    Return to your dashboard or go back to the
                    previous page.

                </p>

                {/* ================= ACTIONS ================= */}

                <div className={styles.actions}>

                    <button
                        type="button"
                        className={styles.primaryButton}
                        onClick={() => navigate("/dashboard")}
                    >

                        <Home size={18} />

                        {" "}

                        Dashboard

                    </button>

                    <button
                        type="button"
                        className={styles.secondaryButton}
                        onClick={() => navigate(-1)}
                    >

                        <ArrowLeft size={18} />

                        {" "}

                        Go Back

                    </button>

                </div>

            </section>

        </main>

    );

};

export default NotFound;