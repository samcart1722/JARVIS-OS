"use strict";

// Actual app.js + HTML via the shared DOM double. All fetches are controlled.
// This is browser-mock evidence, not native Windows/Edge acceptance.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const { createEnvironment } = require("./local_knowledge_command_assistance.js");
const golden = JSON.parse(fs.readFileSync(path.join(__dirname,
  "local_model_intent_preparation_vectors.json"), "utf8"));
const plain = (value) => JSON.parse(JSON.stringify(value));
const flush = async () => { for (let i = 0; i < 32; i += 1) await Promise.resolve(); };
let passed = 0, forbiddenAccesses = 0, implicitSubmissions = 0;
const unhandled = [];
process.on("unhandledRejection", (error) => unhandled.push(error));
const categories = new Set(), vectors = [];
const equal = (category, actual, expected) => {
  assert.deepEqual(plain(actual), plain(expected), category); passed++; categories.add(category);
};
const check = (category, value) => { assert.ok(value, category); passed++; categories.add(category); };
const semantic = (intent, fields) => ({ state: "candidate_accepted",
  candidate: { intent, fields, provenance: "local_model_assisted" } });
const recall = (key = "K") => semantic("RECALL_KNOWLEDGE", { key });
const base = { record_id: "synthetic-42", kind: "fact", key: "explicit-key",
  source_type: "manual", source_reference: "synthetic:42" };
const fieldNames = [...Object.keys(base), "value", "list_id", "item"];
const forbidden = () => { forbiddenAccesses++; throw new Error("Forbidden preparation authority"); };

function fixture() {
  const { scope, context } = createEnvironment();
  const get = (id) => scope.document.querySelector("#" + id);
  const fire = (id, type = "click") => get(id).dispatchEvent(
    new scope.Event(type, { bubbles: true, cancelable: true }));
  const calls = [], timers = new Map();
  let now = 0, timerIdentity = 0, aborts = 0;
  // Only this authorized harness owns these mocks; shared fixtures stay unchanged.
  scope.performance = { now: () => now };
  scope.setTimeout = (callback, delay) => {
    const id = ++timerIdentity;
    timers.set(id, { callback, due: now + delay });
    return id;
  };
  scope.clearTimeout = (id) => timers.delete(id);
  scope.AbortController = class extends AbortController {
    abort() { aborts++; super.abort(); }
  };
  async function advance(milliseconds) {
    const target = now + milliseconds;
    for (;;) {
      const due = [...timers].filter(([, timer]) => timer.due <= target)
        .sort((a, b) => a[1].due - b[1].due)[0];
      if (!due) break;
      now = due[1].due; timers.delete(due[0]); due[1].callback();
      await flush();
    }
    now = target;
    await flush();
  }
  let pureCalls = 0, sending = false;
  const realPrepare = scope.prepareBoundedNaturalLanguageIntent;
  scope.prepareBoundedNaturalLanguageIntent = (...args) => { pureCalls++; return realPrepare(...args); };
  for (const name of ["localStorage", "sessionStorage", "indexedDB", "gateway",
    "repository", "memory", "knowledge", "permissions", "workspace", "actor",
    "CognitiveProcessor", "ReasoningProvider", "provider", "readiness"]) {
    Object.defineProperty(scope, name, { get: forbidden, set: forbidden });
  }
  for (const id of ["proof", "cognitive-fallback"]) {
    const prop = id === "proof" ? "value" : "checked";
    let value = id === "proof" ? "synthetic-explicit-proof" : false;
    Object.defineProperty(get(id), prop, {
      get() { if (!sending) forbidden(); return value; },
      set(v) { if (!sending) forbidden(); value = v; },
    });
  }
  for (const match of fs.readFileSync(path.resolve(__dirname,
    "../../app/api/static/local_ui/index.html"), "utf8").matchAll(/\bid="([^"]+)"/gu)) {
    Object.defineProperty(get(match[1]), "innerHTML", { get: forbidden, set: forbidden });
    get(match[1]).insertAdjacentHTML = forbidden;
  }
  get("command-form").submit = get("command-form").requestSubmit = () => {
    implicitSubmissions++; throw new Error("Implicit Send");
  };
  scope.fetch = (url, options) => {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    calls.push({ url, options, resolve, reject });
    return promise;
  };
  const text = (value) => { get("natural-intent-input").value = value; fire("natural-intent-input", "input"); };
  const consent = (value) => { get("local-model-consent").checked = value; fire("local-model-consent", "change"); };
  const explicit = (name, value) => {
    const id = "natural-field-" + name.replaceAll("_", "-");
    get(id + "-row").hidden = false; get(id).disabled = false; get(id).value = value;
    fire(id, name === "kind" ? "change" : "input");
  };
  const interpret = (value) => { if (value !== undefined) text(value); fire("natural-intent-prepare"); };
  const result = () => plain(vm.runInContext("naturalProposal.result", context));
  const state = () => get("natural-intent-result").getAttribute("data-natural-state");
  const guide = () => vm.runInContext("JSON.stringify(guidedState)", context);
  async function answer(value, options = {}) {
    const call = options.call || calls.at(-1);
    if (options.error) call.reject(new Error("SECRET_PROVIDER_PROMPT"));
    else call.resolve({ ok: options.ok !== false,
      headers: { get: () => options.contentType || "application/json" },
      text: options.text || (async () => options.raw === undefined ? JSON.stringify(value) : options.raw),
      json: async () => value });
    await flush();
  }
  const send = () => { sending = true; try { fire("command-form", "submit"); } finally { sending = false; } };
  const record = (name) => {
    const r = result();
    check("complete-command", r.outcome === "prepared");
    vectors.push({ name, intent: r.intent, fields: r.fields, command: get("command").value });
  };
  const snapshot = () => [get("command").value, get("command-state").textContent,
    get("natural-intent-status").textContent, state(), guide(),
    vm.runInContext("JSON.stringify(naturalProposal)", context),
    get("guided-status").textContent, get("preparation-status").textContent,
    get("preparation-error").textContent, get("follow-up-error").textContent,
    get("natural-intent-result").hidden,
    Object.values(plain(vm.runInContext("Object.fromEntries(Object.entries(naturalFields).map(([name, {input,row}]) => [name, [input.value,input.disabled,row.hidden]]))", context))),
    Object.values(plain(vm.runInContext("Object.fromEntries(Object.entries(naturalOutputs).map(([name, output]) => [name,output.textContent]))", context))),
    get("assist-operation").value,
    [...Object.keys(base), "value"].map((field) => {
      const input = get("assist-" + field.replaceAll("_", "-"));
      return [input.value, input.disabled];
    }), [get("follow-up-list-id").value, get("follow-up-item").value,
      get("follow-up-list-id").disabled, get("follow-up-item").disabled]];
  return { scope, context, get, fire, calls, text, consent, explicit, interpret, result,
    answer, state, guide, send, record, snapshot, advance, timers,
    jump: (milliseconds) => { now += milliseconds; },
    aborts: () => aborts, pureCalls: () => pureCalls };
}

function request(h, text = "Busca K") {
  const before = h.calls.length, beforePure = h.pureCalls();
  h.consent(true); h.interpret(text);
  equal("one-request", h.calls.length, before + 1);
  equal("deterministic-first", h.pureCalls(), beforePure + 1);
  equal("pending-visible", h.state(), "pending");
  check("pending-editable", !h.get("command").disabled && !h.get("natural-intent-input").disabled
    && !h.get("natural-intent-reject").disabled && !h.get("local-model-consent").disabled);
}

// Set up Follow-up through real Capture, FIND selection and READ events. Sends
// below are explicit DOM submissions to controlled fetches, never application I/O.
async function guidedRecallReady(r) {
  for (const [name, value] of Object.entries({ ...base, value: "synthetic value" })) {
    const id = "assist-" + name.replaceAll("_", "-");
    r.get(id).value = value; r.fire(id, "input");
  }
  const record = { record_id: base.record_id, kind: base.kind,
    key: base.key, value: "synthetic value" };
  r.fire("prepare-command"); r.send();
  await r.answer({ success: true, projection: { kind: "knowledge",
    operation: "store", created: true, record } });
  r.get("assist-operation").value = "find"; r.fire("assist-operation", "change");
  r.get("assist-key").value = base.key; r.fire("assist-key", "input");
  r.fire("prepare-command"); r.send();
  await r.answer({ success: true, projection: { kind: "knowledge",
    operation: "find", records: [record], truncated: false } });
  r.get("knowledge-records").children[0].children[1].dispatchEvent(new r.scope.Event("click"));
  r.send();
  await r.answer({ success: true, projection: { kind: "knowledge", operation: "read", record } });
  equal("guided-real-event-setup", r.get("guided-recall").getAttribute("data-guide-state"), "completed");
}

async function main() {
  let h = fixture();
  equal("default-off", h.get("local-model-consent").checked, false);
  equal("startup-no-request", h.calls.length, 0);
  h.consent(true);
  equal("session-reset", fixture().get("local-model-consent").checked, false);
  const source = fs.readFileSync(path.resolve(__dirname, "../../app/api/static/local_ui/app.js"), "utf8");
  check("no-persistence", !/localStorage|sessionStorage|indexedDB/u.test(source));
  h.interpret("Qué sabes de K");
  equal("deterministic-prepared", [h.result().outcome, h.calls.length], ["prepared", 0]);
  equal("deterministic-provenance", h.get("natural-intent-provenance").textContent, "Deterministic");
  h.interpret("Recuerda que X");
  equal("deterministic-clarification", [h.result().outcome, h.calls.length], ["clarification_required", 0]);
  for (const vector of golden.filter((v) => v.decision === "protected")) {
    h.interpret(vector.text);
    equal("protected-zero-calls", h.calls.length, 0);
  }
  h.consent(false); h.interpret("Busca K");
  equal("eligible-off", [h.result().outcome, h.calls.length], ["unsupported", 0]);

  h = fixture(); request(h, "\u0085Busca K\u001c");
  const call = h.calls[0], body = JSON.parse(call.options.body);
  equal("text-only", body, { text: "\u0085Busca K\u001c" });
  equal("endpoint", call.url, "/local/intent-preparation");
  equal("transport", [call.options.method, call.options.mode, call.options.credentials,
    call.options.headers], ["POST", "same-origin", "same-origin",
    { "Content-Type": "application/json", "X-Luxiom-CSRF": "synthetic-sprint37-csrf" }]);
  h.fire("natural-intent-prepare"); h.fire("natural-intent-prepare");
  equal("duplicate-no-request", h.calls.length, 1);
  equal("duplicate-deterministic-first", h.pureCalls(), 3);
  await h.answer(recall());
  h.record("recall-exact");
  equal("literal-provenance", h.get("natural-intent-provenance").textContent,
    "Local-model assisted (local_model_assisted)");
  equal("recall-exact-key", h.get("command").value, 'knowledge find :: {"key":"K"}');
  h.explicit("kind", "concept"); h.interpret();
  equal("explicit-retry-only", h.calls.length, 2);
  await h.answer(recall());
  h.record("recall-kind");
  equal("recall-kind", h.get("command").value, 'knowledge find :: {"key":"K","kind":"concept"}');
  h.get("command").value = "  list read manual-visible  "; h.fire("command", "input");
  const exactEditor = h.get("command").value;
  const beforeSendPureCalls = h.pureCalls();
  h.send();
  const sent = h.calls.at(-1);
  equal("send-only-boundary", sent.url, "/local/command");
  equal("send-exact-editor-envelope", JSON.parse(sent.options.body),
    { proof: "synthetic-explicit-proof", requested_workspace_id: "luxiom-local-dev-workspace",
      text: exactEditor, allow_cognitive_fallback: false });
  equal("no-reinterpret-on-send", h.pureCalls(), beforeSendPureCalls);
  // Keep authority instrumentation open only around the explicit Send handler.
  await h.answer({ success: true, route: "local", response: "synthetic", error: null });

  h = fixture(); h.get("command").value = "list read retained";
  request(h, "Conserva <svg onload=alert(1)> é e\u0301 😀");
  await h.answer(semantic("CAPTURE_KNOWLEDGE", { value: "<svg onload=alert(1)> é e\u0301 😀" }));
  equal("capture-metadata", h.result().missingFields, Object.keys(base));
  equal("clarification-editor-retained", h.get("command").value, "list read retained");
  for (const [name, value] of Object.entries(base)) h.explicit(name, value);
  h.interpret(); await h.answer(semantic("CAPTURE_KNOWLEDGE", { value: "<svg onload=alert(1)> é e\u0301 😀" }));
  h.record("capture-literal");
  equal("literal-rendering", h.get("natural-intent-extracted-fields").children.length, 0);
  equal("capture-value-only", JSON.parse(h.get("command").value.split(" :: ")[1]),
    { ...base, value: "<svg onload=alert(1)> é e\u0301 😀" });
  const generated = h.get("command").value;
  h.fire("natural-intent-reject");
  equal("reject-untouched", h.get("command").value, "");
  for (const editBack of [false, true]) {
    const r = fixture(); request(r); await r.answer(recall());
    const command = r.get("command").value;
    r.get("command").value = "list read manual"; r.fire("command", "input");
    if (editBack) { r.get("command").value = command; r.fire("command", "input"); }
    const current = r.get("command").value;
    r.fire("natural-intent-reject");
    equal(editBack ? "reject-edit-back" : "reject-manual", r.get("command").value, current);
  }
  check("capture-no-authority", !generated.includes("synthetic-explicit-proof"));

  for (const [text, candidate, command] of [
    ["Incorpora pan a la lista Compras", semantic("ADD_FOLLOW_UP", { item: "pan", list_id: "Compras" }), "list add Compras :: pan"],
    ["¿Consulta la lista Compras?", semantic("READ_FOLLOW_UP", { list_id: "Compras" }), "list read Compras"],
    ["Incorpora \"dato\" :: \\ruta\nsegunda línea a la lista L",
      semantic("ADD_FOLLOW_UP", { item: '"dato" :: \\ruta\nsegunda línea', list_id: "L" }),
      'list add L :: "dato" :: \\ruta\nsegunda línea'],
  ]) {
    const r = fixture(); request(r, text); await r.answer(candidate);
    r.record(candidate.candidate.intent);
    equal("list-builders", r.get("command").value, command);
  }
  // Existing explicit controls conflict; the candidate never silently wins.
  h = fixture(); h.explicit("list_id", "Other"); request(h, "Consulta la lista Compras");
  await h.answer(semantic("READ_FOLLOW_UP", { list_id: "Compras" }));
  equal("explicit-conflict", h.result().conflictingFields, ["list_id"]);
  equal("no-conflicting-command", h.get("command").value, "");

  for (const state of ["unsupported", "provider_unavailable", "provider_failure"]) {
    h = fixture(); h.get("command").value = "list read previous"; request(h);
    await h.answer({ state, candidate: null });
    equal("failure-state", h.result().outcome, state);
    equal("failure-provenance", h.get("natural-intent-provenance").textContent, "Local-model assistance");
    equal("failure-retention", h.get("command").value, "list read previous");
    equal("failure-no-retry", h.calls.length, 1);
    h.fire("natural-intent-reject");
    equal("reject-failure-retains", h.get("command").value, "list read previous");
  }
  const malformed = [
    null, [], {}, { state: "unknown", candidate: null }, { ...recall(), command: "list read hidden" },
    { state: "unsupported", candidate: {} }, { state: "candidate_accepted", candidate: null },
    semantic("DELETE", {}), semantic("RECALL_KNOWLEDGE", { key: "invented" }),
    semantic(["RECALL_KNOWLEDGE"], { key: "K" }), semantic(1, {}), semantic({}, {}),
    semantic("RECALL_KNOWLEDGE", { key: "k" }),
    semantic("RECALL_KNOWLEDGE", { key: "K".repeat(8193) }),
    semantic("RECALL_KNOWLEDGE", { key: null }), semantic("RECALL_KNOWLEDGE", { key: [] }),
    semantic("RECALL_KNOWLEDGE", { key: " " }), semantic("RECALL_KNOWLEDGE", { key: "\ud800" }),
    semantic("RECALL_KNOWLEDGE", { key: "K", kind: "fact" }),
    semantic("RECALL_KNOWLEDGE", { key: "K", command: "list read bad" }),
    semantic("CAPTURE_KNOWLEDGE", { value: "K", record_id: "invented" }),
    { state: "candidate_accepted", candidate: { intent: "RECALL_KNOWLEDGE", fields: { key: "K" }, provenance: "trusted" } },
    { state: "candidate_accepted", candidate: { intent: "RECALL_KNOWLEDGE", fields: { key: "K" }, provenance: "local_model_assisted", proof: "fake" } },
  ];
  for (const value of malformed) {
    h = fixture(); h.get("command").value = "list read previous"; request(h);
    await h.answer(value);
    equal("closed-malformed", h.result().outcome, "provider_failure");
    equal("malformed-retains", h.get("command").value, "list read previous");
    check("fixed-failure-message", !h.get("natural-intent-status").textContent.includes("SECRET"));
    equal("malformed-no-retry", h.calls.length, 1);
  }
  for (const options of [
    { raw: "SECRET_PROVIDER_PROMPT" }, { raw: JSON.stringify(recall()) + "{}" },
    { raw: '{"state":"unsupported","state":"candidate_accepted","candidate":null}' },
    { raw: '{"state":"unsupported","\\u0073tate":"unsupported","candidate":null}' },
    { raw: '{"state":"candidate_accepted","candidate":{"intent":"RECALL_KNOWLEDGE","fields":{"key":"K","key":"K"},"provenance":"local_model_assisted"}}' },
    { raw: " ".repeat(262145) }, { error: true }, { ok: false }, { contentType: "text/html" },
  ]) {
    h = fixture(); h.get("command").value = "list read previous"; request(h);
    await h.answer(null, options);
    equal("wire-failure", h.result().outcome, "provider_failure");
    equal("wire-failure-retains", h.get("command").value, "list read previous");
    check("sanitized-error", !h.get("natural-intent-status").textContent.includes("SECRET"));
  }
  for (const [text, candidate] of [
    ["Consulta Compras", semantic("READ_FOLLOW_UP", { list_id: "Compras" })],
    ["Consulta la lista Compras", semantic("READ_FOLLOW_UP", { list_id: "Consulta" })],
    ['Consulta "la lista Compras"', semantic("READ_FOLLOW_UP", { list_id: "Compras" })],
    ["Incorpora pan a la lista Compras", semantic("ADD_FOLLOW_UP", { item: "Compras", list_id: "Compras" })],
    ["Incorpora pan | leche a la lista Compras", semantic("ADD_FOLLOW_UP", { item: "pan | leche", list_id: "Compras" })],
    ["Consulta la lista dos palabras", semantic("READ_FOLLOW_UP", { list_id: "dos palabras" })],
  ]) {
    h = fixture(); h.consent(true); h.interpret(text); await h.answer(candidate);
    check("list-source-constraints", h.result().outcome !== "prepared");
    equal("list-invalid-no-command", h.get("command").value, "");
  }
  for (const intent of ["CAPTURE_KNOWLEDGE", "RECALL_KNOWLEDGE", "ADD_FOLLOW_UP", "READ_FOLLOW_UP"]) {
    h = fixture(); request(h); await h.answer(semantic(intent, {}));
    equal("partial-clarification", h.result().outcome, "clarification_required");
    equal("partial-no-command", h.get("command").value, "");
  }
  h = fixture(); h.consent(true);
  h.get("command").value = "list read previous";
  h.scope.document.querySelector('meta[name="luxiom-csrf"]').setAttribute("content", "");
  h.interpret("Busca K"); await flush();
  equal("missing-csrf-zero-calls", h.calls.length, 0);
  equal("missing-csrf-retains", h.get("command").value, "list read previous");

  // Every event invalidates by revision, including value edit-back. Old success,
  // malformed response and rejected promise must all leave the new state intact.
  const raceChecksStart = passed;
  const mutations = {
    natural: (r) => r.text("Busca Changed"),
    "natural-edit-back": (r) => { r.text("Busca Changed"); r.text("Busca K"); },
    consent: (r) => r.consent(false),
    "consent-edit-back": (r) => { r.consent(false); r.consent(true); },
    reject: (r) => r.fire("natural-intent-reject"),
    manual: (r) => { r.get("command").value = "list read manual"; r.fire("command", "input"); },
    "manual-edit-back": (r) => { const t = r.get("command").value;
      r.get("command").value = "list read changed"; r.fire("command", "input");
      r.get("command").value = t; r.fire("command", "input"); },
    "new-interpretation": (r) => r.interpret("Qué sabes de Newer"),
    "new-eligible-no-queue": (r) => r.interpret("Busca Newer"),
    replacement: (r) => { r.get("assist-operation").value = "read"; r.fire("assist-operation", "change");
      r.get("assist-record-id").value = "replacement"; r.fire("prepare-command"); },
    "guide-reset": (r) => r.fire("guided-reset"),
    "helper-operation": (r) => { r.get("assist-operation").value = "read"; r.fire("assist-operation", "change"); },
    "helper-operation-edit-back": (r) => {
      r.get("assist-operation").value = "read"; r.fire("assist-operation", "change");
      r.get("assist-operation").value = "store"; r.fire("assist-operation", "change");
    },
    "helper-failed-store": (r) => {
      r.fire("prepare-command");
      check("failed-helper-validation", r.get("preparation-error").textContent !== "");
    },
    "helper-failed-read": (r) => {
      r.fire("prepare-command");
      check("failed-helper-validation", r.get("preparation-error").textContent !== "");
    },
    "guided-state-failed": (r) => {
      r.fire("prepare-command");
      equal("guided-failure-state", r.get("guided-capture").getAttribute("data-guide-state"), "failed");
    },
    "follow-up-list": (r) => { r.get("follow-up-list-id").value = "changed"; r.fire("follow-up-list-id", "input"); },
    "follow-up-item": (r) => { r.get("follow-up-item").value = "changed"; r.fire("follow-up-item", "input"); },
    "follow-up-edit-back": (r) => {
      r.get("follow-up-item").value = "changed"; r.fire("follow-up-item", "input");
      r.get("follow-up-item").value = ""; r.fire("follow-up-item", "input");
    },
    "follow-up-failed": (r) => {
      r.fire("prepare-follow-up");
      check("failed-follow-up-validation", r.get("follow-up-error").textContent !== "");
    },
    "guided-reset-after-recall": (r) => r.fire("guided-reset"),
  };
  for (const field of [...Object.keys(base), "value"]) {
    const id = "assist-" + field.replaceAll("_", "-");
    mutations["helper-field-" + field] = (r) => {
      r.get(id).value = "changed"; r.fire(id, "input");
    };
    mutations["helper-edit-back-" + field] = (r) => {
      const original = r.get(id).value;
      r.get(id).value = "changed"; r.fire(id, "input");
      r.get(id).value = original; r.fire(id, "input");
    };
  }
  mutations["helper-kind-change"] = (r) => {
    r.get("assist-kind").value = "concept"; r.fire("assist-kind", "change");
  };
  for (const field of fieldNames) mutations["field-" + field] = (r) => r.explicit(field, "changed");
  for (const [name, mutate] of Object.entries(mutations)) {
    for (const outcome of ["accepted", "malformed", "rejected", "timeout"]) {
      const r = fixture();
      if (name.startsWith("follow-up-") || name === "guided-reset-after-recall") await guidedRecallReady(r);
      if (name === "helper-failed-read") {
        r.get("assist-operation").value = "read"; r.fire("assist-operation", "change");
      }
      const before = r.calls.length;
      r.get("command").value = "list read previous"; request(r);
      mutate(r);
      const snapshot = r.snapshot();
      if (outcome === "accepted") await r.answer(recall());
      else if (outcome === "timeout") await r.advance(35000);
      else await r.answer(null, outcome === "malformed" ? { raw: "bad" } : { error: true });
      equal("stale-" + name, r.snapshot(), snapshot);
      equal("no-queued-request", r.calls.length, before + 1);
      equal("pending-slot-cleanup", vm.runInContext("localAssistancePending", r.context), null);
      equal("stale-timer-cleanup", r.timers.size, 0);
      // A new explicit attempt after settlement is allowed, never automatic.
      r.fire("natural-intent-reject");
      r.consent(true); r.interpret("Busca K");
      equal("fresh-explicit-after-stale", r.calls.length, before + 2);
      await r.answer(recall());
      equal("new-proposal", r.result().outcome, "prepared");
    }
  }
  const raceChecks = passed - raceChecksStart;
  // Delayed body parsing is also correlated, not merely the fetch promise.
  h = fixture(); request(h);
  let finishBody;
  await h.answer(null, { text: () => new Promise((resolve) => { finishBody = resolve; }) });
  h.interpret("Qué sabes de Newer");
  const newer = [h.get("command").value, h.get("natural-intent-status").textContent];
  finishBody(JSON.stringify(recall())); await flush();
  equal("late-body-correlation", [h.get("command").value, h.get("natural-intent-status").textContent], newer);

  const correctionChecksStart = passed;
  // Absolute deadline spans fetch AND body reading; no dependency on real sleeps.
  for (const phase of ["fetch", "body"]) {
    for (const late of ["accepted", "rejected", "malformed"]) {
      for (const order of ["newer-pending", "newer-settled"]) {
        const r = fixture(); r.get("command").value = "list read manual"; request(r);
        const old = r.calls[0];
        let finishBody, rejectBody;
        if (phase === "body") {
          await r.advance(10000);
          await r.answer(null, { text: () => new Promise((resolve, reject) => {
            finishBody = resolve; rejectBody = reject;
          }) });
        }
        r.fire("natural-intent-prepare"); r.fire("natural-intent-prepare");
        equal("deadline-duplicate-one-request", r.calls.length, 1);
        await r.advance(phase === "body" ? 24999 : 34999);
        equal("absolute-deadline-not-early", r.state(), "pending");
        equal("deadline-one-timer", r.timers.size, 1);
        await r.advance(1);
        equal("deadline-finalized", vm.runInContext("localAssistancePending", r.context), null);
        equal("deadline-fixed-failure", r.result().outcome, "provider_failure");
        equal("deadline-safe-message", r.get("natural-intent-status").textContent,
          "Local-model assistance: Local assistance failed. Editor retained; no new command prepared.");
        equal("deadline-manual-retention", r.get("command").value, "list read manual");
        equal("deadline-abort", [old.options.signal.aborted, r.aborts()], [true, 1]);
        equal("deadline-timer-cleanup", r.timers.size, 0);
        equal("deadline-no-retry", r.calls.length, 1);
        // A new explicit attempt is admitted; old physical work may still exist.
        request(r, "Busca Newer");
        const newIdentity = vm.runInContext("localAssistancePending.identity", r.context);
        if (order === "newer-settled") await r.answer(recall("Newer"));
        const snapshot = r.snapshot();
        if (phase === "fetch") {
          await r.answer(recall(), { call: old,
            ...(late === "rejected" ? { error: true } : late === "malformed" ? { raw: "bad" } : {}) });
        } else {
          if (late === "rejected") rejectBody(new Error("SECRET_LATE_BODY"));
          else finishBody(late === "malformed" ? "bad" : JSON.stringify(recall()));
          await flush();
        }
        equal("expired-" + phase + "-" + late + "-" + order, r.snapshot(), snapshot);
        equal("old-cleanup-cannot-release-new-slot",
          vm.runInContext("localAssistancePending?.identity ?? null", r.context),
          order === "newer-pending" ? newIdentity : null);
        equal("old-cleanup-cannot-clear-new-timer", r.timers.size, order === "newer-pending" ? 1 : 0);
        equal("expired-no-retry-no-send", r.calls.map((c) => c.url),
          ["/local/intent-preparation", "/local/intent-preparation"]);
        if (order === "newer-pending") await r.answer(recall("Newer"));
        equal("recovered-new-proposal", r.get("command").value, 'knowledge find :: {"key":"Newer"}');
        equal("new-settlement-cleans-timer", r.timers.size, 0);
      }
    }
  }
  // Wall-clock progress still expires a response if the timer callback was delayed.
  for (const phase of ["fetch", "body"]) {
    const r = fixture(); request(r);
    let finish;
    if (phase === "body") await r.answer(null, { text: () => new Promise((resolve) => { finish = resolve; }) });
    r.jump(35000);
    if (phase === "fetch") await r.answer(recall());
    else { finish(JSON.stringify(recall())); await flush(); }
    equal("delayed-timer-cannot-accept-" + phase, r.result().outcome, "provider_failure");
    equal("delayed-timer-aborts", r.calls[0].options.signal.aborted, true);
    equal("delayed-timer-cleans-slot", vm.runInContext("localAssistancePending", r.context), null);
  }
  for (const mode of ["sync-throw", "abort-rejection"]) {
    const r = fixture();
    if (mode === "sync-throw") r.scope.fetch = () => { throw new Error("SECRET_SYNC_FETCH"); };
    if (mode === "sync-throw") { r.consent(true); r.interpret("Busca K"); }
    else request(r);
    if (mode === "abort-rejection") {
      r.calls[0].options.signal.addEventListener("abort", () =>
        r.calls[0].reject(Object.assign(new Error("SECRET_ABORT"), { name: "AbortError" })));
      await r.advance(35000);
    } else await flush();
    equal("safe-" + mode, r.result().outcome, "provider_failure");
    check("sanitized-" + mode, !r.get("natural-intent-status").textContent.includes("SECRET"));
    equal("cleanup-" + mode, [vm.runInContext("localAssistancePending", r.context), r.timers.size], [null, 0]);
  }
  const deadlineChecks = passed - correctionChecksStart;

  for (const length of [8191, 8192, 8193]) {
    const r = fixture();
    const overhead = 'knowledge find :: {"key":""}'.length;
    const key = "😀".repeat(length - overhead);
    request(r, "Busca " + key); await r.answer(recall(key));
    equal("model-command-budget", r.result().outcome, length <= 8192 ? "prepared" : "unsupported");
    if (length <= 8192) {
      equal("model-command-codepoints", Array.from(r.get("command").value).length, length);
      // Keep very long command vectors out of stdout; Python's existing shared
      // builder suite separately checks the same complete-command budgets.
    } else equal("oversize-editor-retained", r.get("command").value, "");
  }
  for (const [field, value] of [["kind", "invalid"], ["record_id", "\ud800"],
    ["source_reference", '"'.repeat(4096)]]) {
    const r = fixture(); r.consent(true); r.interpret("Conserva X");
    await r.answer(semantic("CAPTURE_KNOWLEDGE", { value: "X" }));
    for (const [key, text] of Object.entries({ ...base, [field]: value })) r.explicit(key, text);
    r.interpret(); await r.answer(semantic("CAPTURE_KNOWLEDGE", { value: "X" }));
    check("model-explicit-validation", r.result().outcome !== "prepared");
    equal("model-invalid-metadata-no-command", r.get("command").value, "");
  }
  h = fixture(); h.get("command").value = "list read retained";
  request(h);
  const lateAssistance = h.calls[0];
  h.send();
  equal("pending-explicit-send", h.calls.length, 2);
  const sendSnapshot = [h.get("command").value, h.get("natural-intent-status").textContent,
    h.state(), h.guide()];
  await h.answer(recall(), { call: lateAssistance });
  equal("late-response-during-send", [h.get("command").value,
    h.get("natural-intent-status").textContent, h.state(), h.guide()], sendSnapshot);
  equal("pending-no-automatic-send", h.calls.length, 2);
  await h.answer({ success: true, route: "local", response: "synthetic", error: null });
  equal("send-retains-editor", h.get("command").value, "list read retained");

  await new Promise((resolve) => setImmediate(resolve));
  equal("zero-unhandled-rejections", unhandled.length, 0);
  equal("zero-authority-access", forbiddenAccesses, 0);
  equal("zero-implicit-send", implicitSubmissions, 0);
  return { environment: "node-dom-double", passed, categories: [...categories], vectors,
    forbiddenAccesses, implicitSubmissions, actualRequests: 0, raceChecks, deadlineChecks,
    clientTimeoutMs: 35000, unhandledRejections: unhandled.length,
    nativeBrowserVerified: false, nativeKeyboardVerified: false, goldenVectors: golden.length };
}

if (process.argv.includes("--parity")) {
  const { scope, context } = createEnvironment();
  const texts = JSON.parse(fs.readFileSync(0, "utf8"));
  scope.document = new Proxy({}, { get: forbidden, set: forbidden });
  scope.fetch = forbidden;
  for (const name of ["localStorage", "sessionStorage", "gateway", "permissions", "provider"]) {
    Object.defineProperty(scope, name, { get: forbidden, set: forbidden });
  }
  const classifications = texts.map((text) => plain(scope.assessLocalIntentEligibility(text)));
  const ranges = [];
  let start = null;
  for (let p = 0; p <= 0x110000; p++) {
    const yes = p < 0x110000 && scope.localLetterOrNumber(p);
    if (yes && start === null) start = p;
    if (!yes && start !== null) { ranges.push([start, p - 1]); start = null; }
  }
  process.stdout.write(JSON.stringify({ classifications, ranges, forbiddenAccesses,
    keywordText: vm.runInContext('boundedKeywordText("ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑİK")', context) }));
} else {
  main().then((e) => process.stdout.write(JSON.stringify(e)))
    .catch((error) => { process.stderr.write(error.stack); process.exitCode = 1; });
}
