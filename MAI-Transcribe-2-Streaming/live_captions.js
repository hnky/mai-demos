export const workletSource = `
class PCMFrames extends AudioWorkletProcessor {
  constructor() {
    super();
    this.active = false;
    this.frame = new Uint8Array(640);
    this.offset = 0;
    this.pending = 0;
    this.port.onmessage = ({ data }) => {
      if (data === "start") this.active = true;
      if (data === "ack") this.pending = Math.max(0, this.pending - 1);
      if (data === "stop") {
        this.active = false;
        this.flush();
        this.port.postMessage({ type: "stopped" });
      }
    };
  }
  flush() {
    if (!this.offset) return true;
    if (this.pending >= 50) {
      this.active = false;
      this.offset = 0;
      this.port.postMessage({ type: "overflow" });
      return false;
    }
    const buffer = this.frame.slice(0, this.offset).buffer;
    this.pending++;
    this.port.postMessage({ type: "audio", buffer }, [buffer]);
    this.offset = 0;
    return true;
  }
  process(inputs) {
    if (!this.active || !inputs[0]?.[0]) return true;
    const view = new DataView(this.frame.buffer);
    for (const value of inputs[0][0]) {
      const sample = Math.max(-1, Math.min(1, value));
      view.setInt16(this.offset, sample < 0 ? sample * 32768 : sample * 32767, true);
      this.offset += 2;
      if (this.offset === this.frame.length && !this.flush()) break;
    }
    return true;
  }
}
registerProcessor("podcast-pcm", PCMFrames);
`;

function render({ model, el }) {
  const panel = document.createElement("section");
  panel.style.cssText = "padding:16px;border:1px solid #8886;border-radius:10px;max-width:900px;font:inherit";
  const heading = document.createElement("h3");
  heading.textContent = "A Bit of AI - live captions";
  const note = document.createElement("p");
  note.textContent = "Start sends your browser microphone to Azure. Use permitted, non-sensitive speech. Five-minute demo limit; no audio file is saved.";
  const start = document.createElement("button");
  start.textContent = "Start captions";
  const stop = document.createElement("button");
  stop.textContent = "Stop";
  stop.disabled = true;
  stop.style.marginLeft = "8px";
  const status = document.createElement("p");
  status.setAttribute("role", "status");
  status.textContent = "Ready to start. No microphone or Azure connection is open.";
  const caption = document.createElement("div");
  caption.style.cssText = "font-size:1.5em;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere;max-height:320px;overflow:auto";
  caption.setAttribute("role", "log");
  caption.setAttribute("aria-label", "Live captions; italic text is provisional");
  const final = document.createElement("span");
  const partial = document.createElement("em");
  partial.style.opacity = "0.65";
  caption.append(final, partial);
  panel.append(heading, note, start, stop, status, caption);
  el.append(panel);

  let run = null;
  let disposed = false;
  const send = (r, type, buffers = []) => model.send({ type, run_id: r.id }, undefined, buffers);

  function release(r) {
    r.releasing = true;
    clearTimeout(r.limitTimer);
    clearTimeout(r.flushTimer);
    r.stream?.getTracks().forEach((track) => track.stop());
    r.node?.disconnect();
    r.source?.disconnect();
    if (r.context && !r.contextClosing && r.context.state !== "closed") {
      r.contextClosing = true;
      r.context.close().catch(() => {
        status.textContent = "Microphone stopped, but the audio context could not close. Close this notebook tab.";
      });
    }
  }

  function end(r, message) {
    if (run !== r) return;
    release(r);
    clearInterval(r.heartbeat);
    clearInterval(r.healthTimer);
    run = null;
    start.disabled = disposed;
    stop.disabled = true;
    if (message) status.textContent = message;
  }

  function fail(r, message) {
    if (run !== r) return;
    if (r.connected) send(r, "abort");
    end(r, message);
  }

  function finishCapture(r) {
    if (run !== r || r.committed) return;
    r.committed = true;
    release(r);
    send(r, "stop");
    status.textContent = "Microphone off. Waiting for the final transcript...";
  }

  function stopCapture() {
    const r = run;
    if (!r || r.stopping) return;
    r.stopping = true;
    stop.disabled = true;
    // Stop tracks now; flush the already captured, partial PCM frame separately.
    r.stream?.getTracks().forEach((track) => track.stop());
    if (!r.recording) {
      fail(r, "Stopped before recording began.");
      return;
    }
    r.flushTimer = setTimeout(() => fail(r, "Microphone flush timed out; the transcript may be incomplete."), 1000);
    r.node.port.postMessage("stop");
  }

  async function begin() {
    if (run || disposed) return;
    const r = { id: crypto.randomUUID(), outstanding: 0, lastPong: Date.now() };
    run = r;
    start.disabled = true;
    stop.disabled = false;
    final.textContent = partial.textContent = "";
    status.textContent = "Preparing microphone and Azure session. Please wait before speaking.";
    try {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || !window.AudioWorkletNode) {
        throw new Error("unsupported");
      }
      r.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 }, video: false });
      if (run !== r) {
        r.stream.getTracks().forEach((track) => track.stop());
        return;
      }
      r.stream.getAudioTracks().forEach((track) => track.addEventListener("ended", () => {
        if (run === r && !r.stopping) fail(r, "Microphone disconnected; the transcript may be incomplete.");
      }));
      // Web Audio resamples the microphone to the context's 16 kHz rate.
      r.context = new AudioContext({ sampleRate: 16000 });
      if (r.context.sampleRate !== 16000) throw new Error("sample-rate");
      await r.context.resume();
      if (run !== r) return;
      r.context.addEventListener("statechange", () => {
        if (run === r && !r.releasing && !r.stopping && r.context.state !== "running") {
          fail(r, "Browser audio was interrupted; the transcript may be incomplete.");
        }
      });
      const moduleURL = URL.createObjectURL(new Blob([workletSource], { type: "text/javascript" }));
      try {
        await r.context.audioWorklet.addModule(moduleURL);
      } finally {
        URL.revokeObjectURL(moduleURL);
      }
      if (run !== r) return;
      r.node = new AudioWorkletNode(r.context, "podcast-pcm", {
        channelCount: 1, channelCountMode: "explicit",
      });
      r.node.onprocessorerror = () => fail(r, "Microphone processing failed; the transcript may be incomplete.");
      r.source = r.context.createMediaStreamSource(r.stream);
      r.source.connect(r.node);
      // The worklet produces silent output, keeping the graph running without feedback.
      r.node.connect(r.context.destination);
      r.node.port.onmessage = ({ data }) => {
        if (run !== r) return;
        if (data.type === "overflow") {
          fail(r, "Microphone buffering exceeded the demo limit; the transcript is incomplete.");
          return;
        }
        if (data.type === "stopped") return finishCapture(r);
        if (data.type !== "audio" || r.committed) return;
        if (r.outstanding >= 50) {
          fail(r, "The connection cannot keep up with microphone audio; the transcript is incomplete.");
          return;
        }
        r.outstanding++;
        send(r, "audio", [data.buffer]);
      };
      r.connected = true;
      send(r, "start");
      r.heartbeat = setInterval(() => send(r, "ping"), 1000);
      r.healthTimer = setInterval(() => {
        if (Date.now() - r.lastPong > 10000) fail(r, "Kernel connection lost; the microphone has stopped.");
      }, 1000);
    } catch (error) {
      const message = error.name === "NotAllowedError"
        ? "Microphone permission was denied or blocked by this notebook's browser frame. Allow it, or open JupyterLab directly in a browser tab."
        : error.name === "NotFoundError"
          ? "No browser microphone was found."
          : "Browser audio could not start. Use HTTPS or localhost, enable microphone/widgets, and try a current Chrome or Edge browser with 16 kHz Web Audio support.";
      fail(r, message);
    }
  }

  function receive(message) {
    const r = run;
    if (!r || message.run_id !== r.id) return;
    if (message.type === "pong") r.lastPong = Date.now();
    if (message.type === "ready" && !r.stopping && !r.recording) {
      r.recording = true;
      r.node.port.postMessage("start");
      status.textContent = "LIVE - microphone on. Speak now; italic text can still change.";
      r.limitTimer = setTimeout(stopCapture, message.max_seconds * 1000);
    }
    if (message.type === "ack") {
      r.outstanding = Math.max(0, r.outstanding - 1);
      r.node?.port.postMessage("ack");
    }
    if (message.type === "caption") {
      final.textContent = message.final;
      partial.textContent = message.partial;
      caption.scrollTop = caption.scrollHeight;
    }
    if (message.type === "finished") {
      final.textContent = message.text;
      partial.textContent = "";
      status.textContent = message.text ? "Captions finalized. Microphone off." : "Finished without recognized speech. Microphone off.";
    }
    if (message.type === "error") end(r, message.message);
    if (message.type === "closed") {
      end(r, message.complete ? null : "Session ended before completion. The transcript may be incomplete.");
    }
  }

  const hidden = () => { if (document.hidden) stopCapture(); };
  const unload = () => { if (run) fail(run, "Notebook closed; the transcript may be incomplete."); };
  model.on("msg:custom", receive);
  start.addEventListener("click", begin);
  stop.addEventListener("click", stopCapture);
  document.addEventListener("visibilitychange", hidden);
  window.addEventListener("pagehide", unload);
  return () => {
    disposed = true;
    unload();
    model.off("msg:custom", receive);
    document.removeEventListener("visibilitychange", hidden);
    window.removeEventListener("pagehide", unload);
    panel.remove();
  };
}

export default { render };
