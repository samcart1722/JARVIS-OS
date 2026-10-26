"use strict";

// Actual HTML/app.js via the established Node VM/DOM double. No native claims.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { createEnvironment } = require("./local_knowledge_command_assistance.js");
const html = fs.readFileSync(path.resolve(__dirname, "../../app/api/static/local_ui/index.html"), "utf8");
const { scope, context } = createEnvironment();
const get = (id) => scope.document.querySelector(`#${id}`);
const fields = ["record_id", "kind", "key", "value", "source_type", "source_reference", "list_id", "item"];
const fieldId = (field) => `natural-field-${field.replaceAll("_", "-")}`;
const fieldInput = (field) => get(fieldId(field));
const row = (field) => get(`${fieldId(field)}-row`);
const input = get("natural-intent-input");
const editor = get("command");
const prepareButton = get("natural-intent-prepare");
const rejectButton = get("natural-intent-reject");
const categories = new Set();
let passed = 0;
let actualRequests = 0;
let forbiddenAccesses = 0;
let formSubmissions = 0;
let preparationCalls = 0;
let lastExplicitFields;
const check = (category, condition, message) => {
  assert.ok(condition, `${category}: ${message}`);
  categories.add(category);
  passed += 1;
};
const equal = (category, actual, expected) => {
  assert.deepEqual(actual, expected, category);
  categories.add(category);
  passed += 1;
};
const fire = (element, type = "click") => element.dispatchEvent(
  new scope.Event(type, { bubbles: true, cancelable: true }),
);
const forbidden = () => { forbiddenAccesses += 1; throw new Error("Forbidden UI side effect"); };
scope.fetch = () => { actualRequests += 1; throw new Error("Unexpected request"); };
for (const name of ["localStorage", "sessionStorage", "indexedDB", "gateway",
  "provider", "readiness", "CognitiveProcessor", "ReasoningProvider"]) {
  Object.defineProperty(scope, name, { get: forbidden, set: forbidden });
}
const form = get("command-form");
const dispatchGovernedForm = form.dispatchEvent.bind(form);
form.submit = form.requestSubmit = form.dispatchEvent = () => {
  formSubmissions += 1;
  throw new Error("Natural UI must never submit");
};
function literalOnly(element) {
  Object.defineProperty(element, "innerHTML", { get: forbidden, set: forbidden });
  element.insertAdjacentHTML = forbidden;
}
for (const match of html.matchAll(/\bid="([^"]+)"/gu)) literalOnly(get(match[1]));
const createElement = scope.document.createElement;
scope.document.createElement = (...args) => {
  const element = createElement(...args);
  literalOnly(element);
  return element;
};
scope.document.write = forbidden;
// Wrap the real approved entrypoint, recording the actual UI arguments.
const realPrepare = scope.prepareBoundedNaturalLanguageIntent;
scope.prepareBoundedNaturalLanguageIntent = (text, explicitFields) => {
  preparationCalls += 1;
  lastExplicitFields = { ...explicitFields };
  return realPrepare(text, explicitFields);
};
function interpret(text) {
  input.value = text;
  fire(input, "input");
  const before = preparationCalls;
  fire(prepareButton);
  equal("real-entrypoint", preparationCalls, before + 1);
  return vm.runInContext("naturalProposal.result", context);
}
function reject() {
  const text = input.value;
  const calls = preparationCalls;
  fire(rejectButton);
  equal("reject-discard", vm.runInContext("naturalProposal", context), null);
  check("reject-discard", get("natural-intent-result").hidden && rejectButton.disabled, "dismissed");
  equal("reject-discard", input.value, text);
  equal("reject-discard", preparationCalls, calls);
  equal("reject-discard", get("natural-intent-extracted-fields").textContent, "");
  check("reject-discard", fields.every((field) => row(field).hidden
    && fieldInput(field).disabled && fieldInput(field).value === ""), "clarifications cleared");
}
function visible(expected, category = "clarification-controls") {
  equal(category, fields.filter((field) => !row(field).hidden), expected);
  for (const field of fields) equal(category, fieldInput(field).disabled, !expected.includes(field));
}
const attributes = new Map(Array.from(html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/gu),
  (match) => [match[1], match[0]]));
// The shared fixture creates elements from HTML IDs but omits literal content
// and hidden attributes. Hydrate these static defaults from the actual HTML.
get("natural-intent-result").hidden = /\bhidden\b/u.test(attributes.get("natural-intent-result"));
get("natural-intent-status").textContent = html.match(
  /<p id="natural-intent-status"[^>]*>([^<]*)<\/p>/u,
)[1];
for (const id of ["natural-intent-panel", "natural-intent-heading", "natural-intent-input",
  "natural-intent-help", "natural-intent-prepare", "natural-intent-reject", "natural-intent-status",
  "natural-intent-result", "natural-intent-outcome", "natural-intent-detected-intent",
  "natural-intent-extracted-fields", "natural-intent-final-fields", "natural-intent-missing-fields",
  "natural-intent-invalid-fields", "natural-intent-conflicting-fields", "natural-intent-reason",
  "natural-intent-clarification", ...fields.flatMap((field) => [fieldId(field), `${fieldId(field)}-row`])]) {
  check("structure", !!get(id) && attributes.has(id), id);
  check("outside-form", html.indexOf(`id="${id}"`) < html.indexOf('<form id="command-form">'), id);
}
for (const id of ["natural-intent-prepare", "natural-intent-reject"]) {
  check("button-semantics", attributes.get(id).includes('type="button"'), id);
}
check("structure", html.indexOf('id="natural-intent-panel"') < html.indexOf('id="assistance-heading"'), "panel order");
visible([], "initial");
check("initial", rejectButton.disabled && !prepareButton.disabled && !input.disabled
  && get("natural-intent-result").hidden, "inactive initial state");
equal("initial", vm.runInContext("naturalProposal", context), null);
check("initial", get("natural-intent-status").textContent.includes("No natural-language proposal"), "status");
const base = { record_id: "record-41-b", kind: "fact", key: "MedSupply",
  source_type: "manual", source_reference: "test:41-b" };
editor.value = "list read manual";
get("proof").value = "synthetic-ui-test";
get("cognitive-fallback").checked = true;
const capture = "Recuerda que MedSupply entrega los martes.";
let result = interpret(capture);
equal("capture-clarification", result.outcome, "clarification_required");
equal("capture-clarification", editor.value, "list read manual");
equal("capture-clarification", get("natural-intent-missing-fields").textContent,
  "record_id, kind, key, source_type, source_reference");
equal("capture-clarification", JSON.parse(get("natural-intent-extracted-fields").textContent),
  { value: "MedSupply entrega los martes." });
visible(Object.keys(base));
for (const [field, value] of Object.entries(base)) {
  equal("no-default-metadata", fieldInput(field).value, "");
  fieldInput(field).value = value;
  fire(fieldInput(field), "input");
}
const callsBefore = preparationCalls;
equal("explicit-action", callsBefore, 1);
result = interpret(capture);
equal("capture-prepared", result.outcome, "prepared");
equal("capture-prepared", lastExplicitFields, base);
equal("capture-prepared", editor.value, `knowledge store :: ${JSON.stringify({
  record_id: base.record_id, kind: base.kind, key: base.key,
  value: "MedSupply entrega los martes.", source_type: base.source_type,
  source_reference: base.source_reference,
})}`);
equal("final-fields", JSON.parse(get("natural-intent-final-fields").textContent),
  { ...base, value: "MedSupply entrega los martes." });
check("prepared-editor", get("command-state").textContent.includes("explicit Send remains required"), "review wording");
visible([]);
check("reject-available", !rejectButton.disabled, "Prepared rejection");
reject();
equal("reject-untouched", editor.value, "");
equal("unrelated-controls", get("proof").value, "synthetic-ui-test");
equal("unrelated-controls", get("cognitive-fallback").checked, true);

for (const [text, intent, command] of [
  ["Agrega llamar a MedSupply a mis pendientes", "ADD_FOLLOW_UP", "list add tareas :: llamar a MedSupply"],
  ["Qué tengo pendiente", "READ_FOLLOW_UP", "list read tareas"],
]) {
  result = interpret(text);
  equal("generic-clarification", [result.outcome, result.intent], ["clarification_required", intent]);
  visible(["list_id"]);
  fieldInput("list_id").value = "tareas";
  fire(fieldInput("list_id"), "input");
  result = interpret(text);
  equal("generic-prepared", editor.value, command);
  equal("generic-prepared", result.outcome, "prepared");
  reject();
}
result = interpret("Qué sabes de MedSupply");
equal("recall", editor.value, 'knowledge find :: {"key":"MedSupply"}');
equal("recall", get("natural-intent-detected-intent").textContent, "RECALL_KNOWLEDGE");
visible(["kind"]);
equal("recall", fieldInput("kind").value, "");
fieldInput("kind").value = "concept";
fire(fieldInput("kind"), "change");
interpret("Qué sabes de MedSupply");
equal("recall-kind", editor.value, 'knowledge find :: {"key":"MedSupply","kind":"concept"}');
reject();
// Hidden or disabled stale controls never become explicit arguments.
for (const field of fields) fieldInput(field).value = "hidden-stale";
interpret("Muéstrame la lista tareas");
equal("visible-explicit-only", lastExplicitFields, {});
equal("explicit-read", editor.value, "list read tareas");
reject();
interpret("Qué sabes de K");
fieldInput("kind").value = "fact";
fieldInput("kind").disabled = true;
interpret("Qué sabes de K");
equal("visible-explicit-only", lastExplicitFields, {});
equal("visible-explicit-only", editor.value, 'knowledge find :: {"key":"K"}');
reject();

for (const editBack of [false, true]) {
  interpret("Qué sabes de MedSupply");
  const generated = editor.value;
  editor.value = "list read manual-edited";
  fire(editor, "input");
  if (editBack) { editor.value = generated; fire(editor, "input"); }
  const manual = editor.value;
  reject();
  equal(editBack ? "reject-edit-back" : "reject-manual", editor.value, manual);
  check("reject-manual-state", get("command-state").textContent.includes("Manual text retained"), "manual state");
}
interpret("Qué sabes de MedSupply");
editor.value = "list read different-replacement";
reject();
equal("reject-different-editor", editor.value, "list read different-replacement");
for (const [text, outcome] of [[capture, "clarification_required"], ["No recuerdes que X", "unsupported"]]) {
  editor.value = "list read unrelated";
  result = interpret(text);
  equal("nonprepared-preservation", result.outcome, outcome);
  equal("no-hidden-command", vm.runInContext("naturalProposal.generatedCommand", context), null);
  equal("nonprepared-preservation", editor.value, "list read unrelated");
  check("reject-available", !rejectButton.disabled, outcome);
  reject();
  equal("reject-nonprepared", editor.value, "list read unrelated");
}
// Important field feedback remains visible and corrected only by another click.
interpret("Agrega X | Y a mis pendientes");
visible(["list_id", "item"]);
equal("invalid-feedback", get("natural-intent-invalid-fields").textContent, "item");
fieldInput("list_id").value = "tareas";
fieldInput("item").value = "corrected";
interpret("Agrega X | Y a mis pendientes");
equal("conflict-feedback", get("natural-intent-conflicting-fields").textContent, "item");
visible(["item"]);
reject();
for (const literal of ['<script>alert("x")</script>', '<svg onload=alert(1)>',
  '{"html":"<b>x</b>"}', '"quote" \\ ruta é e\u0301 😀\nsegunda línea']) {
  const text = "Recuerda que " + literal;
  result = interpret(text);
  equal("literal-rendering", JSON.parse(get("natural-intent-extracted-fields").textContent), { value: literal });
  equal("literal-rendering", get("natural-intent-extracted-fields").children.length, 0);
  for (const [field, value] of Object.entries(base)) fieldInput(field).value = value;
  result = interpret(text);
  equal("literal-rendering", JSON.parse(editor.value.split(" :: ")[1]).value, literal);
  equal("literal-rendering", result.outcome, "prepared");
  reject();
}
// No actual form submission is needed to test the existing pending lock.
for (const state of ["inactive", "clarification", "prepared", "unsupported"]) {
  if (state === "clarification") interpret(capture);
  if (state === "prepared") interpret("Qué sabes de K");
  if (state === "unsupported") interpret("unsupported");
  const before = { editor: editor.value, calls: preparationCalls,
    proposal: vm.runInContext("naturalProposal", context) };
  const visibleFields = fields.filter((field) => !row(field).hidden);
  vm.runInContext("setRequestPending(true)", context);
  check("pending-lock", input.disabled && prepareButton.disabled && rejectButton.disabled
    && fields.every((field) => fieldInput(field).disabled), state);
  fire(prepareButton);
  fire(rejectButton);
  equal("pending-no-queue", preparationCalls, before.calls);
  equal("pending-no-queue", editor.value, before.editor);
  assert.equal(vm.runInContext("naturalProposal", context), before.proposal);
  vm.runInContext("setRequestPending(false)", context);
  check("pending-restore", !input.disabled && !prepareButton.disabled, state);
  equal("pending-restore", rejectButton.disabled, state === "inactive");
  visible(visibleFields, "pending-restore");
  equal("pending-no-queue", preparationCalls, before.calls);
  if (state !== "inactive") reject();
}
equal("zero-requests", actualRequests, 0);
equal("zero-submit", formSubmissions, 0);
equal("no-provider-storage", forbiddenAccesses, 0);
async function runProposalLifecycle() {
  const proposal = () => vm.runInContext("naturalProposal", context);
  const state = () => get("natural-intent-result").getAttribute("data-natural-state");
  function stale(category, oldCommand, oldCalls) {
    check(category, proposal().stale && state() === "stale", "visible stale state");
    check(category, !get("natural-intent-result").hidden && !rejectButton.disabled, "result/reject retained");
    equal(category, editor.value, oldCommand);
    equal(category, preparationCalls, oldCalls);
    check(category, get("natural-intent-status").textContent.includes("Re-Interpret / Prepare")
      && get("natural-intent-status").textContent.includes("Editor retained"), "status text");
  }
  function current(category) {
    check(category, !proposal().stale && !proposal().manuallyEdited
      && state() === "current" && proposal().uiState === "current", "fresh UI state");
  }
  interpret("Qué sabes de MedSupply");
  current("natural-input-stale");
  let oldCommand = editor.value;
  let oldCalls = preparationCalls;
  const semantic = JSON.stringify(proposal().result);
  input.value = "Qué sabes de AnotherSupplier";
  fire(input, "input");
  stale("natural-input-stale", oldCommand, oldCalls);
  equal("semantic-custody", JSON.stringify(proposal().result), semantic);
  fire(prepareButton);
  current("reprepare-current");
  equal("reprepare-current", editor.value, 'knowledge find :: {"key":"AnotherSupplier"}');
  oldCommand = editor.value;
  oldCalls = preparationCalls;
  fieldInput("kind").value = "concept";
  fire(fieldInput("kind"), "change");
  stale("optional-kind-stale", oldCommand, oldCalls);
  fire(prepareButton);
  current("reprepare-current");
  equal("optional-kind-stale", editor.value, 'knowledge find :: {"key":"AnotherSupplier","kind":"concept"}');
  reject();

  // Exercise every fixed clarification control while actually visible/enabled.
  for (const [field, text] of fields.map((field) => [field,
    field === "list_id" ? "Qué tengo pendiente"
      : field === "item" ? "Agrega  a mis pendientes" : "Recuerda que"])) {
    interpret(text);
    oldCommand = editor.value;
    oldCalls = preparationCalls;
    check("clarification-stale", !row(field).hidden && !fieldInput(field).disabled, field);
    fieldInput(field).value = field === "kind" ? "fact" : "explicit";
    fire(fieldInput(field), field === "kind" ? "change" : "input");
    stale("clarification-stale", oldCommand, oldCalls);
    fire(prepareButton);
    current("reprepare-current");
    reject();
  }
  interpret("unsupported");
  oldCommand = editor.value;
  oldCalls = preparationCalls;
  input.value = "different unsupported";
  fire(input, "input");
  stale("unsupported-stale", oldCommand, oldCalls);
  reject();
  interpret("Qué sabes de K");
  fire(fieldInput("record_id"), "input");
  equal("ignored-hidden-disabled", state(), "current");
  fieldInput("kind").disabled = true;
  fire(fieldInput("kind"), "change");
  equal("ignored-hidden-disabled", state(), "current");
  vm.runInContext("updateNaturalIntentControls()", context);
  oldCalls = preparationCalls;
  const generated = editor.value;
  editor.value = "list read manual-c-command";
  fire(editor, "input");
  stale("manual-editor-stale", editor.value, oldCalls);
  check("manual-editor-stale", proposal().manuallyEdited
    && get("natural-intent-status").textContent.includes("manually edited"), "manual state");
  editor.value = generated;
  fire(editor, "input");
  stale("manual-edit-back-stale", generated, oldCalls);
  check("manual-edit-back-stale", proposal().manuallyEdited, "sticky manual flag");
  reject();
  equal("reject-stale-manual", editor.value, generated);
  interpret("Qué sabes de K");
  fire(input, "input");
  reject();
  equal("reject-stale-untouched", editor.value, "");

  function seedGuide(stage) {
    scope.testGuideStage = stage;
    vm.runInContext(`
      resetGuidedExperience();
      for (const predecessor of GUIDE_STAGES.slice(0, GUIDE_STAGES.indexOf(testGuideStage))) {
        setGuidedStageState(predecessor, "completed");
      }
      for (const dependent of GUIDE_STAGES.slice(GUIDE_STAGES.indexOf(testGuideStage) + 1)) {
        setGuidedStageState(dependent, "failed");
      }
      guidedState.retainedFollowUp = {listId: "guide-tasks", expectedItem: "guide-item"};
      setGuidedPreparation(testGuideStage, {stage: testGuideStage, type: "synthetic-pending"}, "Synthetic preparation");
    `, context);
  }
  const guide = () => JSON.parse(vm.runInContext("JSON.stringify(guidedState)", context));
  for (const stage of ["capture", "recall", "follow-up", "verify"]) {
    seedGuide(stage);
    interpret("Qué sabes de K");
    const after = guide();
    equal("guided-clearing", after.correlation, null);
    equal("guided-clearing", after.stages[stage], "ready");
    const stageIndex = ["capture", "recall", "follow-up", "verify"].indexOf(stage);
    for (const predecessor of ["capture", "recall", "follow-up", "verify"].slice(0, stageIndex)) {
      equal("guided-completed-history", after.stages[predecessor], "completed");
    }
    for (const dependent of ["capture", "recall", "follow-up", "verify"].slice(stageIndex + 1)) {
      equal("guided-dependents", after.stages[dependent], "not-started");
    }
    if (stage !== "verify") equal("guided-dependents", after.retainedFollowUp, null);
    else equal("guided-completed-history", after.retainedFollowUp,
      { listId: "guide-tasks", expectedItem: "guide-item" });
    current("guided-clearing");
    reject();
  }
  for (const text of [capture, "unsupported"]) {
    seedGuide("recall");
    const before = guide();
    oldCommand = editor.value;
    get("response").textContent = "prior actual response";
    interpret(text);
    equal("guided-nonreplacement", guide(), before);
    equal("guided-nonreplacement", editor.value, oldCommand);
    equal("nonreplacement-result-custody", get("response").textContent, "prior actual response");
    reject();
  }
  seedGuide("capture");
  vm.runInContext('setGuidedStageState("capture", "completed")', context);
  interpret("Qué sabes de K");
  equal("guided-completed-history", guide().stages.capture, "completed");
  equal("guided-completed-history", guide().correlation, null);
  reject();
  vm.runInContext("resetGuidedExperience()", context);
  const beforeNoCorrelation = guide();
  get("response").textContent = "stale response";
  get("error").textContent = "stale error";
  get("knowledge-value").textContent = "stale knowledge";
  get("projection-list-id").textContent = "stale list";
  get("list-projection").hidden = get("knowledge-projection").hidden = false;
  interpret("Qué sabes de K");
  equal("no-invented-guide-transition", guide(), beforeNoCorrelation);
  check("draft-clearing", get("list-projection").hidden && get("knowledge-projection").hidden
    && ["response", "error", "knowledge-value", "projection-list-id"].every((id) => get(id).textContent === ""), "old projections cleared");
  reject();
  interpret("Qué sabes de K");
  input.value = '<svg onload=alert(1)> stale';
  fire(input, "input");
  check("stale-literal-rendering", !get("natural-intent-status").textContent.includes("<svg")
    && get("natural-intent-status").children.length === 0, "literal deterministic stale status");
  reject();
  const replacementPaths = {
    knowledge: () => {
      get("assist-operation").value = "read";
      fire(get("assist-operation"), "change");
      get("assist-record-id").value = "other-record";
      fire(get("prepare-command"));
    },
    browse: () => fire(get("prepare-browse")),
    "guided-read": () => vm.runInContext('prepareGuidedRecallRead("other-record")', context),
    "follow-up": () => {
      seedGuide("follow-up");
      get("follow-up-list-id").value = "guide-tasks";
      get("follow-up-item").value = "guide-item";
      fire(get("prepare-follow-up"));
    },
    verify: () => {
      seedGuide("verify");
      fire(get("prepare-verification"));
    },
  };
  for (const [name, replace] of Object.entries(replacementPaths)) {
    vm.runInContext("resetGuidedExperience()", context);
    interpret("Qué sabes de natural-key");
    const active = proposal();
    const naturalText = input.value;
    const generatedCommand = active.generatedCommand;
    oldCalls = preparationCalls;
    replace();
    const replacement = editor.value;
    check("replacement-matrix", replacement !== generatedCommand, name);
    stale("replacement-matrix", replacement, oldCalls);
    assert.equal(proposal(), active);
    equal("replacement-matrix", input.value, naturalText);
    equal("replacement-matrix", proposal().generatedCommand, generatedCommand);
    equal("replacement-matrix", proposal().manuallyEdited, false);
    reject();
    equal("reject-replacement", editor.value, replacement);
  }
  equal("invalidation-zero-requests", actualRequests, 0);

  // Explicit Send tests use only mocked transport. All other actions retain a
  // zero-fetch guard; no backend authorization/native acceptance is claimed.
  vm.runInContext("resetGuidedExperience()", context);
  let mockedFetchCalls = 0;
  let explicitSubmissions = 0;
  let allowSend = false;
  let release;
  let sent;
  scope.fetch = (url, options) => {
    if (!allowSend) { actualRequests += 1; throw new Error("Hidden fetch"); }
    mockedFetchCalls += 1;
    sent = { url, options, body: JSON.parse(options.body) };
    return new Promise((resolve, reject) => { release = { resolve, reject }; });
  };
  const flush = async () => { for (let index = 0; index < 12; index += 1) await Promise.resolve(); };
  const send = () => {
    explicitSubmissions += 1;
    allowSend = true;
    dispatchGovernedForm(new scope.Event("submit", { cancelable: true }));
    allowSend = false;
  };
  for (const mode of ["fresh", "stale", "manual", "denied", "network-failure"]) {
    interpret("Qué sabes de MedSupply");
    if (mode === "stale") { input.value = "Qué sabes de AnotherSupplier"; fire(input, "input"); }
    if (mode === "manual") { editor.value = "list read manual-c-command"; fire(editor, "input"); }
    const expectedText = editor.value;
    const beforeResult = JSON.stringify(proposal().result);
    oldCalls = preparationCalls;
    get("proof").value = "synthetic-c-proof";
    get("cognitive-fallback").checked = false;
    const previousFetches = mockedFetchCalls;
    send();
    equal("send-exact-editor", mockedFetchCalls, previousFetches + 1);
    equal("send-no-reinterpret", preparationCalls, oldCalls);
    equal("send-envelope", sent.body, { proof: "synthetic-c-proof",
      requested_workspace_id: "luxiom-local-dev-workspace", text: expectedText,
      allow_cognitive_fallback: false });
    equal("send-envelope", sent.url, "/local/command");
    equal("send-envelope", sent.options.method, "POST");
    check("submitted-state", state() === "submitted" && proposal().uiState === "submitted"
      && get("natural-intent-status").textContent.includes("submitted"), mode);
    if (["stale", "manual"].includes(mode)) {
      check("submitted-stale-manual", get("natural-intent-status").textContent.includes("stale/manual"), mode);
    }
    const during = JSON.stringify(proposal());
    fire(input, "input");
    fire(fieldInput("kind"), "change");
    fire(editor, "input");
    fire(prepareButton);
    fire(rejectButton);
    equal("pending-event-custody", JSON.stringify(proposal()), during);
    check("pending-event-custody", input.disabled && prepareButton.disabled && rejectButton.disabled
      && fields.every((field) => fieldInput(field).disabled), mode);
    equal("semantic-custody", JSON.stringify(proposal().result), beforeResult);
    if (mode === "network-failure") release.reject(new Error("synthetic disconnect"));
    else release.resolve({ json: async () => ({ success: mode !== "denied", route: "local",
      response: mode === "denied" ? null : "synthetic result", error: mode === "denied"
        ? { code: "synthetic_failure", message: "Synthetic failure" } : null }) });
    await flush();
    equal("send-no-reinterpret", preparationCalls, oldCalls);
    check("settled-state", get("natural-intent-status").textContent.includes("request settled")
      && get("natural-intent-status").textContent.includes("Result"), mode);
    check("pending-restored-after-send", !input.disabled && !prepareButton.disabled && !rejectButton.disabled, mode);
    equal("authoritative-result", get("status").textContent, ["denied", "network-failure"].includes(mode) ? "Failed" : "Success");
    equal("send-exact-editor", editor.value, expectedText);
    const fetchesBeforeReject = mockedFetchCalls;
    reject();
    equal("reject-submitted-zero-requests", mockedFetchCalls, fetchesBeforeReject);
    equal("reject-submitted-editor", editor.value, mode === "manual" ? expectedText : "");
  }
  interpret("Qué sabes de K");
  const csrf = scope.document.querySelector('meta[name="luxiom-csrf"]');
  const token = csrf.getAttribute("content");
  csrf.setAttribute("content", "");
  const fetchesBeforeCsrf = mockedFetchCalls;
  oldCalls = preparationCalls;
  send();
  await flush();
  equal("csrf-start-failure", mockedFetchCalls, fetchesBeforeCsrf);
  equal("csrf-start-failure", preparationCalls, oldCalls);
  equal("csrf-start-failure", state(), "current");
  check("csrf-start-failure", get("natural-intent-status").textContent.includes("could not start")
    && !get("natural-intent-status").textContent.includes("submitted"), "no false submission");
  equal("csrf-start-failure", get("status").textContent, "Failed");
  csrf.setAttribute("content", token);
  reject();
  equal("invalidation-zero-requests", actualRequests, 0);
  equal("no-provider-storage", forbiddenAccesses, 0);
  return { environment: "node-dom-double", passed, categories: [...categories],
    actualRequests, preparationInvalidationRequests: actualRequests, mockedFetchCalls,
    explicitSubmissions, forbiddenAccesses, formSubmissions, preparationCalls,
    nativeBrowserVerified: false, nativeKeyboardVerified: false };
}
runProposalLifecycle().then((evidence) => process.stdout.write(JSON.stringify(evidence)))
  .catch((error) => { process.stderr.write(String(error.stack)); process.exitCode = 1; });
