import streamlit as st

from src.prediction import load_model_metadata
from src.ui import apply_scientific_theme, render_footer, render_navigation
from src.visualization import (
    actual_vs_predicted_figure,
    feature_importance_figure,
    model_comparison_plot,
)

apply_scientific_theme()
render_navigation()
st.title("Model performance")
st.write(
    "Metrics below are computed from genuine labels in the official validation and "
    "test stages. Duplicate sequences are excluded from later stages when they "
    "overlap earlier stages."
)
try:
    metadata = load_model_metadata()
except FileNotFoundError as error:
    st.warning(str(error))
else:
    metrics = metadata["evaluation"]
    st.plotly_chart(model_comparison_plot(metrics), width="stretch")
    model_name = st.selectbox("Inspect model", list(metrics))
    metric_rows = []
    for split_name, values in metrics[model_name].items():
        metric_rows.append(
            {
                "Official split": split_name,
                "MAE": values["mae"],
                "RMSE": values["rmse"],
                "R²": values["r2"],
                "Spearman rank correlation": values["spearman"],
            }
        )
    st.dataframe(metric_rows, hide_index=True, width="stretch")
    predictions = metadata["test_predictions"][model_name]
    st.pyplot(
        actual_vs_predicted_figure(predictions["actual"], predictions["predicted"]),
        width="stretch",
    )
    if model_name in metadata.get("feature_importances", {}):
        st.pyplot(
            feature_importance_figure(metadata["feature_importances"][model_name]),
            width="stretch",
        )
    st.markdown("### Evaluation protocol")
    st.json(
        {
            "training and evaluation split sizes": metadata["records_by_split_after_deduplication"],
            "duplicate and leakage handling": metadata["leakage_exclusions"],
            "protocol": metadata["split_method"],
        }
    )
    st.caption(
        "Feature importance is impurity-based for the tree models and is not causal. "
        "No model accuracy or performance is hardcoded."
    )

render_footer()
