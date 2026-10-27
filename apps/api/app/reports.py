import io
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def draft(run):
    result = run.result
    lines = ["# Investigation report", "", "## Research question", run.question, "", "## Findings"]
    for claim in result.get("claims", []):
        ids = claim.get("source_ids", [])
        refs = " ".join("[" + v + "]" for v in ids)
        if claim.get("analysis_id"):
            refs += " [calculation:" + claim["analysis_id"] + "]"
        lines.append("- " + claim["text"] + " " + refs + " (" + claim["verification"] + ")")
    if result.get("abstained"):
        lines.append(result["answer"])
    lines += ["", "## Reconciliation"]
    for row in result.get("analytics", {}).get("reconciliation", []):
        lines.append(f'- {row["metric"]}: recorded {row["recorded"]}; reported {row["reported"]}; difference {row["difference"]}; {row["status"]}.')
    lines += ["", "## Sources"]
    for s in result.get("sources", []):
        location = ", ".join(f"{k}: {v}" for k,v in s["location"].items() if k != "offset")
        lines.append(f'- [{s["id"]}] {s["name"]} · version {s["version"]} · {location}')
    lines += ["", "## Calculation inputs"]
    for analysis in result.get("analytics", {}).get("analyses", []):
        source = analysis["source"]
        lines.append(f'- [calculation:{analysis["id"]}] {source["name"]} | {source["sheet"]} {source["range"]} | version {source["version_id"]} | SHA-256 {source["hash"]} | operation hash {analysis["provenance"]["operation_hash"]}')
    lines += ["", "## Assumptions and limitations", "Generated from immutable source versions. Source existence is rechecked when opening the run."]
    lines += ["- " + w for w in result.get("warnings", [])]
    lines += ["", "## Reproducibility", f'Run: {run.id}', f'Model: {run.config.get("provider")} / {run.config.get("model")}',
              "Calculations retain operation hashes, source hashes and interpreter versions. Findings are not financial or legal advice."]
    return "\n".join(lines)

def pdf(title, content):
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    styles["BodyText"].textColor = colors.HexColor("#29352e")
    styles["BodyText"].leading = 15
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1,20)]
    for line in content.splitlines():
        if not line.strip():
            story.append(Spacer(1,8))
        else:
            style = styles["Heading2"] if line.startswith("#") else styles["BodyText"]
            story.append(Paragraph(escape(line.lstrip("# ")), style))
    SimpleDocTemplate(output, pagesize=A4, title=title, author="Insyvera", rightMargin=45,
        leftMargin=45, topMargin=45, bottomMargin=45).build(story)
    return output.getvalue()
