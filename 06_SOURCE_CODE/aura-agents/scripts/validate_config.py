"""Configuration validation: checks that each profile loads and validates."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aura_agent.configuration import Profile, load_settings  # noqa: E402


def main() -> int:
    for profile in (Profile.DEVELOPMENT, Profile.PRODUCTION, Profile.RESEARCH):
        settings = load_settings(profile)
        assert settings.profile == profile
        assert settings.agent.autonomy_mode in {
            "MANUAL",
            "ASSISTED",
            "SUPERVISED",
            "AUTONOMOUS",
        }
        assert settings.agent.max_loop_iterations >= 1
        print(f"  {profile}: OK (log={settings.agent.log_level})")
    print("All configuration profiles load and validate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())