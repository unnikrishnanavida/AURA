export const colors = {
  // Brand
  primary: "#D4AF37",
  primaryLight: "#F5D76E",

  // Backgrounds
  background: "#05070A",
  surface: "#0D1117",
  card: "#111827",

  // Borders
  border: "#1F2937",

  // Text
  white: "#F8FAFC",
  gray100: "#E2E8F0",
  gray300: "#CBD5E1",
  gray500: "#94A3B8",
  gray700: "#475569",

  // Status
  success: "#22C55E",
  warning: "#F59E0B",
  danger: "#EF4444",

  // AI Accent Colors
  blue: "#3B82F6",
  cyan: "#06B6D4",
  purple: "#8B5CF6",
} as const;

export type ColorToken = keyof typeof colors;