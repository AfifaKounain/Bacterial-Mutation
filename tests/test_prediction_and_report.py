import joblib
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.feature_extraction import CATEGORICAL_FEATURES, NUMERIC_FEATURES, extract_features, model_feature_row
from src.prediction import load_model_metadata, predict_mutation
from src.reference import REFERENCE_SEQUENCE
from src.report_generator import generate_pdf_report


def test_missing_model_and_metadata_are_explicit(tmp_path):
    with pytest.raises(FileNotFoundError, match="model is not trained"):
        predict_mutation(REFERENCE_SEQUENCE, "M1C", "Random Forest", tmp_path)
    with pytest.raises(FileNotFoundError, match="metadata is missing"):
        load_model_metadata(tmp_path)


def test_loads_a_model_and_generates_prediction(tmp_path):
    features = model_feature_row(extract_features(REFERENCE_SEQUENCE, "M1C"))
    transformer = ColumnTransformer(
        [
            ("numeric", "passthrough", NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    pipeline = Pipeline(
        [
            ("preprocessor", transformer),
            ("regressor", DummyRegressor(strategy="constant", constant=0.75)),
        ]
    )
    pipeline.fit(pd.DataFrame([features, features]), [0.75, 0.75])
    joblib.dump(
        {"pipeline": pipeline, "feature_columns": NUMERIC_FEATURES + CATEGORICAL_FEATURES},
        tmp_path / "random_forest.pkl",
    )
    prediction = predict_mutation(REFERENCE_SEQUENCE, "M1C", "Random Forest", tmp_path)
    assert prediction["predicted_fitness"] == pytest.approx(0.75)
    assert prediction["wild_type_reference_score"] == 1.0
    assert prediction["difference_from_reference"] == pytest.approx(-0.25)
    assert prediction["input_sequence_type"] == "TEM-1 wild-type reference"

    variant_sequence = "C" + REFERENCE_SEQUENCE[1:]
    inferred = predict_mutation(variant_sequence, "", "Random Forest", tmp_path)
    assert inferred["mutation"] == "M1C"
    assert inferred["input_sequence_type"] == "single-mutant TEM-1 sequence"
    assert inferred["features"]["position"] == 1
    explicit = predict_mutation(variant_sequence, "M1C", "Random Forest", tmp_path)
    assert explicit["predicted_fitness"] == pytest.approx(0.75)
    with pytest.raises(ValueError, match="sequence contains mutation M1C"):
        predict_mutation(variant_sequence, "M1A", "Random Forest", tmp_path)
    with pytest.raises(ValueError, match="single-mutant TEM-1 sequence/contiguous fragment"):
        predict_mutation("ACDE", "A1V", "Random Forest", tmp_path)
    with pytest.raises(ValueError, match="single-mutant TEM-1 sequence/contiguous fragment"):
        predict_mutation(
            "C" + "A" + REFERENCE_SEQUENCE[2:], "", "Random Forest", tmp_path
        )
    with pytest.raises(ValueError, match="leave the mutation field blank"):
        predict_mutation(REFERENCE_SEQUENCE, "", "Random Forest", tmp_path)

    fragment = REFERENCE_SEQUENCE[23:179] + "T" + REFERENCE_SEQUENCE[180:]
    assert len(fragment) == 263
    inferred_fragment = predict_mutation(fragment, "", "Random Forest", tmp_path)
    assert inferred_fragment["mutation"] == "M180T"
    assert inferred_fragment["position"] == 180
    assert inferred_fragment["input_sequence_type"] == (
        "single-mutant TEM-1 fragment (reference residues 24–286)"
    )
    assert inferred_fragment["predicted_fitness"] == pytest.approx(0.75)
    explicit_fragment = predict_mutation(fragment, "M180T", "Random Forest", tmp_path)
    assert explicit_fragment["mutation"] == "M180T"
    with pytest.raises(ValueError, match="sequence contains mutation M180T"):
        predict_mutation(fragment, "M180A", "Random Forest", tmp_path)


def test_generates_pdf_report():
    report = {
        "mutation": "M1C",
        "model": "Random Forest",
        "features": extract_features(REFERENCE_SEQUENCE, "M1C"),
        "predicted_fitness": 0.75,
        "wild_type_reference_score": 1.0,
        "difference_from_reference": -0.25,
        "evaluation_metrics": {"test": {"mae": 0.2, "rmse": 0.3, "r2": 0.4, "spearman": 0.5}},
    }
    pdf = generate_pdf_report(report)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
    with pytest.raises(ValueError, match="incomplete"):
        generate_pdf_report({"mutation": "M1C"})
