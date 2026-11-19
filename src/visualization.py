"""Plotting helpers for genuine assay observations and saved model evaluations."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px


def fitness_distribution(frame: pd.DataFrame) -> Any:
    return px.histogram(
        frame,
        x="label",
        color="stage",
        nbins=45,
        marginal="box",
        labels={"label": "Experimental mutation-effect score", "stage": "Official split"},
        title="Observed deep-mutational-scanning scores",
        color_discrete_sequence=["#2684c7", "#46a6b0", "#133b5c"],
    )


def mutation_position_distribution(frame: pd.DataFrame) -> Any:
    counts = frame.groupby("position", as_index=False).size()
    return px.bar(
        counts,
        x="position",
        y="size",
        labels={"position": "TEM-1 reference position", "size": "Dataset records"},
        title="Single-substitution records by reference position",
        color_discrete_sequence=["#2684c7"],
    )


def substitution_distribution(frame: pd.DataFrame) -> Any:
    counts = frame.groupby(["original_aa", "mutant_aa"], as_index=False).size()
    counts["substitution"] = counts["original_aa"] + counts["mutant_aa"]
    return px.bar(
        counts,
        x="substitution",
        y="size",
        labels={"substitution": "Reference-to-mutant substitution", "size": "Records"},
        title="Observed amino-acid substitutions",
        color_discrete_sequence=["#2684c7"],
    )


def model_comparison_plot(metrics: dict[str, dict[str, dict[str, float | None]]]) -> Any:
    rows = [
        {"Model": name, "Metric": metric.upper(), "Value": value}
        for name, split_metrics in metrics.items()
        for metric, value in split_metrics.get("test", {}).items()
        if value is not None
    ]
    return px.bar(
        pd.DataFrame(rows),
        x="Model",
        y="Value",
        color="Metric",
        barmode="group",
        title="Metrics on the sequence-deduplicated official test split",
    )


def actual_vs_predicted_figure(actual: list[float], predicted: list[float]) -> Any:
    figure, axis = plt.subplots(figsize=(6, 5))
    axis.scatter(actual, predicted, alpha=0.55, color="#2684c7", edgecolors="none")
    lower = min(min(actual), min(predicted))
    upper = max(max(actual), max(predicted))
    axis.plot([lower, upper], [lower, upper], linestyle="--", color="#133b5c")
    axis.set(
        xlabel="Observed experimental score",
        ylabel="Predicted experimental score",
        title="Test-split observed versus predicted fitness",
    )
    figure.tight_layout()
    return figure


def feature_importance_figure(importances: dict[str, float], limit: int = 15) -> Any:
    top = sorted(importances.items(), key=lambda item: item[1], reverse=True)[:limit]
    figure, axis = plt.subplots(figsize=(8, 5))
    labels = [name.replace("categorical__", "").replace("numeric__", "") for name, _ in top]
    axis.barh(labels[::-1], [value for _, value in top][::-1], color="#2684c7")
    axis.set(xlabel="Model impurity-based importance", title="Top encoded input features")
    figure.tight_layout()
    return figure


def wild_type_comparison_plot(result: dict[str, Any]) -> Any:
    rows = [
        {
            "Reference": "Dataset-defined wild type",
            "Score": float(result["wild_type_reference_score"]),
        },
        {
            "Reference": f"Predicted {result['mutation']}",
            "Score": float(result["predicted_fitness"]),
        },
    ]
    observed_mean = result.get("wild_type_observed_training_mean")
    if observed_mean is not None:
        rows.append(
            {
                "Reference": "Observed WT mean (train)",
                "Score": float(observed_mean),
            }
        )
    return px.bar(
        pd.DataFrame(rows),
        x="Reference",
        y="Score",
        color="Reference",
        title="Predicted mutation score and wild-type references",
        color_discrete_sequence=["#2684c7", "#46a6b0", "#133b5c"],
        labels={"Score": "Experimental mutation-effect score"},
    )
