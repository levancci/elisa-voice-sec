from tools.record_protocol import DEFAULT_ENROLLMENT_PROMPTS, build_plan


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