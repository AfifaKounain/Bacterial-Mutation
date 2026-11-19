import streamlit as st

from src.feature_extraction import extract_features
from src.mutation_analysis import analyze_mutation
from src.ui import (
    apply_scientific_theme,
    render_footer,
    render_mutation_details,
    render_navigation,
    sequence_input,
)

apply_scientific_theme()
render_navigation()
st.title("Mutation analysis")
st.write("Validate one amino-acid substitution and inspect its sequence-derived features.")

sequence, _ = sequence_input("mutation_analysis")
notation = st.text_input("Mutation notation", value="V42A", placeholder="V42A")
if st.button("Analyze mutation", type="primary"):
    try:
        analysis = analyze_mutation(sequence, notation)
        details = {
            "original_aa": analysis.wild_type_residue,
            "mutant_aa": analysis.mutant_residue,
            "position": analysis.mutation.position,
        }
        st.success(analysis.message)
        render_mutation_details(details)
        features = extract_features(sequence, notation)
        st.markdown("### Biological and physicochemical features")
        st.dataframe(
            [
                {"Feature": "BLOSUM62 substitution score", "Value": f"{features['blosum62']:.3f}"},
                {"Feature": "Original amino-acid molecular weight (Da)", "Value": f"{features['original_molecular_weight']:.3f}"},
                {"Feature": "Mutant amino-acid molecular weight (Da)", "Value": f"{features['mutant_molecular_weight']:.3f}"},
                {"Feature": "Molecular-weight difference (Da)", "Value": f"{features['molecular_weight_difference']:+.3f}"},
                {"Feature": "Original hydrophobicity (Kyte-Doolittle)", "Value": f"{features['original_hydrophobicity']:+.3f}"},
                {"Feature": "Mutant hydrophobicity (Kyte-Doolittle)", "Value": f"{features['mutant_hydrophobicity']:+.3f}"},
                {"Feature": "Hydrophobicity difference (Kyte-Doolittle)", "Value": f"{features['hydrophobicity_difference']:+.3f}"},
                {"Feature": "Original charge (approx. pH 7)", "Value": f"{features['original_charge']:+.3f}"},
                {"Feature": "Mutant charge (approx. pH 7)", "Value": f"{features['mutant_charge']:+.3f}"},
                {"Feature": "Charge difference (approx. pH 7)", "Value": f"{features['charge_difference']:+.3f}"},
                {"Feature": "Reference local context", "Value": features["local_context"]},
                {"Feature": "Mutant local context", "Value": features["mutant_local_context"]},
            ],
            hide_index=True,
            width="stretch",
        )
    except ValueError as error:
        st.error(str(error))

render_footer()
