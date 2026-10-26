"use strict";

// Actual app.js in the established VM/DOM double. No native browser claim.
const assert = require("node:assert/strict");
const vm = require("node:vm");
const { createEnvironment } = require("./local_knowledge_command_assistance.js");
const { scope, context } = createEnvironment();
let passed = 0;
let actualRequests = 0;
let forbiddenAccesses = 0;
const categories = new Set();
const vectors = [];
const forbidden = () => { forbiddenAccesses += 1; throw new Error("Impure preparation"); };
scope.fetch = () => { actualRequests += 1; throw new Error("Unexpected request"); };
// Install after existing app initialization: every preparation must work without
// even reading the DOM, storage, submit, or any of these observable service hooks.
scope.document = new Proxy({}, { get: forbidden, set: forbidden });
for (const name of ["localStorage", "sessionStorage", "indexedDB", "gateway",
  "provider", "readiness", "CognitiveProcessor", "ReasoningProvider"]) {
  Object.defineProperty(scope, name, { get: forbidden, set: forbidden });
}
vm.runInContext("form.submit = form.requestSubmit = () => { throw new Error('submit'); }", context);
for (const name of ["prepareEditorCommand", "prepareGuidedCapture", "prepareGuidedRecallQuery",
  "beginGuidedRequest", "renderGuidedState", "clearDraftResults"]) {
  scope[name] = forbidden;
}
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
const keys = ["outcome", "intent", "extractedFields", "fields", "missingFields",
  "invalidFields", "conflictingFields", "reason", "clarification", "command"].sort();
const intents = ["CAPTURE_KNOWLEDGE", "RECALL_KNOWLEDGE", "ADD_FOLLOW_UP", "READ_FOLLOW_UP"];
const base = { record_id: "record-41", kind: "fact", key: "MedSupply",
  source_type: "manual", source_reference: "test:41" };
equal("keyword-map", vm.runInContext('boundedKeywordText("ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑİK")', context),
  "abcdefghijklmnopqrstuvwxyzáéíóúüñİK");
function run(text, explicit = {}, category = "corpus") {
  scope.testText = text;
  scope.testFields = explicit;
  const invoke = () => JSON.parse(JSON.stringify(vm.runInContext(
    "prepareBoundedNaturalLanguageIntent(testText, testFields)", context,
  )));
  const result = invoke();
  equal("determinism", invoke(), result);
  equal("closed-result", Object.keys(result).sort(), keys);
  check("closed-result", ["prepared", "clarification_required", "unsupported"].includes(result.outcome), "closed outcome");
  if (result.outcome === "prepared") {
    check(category, intents.includes(result.intent) && typeof result.command === "string"
      && Array.from(result.command).length <= 8192, "valid prepared command");
    equal("closed-result", [result.missingFields, result.invalidFields, result.conflictingFields,
      result.reason, result.clarification], [[], [], [], null, null]);
    vectors.push({ intent: result.intent, command: result.command, fields: result.fields });
  } else {
    equal("closed-result", result.command, null);
    check("closed-result", typeof result.clarification === "string" && result.clarification.length > 0,
      "literal explanation");
    if (result.outcome === "unsupported") {
      equal("closed-result", [result.intent, result.missingFields, result.invalidFields,
        result.conflictingFields], [null, [], [], []]);
      check("closed-result", ["invalid_input", "unsupported_request", "conditional_request",
        "multiple_actions", "context_reference", "ambiguous_structure", "unrepresentable"]
        .includes(result.reason), "closed rejection reason");
    } else {
      check("closed-result", intents.includes(result.intent), "recognized clarification");
      equal("closed-result", result.reason, null);
    }
  }
  return result;
}
function reject(text, reason, explicit = {}, category = "rejection") {
  const result = run(text, explicit, category);
  equal(category, [result.outcome, result.reason], ["unsupported", reason]);
}
function prepared(text, explicit, intent, fields, category = "corpus") {
  const result = run(text, explicit, category);
  equal(category, [result.outcome, result.intent, result.fields], ["prepared", intent, fields]);
  return result;
}
for (const prefix of ["Recuerda que", "Guarda que", "Anota que", "RECUERDA QUE"]) {
  const result = prepared(`${prefix} MedSupply entrega los martes.`, base,
    intents[0], { ...base, value: "MedSupply entrega los martes." });
  equal("serialization", result.command, `knowledge store :: ${JSON.stringify({
    record_id: base.record_id, kind: base.kind, key: base.key,
    value: "MedSupply entrega los martes.", source_type: base.source_type,
    source_reference: base.source_reference,
  })}`);
  equal("no-invention", result.extractedFields, { value: "MedSupply entrega los martes." });
}
for (const prefix of ["Qué te dije sobre", "Qué sabes de", "QUÉ SABES DE"]) {
  for (const left of ["", "¿"]) for (const right of ["", "?"]) {
    prepared(`${left}${prefix} MedSupply${right}`, {}, intents[1], { key: "MedSupply" }, "wrappers");
  }
}
for (const prefix of ["Agrega", "Añade", "AÑADE"]) {
  prepared(`${prefix} llamar a MedSupply a la lista tareas`, {}, intents[2],
    { list_id: "tareas", item: "llamar a MedSupply" });
  const missing = run(`${prefix} llamar a MedSupply a mis pendientes`);
  equal("generic-add", missing.missingFields, ["list_id"]);
  prepared(`${prefix} llamar a MedSupply a mis pendientes`, { list_id: "tareas" }, intents[2],
    { list_id: "tareas", item: "llamar a MedSupply" }, "generic-add");
}
for (const prefix of ["Qué hay en la lista", "QUÉ HAY EN LA LISTA"]) {
  for (const left of ["", "¿"]) for (const right of ["", "?"]) {
    prepared(`${left}${prefix} tareas${right}`, {}, intents[3], { list_id: "tareas" }, "wrappers");
  }
}
for (const prefix of ["Muéstrame la lista", "MUÉSTRAME LA LISTA"]) {
  prepared(`${prefix} tareas`, {}, intents[3], { list_id: "tareas" });
}
for (const left of ["", "¿"]) for (const right of ["", "?"]) {
  const text = `${left}Qué tengo pendiente${right}`;
  equal("generic-read", run(text).missingFields, ["list_id"]);
  prepared(text, { list_id: "tareas" }, intents[3], { list_id: "tareas" }, "generic-read");
}
const missing = run("Recuerda que MedSupply entrega los martes.");
equal("capture-metadata", missing.missingFields,
  ["record_id", "kind", "key", "source_type", "source_reference"]);
equal("no-invention", missing.fields, { value: "MedSupply entrega los martes." });
for (const kind of ["fact", "concept", "state"]) {
  prepared("Guarda que X", { ...base, kind }, intents[0], { ...base, kind, value: "X" }, "kinds");
  const result = prepared("Qué sabes de K", { kind }, intents[1], { key: "K", kind }, "kinds");
  equal("serialization", result.command, `knowledge find :: ${JSON.stringify({ key: "K", kind })}`);
}
for (const kind of ["FACT", "unknown", null, 3, [], {}, "fáct"]) {
  equal("invalid-kind", run("Qué sabes de K", { kind }).invalidFields, ["kind"]);
}
for (const [text, explicit, field] of [
  ["Recuerda que X", { ...base, value: "Y" }, "value"],
  ["Qué sabes de K", { key: "Q" }, "key"],
  ["Agrega X a la lista L", { item: "Y" }, "item"],
  ["Agrega X a la lista L", { list_id: "Q" }, "list_id"],
  ["Muéstrame la lista L", { list_id: "Q" }, "list_id"],
]) {
  const result = run(text, explicit);
  equal("conflicts", result.conflictingFields, [field]);
  check("conflicts", !Object.hasOwn(result.fields, field), "conflict omitted from usable fields");
}
prepared("Qué sabes de K", { key: " \u0085K\u001c", kind: "  ", unknown: "X" },
  intents[1], { key: "K" }, "merge-trimming");
prepared("Qué sabes de K", { key: " \u001c" }, intents[1], { key: "K" }, "blank-explicit");
const inherited = Object.create({ kind: "fact", key: "Q", list_id: "hidden" });
prepared("Qué sabes de K", inherited, intents[1], { key: "K" }, "own-properties");
prepared("Qué sabes de K", JSON.parse('{"__proto__":{"kind":"fact"},"constructor":"X"}'),
  intents[1], { key: "K" }, "own-properties");
for (const explicit of [null, undefined, 7, "hidden"]) {
  prepared("Qué sabes de K", explicit, intents[1], { key: "K" }, "own-properties");
}
equal("ordered-fields", run("Agrega X a la lista L", { list_id: "Q", item: "Y" })
  .conflictingFields, ["list_id", "item"]);
equal("ordered-fields", run("Recuerda que X", { record_id: 3, kind: "bad", key: null,
  value: "Y", source_type: false }).invalidFields, ["record_id", "kind", "key", "source_type"]);
for (const [text, fields] of [
  ["Recuerda que", ["record_id", "kind", "key", "value", "source_type", "source_reference"]],
  ["Guarda que", ["record_id", "kind", "key", "value", "source_type", "source_reference"]],
  ["Anota que", ["record_id", "kind", "key", "value", "source_type", "source_reference"]],
  ["¿Qué te dije sobre?", ["key"]], ["Qué sabes de", ["key"]],
  ["Qué hay en la lista", ["list_id"]], ["Muéstrame la lista", ["list_id"]],
  ["Agrega  a la lista L", ["item"]], ["Añade X a la lista ", ["list_id"]],
  ["Agrega  a la lista ", ["list_id", "item"]],
]) equal("empty-placeholders", run(text).missingFields, fields);
for (const text of ["Recuerda", "Agrega", "Añade", "Recuerda  que X", "Qué  sabes de K",
  "Que sabes de K", "Muestrame la lista L", "Anota\tque X", "Guardar que X",
  "Que\u0301 sabes de K", "Qué sabes de K??", "Qué sabes de ?K", "Qué sabes de ¿K",
  "¿Muéstrame la lista L?", "¿Recuerda que X?", "Dime qué sabes de K",
  "No recuerdes que X", '"Recuerda que X"', "“Recuerda que X”",
  "Por ejemplo: Recuerda que X", '"Recuerda que X y agrega Y"',
  "Si recuerda que X", "Cuando agrega X a la lista L"]) reject(text, "unsupported_request");
for (const text of ["Recuerda que si X", "Guarda que CUANDO X", "Qué sabes de si",
  "Recuerda que X si Y y agrega Z"]) reject(text, "conditional_request");
prepared("Recuerda que No entrega", base, intents[0], { ...base, value: "No entrega" }, "negation");
for (const word of ["esto", "eso", "aquello", "ello", "él", "ella", "ellos", "ellas", "ÉL"]) {
  reject(`Recuerda que (${word})`, "context_reference");
}
prepared("Qué sabes de camellos", {}, intents[1], { key: "camellos" }, "standalone");
prepared("Qué sabes de xesto9", {}, intents[1], { key: "xesto9" }, "standalone");
for (const text of ["Agrega X a la lista L a la lista Q",
  "Agrega X a la lista L a mis pendientes"]) reject(text, "ambiguous_structure");
for (const list_id of ["a b", "a\tb", "a::b", "a\u0085b", "a\u001cb", "a\ud800b"]) {
  equal("list-validation", run("Qué tengo pendiente", { list_id }).invalidFields, ["list_id"]);
  equal("list-validation", run("Agrega X a mis pendientes", { list_id }).invalidFields, ["list_id"]);
}
equal("item-validation", run("Agrega X | Y a la lista L").invalidFields, ["item"]);
const whitespace = "\t\n\v\f\r\u001c\u001d\u001e\u001f \u0085\u00a0\u1680"
  + "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
  + "\u2028\u2029\u202f\u205f\u3000";
for (const edge of whitespace) {
  prepared(`${edge}Qué sabes de K${edge}`, {}, intents[1], { key: "K" }, "python-whitespace");
  reject(edge, "invalid_input");
}
for (const invalid of [null, undefined, false, 1, [], {}, "", "\ud800", "x\udfff", "\ud800x"]) {
  reject(invalid, "invalid_input");
}
for (const field of [...Object.keys(base), "value"]) {
  equal("explicit-surrogate", run("Recuerda que", { ...base, value: "X", [field]: "\ud800" })
    .invalidFields, [field]);
}
const boundaries = [" y ", " y también ", " luego ", " después ", " entonces ", "; ",
  ". ", "! ", "? ", "\n", "\r\n", "\r", "\n \t", "\r\n\t ", "\r  "];
const introducers = ["recuerda", "guarda", "anota", "agrega", "añade", "agrégalo",
  "añádelo", "muéstrame", "qué", "¿qué"];
for (const boundary of boundaries) for (const introducer of introducers) {
  for (const upper of [false, true]) {
    const pair = boundary + introducer + " Y";
    reject("Recuerda que X" + (upper ? pair.toUpperCase() : pair), "multiple_actions", {}, "multi-action-matrix");
  }
  for (const [open, close] of [['"', '"'], ["“", "”"]]) {
    prepared(`Recuerda que X${open}${boundary}${introducer} Y${close}`, base,
      intents[0], { ...base, value: `X${open}${boundary}${introducer} Y${close}` }, "quoted-matrix");
  }
}
for (const boundary of [" y ", "; ", ". ", "\n"]) {
  reject(`Recuerda que X${boundary}Agrega Y a la lista Z`, "multiple_actions");
}
for (const value of ['X " y agrega Y', 'X \\" y agrega Y', 'X \\" y agrega Y \\"',
  'X “ y agrega Y', 'X "literal" y agrega Y']) reject(`Recuerda que ${value}`, "multiple_actions");
for (const value of ['X "literal \\" y agrega Y"', 'X \\\\" y agrega Y"',
  'X “ y agrega Y”', 'X " y agrega Y"']) {
  prepared(`Recuerda que ${value}`, base, intents[0], { ...base, value }, "quote-escapes");
}
for (const value of ["X, agrega Y", "X;agrega Y", "X y busca Y", "X Y\tagrega Y",
  "X y agregamos Y", "X y anota\tY", "ir a mis pendientes favoritos"]) {
  prepared(`Recuerda que ${value}`, base, intents[0], { ...base, value }, "unlisted-guard");
}
prepared("Agrega ir a mis pendientes favoritos a la lista L", {}, intents[2],
  { list_id: "L", item: "ir a mis pendientes favoritos" }, "destination-suffix");
prepared("Añade X a mis pendientes a la lista L", {}, intents[2],
  { list_id: "L", item: "X a mis pendientes" }, "destination-suffix");
for (const value of ['<script>alert("x")</script> :: | {"a":"b"}', 'é e\u0301 😀 ÑÜ',
  '"quote" \\ path\nline\t::', "\ufeffX\u200b", "X siembra cuando2"]) {
  prepared(`Recuerda que ${value}`, base, intents[0], { ...base, value }, "literal-preservation");
}
prepared("Agrega  \"dato\" :: \\ruta\nsegunda línea  a la lista L", {}, intents[2],
  { list_id: "L", item: '\"dato\" :: \\ruta\nsegunda línea' }, "literal-preservation");
const frozenFields = Object.freeze({ key: "  K  ", kind: "", extra: "ignored" });
prepared("Qué sabes de K", frozenFields, intents[1], { key: "K" }, "input-immutability");
equal("input-immutability", frozenFields, { key: "  K  ", kind: "", extra: "ignored" });
// Both natural-input and complete-command budgets count code points, including
// supplementary characters; JSON escapes consume their serialized size.
const natural = "Recuerda que " + "😀".repeat(8192 - "Recuerda que ".length);
equal("input-length", run(natural).outcome, "clarification_required");
reject(natural + "😀", "invalid_input");
for (const [textPrefix, explicit, intent, overhead] of [
  ["Qué sabes de ", {}, intents[1], 'knowledge find :: {"key":""}'.length],
  ["Recuerda que ", base, intents[0], null],
  ["Agrega ", {}, intents[2], "list add L :: ".length],
  ["Muéstrame la lista ", {}, intents[3], "list read ".length],
]) {
  const storeOverhead = `knowledge store :: ${JSON.stringify({ record_id: base.record_id,
    kind: base.kind, key: base.key, value: "", source_type: base.source_type,
    source_reference: base.source_reference })}`.length;
  for (const length of [8191, 8192, 8193]) {
    const payload = "😀".repeat(length - (overhead ?? storeOverhead));
    // READ's natural prefix is longer than its command prefix: use explicit ID.
    const text = intent === intents[3] ? "Qué tengo pendiente"
      : intent === intents[2] ? "Agrega  a la lista L"
      : textPrefix + payload + (intent === intents[2] ? " a la lista L" : "");
    const fields = intent === intents[3] ? { list_id: payload }
      : intent === intents[2] ? { item: payload } : explicit;
    const result = run(text, fields, "command-length");
    equal("command-length", result.outcome, length <= 8192 ? "prepared" : "unsupported");
    if (length > 8192) equal("command-length", result.reason, "unrepresentable");
    else equal("command-length", Array.from(result.command).length, length);
  }
}
reject("Recuerda que X", "unrepresentable",
  { ...base, source_reference: '"'.repeat(4096) }, "json-escape-budget");
equal("purity", actualRequests, 0);
equal("purity", forbiddenAccesses, 0);
process.stdout.write(JSON.stringify({ environment: "node-dom-double", passed,
  categories: [...categories], actualRequests, forbiddenAccesses, vectors,
  nativeBrowserVerified: false }));
