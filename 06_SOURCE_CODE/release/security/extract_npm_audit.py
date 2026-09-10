"""Extract npm audit severity summary into release/security/npm-audit.json."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # 06_SOURCE_CODE
WEB = ROOT / "aura-web"
OUT = ROOT / "release" / "security" / "npm-audit.json"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    node_script = (
        "const {execSync}=require('child_process');"
        "try { console.log(execSync('npm audit --json',{encoding:'utf8'})); }"
        "catch(e) { console.log(e.stdout || e.message); }"
    )
    result = subprocess.run(["node", "-e", node_script], cwd=WEB, capture_output=True, text=True, timeout=180)
    out = result.stdout
    start = out.find("{")
    if start < 0:
        print("no JSON from npm audit")
        return 1
    data = json.loads(out[start:])
    vulns = data.get("vulnerabilities", {})
    summary = {
        "tool": "npm audit",
        "total_vulnerabilities": len(vulns),
        "by_severity": {},
        "findings": [],
    }
    for name, item in vulns.items():
        sev = item.get("severity", "unknown")
        summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
        summary["findings"].append({
            "package": name,
            "severity": sev,
            "via": str(item.get("via"))[:300],
            "fix_available": item.get("fixAvailable", None),
        })
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"total": len(vulns), "by_severity": summary["by_severity"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())