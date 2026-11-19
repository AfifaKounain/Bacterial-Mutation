import pandas as pd
import pytest

import src.dataset_loader as dataset_loader


class FakeDataset:
    def to_pandas(self):
        return pd.DataFrame(
            {
                "protein": ["AAA", "AAC"],
                "label": [0.2, 1.1],
                "stage": ["train", "test"],
                "ignored": [1, 2],
            }
        )


def test_loads_observed_schema_and_audits_quality(monkeypatch):
    monkeypatch.setattr(dataset_loader, "load_dataset", lambda *_args: {"train": FakeDataset()})
    frame = dataset_loader.load_experimental_dataset()
    assert list(frame.columns) == ["protein", "label", "stage"]
    audit = dataset_loader.audit_dataset(frame)
    assert audit.rows == 2
    assert audit.stage_counts == {"test": 1, "train": 1}
    assert audit.target_min == 0.2
    assert audit.sequence_lengths == {3: 2}
    assert audit.wild_type_sequence_rows == 0
    assert audit.duplicate_records == 0


def test_rejects_missing_schema(monkeypatch):
    class InvalidDataset:
        def to_pandas(self):
            return pd.DataFrame({"sequence": ["AAA"]})

    monkeypatch.setattr(dataset_loader, "load_dataset", lambda *_args: {"train": InvalidDataset()})
    with pytest.raises(ValueError, match="schema changed"):
        dataset_loader.load_experimental_dataset()


def test_rejects_dataset_without_complete_numeric_labels():
    frame = pd.DataFrame({"protein": [None], "label": [None], "stage": ["train"]})
    with pytest.raises(ValueError, match="no complete"):
        dataset_loader.audit_dataset(frame)
