/** AURA's open-triangle emblem, illuminated globe, wordmark, and tagline. */

type AuraLogoVariant = "mark" | "horizontal" | "stacked" | "mono";

interface AuraLogoProps {
  variant?: AuraLogoVariant;
  className?: string;
}

import { useId } from "react";

export function AuraMark({ className = "", color = "brand" }: { className?: string; color?: "brand" | "mono" }) {
  const ids = `m${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const gold = `gold-${ids}`;
  const globe = `globe-${ids}`;
  const clip = `clip-${ids}`;
  const glow = `glow-${ids}`;
  const mono = color === "mono";
  return (
    <svg className={`aura-mark ${mono ? "is-mono" : ""} ${className}`} viewBox="0 0 100 100" aria-hidden="true">
      <defs>
        <linearGradient id={gold} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={mono ? "#ffffff" : "#fff2c2"} />
          <stop offset="0.42" stopColor={mono ? "#f5f5f5" : "#e5b653"} />
          <stop offset="0.78" stopColor={mono ? "#d8d8d8" : "#b77a22"} />
          <stop offset="1" stopColor={mono ? "#ffffff" : "#f8d77f"} />
        </linearGradient>
        <radialGradient id={globe} cx="0.38" cy="0.3" r="0.8">
          <stop offset="0" stopColor={mono ? "#ffffff" : "#513715"} />
          <stop offset="0.55" stopColor={mono ? "#d8d8d8" : "#1b1309"} />
          <stop offset="1" stopColor={mono ? "#ffffff" : "#080705"} />
        </radialGradient>
        <clipPath id={clip}><circle cx="50" cy="66" r="15.8" /></clipPath>
        <filter id={glow} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>

      <circle cx="50" cy="67" r="19" fill={mono ? "#ffffff" : "#d99d3c"} opacity={mono ? 0.12 : 0.22} filter={`url(#${glow})`} />
      <path d="M50 6 11 79 28 75 52 29Z" fill={`url(#${gold})`} stroke={mono ? "#ffffff" : "#f6d88c"} strokeWidth="0.8" />
      <path d="M50 6 48 29 72 75 89 79Z" fill={`url(#${gold})`} stroke={mono ? "#ffffff" : "#f6d88c"} strokeWidth="0.8" />
      <path d="m12 78 16-4-1 3-15 4Z" fill={mono ? "#ffffff" : "#8c5a17"} opacity="0.7" />
      <path d="m88 78-16-4 1 3 15 4Z" fill={mono ? "#ffffff" : "#8c5a17"} opacity="0.7" />

      <circle cx="50" cy="66" r="16.4" fill={`url(#${globe})`} stroke={mono ? "#ffffff" : "#f2c66c"} strokeWidth="1.1" />
      <g clipPath={`url(#${clip})`} fill="none" stroke={mono ? "#ffffff" : "#e5b653"} strokeLinecap="round" opacity={mono ? 0.8 : 0.88}>
        <path d="M33 58c4-5 8-4 11-1 3 3 4 5 7 3 4-3 7-5 12-1 3 2 5 5 7 4" strokeWidth="0.9" />
        <path d="M33 63c4-3 7-2 10 1 3 4 6 5 9 2 4-4 8-4 12-1 3 2 5 4 7 2" strokeWidth="1.1" />
        <path d="M33 69c4-4 7-4 11-1 4 4 7 5 10 2 3-3 7-4 11-1 3 2 5 4 7 2" strokeWidth="0.85" />
        <path d="M37 76c3-3 6-3 9-1 4 3 7 3 10 0 3-3 6-3 9-1" strokeWidth="0.8" />
        <path d="M40 51c-2 5-1 9 2 12 3 3 3 6 0 9-2 2-2 5 0 9" strokeWidth="0.65" opacity="0.8" />
        <path d="M59 50c2 5 1 9-2 12-3 3-3 6 0 9 2 2 2 5 0 9" strokeWidth="0.65" opacity="0.8" />
      </g>
      <circle cx="43" cy="57" r="1.2" fill="#fff4d3" opacity="0.9" />
      <path d="M39 81c6 3 16 4 22 0" fill="none" stroke={mono ? "#ffffff" : "#fff0bd"} strokeWidth="1.2" strokeLinecap="round" opacity="0.9" />
      <circle cx="50" cy="83" r="2" fill={mono ? "#ffffff" : "#fff0bd"} />
    </svg>
  );
}

export function AuraWordmark({ stacked = false }: { stacked?: boolean }) {
  return (
    <span className={stacked ? "aura-word is-stacked" : "aura-word"}>
      <span className="aura-name">AURA</span>
      <span className="aura-tag">The AI Ecosystem</span>
    </span>
  );
}

export function AuraLogo({ variant = "horizontal", className = "" }: AuraLogoProps) {
  if (variant === "mark") {
    return <AuraMark className={className} />;
  }
  if (variant === "mono") {
    return (
      <span className={`aura-logo ${variant} ${className}`}>
        <AuraMark color="mono" />
        <AuraWordmark />
      </span>
    );
  }
  return (
    <span className={`aura-logo ${variant} ${className}`}>
      <AuraMark />
      <AuraWordmark stacked={variant === "stacked"} />
    </span>
  );
}