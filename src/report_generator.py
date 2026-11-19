"""Create a downloadable, formatted PDF summary of one mutation prediction."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.reference import DATASET_URL, REFERENCE_ID, REFERENCE_SEQUENCE

LIMITATIONS = (
    "This is a computational estimate of the dataset-specific TEM-1 deep-mutational-"
    "scanning score, not an experimentally confirmed result. It does not predict "
    "bacterial survival, clinical pathogenicity, antibiotic resistance, or patient "
    "outcomes. The model supports only single amino-acid substitutions relative to "
    "the exact TEM-1 reference and should not be extrapolated to other proteins or "
    "assays. The dataset card defines score 1.0 as wild type. Replicate wild-type "
    "sequence measurements vary; their mean is shown only as a secondary reference."
)


def generate_pdf_report(report: dict[str, Any]) -> bytes:
    required = {"mutation", "features", "predicted_fitness", "model"}
    missing = required.difference(report)
    if missing:
        raise ValueError(f"Report data is incomplete: missing {sorted(missing)}.")
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#133b5c"),
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#176b9b"),
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
        )
    )
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="BactoMut Mutation Research Report",
    )
    story = [
        Paragraph("BactoMut", styles["ReportTitle"]),
        Paragraph(
            "An AI-Based Bacterial Protein Mutation Impact Prediction System",
            styles["BodyText"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Mutation and protein", styles["SectionHeading"]),
    ]
    feature = report["features"]
    protein_info = [
        ["Reference protein", REFERENCE_ID],
        ["Reference sequence length", "286 amino acids"],
        ["Mutation", str(report["mutation"])],
        ["Original residue", str(feature.get("original_aa", "Not available"))],
        ["Substituted residue", str(feature.get("mutant_aa", "Not available"))],
        ["Position (1-based)", str(feature.get("position", "Not available"))],
        ["Selected model", str(report["model"])],
        ["Predicted experimental score", f"{float(report['predicted_fitness']):.6g}"],
    ]
    if report.get("wild_type_reference_score") is not None:
        protein_info.append(
            ["Dataset-defined wild-type reference", f"{float(report['wild_type_reference_score']):.6g}"]
        )
    if report.get("difference_from_reference") is not None:
        protein_info.append(
            ["Difference from reference", f"{float(report['difference_from_reference']):+.6g}"]
        )
    if report.get("wild_type_observed_training_mean") is not None:
        protein_info.append(
            [
                f"Observed WT train mean (n={report.get('wild_type_observed_training_count', 0)})",
                f"{float(report['wild_type_observed_training_mean']):.6g}",
            ]
        )
        if report.get("difference_from_observed_wild_type_mean") is not None:
            protein_info.append(
                [
                    "Difference from observed WT mean",
                    f"{float(report['difference_from_observed_wild_type_mean']):+.6g}",
                ]
            )
    story.append(_styled_table(protein_info))
    story.append(Paragraph("Reference sequence (UniProt P62593)", styles["SectionHeading"]))
    story.append(
        Paragraph(
            "<br/>".join(
                REFERENCE_SEQUENCE[index : index + 60]
                for index in range(0, len(REFERENCE_SEQUENCE), 60)
            ),
            styles["Code"],
        )
    )
    story.append(Paragraph("Extracted biological features", styles["SectionHeading"]))
    feature_rows = [
        ["Feature", "Value"],
        ["BLOSUM62 substitution score", f"{float(feature['blosum62']):.3f}"],
        ["Original amino-acid molecular weight (Da)", f"{float(feature['original_molecular_weight']):.3f}"],
        ["Mutant amino-acid molecular weight (Da)", f"{float(feature['mutant_molecular_weight']):.3f}"],
        ["Molecular-weight difference (Da)", f"{float(feature['molecular_weight_difference']):+.3f}"],
        ["Original hydrophobicity (Kyte-Doolittle)", f"{float(feature['original_hydrophobicity']):+.3f}"],
        ["Mutant hydrophobicity (Kyte-Doolittle)", f"{float(feature['mutant_hydrophobicity']):+.3f}"],
        ["Hydrophobicity difference (Kyte-Doolittle)", f"{float(feature['hydrophobicity_difference']):+.3f}"],
        ["Original charge (approx. pH 7)", f"{float(feature['original_charge']):+.3f}"],
        ["Mutant charge (approx. pH 7)", f"{float(feature['mutant_charge']):+.3f}"],
        ["Charge difference (approx. pH 7)", f"{float(feature['charge_difference']):+.3f}"],
        ["Local reference context", str(feature["local_context"])],
    ]
    story.append(_styled_table(feature_rows))
    story.append(Paragraph("Model evaluation", styles["SectionHeading"]))
    metrics = report.get("evaluation_metrics", {})
    metric_rows = [["Official split", "MAE", "RMSE", "R²", "Spearman"]]
    for split_name, values in metrics.items():
        metric_rows.append(
            [
                str(split_name),
                _format_metric(values.get("mae")),
                _format_metric(values.get("rmse")),
                _format_metric(values.get("r2")),
                _format_metric(values.get("spearman")),
            ]
        )
    if len(metric_rows) == 1:
        metric_rows.append(["Not available", "—", "—", "—", "—"])
    story.append(_styled_table(metric_rows, header=True))
    story.extend(
        [
            Paragraph("Dataset and limitations", styles["SectionHeading"]),
            Paragraph(
                f"Source: <link href='{DATASET_URL}' color='#176b9b'>{DATASET_URL}</link>",
                styles["BodyText"],
            ),
            Paragraph(
                str(report.get("reference_score_note", "")),
                styles["BodyText"],
            ),
            Paragraph(LIMITATIONS, styles["BodyText"]),
            Spacer(1, 4 * mm),
            Paragraph("Developed by Afifa Kounain", styles["BodyText"]),
        ]
    )
    document.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buffer.getvalue()


def _format_metric(value: Any) -> str:
    return "N/A" if value is None else f"{float(value):.4f}"


def _styled_table(rows: list[list[str]], header: bool = False) -> Table:
    table = Table(rows, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7e3ec")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f9fc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcecf7")))
    table.setStyle(TableStyle(style))
    return table


def _page_number(canvas: Any, document: SimpleDocTemplate) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#687987"))
    canvas.drawCentredString(A4[0] / 2, 10 * mm, f"BactoMut | Page {document.page}")
    canvas.restoreState()
