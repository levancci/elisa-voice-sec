const state = { mode: "verify", challenge: null, samples: [], recorder: null, recording: false, readyToRecord: false };
const enrollmentPrompts = ["0123", "4567", "8901", "2345", "6789"];
const $ = (id) => document.getElementById(id);

async function api(path, payload) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  const body = await response.json();
  if (!response.ok) { const reason = body.detail?.reason_code; const message = body.detail?.message; throw new Error(reason && message ? `${reason}: ${message}` : reason || message || "request_failed"); }
  return body;
}

function setFeedback(message = "") { $("feedback").textContent = message; }
function setMode(mode) {
  state.mode = mode;
  state.challenge = null;
  state.samples = [];
  state.readyToRecord = false;
  document.querySelectorAll(".mode").forEach((button) => { const active = button.dataset.mode === mode; button.classList.toggle("active", active); button.setAttribute("aria-selected", active); });
  $("enrollment-progress").hidden = mode !== "enroll";
  $("prompt").textContent = mode === "enroll" ? enrollmentPrompts[0] : "Ready when you are";
  $("prompt-meta").textContent = mode === "enroll" ? "Say the digits exactly as shown." : "Verification uses a new challenge each time.";
  $("primary-action").lastElementChild.textContent = mode === "enroll" ? "Record sample" : "Get challenge";
  updateProgress();
  setFeedback();
}
function updateProgress() { $("progress-count").textContent = `${state.samples.length} / ${enrollmentPrompts.length}`; $("progress-bar").style.width = `${state.samples.length / enrollmentPrompts.length * 100}%`; }
function showResult(result) {
  $("capture-screen").hidden = true; $("result-screen").hidden = false;
  const passed = result.decision === "pass";
  $("result-word").textContent = passed ? "granted." : "denied.";
  $("result-word").style.color = passed ? "#82a52e" : "var(--coral)";
  $("result-digits").textContent = result.recognized_digits || "--";
  $("result-score").textContent = result.speaker_score == null ? "--" : result.speaker_score.toFixed(3);
  $("result-threshold").textContent = result.threshold == null ? "--" : result.threshold.toFixed(3);
  $("result-latency").textContent = result.latency_ms == null ? "--" : `${Math.round(result.latency_ms)} ms`;
  $("result-reasons").textContent = result.reason_codes?.length ? result.reason_codes.join(" / ") : "all checks passed";
}
function reset() { state.challenge = null; state.samples = []; $("capture-screen").hidden = false; $("result-screen").hidden = true; setMode(state.mode); }

async function recordAudio() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
  const context = new AudioContext();
  await context.resume();
  await context.audioWorklet.addModule("/audio-worklet.js");
  const source = context.createMediaStreamSource(stream);
  const recorder = new AudioWorkletNode(context, "elisa-recorder");
  const chunks = [];
  recorder.port.onmessage = (event) => chunks.push(event.data);
  source.connect(recorder);
  const silentSink = context.createGain();
  silentSink.gain.value = 0;
  recorder.connect(silentSink).connect(context.destination);
  state.recorder = { stream, context, source, recorder, chunks, sampleRate: context.sampleRate };
  await new Promise((resolve) => { state.resolveRecording = resolve; });
  recorder.disconnect(); silentSink.disconnect(); source.disconnect(); stream.getTracks().forEach((track) => track.stop()); await context.close();
  const samples = new Float32Array(chunks.reduce((total, chunk) => total + chunk.length, 0)); let offset = 0;
  chunks.forEach((chunk) => { samples.set(chunk, offset); offset += chunk.length; });
  const rms = Math.sqrt(samples.reduce((sum, sample) => sum + sample * sample, 0) / Math.max(samples.length, 1));
  if (rms < 0.001) throw new Error("No microphone signal detected. Check the selected microphone and browser permission.");
  return wavBase64(samples, state.recorder.sampleRate);
}
function wavBase64(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2); const view = new DataView(buffer);
  const text = (offset, value) => [...value].forEach((character, index) => view.setUint8(offset + index, character.charCodeAt(0)));
  text(0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true); text(8, "WAVE"); text(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true); text(36, "data"); view.setUint32(40, samples.length * 2, true);
  samples.forEach((sample, index) => view.setInt16(44 + index * 2, Math.max(-1, Math.min(1, sample)) * 0x7fff, true));
  let binary = ""; const bytes = new Uint8Array(buffer); for (let index = 0; index < bytes.length; index += 1) binary += String.fromCharCode(bytes[index]); return btoa(binary);
}
async function startRecording() { if (state.mode === "verify" && !state.readyToRecord) return; if (state.recording) { state.recording = false; state.resolveRecording?.(); $("primary-action").lastElementChild.textContent = state.mode === "enroll" ? "Record sample" : "Record response"; return; } state.recording = true; $("primary-action").lastElementChild.textContent = "Stop recording"; setFeedback("Listening..."); try { const audio = await recordAudio(); await handleRecording(audio); } catch (error) { console.error(error); if (state.mode === "verify") reset(); setFeedback(error.name === "NotAllowedError" ? "Microphone permission is required." : `Recording failed: ${error.message || error.name}`); } finally { state.recording = false; } }
async function handleRecording(audio) {
  if (state.mode === "enroll") { state.samples.push({ digits: enrollmentPrompts[state.samples.length], audio_base64: audio }); updateProgress(); if (state.samples.length === enrollmentPrompts.length) { setFeedback("Saving voiceprint..."); try { await api("/enroll", { user_id: "demo-user", audio_samples: state.samples }); setFeedback("Enrollment saved. Switch to Verify when ready."); } catch (error) { state.samples = []; updateProgress(); $("prompt").textContent = enrollmentPrompts[0]; setFeedback(error.message); } } else { $("prompt").textContent = enrollmentPrompts[state.samples.length]; setFeedback("Sample saved."); } return; }
  setFeedback("Checking voiceprint..."); const result = await api("/verify", { user_id: "demo-user", challenge_id: state.challenge.challenge_id, audio_base64: audio }); showResult(result);
}
async function primaryAction() { try { if (state.mode === "verify" && !state.challenge) { state.challenge = await api("/challenge", { user_id: "demo-user" }); $("prompt").textContent = state.challenge.digits.split("").join("  "); $("prompt-meta").textContent = "Listen, then repeat the sequence."; state.readyToRecord = false; const speech = new SpeechSynthesisUtterance(state.challenge.digits.split("").join(" ")); speech.onend = () => { state.readyToRecord = true; $("primary-action").disabled = false; $("primary-action").lastElementChild.textContent = "Record response"; setFeedback("Your turn."); }; $("primary-action").disabled = true; $("primary-action").lastElementChild.textContent = "Speaking..."; speechSynthesis.speak(speech); return; } await startRecording(); } catch (error) { setFeedback(error.message); } }

document.querySelectorAll(".mode").forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));
$("primary-action").addEventListener("click", primaryAction); $("reset-action").addEventListener("click", reset); $("again-action").addEventListener("click", reset);
setMode("verify");
