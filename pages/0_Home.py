"""BactoMut local Streamlit landing page."""

import streamlit as st

from src.reference import DATASET_LICENSE, DATASET_PAPER, DATASET_URL, REFERENCE_ID
from src.ui import apply_scientific_theme, render_footer, render_navigation

apply_scientific_theme()
render_navigation()

pages = st.session_state.get("bactomut_pages", {})
with st.container(key="bm-hero"):
    hero_copy, hero_visual = st.columns([1.08, 0.92], gap="medium")
    with hero_copy:
        st.markdown(
            """
            <div class="bm-hero-copy">
              <div class="bm-eyebrow">TEM-1 β-lactamase · Experimental fitness</div>
              <h1>Explore protein mutations through experimental data</h1>
              <p>Analyze a single amino-acid substitution and estimate its score against a real TEM-1 research dataset.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        button_left, button_right = st.columns(2, gap="small")
        with button_left:
            if st.button("Try prediction", type="primary", width="stretch"):
                if "Prediction" in pages:
                    st.switch_page(pages["Prediction"])
        with button_right:
            if st.button("Explore data", width="stretch"):
                if "Dataset" in pages:
                    st.switch_page(pages["Dataset"])
    with hero_visual:
        st.markdown(
            """
            <div class="bm-data-visual">
              <div class="bm-data-visual-top">
                <span class="bm-data-label">PUBLIC ASSAY DATASET</span>
                <span class="bm-data-tag">BLAT_ECOLX</span>
              </div>
              <div>
                <h3>TEM-1 variant fitness</h3>
                <p>Official dataset split · 5,468 measured records</p>
                <div class="bm-split-bar"><span></span><span></span><span></span></div>
                <div class="bm-split-legend">
                  <span><b>Train</b> 4,366</span>
                  <span><b>Valid</b> 575</span>
                  <span><b>Test</b> 527</span>
                </div>
              </div>
              <div class="bm-data-visual-top">
                <span class="bm-data-label">REFERENCE</span>
                <span class="bm-data-tag">UniProt P62593 · 286 aa</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="bm-section">
      <div class="bm-section-kicker">Real data · clear scope</div>
      <h2 class="bm-section-title">A focused workflow for mutation research</h2>
      <p class="bm-section-copy">Built around one public experimental assay, with sequence checks and transparent model evaluation at each step.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

stat_columns = st.columns(4)
for column, value, label in zip(
    stat_columns,
    ["5,468", "3", "286 aa", "1.0"],
    [
        "Published assay records",
        "Regression models",
        "TEM-1 reference length",
        "Dataset-defined WT score",
    ],
):
    with column:
        st.markdown(
            f'<div class="bm-stat"><b>{value}</b><span>{label}</span></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="bm-section">
      <div class="bm-section-kicker">How it works</div>
      <h2 class="bm-section-title">From sequence to an assay estimate</h2>
      <p class="bm-section-copy">A simple four-step process keeps the prediction tied to its experimental context.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
steps = st.columns(4, gap="medium")
for column, number, title, copy in zip(
    steps,
    ["01", "02", "03", "04"],
    ["Add a sequence", "Check the change", "Extract features", "Review the estimate"],
    [
        "Paste the TEM-1 reference or a single-mutant sequence from the dataset.",
        "Validate a substitution such as V42A against the reference residue.",
        "Calculate substitution, physicochemical, and local-context features.",
        "Compare model output with the dataset's normalized wild-type score.",
    ],
):
    with column:
        st.markdown(
            f'<div class="bm-step"><span class="num">{number} / WORKFLOW</span>'
            f"<h3>{title}</h3><p>{copy}</p></div>",
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="bm-section">
      <div class="bm-section-kicker">Research toolkit</div>
      <h2 class="bm-section-title">One project, four useful views</h2>
      <p class="bm-section-copy">Move from a mutation-level question to dataset context and model evaluation without losing the scientific details.</p>
    </div>
    <div class="bm-feature-panel">
    """,
    unsafe_allow_html=True,
)
feature_columns = st.columns(4, gap="medium")
for column, title, copy in zip(
    feature_columns,
    ["Mutation analysis", "Fitness prediction", "Dataset explorer", "Model evaluation"],
    [
        "Check notation, reference residues, and biological features.",
        "Estimate a single-mutant TEM-1 assay score with three models.",
        "Inspect real sequences, score distributions, and official splits.",
        "Compare MAE, RMSE, R², and Spearman on held-out records.",
    ],
):
    with column:
        st.markdown(
            f'<div class="bm-model-card"><h3>{title}</h3><p>{copy}</p></div>',
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="bm-section">
      <div class="bm-section-kicker">Study boundary</div>
      <h2 class="bm-section-title">A prediction, not an experiment</h2>
      <div class="bm-disclaimer">
        BactoMut estimates the TEM-1 deep-mutational-scanning score from the
        SaProtHub Dataset-BLAT_ECOLX assay. It does not predict bacterial survival,
        clinical pathogenicity, antibiotic resistance, or outcomes for other proteins.
        Model results are computational estimates—not experimentally confirmed measurements.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
source_left, source_right = st.columns([2, 1], vertical_alignment="center")
with source_left:
    st.markdown(
        f"**Dataset:** [{REFERENCE_ID}]({DATASET_URL})  \n"
        f"**Reference:** UniProt P62593 · **License:** {DATASET_LICENSE}  \n"
        f"**Related study:** {DATASET_PAPER}"
    )
with source_right:
    pages = st.session_state.get("bactomut_pages", {})
    if st.button("Create a research report", width="stretch") and "Report" in pages:
        st.switch_page(pages["Report"])

render_footer()
