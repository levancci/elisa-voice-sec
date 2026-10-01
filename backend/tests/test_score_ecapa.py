from tools.score_ecapa import protocol_records


def test_ecapa_protocol_records_include_local_audio_paths() -> None:
    records = protocol_records(__import__("pathlib").Path("data/phase2"), "p02")

    assert len(records) == 30
    assert all(record["path"].endswith(".wav") for record in records)