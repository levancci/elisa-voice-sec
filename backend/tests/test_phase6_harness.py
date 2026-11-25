from tools.evaluate_phase6 import threshold_sweep


def test_threshold_sweep_separates_eer_rate_from_threshold() -> None:
    report = threshold_sweep(
        [
            {"label": 1, "score": 0.9},
            {"label": 1, "score": 0.8},
            {"label": 0, "score": 0.2},
            {"label": 0, "score": 0.3},
        ]
    )

    assert report["eer_rate"] == 0.0
    assert report["eer_far"] == 0.0
    assert report["eer_frr"] == 0.0
    assert report["eer_threshold"] in {0.8, 0.9}
    assert "eer_operating_point" not in report
