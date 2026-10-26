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
process.stdout.write(JSON.stringify({ environment: "node-dom-double", passed,
  categories: [...categories], actualRequests, forbiddenAccesses, formSubmissions,
  preparationCalls, nativeBrowserVerified: false, nativeKeyboardVerified: false }));
