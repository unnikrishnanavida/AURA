import type { ActivityCardProps } from "./ActivityCard.types";

const ActivityCard = ({ title, description, timestamp, status = "info" }: ActivityCardProps) => (
  <article style={{ padding: 16, borderRadius: 16, background: "#0f172a", marginBottom: 12 }}>
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 8 }}>
      <div>
        <h3 style={{ margin: 0, fontSize: 16 }}>{title}</h3>
        {description && <p style={{ margin: "8px 0 0", color: "#cbd5e1" }}>{description}</p>}
      </div>
      {timestamp && <time style={{ color: "#94a3b8", fontSize: 12 }}>{timestamp}</time>}
    </div>
    <span style={{ fontSize: 12, color: "#94a3b8" }}>Status: {status}</span>
  </article>
);

export default ActivityCard;
