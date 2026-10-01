# Phase 2 recording protocol

This is the coordination guide for collecting the data needed before CP2.
Recordings are biometric data: get explicit written consent, use pseudonymous
participant IDs, keep files local, and delete a participant's files on request.
Do not commit anything under `data/`.

## Coordinator checklist

1. Give the participant the purpose, what is recorded, where it is stored, who
   can access it, how long it will be kept, and how to request deletion.
2. Get written consent before recording. Do not record anyone who declines.
3. Assign a pseudonymous ID such as `p01`; do not use names in filenames.
4. Use the same microphone and room setup for the quiet and noisy passes when
   possible, and note the device/microphone in the session notes.
5. Keep tuning participants separate from held-out evaluation participants.
   Do not use the held-out recordings to choose thresholds.

## Generate a session plan

From the repository root:

```powershell
python tools/record_protocol.py --participant p01
```

This writes an ignored JSONL plan under `data/phase2/p01/`. The plan has:

- 5 enrollment digit strings, repeated in quiet and noisy conditions;
- 10 fresh verification strings in each condition;
- enrollment prompts covering all ten digits;
- no shared verification strings between quiet and noisy conditions.

The default seed is recorded by the coordinator. Use another integer with
`--seed` for another participant, and record it in the session notes.

## Record locally

Install the optional microphone package in the project virtual environment,
then run the same command with the consent gate:

```powershell
python -m pip install sounddevice==0.5.2
python tools/record_protocol.py --participant p01 --record --consent-confirmed
```

The recorder captures 4-second, 16 kHz, mono, signed-16-bit PCM WAV files. It
waits for Enter before every take so the participant can prepare. For each
prompt, say the four digits naturally in one utterance. In the noisy pass,
play a consistent background noise source locally at the agreed level; do not
stream or upload audio.

The package may require a local PortAudio installation on some systems. If the
microphone cannot be opened, use the generated plan with an approved local
recorder, then preserve the same filenames and metadata fields.

## Attack and negative recordings

These are collected only with consent and remain separate from genuine trials:

- wrong speaker: another participant says the requested digits;
- wrong digits: participant says a changed sequence;
- missing or extra digit: participant omits or adds one digit;
- replay: play a previously recorded utterance against a new prompt;
- splicing: concatenate individual digit recordings into a requested sequence.

Label these cases in a separate manifest. Do not use them to tune the speaker
threshold. The replay and splicing tests are required for Phase 6, not a reason
to retain more audio than necessary.

## After recording

Verify the JSONL plan points to the expected WAV files, copy only the
pseudonymous plan and local audio into the ignored `data/phase2/` tree, and
send the coordinator the participant/session metadata rather than audio. The
next implementation step is a local inference adapter that converts these
recordings into trial scores for `tools/benchmark_embedding.py`.