# How I built Elisa with Claude

I didn't sit down one day and type "build me voice unlock." That gets you a demo that looks right and breaks the moment you poke it.

What worked was treating Claude like a very fast teammate who needs a clear plan and someone checking its work. Here's the process, step by step. Copy it for your own project.

---

## 1. Talk the idea through before writing any code

I started in a normal Claude chat. I explained what I wanted (phone-style voice unlock), and we went back and forth on how it could actually work. Which models? What could go wrong?

Claude pushed back on my first idea. I wanted a keyword-spotting model for the digits, but those only recognise one word at a time, not four digits said together. Fixing that on paper cost me five minutes. Fixing it in code would have cost days.

**Output:** a design doc → [`vomo_voice_security_design_v1.1.md`](vomo_voice_security_design_v1.1.md)

## 2. Write down the hard rules

Before any building, I set constraints the AI couldn't break:

- Runs fully **offline**
- Only models with **permissive licenses**
- **No accounts, API keys or spending money**
- **Stop at every checkpoint** and wait for my approval

For the actual building I switched to **Claude Code**, which works right inside your project folder: it reads files, writes code and runs tests. The rules went into a short instruction file it reads first → [`agents.md`](agents.md). Short is fine. Mine is one sentence.

## 3. Split the build into phases with checkpoints

I broke the project into phases, each ending in a checkpoint (CP) where the agent stops, reports and waits:

| Phase | What happened |
|---|---|
| 0 | Project skeleton, tests, config |
| 1 | License audit of every candidate model |
| 2 | Record real voices and benchmark speaker models |
| 3 | Benchmark digit recognition |
| 4 | Build the backend API |
| 5 | Build the browser frontend |
| 6 | Evaluate it properly (attacks, thresholds) |

So I never ended up with 2,000 lines of code I didn't understand. I reviewed one small chunk at a time.

## 4. Make the agent report, then you decide

At the end of each phase Claude Code wrote a short report: what got done, the evidence (test results, numbers), what surprised it, and open questions for me. Look at any `PHASE_*_REPORT.md` in this folder.

Then *I* made the call. Every decision got logged in [`DECISIONS.md`](DECISIONS.md) with the reason behind it. A month later, when you've forgotten why you picked model X, that log saves you.

## 5. Test with real data, not vibes

The models looked fine on paper. Then I recorded real people (with written consent, following [`RECORDING_PROTOCOL.md`](RECORDING_PROTOCOL.md)) saying digits in quiet and noisy rooms. That's where the truth showed up.

## 6. Expect bugs and dig into them

Two real examples from this project:

- **Quantization broke the model.** Shrinking ECAPA to int8 dropped similarity with the original to 0.22, so it was basically guessing. I asked Claude to investigate, and it found the normalization layers getting squashed. After the fix: 0.99.
- **Wrong audio preprocessing.** The evaluation was feeding ECAPA audio features prepared for a *different* model. The results looked plausible but were invalid. We only caught it by asking "does this number actually make sense?"

The AI writes code fast. It also makes confident mistakes. Your job is to stay suspicious.

## 7. Be honest about where it ends

Elisa isn't production-ready, and the docs say so. Writing down the limits (error rate, voice cloning risk) is part of building like an engineer.

---

## The short version

1. Chat through the idea and write a design doc
2. Set hard rules for the AI
3. Break the work into phases with checkpoints
4. Read every report and make the decisions yourself
5. Test with real data
6. Question numbers that look too good (or too bad)
7. Write down what doesn't work yet

You don't need to be an ML expert to do this. I went in with only a little machine learning experience. You need a clear idea, patience, and the habit of asking "why?" a lot.

Now go build something. 🚀
