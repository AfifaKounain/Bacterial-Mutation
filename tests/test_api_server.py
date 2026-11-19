import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import joblib
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from api_server import create_server
from src.feature_extraction import CATEGORICAL_FEATURES, NUMERIC_FEATURES, extract_features, model_feature_row
from src.reference import REFERENCE_SEQUENCE


@pytest.fixture
def api_url(tmp_path):
    features = model_feature_row(extract_features(REFERENCE_SEQUENCE, "M1I"))
    transformer = ColumnTransformer(
        [
            ("numeric", "passthrough", NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    pipeline = Pipeline(
        [
            ("preprocessor", transformer),
            ("regressor", DummyRegressor(strategy="constant", constant=0.42)),
        ]
    )
    pipeline.fit(pd.DataFrame([features, features]), [0.42, 0.42])
    joblib.dump(
        {"pipeline": pipeline, "feature_columns": NUMERIC_FEATURES + CATEGORICAL_FEATURES},
        tmp_path / "random_forest.pkl",
    )
    server = create_server(port=0, model_directory=tmp_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def test_postman_style_prediction_defaults_to_reference(api_url):
    body = json.dumps({"mutation": "M1I"}).encode("utf-8")
    request = Request(
        f"{api_url}/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        result = json.loads(response.read())
    assert result["mutation"] == "M1I"
    assert result["input_sequence_type"] == "TEM-1 wild-type reference"
    assert result["predicted_fitness"] == pytest.approx(0.42)


def test_api_infers_mutation_from_variant_sequence(api_url):
    variant = "I" + REFERENCE_SEQUENCE[1:]
    body = json.dumps({"sequence": variant}).encode("utf-8")
    request = Request(
        f"{api_url}/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        result = json.loads(response.read())
    assert result["mutation"] == "M1I"


def test_api_returns_clear_validation_errors(api_url):
    body = json.dumps({"sequence": "ACDE", "mutation": "A1V"}).encode("utf-8")
    request = Request(
        f"{api_url}/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(HTTPError) as raised:
        urlopen(request, timeout=5)
    assert raised.value.code == 422
    result = json.loads(raised.value.read())
    assert "single-mutant TEM-1" in result["error"]


def test_api_health_lists_available_models(api_url):
    with urlopen(f"{api_url}/health", timeout=5) as response:
        result = json.loads(response.read())
    assert result["status"] == "ok"
    assert result["available_models"] == ["Random Forest"]
