"""Load trained estimators and produce reference-compatible mutation estimates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.feature_extraction import CATEGORICAL_FEATURES, NUMERIC_FEATURES, extract_features, model_feature_row
from src.mutation_analysis import (
    analyze_mutation,
    derive_single_substitution,
    derive_single_substitution_from_reference_fragment,
    parse_mutation,
    validate_protein_sequence,
)
from src.model_training import MODEL_DIRECTORY, MODEL_FILES
from src.reference import REFERENCE_SCORE, REFERENCE_SEQUENCE


def load_model_metadata(model_directory: Path = MODEL_DIRECTORY) -> dict[str, Any]:
    path = model_directory / "model_metadata.json"
    if not path.is_file():
        raise FileNotFoundError(
            "Trained model metadata is missing. From the project folder run "
            "`python -m src.model_training` to download the dataset and train the models."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def available_models(model_directory: Path = MODEL_DIRECTORY) -> list[str]:
    return [
        name
        for name, filename in MODEL_FILES.items()
        if (model_directory / filename).is_file()
    ]


def predict_mutation(
    sequence: str,
    notation: str | None,
    model_name: str,
    model_directory: Path = MODEL_DIRECTORY,
) -> dict[str, Any]:
    protein = validate_protein_sequence(sequence)
    entered_notation = (notation or "").strip()
    if protein == REFERENCE_SEQUENCE:
        if not entered_notation:
            raise ValueError(
                "Enter a mutation such as V42A, or provide a single-mutant TEM-1 "
                "dataset sequence and leave the mutation field blank to infer it."
            )
        resolved_notation = parse_mutation(entered_notation).notation
        input_sequence_type = "TEM-1 wild-type reference"
    else:
        resolved_notation = derive_single_substitution(protein, REFERENCE_SEQUENCE)
        fragment_coordinates = None
        if resolved_notation is None:
            fragment_match = derive_single_substitution_from_reference_fragment(
                protein, REFERENCE_SEQUENCE
            )
            if fragment_match is not None:
                (
                    resolved_notation,
                    fragment_start,
                    fragment_end,
                ) = fragment_match
                fragment_coordinates = (fragment_start, fragment_end)
        if resolved_notation is None:
            raise ValueError(
                "Prediction requires the TEM-1 reference or a single-mutant TEM-1 "
                "sequence/contiguous fragment that aligns uniquely to it and differs "
                "at exactly one residue. Other proteins and multi-mutant sequences "
                "are not supported by this assay model."
            )
        input_sequence_type = (
            "single-mutant TEM-1 fragment "
            f"(reference residues {fragment_coordinates[0]}–{fragment_coordinates[1]})"
            if fragment_coordinates is not None
            else "single-mutant TEM-1 sequence"
        )
        if entered_notation:
            supplied_notation = parse_mutation(entered_notation).notation
            if supplied_notation != resolved_notation:
                raise ValueError(
                    f"The supplied sequence contains mutation {resolved_notation}, "
                    f"but the entered notation is {supplied_notation}. The dataset's "
                    "mutation notation describes the change from wild type to variant."
                )
    analysis = analyze_mutation(REFERENCE_SEQUENCE, resolved_notation)
    if model_name not in MODEL_FILES:
        raise ValueError(f"Unknown model: {model_name}.")
    path = model_directory / MODEL_FILES[model_name]
    if not path.is_file():
        raise FileNotFoundError(
            f"The {model_name} model is not trained. Run `python -m src.model_training`."
        )
    model_artifact = joblib.load(path)
    features = extract_features(REFERENCE_SEQUENCE, analysis.mutation.notation)
    feature_values = model_feature_row(features)
    feature_order = model_artifact.get(
        "feature_columns", NUMERIC_FEATURES + CATEGORICAL_FEATURES
    )
    prediction = float(
        model_artifact["pipeline"].predict(
            pd.DataFrame(
                [{column: feature_values[column] for column in feature_order}],
                columns=feature_order,
            )
        )[0]
    )
    metadata_path = model_directory / "model_metadata.json"
    wild_type_observations = {}
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        wild_type_observations = metadata.get("wild_type_reference_observations", {})
    observed_mean = wild_type_observations.get("training_score_mean")
    return {
        "mutation": analysis.mutation.notation,
        "input_sequence_type": input_sequence_type,
        "original_aa": analysis.wild_type_residue,
        "mutant_aa": analysis.mutant_residue,
        "position": analysis.mutation.position,
        "features": features,
        "predicted_fitness": prediction,
        "wild_type_reference_score": REFERENCE_SCORE,
        "difference_from_reference": prediction - REFERENCE_SCORE,
        "wild_type_observed_training_mean": observed_mean,
        "wild_type_observed_training_std": wild_type_observations.get(
            "training_score_standard_deviation"
        ),
        "wild_type_observed_training_count": wild_type_observations.get(
            "unique_training_score_rows", 0
        ),
        "difference_from_observed_wild_type_mean": (
            prediction - float(observed_mean) if observed_mean is not None else None
        ),
        "reference_score_note": (
            "The dataset card defines 1.0 as wild type. Wild-type sequence score "
            "replicates are also present; the empirical mean shown is calculated from "
            "unique official training-stage records only."
        ),
        "model": model_name,
    }
