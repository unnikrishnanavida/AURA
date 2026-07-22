import Logo from "../Logo";
import Container from "../Container";
import styles from "./Navbar.module.css";

export default function Navbar() {
  return (
    <header className={styles.navbar}>
      <Container>
        <div className={styles.wrapper}>
          <Logo />

          <nav className={styles.links}>
            <a href="#">Features</a>
            <a href="#">Modules</a>
            <a href="#">Pricing</a>
            <a href="#">About</a>
          </nav>

          <button className={styles.button}>
            Get Started
          </button>
        </div>
      </Container>
    </header>
  );
}