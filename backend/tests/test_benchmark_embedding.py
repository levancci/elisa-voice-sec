from tools.benchmark_embedding import _metrics


def test_metrics_find_balanced_threshold() -> None:
    metrics = _metrics(
        [
            {"label": 1, "score": 0.9},
            {"label": 1, "score": 0.8},
            {"label": 0, "score": 0.2},
            {"label": 0, "score": 0.1},
        ]
    )

    assert metrics["eer"] == 0.0
    assert metrics["eer_threshold"] == 0.8