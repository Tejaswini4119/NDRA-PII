import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import re

def main():
    md_file = "reports/NDRA_Implementation_Report_2025_12_30.md"
    pdf_file = "reports/NDRA_Implementation_Report_2025_12_30.pdf"
    
    if not os.path.exists(md_file):
        print(f"Error: {md_file} not found.")
        return

    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='H1', parent=styles['Heading1'], fontSize=18, spaceAfter=12, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='H2', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=colors.black))
    styles.add(ParagraphStyle(name='MD_Body', parent=styles['BodyText'], spaceAfter=8))
    
    story = []
    
    with open(md_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Headers
        if line.startswith("# "):
            text = line[2:].strip()
            story.append(Paragraph(text, styles["H1"]))
        elif line.startswith("## "):
            text = line[3:].strip()
            story.append(Paragraph(text, styles["H2"]))
        elif line.startswith("### "):
            text = line[4:].strip()
            story.append(Paragraph(text, styles["Heading3"]))
            
        # Lists
        elif line.startswith("- "):
            text = line[2:].strip()
            # Basic Bold formatting **text** -> <b>text</b>
            text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
            # Code formatted `text` -> <font name=Courier>text</font>
            text = re.sub(r"`(.*?)`", r'<font face="Courier">\1</font>', text)
            
            story.append(Paragraph(f"• {text}", styles["MD_Body"], bulletText="•"))
            
        # Divider
        elif line.startswith("---"):
            story.append(Spacer(1, 12))
            
        # Normal Text
        else:
            text = line
            text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
            text = re.sub(r"`(.*?)`", r'<font face="Courier">\1</font>', text)
            story.append(Paragraph(text, styles["MD_Body"]))
            
    try:
        doc.build(story)
        print(f"[SUCCESS] Generated PDF: {os.path.abspath(pdf_file)}")
    except Exception as e:
        print(f"[ERROR] Failed to generate PDF: {e}")

if __name__ == "__main__":
    main()
