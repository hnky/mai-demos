import widget, { workletSource } from "../live_captions.js";

const { render } = widget;

const results = document.querySelector("#results");
const fixture = document.querySelector("#fixture");
const report = [];
function assert(value, message) {
  if (!value) throw new Error(message);
}
async function until(check) {
  const deadline = performance.now() + 2500;
  while (!check()) {
    if (performance.now() > deadline) throw new Error("Condition timed out");
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
}
async function test(name, fn) {
  try {
    await fn();
    report.push(`PASS ${name}`);
  } catch (error) {
    report.push(`FAIL ${name}: ${error.message}`);
  }
  results.textContent = report.join("\n");
}

let Processor;
class MockProcessor {
  constructor() {
    this.messages = [];
    this.port = { postMessage: (m) => this.messages.push(m) };
  }
}
new Function("AudioWorkletProcessor", "registerProcessor", workletSource)(
  MockProcessor, (_, cls) => { Processor = cls; },
);

await test("PCM: gated capture, clipping, signed little-endian samples, partial flush", () => {
  const p = new Processor();
  p.process([[new Float32Array([1])]]);
  assert(p.messages.length === 0, "Audio captured before Start");
  p.port.onmessage({ data: "start" });
  p.process([[new Float32Array([-2, -1, -0.5, 0, 0.5, 1, 2])]]);
  p.port.onmessage({ data: "stop" });
  const view = new DataView(p.messages[0].buffer);
  const actual = Array.from({ length: 7 }, (_, i) => view.getInt16(i * 2, true));
  assert(JSON.stringify(actual) === "[-32768,-32768,-16384,0,16383,32767,32767]", "Incorrect PCM conversion");
  assert(view.byteLength === 14 && p.messages[1].type === "stopped", "Partial frame did not precede Stop");
  p.process([[new Float32Array(320)]]);
  assert(p.messages.length === 2, "Audio continued after Stop");
});

await test("PCM: exact 20 ms frames and bounded worklet queue", () => {
  const p = new Processor();
  p.port.onmessage({ data: "start" });
  for (let i = 0; i < 50; i++) p.process([[new Float32Array(320)]]);
  assert(p.messages.length === 50, "Wrong frame count");
  assert(p.messages.every((m) => m.buffer.byteLength === 640), "Wrong frame size");
  p.port.onmessage({ data: "ack" });
  p.process([[new Float32Array(320)]]);
  assert(p.messages.length === 51, "Credit was not released");
  p.process([[new Float32Array(320)]]);
  assert(p.messages.at(-1).type === "overflow" && !p.active, "Overflow did not stop processing");
});

for (const sourceRate of [44100, 48000]) {
  await test(`Real Web Audio: ${sourceRate} Hz stereo -> 16000 Hz mono PCM`, async () => {
    const context = new OfflineAudioContext(1, 16000, 16000);
    const url = URL.createObjectURL(new Blob([workletSource], { type: "text/javascript" }));
    try {
      await context.audioWorklet.addModule(url);
    } finally {
      URL.revokeObjectURL(url);
    }
    const source = context.createBufferSource();
    source.buffer = context.createBuffer(2, sourceRate, sourceRate);
    source.buffer.getChannelData(0).fill(0.25);
    source.buffer.getChannelData(1).fill(0.75);
    const node = new AudioWorkletNode(context, "podcast-pcm", { channelCount: 1, channelCountMode: "explicit" });
    const frames = [];
    node.port.onmessage = ({ data }) => frames.push(data);
    source.connect(node).connect(context.destination);
    node.port.postMessage("start");
    source.start();
    // Deliver the control message before accelerated offline rendering starts.
    const suspended = context.suspend(0);
    const rendered = context.startRendering();
    await suspended;
    await new Promise((resolve) => setTimeout(resolve, 100));
    await context.resume();
    await rendered;
    await until(() => frames.length >= 50);
    assert(frames.length === 50 && frames.every((m) => m.buffer.byteLength === 640), "Expected exactly one second of mono PCM");
    assert(Math.abs(new DataView(frames[10].buffer).getInt16(0, true) - 16383) <= 2, "Stereo was not downmixed/resampled correctly");
    node.disconnect();
  });
}

const originalContext = window.AudioContext;
const originalNode = window.AudioWorkletNode;
const originalMedia = Object.getOwnPropertyDescriptor(navigator, "mediaDevices");
let streams = [];
let nodes = [];
let contexts = [];
class Track extends EventTarget {
  stop() { this.stopped = true; }
}
function stream() {
  const track = new Track();
  const result = { getTracks: () => [track], getAudioTracks: () => [track] };
  streams.push(result);
  return result;
}
let getMedia = async () => stream();
Object.defineProperty(navigator, "mediaDevices", {
  configurable: true, value: { getUserMedia: (...args) => getMedia(...args) },
});
window.AudioContext = class extends EventTarget {
  constructor(options) {
    super();
    this.sampleRate = options.sampleRate;
    this.state = "running";
    this.destination = {};
    this.audioWorklet = { addModule: async () => {} };
    contexts.push(this);
  }
  async resume() {}
  async close() { this.state = "closed"; }
  createMediaStreamSource() { return { connect() {}, disconnect() {} }; }
};
window.AudioWorkletNode = class {
  constructor() {
    this.commands = [];
    this.port = {
      postMessage: (command) => {
        this.commands.push(command);
        if (command === "stop") {
          this.emit({ type: "audio", buffer: new ArrayBuffer(2) });
          this.emit({ type: "stopped" });
        }
      },
    };
    nodes.push(this);
  }
  connect() {}
  disconnect() { this.disconnected = true; }
  emit(data) { this.port.onmessage({ data }); }
};

function mount() {
  const callbacks = new Set();
  const model = {
    sent: [],
    send(message, callbacks, buffers = []) {
      assert(callbacks === undefined, "Binary buffers were passed as Jupyter callbacks");
      this.sent.push({ ...message, buffers });
    },
    on(_, callback) { callbacks.add(callback); },
    off(_, callback) { callbacks.delete(callback); },
    receive(type, values = {}) {
      const run_id = this.sent.findLast((m) => m.type === "start").run_id;
      callbacks.forEach((cb) => cb({ type, run_id, ...values }));
    },
  };
  const cleanup = render({ model, el: fixture });
  const [start, stop] = fixture.querySelectorAll("button");
  const status = fixture.querySelector("[role=status]");
  return { model, cleanup, start, stop, status, callbacks };
}
async function startRun(ui, seconds = 300) {
  ui.start.click();
  await until(() => ui.model.sent.some((m) => m.type === "start"));
  ui.model.receive("ready", { max_seconds: seconds });
}

try {
  await test("Rendering stays offline; Start gates recording; Stop drains before commit", async () => {
    const ui = mount();
    try {
      assert(ui.model.sent.length === 0 && streams.length === 0, "Render started a session");
      await startRun(ui);
      assert(nodes.at(-1).commands[0] === "start", "Worklet was not activated");
      nodes.at(-1).emit({ type: "audio", buffer: new ArrayBuffer(640) });
      ui.model.receive("ack");
      ui.stop.click();
      assert(streams.at(-1).getTracks()[0].stopped, "Stop left microphone running");
      const messages = ui.model.sent.filter((m) => ["audio", "stop"].includes(m.type));
      assert(messages.map((m) => m.type).join(",") === "audio,audio,stop", "Tail frame was lost");
      assert(messages[0].buffers[0].byteLength === 640, "Audio did not use a binary buffer");
      assert(ui.status.textContent.includes("Waiting"), "Claimed completion before Azure final");
      ui.model.receive("finished", { text: "Welcome to A Bit of AI." });
      ui.model.receive("closed", { complete: true });
      assert(!ui.start.disabled && ui.stop.disabled, "Controls did not reset");
      assert(contexts.at(-1).state === "closed", "Audio context still open");
    } finally { ui.cleanup(); }
  });

  await test("Captions replace provisional text, render as text, and ignore stale runs", async () => {
    const ui = mount();
    try {
      await startRun(ui);
      ui.model.receive("caption", { final: "Hello", partial: " world" });
      ui.model.receive("caption", { final: "Hello", partial: " there" });
      assert(fixture.querySelector("em").textContent === " there", "Provisional text appended");
      ui.model.receive("caption", { final: "<img src=x onerror=alert(1)>", partial: "" });
      assert(!fixture.querySelector("img"), "Caption interpreted as HTML");
      ui.model.receive("error", { run_id: "old-session", message: "stale" });
      assert(ui.status.textContent.includes("LIVE"), "Stale event affected active session");
    } finally { ui.cleanup(); }
    assert(streams.at(-1).getTracks()[0].stopped && ui.callbacks.size === 0, "Disposal leaked capture or listeners");
  });

  await test("Backpressure stops capture with a visible incomplete-transcript error", async () => {
    const ui = mount();
    try {
      await startRun(ui);
      for (let i = 0; i < 51; i++) nodes.at(-1).emit({ type: "audio", buffer: new ArrayBuffer(640) });
      assert(ui.status.textContent.includes("cannot keep up"), "Overflow was silent");
      assert(streams.at(-1).getTracks()[0].stopped, "Overflow left microphone on");
      assert(ui.model.sent.at(-1).type === "abort", "Overflow did not abort backend");
    } finally { ui.cleanup(); }
  });

  await test("Stop during pending permission releases a late microphone without connecting", async () => {
    let grant;
    getMedia = () => new Promise((resolve) => { grant = resolve; });
    const ui = mount();
    try {
      ui.start.click();
      ui.stop.click();
      const lateStream = stream();
      grant(lateStream);
      await until(() => lateStream.getTracks()[0].stopped);
      assert(ui.model.sent.length === 0, "Cancelled permission opened Azure");
    } finally {
      ui.cleanup();
      getMedia = async () => stream();
    }
  });

  await test("Permission denial is explicit and does not connect", async () => {
    getMedia = async () => { throw new DOMException("denied", "NotAllowedError"); };
    const ui = mount();
    try {
      ui.start.click();
      await until(() => !ui.start.disabled);
      assert(ui.status.textContent.includes("permission was denied"), "No permission explanation");
      assert(ui.model.sent.length === 0, "Permission failure opened Azure");
    } finally {
      ui.cleanup();
      getMedia = async () => stream();
    }
  });

  await test("Backend, microphone, worklet, and audio-context failures release capture", async () => {
    for (const reason of ["backend", "microphone", "worklet", "context"]) {
      const ui = mount();
      try {
        await startRun(ui);
        if (reason === "backend") ui.model.receive("error", { message: "Azure request failed." });
        if (reason === "microphone") streams.at(-1).getTracks()[0].dispatchEvent(new Event("ended"));
        if (reason === "worklet") nodes.at(-1).emit({ type: "overflow" });
        if (reason === "context") {
          contexts.at(-1).state = "suspended";
          contexts.at(-1).dispatchEvent(new Event("statechange"));
        }
        assert(streams.at(-1).getTracks()[0].stopped, "Failure left microphone on");
        assert(!ui.start.disabled && ui.stop.disabled, "Failure left stale controls");
      } finally { ui.cleanup(); }
    }
  });

  await test("Demo time limit stops and finalizes; a new Start gets a new session", async () => {
    const ui = mount();
    try {
      await startRun(ui, 0.01);
      const first = ui.model.sent[0].run_id;
      await until(() => ui.model.sent.some((m) => m.type === "stop"));
      ui.model.receive("finished", { text: "" });
      ui.model.receive("closed", { complete: true });
      ui.start.click();
      await until(() => ui.model.sent.filter((m) => m.type === "start").length === 2);
      assert(ui.model.sent.findLast((m) => m.type === "start").run_id !== first, "Session ID reused");
    } finally { ui.cleanup(); }
  });

  await test("Lost kernel heartbeat stops the microphone", async () => {
    const ui = mount();
    const now = Date.now;
    try {
      await startRun(ui);
      Date.now = () => now() + 11000;
      await until(() => ui.status.textContent.includes("Kernel connection lost"));
      assert(streams.at(-1).getTracks()[0].stopped, "Lost connection left microphone on");
    } finally {
      Date.now = now;
      ui.cleanup();
    }
  });
} finally {
  window.AudioContext = originalContext;
  window.AudioWorkletNode = originalNode;
  if (originalMedia) Object.defineProperty(navigator, "mediaDevices", originalMedia);
  else delete navigator.mediaDevices;
}

document.title = report.some((line) => line.startsWith("FAIL")) ? "FAIL - live captions" : "PASS - live captions";
document.body.dataset.testResult = document.title.startsWith("PASS") ? "pass" : "fail";
