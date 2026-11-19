import streamlit as st

from src.dataset_loader import audit_dataset, load_experimental_dataset
from src.preprocessing import prepare_mutation_dataset
from src.reference import DATASET_LICENSE, DATASET_URL, REFERENCE_SEQUENCE
from src.ui import apply_scientific_theme, render_footer, render_navigation
from src.visualization import (
    fitness_distribution,
    mutation_position_distribution,
    substitution_distribution,
)

apply_scientific_theme()
render_navigation()
st.title("Dataset explorer")
st.markdown(
    f"Live source: [{DATASET_URL}]({DATASET_URL}) · License: {DATASET_LICENSE}. "
    "The published dataset exposes `protein`, `label`, and `stage`; the mutation is "
    "derived by comparison with the verified TEM-1 reference."
)
if st.button("Load / refresh public dataset", type="primary"):
    try:
        raw = load_experimental_dataset()
        variants, audit_summary = prepare_mutation_dataset(raw)
        audit = audit_dataset(raw)
        st.session_state["dataset_raw"] = raw
        st.session_state["dataset_variants"] = variants
        st.session_state["dataset_audit"] = audit_summary
        st.session_state["dataset_quality"] = {
            "rows": audit.rows,
            "missing_values": audit.missing_values,
            "duplicate_sequence_rows": audit.duplicate_sequence_rows,
            "duplicate_records": audit.duplicate_records,
            "stage_counts": audit.stage_counts,
            "target_min": audit.target_min,
            "target_max": audit.target_max,
            "target_mean": audit.target_mean,
            "sequence_lengths": audit.sequence_lengths,
            "wild_type_sequence_rows": audit.wild_type_sequence_rows,
            "wild_type_training_score_rows": audit.wild_type_training_score_rows,
            "wild_type_training_score_mean": audit.wild_type_training_score_mean,
            "wild_type_training_score_median": audit.wild_type_training_score_median,
            "wild_type_training_score_std": audit.wild_type_training_score_std,
            "wild_type_training_duplicate_records": audit.wild_type_training_duplicate_records,
            "wild_type_stage_counts": audit.wild_type_stage_counts,
        }
    except Exception as error:
        st.error(f"Dataset loading failed ({type(error).__name__}): {error}")

if "dataset_raw" not in st.session_state:
    st.info("Load the public dataset to view its observations and statistics.")
else:
    raw = st.session_state["dataset_raw"]
    variants = st.session_state["dataset_variants"]
    quality = st.session_state["dataset_quality"]
    first, second, third, fourth = st.columns(4)
    first.metric("Source records", f"{quality['rows']:,}")
    second.metric("Single substitutions retained", f"{len(variants):,}")
    third.metric("Target range", f"{quality['target_min']:.4f}–{quality['target_max']:.4f}")
    wild_type_mean = quality["wild_type_training_score_mean"]
    fourth.metric(
        "Observed WT mean (train)",
        f"{wild_type_mean:.4f}" if wild_type_mean is not None else "N/A",
    )
    st.markdown("### Dataset preview")
    st.dataframe(raw.head(20), hide_index=True, width="stretch")
    st.markdown("### Data quality")
    st.json(
        {
            "missing values by source column": quality["missing_values"],
            "duplicate-sequence rows": quality["duplicate_sequence_rows"],
            "exact duplicate records": quality["duplicate_records"],
            "official stage counts": quality["stage_counts"],
            "sequence lengths": quality["sequence_lengths"],
            "wild-type sequence rows by stage": quality["wild_type_stage_counts"],
            "unique wild-type training score rows": quality["wild_type_training_score_rows"],
            "wild-type training score median": quality["wild_type_training_score_median"],
            "wild-type training score standard deviation": quality["wild_type_training_score_std"],
            "duplicate wild-type training records removed from baseline": quality[
                "wild_type_training_duplicate_records"
            ],
            "single-substitution preprocessing": st.session_state["dataset_audit"]["rejected"],
        }
    )
    st.plotly_chart(fitness_distribution(raw), width="stretch")
    st.plotly_chart(mutation_position_distribution(variants), width="stretch")
    st.plotly_chart(substitution_distribution(variants), width="stretch")
    st.caption(
        f"Reference: UniProt P62593, {len(REFERENCE_SEQUENCE)} residues. Figures show "
        "observed assay records only; no synthetic observations are added. The empirical "
        "wild-type mean is secondary to the dataset-card normalized reference score of 1."
    )

render_footer()
