"""Load and validate the public TEM-1 deep-mutational-scanning dataset."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
from datasets import DatasetDict, load_dataset

from src.reference import DATASET_ID, REFERENCE_SEQUENCE

REQUIRED_COLUMNS = {"protein", "label", "stage"}


@dataclass(frozen=True)
class DatasetAudit:
    rows: int
    missing_values: dict[str, int]
    duplicate_sequence_rows: int
    duplicate_records: int
    stage_counts: dict[str, int]
    target_min: float
    target_max: float
    target_mean: float
    sequence_lengths: dict[int, int]
    wild_type_sequence_rows: int
    wild_type_training_score_rows: int
    wild_type_training_score_mean: float | None
    wild_type_training_score_median: float | None
    wild_type_training_score_std: float | None
    wild_type_training_duplicate_records: int
    wild_type_stage_counts: dict[str, int]


def load_experimental_dataset() -> pd.DataFrame:
    """Load the dataset through Hugging Face Datasets and validate its observed schema."""
    loaded: DatasetDict = load_dataset(DATASET_ID, "dataset")
    if "train" not in loaded:
        raise ValueError("The published dataset does not expose its expected data split.")
    frame = loaded["train"].to_pandas()
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            "The published dataset schema changed; expected columns "
            f"{sorted(REQUIRED_COLUMNS)}, missing {sorted(missing_columns)}."
        )
    return frame.loc[:, ["protein", "label", "stage"]].copy()


def audit_dataset(frame: pd.DataFrame) -> DatasetAudit:
    """Summarize data quality without silently dropping incomplete records."""
    missing_values = {
        column: int(count)
        for column, count in frame[["protein", "label", "stage"]].isna().sum().items()
    }
    clean = frame.dropna(subset=["protein", "label", "stage"])
    if clean.empty:
        raise ValueError("The dataset contains no complete protein/label/stage records.")
    labels = pd.to_numeric(clean["label"], errors="coerce").dropna()
    if labels.empty:
        raise ValueError("The dataset has no numeric experimental fitness labels.")
    sequence_lengths = (
        clean["protein"].astype(str).str.len().value_counts().sort_index().to_dict()
    )
    wild_type = clean.loc[clean["protein"].astype(str) == REFERENCE_SEQUENCE]
    wild_type_train = wild_type.loc[wild_type["stage"].astype(str).str.lower() == "train"]
    wild_type_train_unique = wild_type_train.drop_duplicates(
        subset=["protein", "label", "stage"]
    )
    wild_type_labels = pd.to_numeric(wild_type_train_unique["label"], errors="coerce").dropna()
    return DatasetAudit(
        rows=len(frame),
        missing_values=missing_values,
        duplicate_sequence_rows=int(clean["protein"].duplicated(keep=False).sum()),
        duplicate_records=int(clean.duplicated(["protein", "label", "stage"]).sum()),
        stage_counts={
            str(stage): int(count)
            for stage, count in clean["stage"].value_counts().sort_index().items()
        },
        target_min=float(labels.min()),
        target_max=float(labels.max()),
        target_mean=float(labels.mean()),
        sequence_lengths={int(length): int(count) for length, count in sequence_lengths.items()},
        wild_type_sequence_rows=len(wild_type),
        wild_type_training_score_rows=len(wild_type_labels),
        wild_type_training_score_mean=(
            float(wild_type_labels.mean()) if not wild_type_labels.empty else None
        ),
        wild_type_training_score_median=(
            float(wild_type_labels.median()) if not wild_type_labels.empty else None
        ),
        wild_type_training_score_std=(
            float(wild_type_labels.std()) if len(wild_type_labels) > 1 else None
        ),
        wild_type_training_duplicate_records=len(wild_type_train) - len(wild_type_train_unique),
        wild_type_stage_counts={
            str(stage): int(count)
            for stage, count in wild_type["stage"].value_counts().sort_index().items()
        },
    )
