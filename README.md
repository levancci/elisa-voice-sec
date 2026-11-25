# Elisa: unlock with your voice 🎙️

Remember the old "Voice Match" / voice unlock on Samsung and Google phones? You'd say a phrase and the phone opened. Elisa is my attempt to rebuild that idea from scratch, and it runs **fully offline** on a laptop.

Here's how it works. The app reads out four random digits, like `4 7 1 9`. You say them back. Elisa then checks two things at once:

1. **Did you say the right digits?** A small speech model (Vosk) listens for the exact sequence.
2. **Is it actually your voice?** A speaker model (ECAPA) turns your voice into a "voiceprint" and compares it with the one saved when you enrolled.

Both have to pass. The digits change every time, so a recording of you saying yesterday's code won't get in.

> I built this with Claude, step by step. Want to see how? Read **[How I built this with Claude](docs/BUILDING_WITH_CLAUDE.md)**.

---

## What you need

- **Python 3.11, 3.12 or 3.13**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)**, a fast Python package manager (one-line install)
- A microphone and a browser (Chrome or Edge works best)
- About **3 GB of free disk space**. PyTorch is heavy.

Works on Windows, macOS and Linux.

## Set it up (about 10 minutes)

**1. Get the code**

```bash
git clone https://github.com/levancci/elisa-voice-sec.git
cd elisa-voice-sec
```

**2. Install everything**

```bash
uv sync
```

This creates a virtual environment and installs all dependencies from `uv.lock`. First run takes a while. Go grab water.

**3. Download the models**

```bash
uv run python tools/download_models.py
```

This pulls two files into `models/weights/` and checks their fingerprints (SHA-256):

| Model | Job | Size |
|---|---|---|
| ECAPA int8 (ONNX) | Who is speaking? | ~22 MB |
| Vosk small English | Which digits were said? | ~40 MB zipped |

**4. Run it**

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** and allow mic access.

## Try it

1. Click **Enroll**. Read out the 5 digit prompts it gives you. That builds your voiceprint.
2. Switch to **Verify** and click **Get challenge**. The browser speaks 4 new digits.
3. Say them back. You'll get **Access granted** or **Access denied**, plus the numbers behind the decision: recognized digits, speaker score, threshold and latency.

Now hand the laptop to a friend and let them try to get in as you. 😄

## How the code is laid out

```
main.py                 starts the FastAPI app
config/default.yaml     settings you can tweak (threshold, challenge length, ...)
models/registry.yaml    which model files to load, with their SHA-256 hashes
backend/app/
  api.py                the HTTP endpoints: /enroll, /challenge, /verify, /health
  service.py            the actual logic: enroll, issue challenge, verify
  models.py             wrappers around the ECAPA and Vosk models
  audio.py              cleans up audio (16 kHz mono, length and silence checks)
  scoring.py            builds voiceprints and compares them (cosine similarity)
  storage.py            saves voiceprints and challenges in SQLite
frontend/               plain HTML/CSS/JS page, served by the same app
tools/                  benchmark and evaluation scripts I used while building
docs/                   design doc, decision log, and a report for every build phase
```

## Things to tweak first

- **Make it stricter or looser:** change `speaker_threshold` in `config/default.yaml`. Higher means harder to fool, but it'll also reject *you* more often.
- **Longer codes:** change `challenge.length`.
- **Run the tests:** `uv run pytest`

## Ideas if you want to build on it

- Make it work in Twi, or another local language
- Swap in a smaller speaker model (the registry makes that a config change)
- Add liveness detection so a voice clone or recording can't pass
- Wrap it as an Android app

## Honest limitations

This is a prototype, not a production lock. On my small test group (5 speakers) the error rate sat around 23%, which is fine for a demo and nowhere near good enough to protect anything real. AI voice cloning could also fool it. The full story lives in `docs/`: the design doc, `DECISIONS.md` and the phase reports.

## Troubleshooting

- **"Model artifact ... was not found"**: step 3 didn't finish. Run the download script again.
- **"SHA-256 mismatch"**: the file is corrupted or not the one the registry expects. Delete it from `models/weights/` and download again.
- **It says no speech was detected**: check that the browser picked the right mic, and speak a bit louder or closer.
- **Digits keep getting misheard**: try a quieter room and say each digit clearly. Vosk scored about 86% on my recordings, so it will slip sometimes.

## Credits

- Speaker model: [SpeechBrain ECAPA-TDNN](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb) (Apache-2.0), exported to ONNX and quantized for this project
- Digit recognition: [Vosk](https://alphacephei.com/vosk/) small English model (Apache-2.0)
- License details for every model I tried are in `docs/MODEL_LICENSES.md`

## License

The code is MIT licensed (see [LICENSE](LICENSE)). Use it, change it, ship it. Just keep the copyright notice. The models carry their own licenses, listed above.

Built by Gabby, with Claude. If you build something with this, show us in the group!
