"""Fit, compare, evaluate, and persist the three requested regressors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

from src.dataset_loader import load_experimental_dataset
from src.feature_extraction import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from src.preprocessing import prepare_mutation_dataset
from src.reference import (
    DATASET_ID,
    DATASET_LICENSE,
    DATASET_URL,
    REFERENCE_ID,
    REFERENCE_SCORE,
    REFERENCE_SEQUENCE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIRECTORY = PROJECT_ROOT / "models"
PROCESSED_DIRECTORY = PROJECT_ROOT / "data" / "processed"
MODEL_FILES = {
    "Random Forest": "random_forest.pkl",
    "Decision Tree": "decision_tree.pkl",
    "Linear Regression": "linear_regression.pkl",
}


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def _new_models() -> dict[str, Any]:
    return {
        "Random Forest": RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
        "Decision Tree": DecisionTreeRegressor(random_state=42, min_samples_leaf=2),
        "Linear Regression": LinearRegression(),
    }


def _evaluation(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float | None]:
    correlation = spearmanr(y_true, y_pred)
    spearman = float(correlation.statistic)
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "spearman": spearman if np.isfinite(spearman) else None,
    }


def _split_without_sequence_leakage(
    variants: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], dict[str, int]]:
    grouped = (
        variants.groupby(["stage", "protein"], as_index=False, sort=False)
        .agg(label=("label", "mean"))
        .merge(
            variants[["stage", "protein"] + NUMERIC_FEATURES + CATEGORICAL_FEATURES]
            .drop_duplicates(["stage", "protein"]),
            on=["stage", "protein"],
            how="left",
            validate="one_to_one",
        )
    )
    train = grouped.loc[grouped["stage"] == "train"].copy()
    valid = grouped.loc[grouped["stage"] == "valid"].copy()
    test = grouped.loc[grouped["stage"] == "test"].copy()
    train_sequences = set(train["protein"])
    valid_sequences = set(valid["protein"]) - train_sequences
    valid = valid.loc[valid["protein"].isin(valid_sequences)].copy()
    test_sequences = set(test["protein"]) - train_sequences - valid_sequences
    test = test.loc[test["protein"].isin(test_sequences)].copy()
    excluded = {
        "duplicate_measurements_collapsed": int(len(variants) - len(grouped)),
        "validation_sequences_overlapping_training_excluded": int(
            len(grouped.loc[grouped["stage"] == "valid"]) - len(valid)
        ),
        "test_sequences_overlapping_training_or_validation_excluded": int(
            len(grouped.loc[grouped["stage"] == "test"]) - len(test)
        ),
    }
    splits = {"train": train, "valid": valid, "test": test}
    for name, split in splits.items():
        if len(split) < 2:
            raise ValueError(
                f"The {name} split has {len(split)} sequence-unique records after "
                "leakage checks; at least two are required for training and reliable "
                "regression evaluation."
            )
    return splits, excluded


def train_and_save_models() -> dict[str, Any]:
    """Train only on the official train stage and evaluate untouched official stages."""
    raw = load_experimental_dataset()
    variants, audit = prepare_mutation_dataset(raw)
    splits, excluded = _split_without_sequence_leakage(variants)
    PROCESSED_DIRECTORY.mkdir(parents=True, exist_ok=True)
    MODEL_DIRECTORY.mkdir(parents=True, exist_ok=True)
    variants.to_csv(PROCESSED_DIRECTORY / "processed_dataset.csv", index=False)
    models: dict[str, Any] = {}
    evaluation: dict[str, dict[str, dict[str, float | None]]] = {}
    predictions: dict[str, dict[str, list[float]]] = {}
    feature_importances: dict[str, dict[str, float]] = {}

    x_train = splits["train"][NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = splits["train"]["label"]
    for name, estimator in _new_models().items():
        pipeline = Pipeline(
            [
                ("preprocessor", _preprocessor()),
                ("regressor", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        models[name] = pipeline
        joblib.dump(
            {"pipeline": pipeline, "feature_columns": NUMERIC_FEATURES + CATEGORICAL_FEATURES},
            MODEL_DIRECTORY / MODEL_FILES[name],
        )
        evaluation[name] = {}
        predictions[name] = {}
        for split_name in ("valid", "test"):
            split = splits[split_name]
            x_split = split[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
            predicted = pipeline.predict(x_split)
            evaluation[name][split_name] = _evaluation(split["label"], predicted)
            if split_name == "test":
                predictions[name] = {
                    "actual": split["label"].astype(float).tolist(),
                    "predicted": [float(value) for value in predicted],
                }
        if name in {"Random Forest", "Decision Tree"}:
            transformed_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
            importances = pipeline.named_steps["regressor"].feature_importances_
            feature_importances[name] = {
                str(feature): float(value)
                for feature, value in zip(transformed_names, importances)
            }

    joblib.dump(
        models["Random Forest"].named_steps["preprocessor"],
        MODEL_DIRECTORY / "preprocessing.pkl",
    )
    metadata = {
        "dataset_id": DATASET_ID,
        "dataset_url": DATASET_URL,
        "dataset_license": DATASET_LICENSE,
        "reference_id": REFERENCE_ID,
        "target_definition": (
            "Experimental deep-mutational-scanning mutation-effect score; the dataset "
            "card defines 1 as the wild-type reference and scores greater than 1 as "
            "higher fitness than wild type."
        ),
        "wild_type_reference_score": REFERENCE_SCORE,
        "wild_type_record_observed": audit["wild_type_sequence_rows"] > 0,
        "wild_type_reference_observations": {
            "sequence_rows_by_official_stage": audit["wild_type_stage_counts"],
            "unique_training_score_rows": audit["wild_type_training_score_rows"],
            "training_score_mean": audit["wild_type_training_score_mean"],
            "training_score_median": audit["wild_type_training_score_median"],
            "training_score_standard_deviation": audit["wild_type_training_score_std"],
            "exact_duplicate_training_records_removed": audit[
                "wild_type_training_duplicate_records"
            ],
            "comparison_note": (
                "The primary comparison baseline remains the dataset-card normalized "
                "wild-type score of 1.0. The empirical mean is a secondary reference "
                "calculated from unique wild-type sequence records in the official "
                "training stage only."
            ),
        },
        "split_method": (
            "Official stage column preserved. Fit on train only; validation and test "
            "sequences overlapping an earlier stage are excluded from evaluation."
        ),
        "dataset_audit": audit,
        "leakage_exclusions": excluded,
        "records_by_split_after_deduplication": {
            name: int(len(split)) for name, split in splits.items()
        },
        "models": list(MODEL_FILES),
        "evaluation": evaluation,
        "test_predictions": predictions,
        "feature_importances": feature_importances,
    }
    metadata_path = MODEL_DIRECTORY / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    result = train_and_save_models()
    print(json.dumps(result["records_by_split_after_deduplication"], indent=2))
    print(json.dumps(result["evaluation"], indent=2))
