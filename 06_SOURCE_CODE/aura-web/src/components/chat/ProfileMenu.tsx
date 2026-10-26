/**
 * ProfileMenu — compact account menu with Settings and Sign out.
 */

import { Settings, LogOut, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSession } from "../../lib/session-context";

interface ProfileMenuProps {
  onNavigate: (tab: string) => void;
}

export function ProfileMenu({ onNavigate }: ProfileMenuProps) {
  const { signOut } = useSession();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onPointer(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <div className="profile" ref={ref}>
      <button
        type="button"
        className="profile-chip"
        aria-label="Account menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="profile-avatar" aria-hidden="true">A</span>
        <span className="profile-meta">
          <span className="profile-name">You</span>
        </span>
        <ChevronDown aria-hidden="true" className="profile-chevron" />
      </button>
      {open ? (
        <div className="profile-menu" role="menu" aria-label="Account">
          <button type="button" role="menuitem" onClick={() => { setOpen(false); onNavigate("settings"); }}>
            <Settings aria-hidden="true" /> Settings
          </button>
          <button type="button" role="menuitem" onClick={() => { setOpen(false); signOut(); }}>
            <LogOut aria-hidden="true" /> Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}