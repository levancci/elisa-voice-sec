from tools.record_protocol import DEFAULT_ENROLLMENT_PROMPTS, build_plan, write_plan


def test_plan_is_reproducible_and_enrollment_covers_all_digits() -> None:
    first = build_plan(seed=7, verification_count=10)
    second = build_plan(seed=7, verification_count=10)

    assert first == second
    enrollment_digits = "".join(item["digits"] for item in first if item["kind"] == "enrollment")
    assert set(enrollment_digits) == set("0123456789")
    assert len([item for item in first if item["kind"] == "enrollment"]) == 10
    assert DEFAULT_ENROLLMENT_PROMPTS == tuple(
        item["digits"] for item in first if item["condition"] == "quiet" and item["kind"] == "enrollment"
    )


def test_quiet_and_noisy_verification_prompts_are_disjoint() -> None:
    plan = build_plan(seed=7, verification_count=10)
    quiet = {item["digits"] for item in plan if item["condition"] == "quiet" and item["kind"] == "verification"}
    noisy = {item["digits"] for item in plan if item["condition"] == "noisy" and item["kind"] == "verification"}

    assert quiet.isdisjoint(noisy)


def test_manifest_repeats_session_metadata_and_derives_room_type(tmp_path) -> None:
    output = tmp_path / "protocol.jsonl"
    metadata = {
        "session_started_at_utc": "2026-10-01T12:00:00Z",
        "device_model": "laptop model",
        "microphone_model": "headset model",
        "environment_note": "desk beside a closed window",
    }

    write_plan(build_plan(seed=7, verification_count=1), output, "p99", metadata)
    records = [__import__("json").loads(line) for line in output.read_text().splitlines()]

    assert {record["session_started_at_utc"] for record in records} == {metadata["session_started_at_utc"]}
    assert {record["device_model"] for record in records} == {metadata["device_model"]}
    assert {record["microphone_model"] for record in records} == {metadata["microphone_model"]}
    assert {record["environment_note"] for record in records} == {metadata["environment_note"]}
    assert {record["room_type"] for record in records} == {"quiet", "noisy"}