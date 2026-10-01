from pathlib import Path


def test_phase0_project_markers_exist() -> None:
    root = Path(__file__).parents[2]

    assert (root / "pyproject.toml").is_file()
    assert (root / "config" / "default.yaml").is_file()