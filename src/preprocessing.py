"""Convert the published protein/label records into compatible mutation features."""

from __future__ import annotations

import pandas as pd

from src.dataset_loader import audit_dataset
from src.feature_extraction import FEATURE_COLUMNS, extract_features, model_feature_row
from src.mutation_analysis import derive_single_substitution
from src.reference import REFERENCE_SEQUENCE


def prepare_mutation_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Keep valid, single-substitution records and preserve their official stage."""
    audit = audit_dataset(frame)
    rows: list[dict[str, object]] = []
    rejected = {
        "missing": 0,
        "invalid_sequence": 0,
        "wild_type_reference": 0,
        "unsupported_variant": 0,
    }
    for record in frame.to_dict(orient="records"):
        if pd.isna(record["protein"]) or pd.isna(record["label"]) or pd.isna(record["stage"]):
            rejected["missing"] += 1
            continue
        try:
            sequence = str(record["protein"])
            mutation = derive_single_substitution(sequence, REFERENCE_SEQUENCE)
        except ValueError:
            rejected["invalid_sequence"] += 1
            continue
        if mutation is None:
            rejected[
                "wild_type_reference"
                if sequence == REFERENCE_SEQUENCE
                else "unsupported_variant"
            ] += 1
            continue
        features = extract_features(REFERENCE_SEQUENCE, mutation)
        rows.append(
            {
                **model_feature_row(features),
                "mutation": mutation,
                "label": float(record["label"]),
                "stage": str(record["stage"]).lower(),
                "protein": str(record["protein"]),
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("No valid single-substitution records were found in the dataset.")
    unexpected_stages = set(result["stage"]) - {"train", "valid", "test"}
    if unexpected_stages:
        raise ValueError(f"Unrecognized official dataset stages: {sorted(unexpected_stages)}.")
    audit_summary: dict[str, object] = {
        "source_rows": audit.rows,
        "stage_counts": audit.stage_counts,
        "missing_values": audit.missing_values,
        "duplicate_sequence_rows": audit.duplicate_sequence_rows,
        "duplicate_records": audit.duplicate_records,
        "sequence_lengths": audit.sequence_lengths,
        "wild_type_sequence_rows": audit.wild_type_sequence_rows,
        "wild_type_training_score_rows": audit.wild_type_training_score_rows,
        "wild_type_training_score_mean": audit.wild_type_training_score_mean,
        "wild_type_training_score_median": audit.wild_type_training_score_median,
        "wild_type_training_score_std": audit.wild_type_training_score_std,
        "wild_type_training_duplicate_records": audit.wild_type_training_duplicate_records,
        "wild_type_stage_counts": audit.wild_type_stage_counts,
        "target_min": audit.target_min,
        "target_max": audit.target_max,
        "target_mean": audit.target_mean,
        "retained_single_substitutions": len(result),
        "rejected": rejected,
        "feature_columns": FEATURE_COLUMNS,
    }
    return result, audit_summary
