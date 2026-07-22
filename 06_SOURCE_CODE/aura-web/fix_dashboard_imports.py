from pathlib import Path
import re

root = Path(r"c:\Users\navid\Desktop\AURA\06_SOURCE_CODE\aura-web")

# Patch tsconfig.app.json
app = root / 'tsconfig.app.json'
if app.exists():
    text = app.read_text(encoding='utf-8')
    text = re.sub(r'\s*"baseUrl"\s*:\s*"[^"]+",?\n', '', text)
    if '"paths"' not in text:
        text = text.replace(
            '    "allowImportingTsExtensions": true,\n',
            '    "allowImportingTsExtensions": true,\n    "paths": { "@/*": ["./src/*"] },\n'
        )
    app.write_text(text, encoding='utf-8')
    print('patched tsconfig.app.json')

# Patch vite.config.ts alias
vite = root / 'vite.config.ts'
if vite.exists():
    text = vite.read_text(encoding='utf-8')
    if "fileURLToPath" not in text:
        text = text.replace(
            "import { defineConfig } from 'vite'\n",
            "import { defineConfig } from 'vite'\nimport { fileURLToPath, URL } from 'node:url'\n"
        )
    if 'resolve:' not in text:
        text = text.replace(
            'export default defineConfig({\n',
            'export default defineConfig({\n  resolve: { alias: [{ find: \'@\', replacement: fileURLToPath(new URL(\'./src\', import.meta.url)) }] },\n'
        )
    vite.write_text(text, encoding='utf-8')
    print('patched vite.config.ts')

# Patch type-only imports in relevant files
patterns = [
    (re.compile(r'^import \{\s*([A-Za-z0-9_]+Props)\s*\} from "(\.\/.+?\.types)";', flags=re.MULTILINE), r'import type { \1 } from "\2";'),
    (re.compile(r'^import \{\s*ReactNode\s*\} from "react";', flags=re.MULTILINE), 'import type { ReactNode } from "react";'),
    (re.compile(r'^import \{\s*ButtonHTMLAttributes\s*,\s*ReactNode\s*\} from "react";', flags=re.MULTILINE), 'import type { ButtonHTMLAttributes, ReactNode } from "react";'),
    (re.compile(r'^import \{\s*ButtonHTMLAttributes\s*\} from "react";', flags=re.MULTILINE), 'import type { ButtonHTMLAttributes } from "react";'),
    (re.compile(r'^import \{\s*LucideIcon\s*\} from "lucide-react";', flags=re.MULTILINE), 'import type { LucideIcon } from "lucide-react";'),
    (re.compile(r'^import \{\s*Agent\s*,\s*AgentStatus\s*\} from "(.*)";', flags=re.MULTILINE), r'import type { Agent, AgentStatus } from "\1";'),
]

for path in root.rglob('src/**/*'):
    if path.suffix not in {'.ts', '.tsx'}:
        continue
    text = path.read_text(encoding='utf-8')
    new_text = text
    for pattern, repl in patterns:
        new_text = pattern.sub(repl, new_text)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        print(f'patched {path.relative_to(root)}')

# Patch PieChart label callback type
pie = root / 'src/components/dashboard/Charts/PieChart/PieChart.tsx'
if pie.exists():
    text = pie.read_text(encoding='utf-8')
    if '({ percent }) =>' in text:
        text = text.replace('({ percent }) =>', '({ percent }: { percent?: number }) =>')
        pie.write_text(text, encoding='utf-8')
        print('patched PieChart label typing')

# Patch RadialChart types and props imports
rad_types = root / 'src/components/dashboard/Charts/RadialChart/RadialChart.types.ts'
if rad_types.exists():
    text = rad_types.read_text(encoding='utf-8')
    text = text.replace('    innerRadius?: number;', '    innerRadius?: number | string;')
    text = text.replace('    outerRadius?: number;', '    outerRadius?: number | string;')
    rad_types.write_text(text, encoding='utf-8')
    print('patched RadialChart.types.ts')

rad_comp = root / 'src/components/dashboard/Charts/RadialChart/RadialChart.tsx'
if rad_comp.exists():
    text = rad_comp.read_text(encoding='utf-8')
    text = re.sub(r'^import \{\s*RadialChartProps\s*\} from "\.\/RadialChart\.types";', 'import type { RadialChartProps } from "./RadialChart.types";', text, flags=re.MULTILINE)
    if text != rad_comp.read_text(encoding='utf-8'):
        rad_comp.write_text(text, encoding='utf-8')
        print('patched RadialChart.tsx import')

# Create ActivityCard component files if missing
activity_types_file = root / 'src/components/dashboard/ActivityCard.types.ts'
activity_file = root / 'src/components/dashboard/ActivityCard.tsx'
if not activity_types_file.exists():
    activity_types_file.write_text(
        'export interface ActivityCardProps {\n'
        '  id: string;\n'
        '  title: string;\n'
        '  description?: string;\n'
        '  timestamp?: string;\n'
        '  status?: "info" | "success" | "warning" | "error";\n'
        '}\n',
        encoding='utf-8'
    )
    print('created ActivityCard.types.ts')
if not activity_file.exists():
    activity_file.write_text(
        'import type { ActivityCardProps } from "./ActivityCard.types";\n\n'
        'const ActivityCard = ({ title, description, timestamp, status = "info" }: ActivityCardProps) => (\n'
        '  <article style={{ padding: 16, borderRadius: 16, background: "#0f172a", marginBottom: 12 }}>\n'
        '    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 8 }}>\n'
        '      <div>\n'
        '        <h3 style={{ margin: 0, fontSize: 16 }}>{title}</h3>\n'
        '        {description && <p style={{ margin: "8px 0 0", color: "#cbd5e1" }}>{description}</p>}\n'
        '      </div>\n'
        '      {timestamp && <time style={{ color: "#94a3b8", fontSize: 12 }}>{timestamp}</time>}\n'
        '    </div>\n'
        '    <span style={{ fontSize: 12, color: "#94a3b8" }}>Status: {status}</span>\n'
        '  </article>\n'
        ');\n\n'
        'export default ActivityCard;\n',
        encoding='utf-8'
    )
    print('created ActivityCard.tsx')

print('done')
