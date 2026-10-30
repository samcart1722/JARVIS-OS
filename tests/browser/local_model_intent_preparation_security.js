"use strict";
// Block D: actual app.js, controlled DOM/transport/clock; never native acceptance.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const { createEnvironment } = require("./local_knowledge_command_assistance.js");
const flush = async () => { for (let i = 0; i < 40; i++) await Promise.resolve(); };
let checks = 0, forbiddenAccesses = 0;
const check = (value, message) => { assert.ok(value, message); checks++; };
const same = (a, b, message) => { assert.deepEqual(JSON.parse(JSON.stringify(a)), b, message); checks++; };
function fixture() {
  const { scope, context } = createEnvironment();
  const get = (id) => scope.document.querySelector("#" + id);
  const fire = (id, type = "click") => get(id).dispatchEvent(new scope.Event(type, { bubbles: true, cancelable: true }));
  let now = 0, id = 0, sending = false;
  const timers = new Map(), calls = [];
  scope.performance = { now: () => now };
  scope.setTimeout = (fn, delay) => { timers.set(++id, { fn, due: now + delay }); return id; };
  scope.clearTimeout = (key) => timers.delete(key);
  scope.AbortController = AbortController;
  const forbidden = () => { forbiddenAccesses++; throw new Error("Forbidden authority"); };
  for (const key of ["localStorage", "sessionStorage", "indexedDB", "repository", "memory",
    "gateway", "workspace", "actor", "permissions", "CognitiveProcessor", "provider", "readiness"])
    Object.defineProperty(scope, key, { get: forbidden, set: forbidden });
  for (const key of ["proof", "cognitive-fallback"]) {
    Object.defineProperty(get(key), key === "proof" ? "value" : "checked", {
      get: () => { if (!sending) forbidden(); return key === "proof" ? "synthetic-D-proof" : false; },
      set: () => { if (!sending) forbidden(); },
    });
  }
  for (const match of fs.readFileSync("app/api/static/local_ui/index.html", "utf8").matchAll(/\bid="([^"]+)"/gu))
    Object.defineProperty(get(match[1]), "innerHTML", { set: forbidden, get: forbidden });
  get("command-form").submit = get("command-form").requestSubmit = forbidden;
  scope.fetch = (url, options) => {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    calls.push({ url, options, resolve, reject });
    return promise;
  };
  const text = (value) => { get("natural-intent-input").value = value; fire("natural-intent-input", "input"); };
  const consent = (value) => { get("local-model-consent").checked = value; fire("local-model-consent", "change"); };
  const interpret = (value) => { if (value !== undefined) text(value); fire("natural-intent-prepare"); };
  const explicit = (fields) => {
    for (const [name, value] of Object.entries(fields)) {
      const key = "natural-field-" + name.replaceAll("_", "-");
      get(key + "-row").hidden = false; get(key).disabled = false; get(key).value = value;
      fire(key, name === "kind" ? "change" : "input");
    }
  };
  const answer = async (envelope, call = calls.at(-1), body) => {
    call.resolve({ ok: true, headers: { get: () => "application/json" },
      text: body || (() => Promise.resolve(JSON.stringify(envelope))) });
    await flush();
  };
  const advance = async (delta, dispatch = true) => {
    now += delta;
    if (dispatch) for (const [key, timer] of [...timers]) {
      if (timer.due <= now) { timers.delete(key); timer.fn(); }
    }
    await flush();
  };
  const snapshot = () => JSON.stringify([get("command").value, get("natural-intent-status").textContent,
    vm.runInContext("naturalProposal", context), vm.runInContext("guidedState", context)]);
  const send = () => { sending = true; try { fire("command-form", "submit"); } finally { sending = false; } };
  return { scope, context, get, fire, calls, timers, text, consent, interpret, explicit, answer, advance, snapshot, send };
}
const envelope = (key = "K") => ({ state: "candidate_accepted", candidate: {
  intent: "RECALL_KNOWLEDGE", fields: { key }, provenance: "local_model_assisted" } });
async function main() {
  const input = process.argv.includes("--commands") ? JSON.parse(fs.readFileSync(0, "utf8")) : [];
  const commands = [];
  for (const row of input) {
    const h = fixture(); h.consent(true); h.explicit(row.explicit || {}); h.interpret(row.text);
    same(h.calls.length, 1, "eligible endpoint request");
    same(JSON.parse(h.calls[0].options.body), { text: row.text }, "text only");
    check(h.calls[0].options.headers["X-Luxiom-CSRF"] === "synthetic-sprint37-csrf", "runtime CSRF");
    await h.answer(row.envelope);
    commands.push({ text: h.get("command").value, result: vm.runInContext("naturalProposal.result", h.context) });
    same(h.calls.length, 1, "no automatic Send");
  }
  const golden = JSON.parse(fs.readFileSync("tests/browser/local_model_intent_preparation_vectors.json", "utf8"));
  let h = fixture();
  same(h.get("local-model-consent").checked, false, "fresh OFF");
  h.consent(true);
  same(fixture().get("local-model-consent").checked, false, "new session OFF");
  for (const row of golden.filter((r) => typeof r.text === "string" && r.decision === "protected")) {
    h.interpret(row.text);
    same(h.calls.length, 0, "protected => zero fetch");
  }
  h.consent(false); h.interpret("Busca K"); same(h.calls.length, 0, "OFF => zero fetch");
  // Positive response just BEFORE deadline, then old timer must be gone.
  for (const phase of ["fetch", "body"]) {
    h = fixture(); h.consent(true); h.interpret("Busca K");
    let bodyResolve;
    if (phase === "body") await h.answer(null, h.calls[0], () => new Promise((resolve) => { bodyResolve = resolve; }));
    await h.advance(34999, false);
    if (phase === "fetch") await h.answer(envelope());
    else { bodyResolve(JSON.stringify(envelope())); await flush(); }
    same(h.get("command").value, 'knowledge find :: {"key":"K"}', "valid before deadline");
    same(h.timers.size, 0, "success timer cleaned");
    const snapshot = h.snapshot();
    await h.advance(100);
    same(h.snapshot(), snapshot, "no expired cleanup after success");
  }
  // Both fulfilled promises become observable in different orders at/after deadline.
  for (const phase of ["fetch", "body"]) for (const timerFirst of [false, true]) for (const delta of [35000, 35001]) {
    h = fixture(); h.get("command").value = "list read manual";
    h.consent(true); h.interpret("Busca K");
    let bodyResolve;
    if (phase === "body") await h.answer(null, h.calls[0], () => new Promise((resolve) => { bodyResolve = resolve; }));
    await h.advance(delta, timerFirst);
    if (phase === "fetch") await h.answer(envelope());
    else { bodyResolve(JSON.stringify(envelope())); await flush(); }
    same(h.get("command").value, "list read manual", "deadline never publishes");
    same(vm.runInContext("naturalProposal.result.outcome", h.context), "provider_failure", "safe terminal outcome");
    same(vm.runInContext("localAssistancePending", h.context), null, "slot recovered");
    same(h.calls.length, 1, "no retry");
    check(h.calls[0].options.signal.aborted, "abort requested");
    h.interpret("Busca K"); same(h.calls.length, 2, "new explicit admission");
    await h.answer(envelope());
  }
  // Hostile literals stay inert, then Send uses exactly the manually visible text.
  h = fixture(); h.consent(true); h.interpret("Busca K"); await h.answer(envelope());
  const manual = "  list read explicit-manual  ";
  h.get("command").value = manual; h.fire("command", "input");
  h.send();
  same(h.calls.at(-1).url, "/local/command", "explicit Send only");
  same(JSON.parse(h.calls.at(-1).options.body), { proof: "synthetic-D-proof",
    requested_workspace_id: "luxiom-local-dev-workspace", text: manual,
    allow_cognitive_fallback: false }, "exact unchanged execution envelope");
  same(forbiddenAccesses, 0, "zero authority accesses");
  return { checks, commands, forbiddenAccesses, nativeBrowserVerified: false, realProviderCalls: 0 };
}
main().then((value) => process.stdout.write(JSON.stringify(value)))
  .catch((error) => { process.stderr.write(error.stack); process.exitCode = 1; });
