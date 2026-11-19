import pandas as pd
import pytest

from src.feature_extraction import extract_features, model_feature_row
from src.model_training import _split_without_sequence_leakage
from src.reference import REFERENCE_SEQUENCE


def _record(mutation, stage, label):
    features = model_feature_row(extract_features(REFERENCE_SEQUENCE, mutation))
    mutant = mutation[-1]
    sequence = REFERENCE_SEQUENCE[:0] + mutant + REFERENCE_SEQUENCE[1:]
    return {
        **features,
        "mutation": mutation,
        "stage": stage,
        "label": label,
        "protein": sequence,
    }


def test_collapses_repeated_measurements_and_excludes_cross_stage_overlap():
    rows = [
        _record("M1C", "train", 0.1),
        _record("M1C", "train", 0.3),
        _record("M1A", "train", 0.4),
        _record("M1D", "train", 0.5),
        _record("M1C", "valid", 0.2),
        _record("M1E", "valid", 0.6),
        _record("M1F", "valid", 0.7),
        _record("M1E", "test", 0.4),
        _record("M1G", "test", 0.8),
        _record("M1H", "test", 0.9),
    ]
    splits, excluded = _split_without_sequence_leakage(pd.DataFrame(rows))
    c_variant = "C" + REFERENCE_SEQUENCE[1:]
    assert splits["train"].loc[splits["train"]["protein"] == c_variant, "label"].item() == 0.2
    assert len(splits["valid"]) == 2
    assert len(splits["test"]) == 2
    assert excluded == {
        "duplicate_measurements_collapsed": 1,
        "validation_sequences_overlapping_training_excluded": 1,
        "test_sequences_overlapping_training_or_validation_excluded": 1,
    }


def test_rejects_too_small_official_split():
    rows = [
        _record("M1C", "train", 0.1),
        _record("M1A", "train", 0.2),
        _record("M1D", "valid", 0.3),
        _record("M1E", "valid", 0.4),
        _record("M1F", "test", 0.5),
    ]
    with pytest.raises(ValueError, match="at least two"):
        _split_without_sequence_leakage(pd.DataFrame(rows))
