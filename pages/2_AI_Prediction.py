import streamlit as st

from src.prediction import available_models, load_model_metadata, predict_mutation
from src.ui import (
    apply_scientific_theme,
    render_footer,
    render_mutation_details,
    render_navigation,
    sequence_input,
)
from src.visualization import wild_type_comparison_plot

apply_scientific_theme()
render_navigation()
st.title("AI fitness-score prediction")
st.caption(
    "Enter the TEM-1 reference and a mutation, or paste a single-mutant TEM-1 "
    "sequence (including a contiguous fragment) and leave the mutation blank for "
    "automatic inference. This "
    "estimates the experimental score; it is not an experiment or a general "
    "biological-impact classification."
)
models = available_models()
if not models:
    st.warning(
        "No trained model files are available. In a terminal opened in the project "
        "folder, run `python -m src.model_training` while connected to the internet."
    )
else:
    sequence, _ = sequence_input("ai_prediction")
    notation = st.text_input(
        "Mutation from wild type to variant (optional for a single-mutant sequence)",
        value="",
        placeholder="V42A",
        help=(
            "For the TEM-1 reference sequence, enter notation such as V42A. If the "
            "sequence above is a single-mutant TEM-1 variant or contiguous reference "
            "fragment, leave this blank and the substitution will be inferred."
        ),
    )
    model_name = st.selectbox("Trained model", models)
    if st.button("Predict experimental fitness score", type="primary"):
        try:
            result = predict_mutation(sequence, notation, model_name)
            st.session_state["prediction_result"] = result
            metadata = load_model_metadata()
            st.caption(
                f"Input: {result['input_sequence_type']}. "
                f"Analyzed substitution: {result['mutation']}."
            )
            render_mutation_details(result)
            first, second, third = st.columns(3)
            first.metric("Predicted score", f"{result['predicted_fitness']:.4f}")
            second.metric(
                "Dataset-defined WT reference",
                f"{result['wild_type_reference_score']:.2f}",
                help=result["reference_score_note"],
            )
            third.metric("Difference from reference", f"{result['difference_from_reference']:+.4f}")
            observed_mean = result["wild_type_observed_training_mean"]
            if observed_mean is not None:
                st.metric(
                    f"Observed WT mean (train n={result['wild_type_observed_training_count']}; Δ=prediction−mean)",
                    f"{observed_mean:.4f}",
                    delta=f"{result['difference_from_observed_wild_type_mean']:+.4f}",
                    help=(
                        "Secondary empirical comparison from unique reference-sequence "
                        f"training records; SD={result['wild_type_observed_training_std']:.4f}. "
                        "The dataset-card normalized wild-type reference remains 1.0."
                    ),
                )
            st.write(
                f"**Interpretation:** the dataset card defines 1.0 as wild type and "
                f"scores above 1.0 as higher assay fitness. This model estimates "
                f"{result['predicted_fitness']:.4f}; it does not establish a universal "
                "beneficial/harmful classification."
            )
            st.caption(result["reference_score_note"])
            st.plotly_chart(wild_type_comparison_plot(result), width="stretch")
            st.caption(
                f"Selected model: {model_name}. Metrics are evaluated on the "
                f"sequence-deduplicated official test split: "
                f"{metadata['evaluation'][model_name]['test']}."
            )
            st.info("This computational estimate is not experimentally confirmed.")
        except (ValueError, FileNotFoundError) as error:
            st.error(str(error))

render_footer()
