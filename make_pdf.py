from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT

root = Path(r'c:/Users/navid/Desktop/AURA')
out_dir = root / 'out'
out_dir.mkdir(exist_ok=True)
files = [
    root / '01_FOUNDATION/Identity/CH-001/01-front-matter.md',
    root / '01_FOUNDATION/Identity/CH-001/02-part-i-the-beginning.md',
]
output = out_dir / 'AURA-CH-001.pdf'

styles = getSampleStyleSheet()
body_style = styles['BodyText']
body_style.fontName = 'Helvetica'
body_style.fontSize = 11
body_style.leading = 14
body_style.alignment = TA_LEFT

story = []
for path in files:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    for line in lines:
        if line.startswith('#'):
            if line.startswith('# '):
                style = styles['Title']
            elif line.startswith('## '):
                style = styles['Heading2']
            elif line.startswith('### '):
                style = styles['Heading3']
            else:
                style = body_style
            story.append(Paragraph(line.lstrip('#').strip(), style))
            story.append(Spacer(1, 6))
        else:
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))
            else:
                story.append(Spacer(1, 6))
    story.append(PageBreak())

if story and isinstance(story[-1], PageBreak):
    story.pop()

doc = SimpleDocTemplate(str(output), pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
doc.build(story)
print(output)
