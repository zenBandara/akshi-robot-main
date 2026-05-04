"""Generate a professional PDF from the AI Thinker implementation plan."""
import markdown2
from xhtml2pdf import pisa
import os

PLAN_PATH = os.path.expanduser(
    "~/.gemini/antigravity/brain/b9bdda7c-b33a-4bd7-989f-c05bbc732e02/"
    "artifacts/ai_thinker_implementation_plan.md"
)
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "AI_Thinker_Implementation_Plan.pdf")

with open(PLAN_PATH, "r") as f:
    md_text = f.read()

# Convert markdown to HTML
html_body = markdown2.markdown(
    md_text,
    extras=["tables", "fenced-code-blocks", "code-friendly", "header-ids"]
)

# Wrap in a styled HTML document
full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    @page {{
        size: A4;
        margin: 2cm;
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #1a1a1a;
    }}
    h1 {{
        color: #1565C0;
        font-size: 22pt;
        border-bottom: 3px solid #1565C0;
        padding-bottom: 8px;
        margin-top: 30px;
    }}
    h2 {{
        color: #1976D2;
        font-size: 16pt;
        border-bottom: 2px solid #90CAF9;
        padding-bottom: 5px;
        margin-top: 25px;
    }}
    h3 {{
        color: #1E88E5;
        font-size: 13pt;
        margin-top: 18px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 9.5pt;
    }}
    th {{
        background-color: #1976D2;
        color: white;
        padding: 8px 10px;
        text-align: left;
        font-weight: bold;
    }}
    td {{
        border: 1px solid #E0E0E0;
        padding: 6px 10px;
    }}
    tr:nth-child(even) {{
        background-color: #F5F5F5;
    }}
    code {{
        background-color: #F5F5F5;
        padding: 2px 5px;
        border-radius: 3px;
        font-family: "Courier New", monospace;
        font-size: 9.5pt;
    }}
    pre {{
        background-color: #263238;
        color: #ECEFF1;
        padding: 14px;
        border-radius: 6px;
        font-size: 9pt;
        line-height: 1.4;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
    }}
    pre code {{
        background-color: transparent;
        color: #ECEFF1;
        padding: 0;
    }}
    blockquote {{
        border-left: 4px solid #1976D2;
        margin: 12px 0;
        padding: 8px 16px;
        background-color: #E3F2FD;
        font-size: 10pt;
    }}
    hr {{
        border: none;
        border-top: 2px solid #E0E0E0;
        margin: 20px 0;
    }}
    strong {{
        color: #0D47A1;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

with open(OUTPUT_PDF, "wb") as pdf_file:
    status = pisa.CreatePDF(full_html, dest=pdf_file)

if status.err:
    print(f"Error generating PDF: {status.err}")
else:
    print(f"PDF generated successfully: {OUTPUT_PDF}")
