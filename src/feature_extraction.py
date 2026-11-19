"""Mutation feature extraction shared by training and interactive prediction."""

from __future__ import annotations

from typing import Any

from Bio.Align import substitution_matrices
from Bio.SeqUtils import molecular_weight

from src.mutation_analysis import analyze_mutation, validate_protein_sequence

_BLOSUM62 = substitution_matrices.load("BLOSUM62")
_HYDROPATHY = {
    "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
    "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
    "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
    "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
}
_CHARGE_AT_PH7 = {
    "A": 0.0, "C": 0.0, "D": -1.0, "E": -1.0, "F": 0.0,
    "G": 0.0, "H": 0.1, "I": 0.0, "K": 1.0, "L": 0.0,
    "M": 0.0, "N": 0.0, "P": 0.0, "Q": 0.0, "R": 1.0,
    "S": 0.0, "T": 0.0, "V": 0.0, "W": 0.0, "Y": 0.0,
}
_MOLECULAR_WEIGHT = {
    amino_acid: molecular_weight(amino_acid, seq_type="protein")
    for amino_acid in _HYDROPATHY
}

NUMERIC_FEATURES = [
    "position",
    "blosum62",
    "original_molecular_weight",
    "mutant_molecular_weight",
    "molecular_weight_difference",
    "original_hydrophobicity",
    "mutant_hydrophobicity",
    "hydrophobicity_difference",
    "original_charge",
    "mutant_charge",
    "charge_difference",
]
CATEGORICAL_FEATURES = [
    "original_aa",
    "mutant_aa",
    "context_left",
    "context_right",
    "local_context",
]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def extract_features(sequence: str, notation: str, context_radius: int = 2) -> dict[str, Any]:
    protein = validate_protein_sequence(sequence)
    analysis = analyze_mutation(protein, notation)
    mutation = analysis.mutation
    index = mutation.position - 1
    start = max(0, index - context_radius)
    end = min(len(protein), index + context_radius + 1)
    context = protein[start:end]
    position_in_context = index - start
    mutant_context = context[:position_in_context] + mutation.mutant + context[position_in_context + 1:]
    left = protein[index - 1] if index > 0 else "TERMINUS"
    right = protein[index + 1] if index + 1 < len(protein) else "TERMINUS"
    original_weight = _MOLECULAR_WEIGHT[mutation.original]
    mutant_weight = _MOLECULAR_WEIGHT[mutation.mutant]
    return {
        "mutation": mutation.notation,
        "position": mutation.position,
        "original_aa": mutation.original,
        "mutant_aa": mutation.mutant,
        "blosum62": float(_BLOSUM62[mutation.original, mutation.mutant]),
        "original_molecular_weight": float(original_weight),
        "mutant_molecular_weight": float(mutant_weight),
        "molecular_weight_difference": float(mutant_weight - original_weight),
        "original_hydrophobicity": _HYDROPATHY[mutation.original],
        "mutant_hydrophobicity": _HYDROPATHY[mutation.mutant],
        "hydrophobicity_difference": _HYDROPATHY[mutation.mutant] - _HYDROPATHY[mutation.original],
        "original_charge": _CHARGE_AT_PH7[mutation.original],
        "mutant_charge": _CHARGE_AT_PH7[mutation.mutant],
        "charge_difference": _CHARGE_AT_PH7[mutation.mutant] - _CHARGE_AT_PH7[mutation.original],
        "local_context": context,
        "mutant_local_context": mutant_context,
        "context_left": left,
        "context_right": right,
    }


def model_feature_row(features: dict[str, Any]) -> dict[str, Any]:
    """Select the fixed, target-independent feature schema used by every model."""
    return {name: features[name] for name in FEATURE_COLUMNS}
