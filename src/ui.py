"""Reusable Streamlit styling, sequence input, and footer helpers."""

from __future__ import annotations

import hashlib

import streamlit as st

from src.mutation_analysis import parse_fasta
from src.reference import REFERENCE_SEQUENCE


def apply_scientific_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #ffffff; color: #172b4d; }
        h1, h2, h3 { color: #102a56; letter-spacing: -.025em; }
        [data-testid="stMainBlockContainer"] {
            max-width: 1240px; padding: 1rem clamp(1rem, 3vw, 2rem) 2rem;
        }
        [class*="st-key-bm-navigation"] {
            border: 1px solid #e6edf5; border-radius: 14px; padding: .35rem .65rem;
            margin-bottom: 1.15rem; background: rgba(255,255,255,.96);
            box-shadow: 0 4px 18px rgba(20,54,94,.045);
        }
        .bm-brand {
            display: flex; align-items: center; gap: .45rem; color: #102a56;
            font-weight: 750; font-size: 1rem; letter-spacing: -.04em; white-space: nowrap;
        }
        .bm-brand-ai {
            color: #2862b9; background: #eaf3ff; border: 1px solid #dceaff;
            border-radius: 6px; padding: .13rem .34rem; font-size: .62rem;
            letter-spacing: .06em; font-weight: 800;
        }
        [class*="st-key-bm-navigation"] [data-testid="stBaseButton-secondary"] {
            border: 1px solid transparent; border-radius: 9px; background: transparent;
            box-shadow: none; color: #52657b; font-size: .76rem; font-weight: 600;
            padding: .35rem .15rem; white-space: nowrap; transition: background .15s, color .15s;
        }
        [class*="st-key-bm-navigation"] [data-testid="stBaseButton-secondary"]:hover {
            border-color: #e6eefb; background: #f5f8ff; color: #245fd1;
        }
        div[data-testid="stPageLink"] a {
            border: 1px solid #dce8f3; background: #fff; border-radius: 10px;
            box-shadow: 0 3px 12px rgba(27,65,112,.05); padding: .5rem .85rem;
            justify-content: center; transition: all .15s ease;
        }
        div[data-testid="stPageLink"] a:hover {
            border-color: #9dc3ff; background: #f5f9ff; color: #245fd1;
        }
        [data-testid="stMetric"] {
            background: #ffffff; border: 1px solid #dceaf3; padding: 1rem;
            border-radius: 0.8rem; box-shadow: 0 2px 8px rgba(19,59,92,.04);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff; border-radius: .8rem;
        }
        [class*="st-key-bm-hero"] {
            overflow: hidden; border-radius: 22px; padding: clamp(1.1rem, 3vw, 2.4rem);
            background: radial-gradient(ellipse at 78% 42%, rgba(166,217,255,.38), transparent 40%),
                        radial-gradient(ellipse at 98% 90%, rgba(197,189,255,.2), transparent 36%),
                        linear-gradient(130deg, #fff 12%, #f5faff 72%, #f8f6ff);
            border: 1px solid #e9f1f8;
        }
        .bm-eyebrow { color: #3478f6; text-transform: uppercase; letter-spacing: .1em; font-weight: 700; font-size: .66rem; }
        .bm-hero-copy h1 { font-size: clamp(2rem, 3.6vw, 3.1rem); line-height: 1.04; letter-spacing: -.055em; margin: .55rem 0 .75rem; }
        .bm-hero-copy p { color: #596c83; font-size: .94rem; line-height: 1.6; max-width: 490px; margin-bottom: .55rem; }
        .bm-data-visual {
            min-height: 218px; height: 100%; padding: 1.15rem; border: 1px solid #deebf5;
            border-radius: 16px; background: rgba(255,255,255,.82);
            box-shadow: 0 12px 32px rgba(34,83,130,.07);
            display: flex; flex-direction: column; justify-content: space-between;
        }
        .bm-data-visual-top { display:flex; align-items:center; justify-content:space-between; gap:.5rem; }
        .bm-data-label { color:#718198; font-size:.62rem; font-weight:750; letter-spacing:.12em; }
        .bm-data-tag { color:#2862b9; background:#edf5ff; border-radius:99px; padding:.3rem .55rem; font-size:.64rem; font-weight:700; white-space:nowrap; }
        .bm-data-visual h3 { font-size:1.04rem; margin:.8rem 0 .25rem; }
        .bm-data-visual p { color:#718198; font-size:.76rem; line-height:1.5; margin:0; }
        .bm-split-bar { display:flex; height:9px; overflow:hidden; border-radius:99px; margin:1.1rem 0 .65rem; background:#e8eef5; }
        .bm-split-bar span:nth-child(1) { width:79.85%; background:#3478f6; }
        .bm-split-bar span:nth-child(2) { width:10.52%; background:#75b5eb; }
        .bm-split-bar span:nth-child(3) { width:9.63%; background:#b9a8f4; }
        .bm-split-legend { display:flex; justify-content:space-between; gap:.3rem; color:#667990; font-size:.62rem; }
        .bm-split-legend b { color:#243b5a; font-weight:700; }
        .bm-section { padding: 2.35rem .25rem .4rem; }
        .bm-section-kicker { color: #3478f6; text-transform: uppercase; letter-spacing: .14em; font-size: .7rem; font-weight: 750; text-align: center; }
        .bm-section-title { color: #102a56; text-align: center; font-size: clamp(1.5rem, 2.6vw, 2.1rem); letter-spacing: -.045em; margin: .45rem auto; }
        .bm-section-copy { color: #708197; text-align: center; max-width: 690px; margin: .35rem auto 1.2rem; line-height: 1.6; }
        .bm-stat { text-align: center; padding: .85rem .55rem; border: 1px solid #e6eef5; border-radius: 14px; background: #fff; }
        .bm-stat b { display:block; font-size: 1.3rem; color:#102a56; }
        .bm-stat span { display:block; color:#718198; font-size:.78rem; margin-top:.3rem; }
        .bm-step { height:100%; min-height:145px; padding:1.1rem; border-radius:16px; border:1px solid #e5edf5; background:linear-gradient(150deg,#fff,#f8fbff); }
        .bm-step .num { color:#3478f6; font-size:.76rem; font-weight:750; letter-spacing:.1em; }
        .bm-step h3 { font-size:1.04rem; margin:.6rem 0 .4rem; }
        .bm-step p { color:#718198; font-size:.88rem; line-height:1.65; }
        .bm-feature-panel { border-radius:20px; padding:clamp(1rem,3vw,2rem); background:linear-gradient(145deg,#eff8ff,#f7f6ff); border:1px solid #e7f0f8; }
        .bm-model-card { min-height:135px; padding:1.1rem; border-radius:16px; background:rgba(255,255,255,.82); border:1px solid #e4edf5; }
        .bm-model-card h3 { font-size:1rem; margin:.1rem 0 .45rem; }
        .bm-model-card p { color:#718198; font-size:.83rem; line-height:1.6; margin-bottom:0; }
        .bm-disclaimer { border-left:3px solid #6da7ff; border-radius:0 12px 12px 0; padding:1rem 1.1rem; background:#f3f8ff; color:#506580; line-height:1.7; }
        @media (max-width: 900px) {
            .bm-hero-copy h1 { font-size: clamp(1.8rem, 4vw, 2.35rem); }
            .bm-data-visual { min-height: 200px; padding: .9rem; }
            [class*="st-key-bm-navigation"] [data-testid="stBaseButton-secondary"] { font-size: .69rem; }
        }
        @media (max-width: 640px) {
            [class*="st-key-bm-navigation"] { margin-bottom: .55rem; }
            .bm-brand { font-size: .78rem; }
            [class*="st-key-bm-navigation"] [data-testid="stBaseButton-secondary"] { font-size: .62rem; padding-left: 0; padding-right: 0; }
            [class*="st-key-bm-hero"] { padding: 1rem; border-radius: 16px; }
            .bm-hero-copy h1 { font-size: 1.85rem; }
            .bm-data-visual { min-height: 185px; }
            .bm-section { padding-top: 1.8rem; }
        }
        .bactomut-footer {
            margin-top: 3rem; padding: 1rem .5rem; border-top: 1px solid #dce5eb;
            background: #f1f5f8; color: #647482; text-align: center;
            font-size: .82rem; line-height: 1.65;
        }
        .bactomut-footer strong { color: #35566d; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_navigation() -> None:
    pages = st.session_state.get("bactomut_pages", {})
    with st.container(key="bm-navigation"):
        brand, home, analysis, prediction, dataset, models, report = st.columns(
            [1.25, 0.65, 0.75, 0.7, 0.6, 0.7, 0.65],
            vertical_alignment="center",
        )
        with brand:
            st.markdown(
                '<div class="bm-brand">BactoMut</div>',
                unsafe_allow_html=True,
            )
        route_name = st.context.url.rstrip("/").rsplit("/", 1)[-1]
        active_page = {
            "Mutation_Analysis": "analysis",
            "AI_Prediction": "prediction",
            "Dataset_Explorer": "dataset",
            "Model_Performance": "models",
            "Research_Report": "report",
        }.get(route_name, "home")
        st.markdown(
            f"""
            <style>
            [class*="st-key-bm-nav-{active_page}"] [data-testid="stBaseButton-secondary"] {{
                color: #245fd1; background: #edf4ff; border-color: #e1ecff;
                font-weight: 700;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        for column, key, label in [
            (home, "Home", "Home"),
            (analysis, "Analysis", "Analyze"),
            (prediction, "Prediction", "Predict"),
            (dataset, "Dataset", "Data"),
            (models, "Models", "Models"),
            (report, "Report", "Report"),
        ]:
            with column:
                if st.button(
                    label,
                    key=f"bm-nav-{key.lower()}",
                    width="stretch",
                ):
                    if key in pages:
                        st.switch_page(pages[key])


def render_footer() -> None:
    st.markdown(
        """
        <div class="bactomut-footer">
          <strong>Developed by Afifa Kounain</strong><br>
          BactoMut – Bacterial Protein Mutation Impact Prediction System
        </div>
        """,
        unsafe_allow_html=True,
    )


def sequence_input(key: str = "sequence") -> tuple[str, str]:
    st.info(
        "For fitness prediction: keep the prefilled TEM-1 reference and enter a "
        "matching mutation (for example `V42A`), OR paste a single-mutant TEM-1 "
        "sequence or contiguous fragment and leave the mutation field blank. The "
        "app will align a fragment to the reference and infer the substitution. "
        "Multi-mutant and non-TEM-1 sequences are not supported by this assay model.",
    )
    uploaded = st.file_uploader(
        "Optional: upload a single-record FASTA file",
        type=["fa", "fasta", "faa", "txt"],
        key=f"{key}_fasta",
    )
    initial = REFERENCE_SEQUENCE
    description = "TEM-1 reference (UniProt P62593)"
    sequence_key = f"{key}_sequence"
    upload_key = f"{key}_fasta_hash"
    sequence_loaded = False
    if uploaded is not None:
        uploaded_content = uploaded.getvalue()
        upload_hash = hashlib.sha256(uploaded_content).hexdigest()
        try:
            description, initial = parse_fasta(uploaded_content.decode("utf-8"))
            sequence_loaded = True
        except (UnicodeDecodeError, ValueError) as error:
            st.error(f"Invalid FASTA input: {error}")
            initial = ""
        if st.session_state.get(upload_key) != upload_hash:
            st.session_state[sequence_key] = initial
            st.session_state[upload_key] = upload_hash
        if sequence_loaded:
            st.success(
                "FASTA sequence loaded below. It is ready to use; you do not need "
                "to paste it again."
            )
    elif st.session_state.get(upload_key) is not None:
        st.session_state[sequence_key] = initial
        st.session_state[upload_key] = None

    st.session_state.setdefault(sequence_key, initial)
    sequence = st.text_area(
        "Protein sequence (loaded from FASTA)"
        if sequence_loaded
        else "Protein sequence",
        height=120,
        help=(
            "This sequence was loaded from your FASTA file. You can edit it here if needed."
            if sequence_loaded
            else "Paste a single-letter amino-acid sequence, or use the FASTA upload above."
        ),
        key=sequence_key,
    )
    return sequence, description


def render_mutation_details(result: dict[str, object]) -> None:
    first, second, third = st.columns(3)
    first.metric("Original residue", str(result["original_aa"]))
    second.metric("Mutant residue", str(result["mutant_aa"]))
    third.metric("Position", str(result["position"]))
