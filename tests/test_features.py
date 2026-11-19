from src.feature_extraction import FEATURE_COLUMNS, extract_features, model_feature_row
from src.mutation_analysis import derive_single_substitution
from src.reference import REFERENCE_SEQUENCE


def test_extracts_mutation_features_from_shared_schema():
    features = extract_features(REFERENCE_SEQUENCE, "M1C")
    assert features["position"] == 1
    assert features["original_aa"] == "M"
    assert features["mutant_aa"] == "C"
    assert isinstance(features["blosum62"], float)
    assert isinstance(features["molecular_weight_difference"], float)
    assert features["local_context"].startswith("MSI")
    assert list(model_feature_row(features)) == FEATURE_COLUMNS


def test_derives_only_single_substitutions():
    variant = "C" + REFERENCE_SEQUENCE[1:]
    assert derive_single_substitution(variant, REFERENCE_SEQUENCE) == "M1C"
    assert derive_single_substitution(REFERENCE_SEQUENCE, REFERENCE_SEQUENCE) is None
    assert derive_single_substitution("CC" + REFERENCE_SEQUENCE[2:], REFERENCE_SEQUENCE) is None
