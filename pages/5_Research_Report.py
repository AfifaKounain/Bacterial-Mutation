import streamlit as st

from src.prediction import available_models, load_model_metadata, predict_mutation
from src.report_generator import generate_pdf_report
from src.ui import apply_scientific_theme, render_footer, render_navigation, sequence_input

apply_scientific_theme()
render_navigation()
st.title("Research report")
st.write("Generate a downloadable PDF with mutation features, model output, and limitations.")
models = available_models()
if not models:
    st.warning(
        "No trained models are available. Run `python -m src.model_training` from the "
        "project folder before generating a prediction report."
    )
else:
    sequence, _ = sequence_input("research_report")
    notation = st.text_input(
        "Mutation from wild type to variant (optional for a single-mutant sequence)",
        value="",
        placeholder="V42A",
        help=(
            "Leave blank to infer the substitution from a single-mutant TEM-1 "
            "sequence or uniquely reference-aligned fragment."
        ),
    )
    model_name = st.selectbox("Model for report", models)
    if st.button("Generate prediction report", type="primary"):
        try:
            prediction = predict_mutation(sequence, notation, model_name)
            metadata = load_model_metadata()
            report_data = {
                **prediction,
                "evaluation_metrics": metadata["evaluation"][model_name],
            }
            pdf_bytes = generate_pdf_report(report_data)
            mutation = prediction["mutation"]
            st.download_button(
                "Download PDF research report",
                data=pdf_bytes,
                file_name=f"bactomut_{mutation}_{model_name.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
            )
            st.success("The PDF was generated successfully.")
        except (ValueError, FileNotFoundError) as error:
            st.error(str(error))

render_footer()
