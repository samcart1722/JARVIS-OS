"use strict";

// Actual app.js in the shared DOM double. No native focus/layout/transport claim.
const vm = require("node:vm");
const { createEnvironment } = require("./local_knowledge_command_assistance.js");

async function runBrowse() {
  const { scope, context } = createEnvironment();
  const get = (id) => scope.document.querySelector(`#${id}`);
  const fire = (element, type = "click") => element.dispatchEvent(
    new scope.Event(type, { bubbles: true, cancelable: true }),
  );
  const categories = new Set();
  const vectors = [];
  let passed = 0;
  const check = (category, condition, message) => {
    if (!condition) throw new Error(`${category}: ${message}`);
    categories.add(category); passed += 1;
  };
  const calls = [];
  let reply;
  scope.fetch = (url, options) => {
    calls.push({ url, options });
    return new Promise((resolve, reject) => { reply = { resolve, reject }; });
  };
  const flush = async () => { for (let i = 0; i < 12; i += 1) await Promise.resolve(); };
  const show = (records, truncated = false) => {
    scope.result = { success: true, route: "local", response: "Knowledge records browsed locally.",
      error: null, projection: { kind: "knowledge", operation: "browse", records, truncated } };
    vm.runInContext("renderResult(result)", context);
  };
  const summary = (record_id = "id") => ({ record_id, kind: "fact", key: 'key  <b> e\u0301 "\\' });
  const button = () => get("knowledge-records").children[0].children[1];
  const cleared = () => get("knowledge-projection").hidden
    && get("knowledge-records").children.length === 0 && get("response").textContent === "";

  fire(get("prepare-browse"));
  check("preparation", get("command").value === "knowledge browse :: {}" && calls.length === 0,
    "browse writes the canonical command without fetch");
  vectors.push({ name: "browse-empty-payload", operation: "browse", command: get("command").value });
  check("preparation", get("preparation-status").textContent.includes("No operation"), "prepared state");
  get("command").value = "manual text"; fire(get("command"), "input");
  check("replacement", get("prepare-browse").textContent.includes("replace"), "replacement disclosed before action");
  fire(get("prepare-browse"));
  check("replacement", get("preparation-status").textContent.includes("replaced"), "replacement acknowledged");

  show([]);
  check("states", !get("knowledge-projection").hidden && !get("knowledge-empty").hidden
    && get("knowledge-empty").textContent === "No knowledge records in this workspace."
    && get("knowledge-truncated").hidden, "empty");
  const fifty = Array.from({ length: 50 }, (_, i) => summary(`id-${String(i).padStart(3, "0")}`));
  for (const truncated of [false, true]) {
    show(fifty, truncated);
    check("states", get("knowledge-records").children.length === 50
      && get("knowledge-empty").hidden && get("knowledge-truncated").hidden === !truncated
      && get("knowledge-count-row").hidden && get("knowledge-record-details").hidden,
    "full versus truncated without value or invented total");
  }
  check("states", get("knowledge-truncated").textContent
    === "Showing the first 50 records by ID. More records exist; this version cannot browse them.", "contractual truncation text");

  for (const id of ['id"\\<img src=x onerror=alert(1)>', "é e\u0301 😀", "line\ninside\tID", "a\u0000b", "\ufeff"]) {
    const record = summary(id);
    show([record]);
    const article = get("knowledge-records").children[0];
    const rows = article.children[0].children;
    check("literal-metadata", rows.length === 3 && rows[0].children[1].textContent === id
      && rows[1].children[1].textContent === "fact" && rows[2].children[1].textContent === record.key,
    "only three literal metadata fields");
    const select = button();
    check("selection", select.type === "button" && select.textContent.includes("Prepare READ"), "selection cannot submit");
    // Neither labels nor a changed data object may replace the ID captured at render.
    rows[0].children[1].textContent = "misleading label";
    record.record_id = "changed data";
    fire(select);
    const command = get("command").value;
    check("selection", cleared() && command === `knowledge read :: ${JSON.stringify({ record_id: id })}`,
      "capture original ID before clearing results");
    check("selection", get("preparation-status").textContent.startsWith("READ command prepared"), "READ prepared state");
    vectors.push({ name: "selected-literal-id", operation: "read", record_id: id, command });
    fire(select);
    check("selection", get("command").value === command && select.disabled, "detached stale selection inert");
  }

  const overhead = Array.from('knowledge read :: {"record_id":""}').length;
  const exact = "😀".repeat(8192 - overhead);
  show([summary(exact)]); fire(button());
  check("limits", Array.from(get("command").value).length === 8192, "code point limit accepted");
  vectors.push({ name: "selected-read-8192", operation: "read", record_id: exact, command: get("command").value });
  for (const id of [exact + "x", '"'.repeat(4096), "\ud800", "a\udfff", "", " \t"]) {
    const previous = get("command").value;
    show([summary(id)]); fire(button());
    check("error-preservation", cleared() && get("command").value === previous
      && get("preparation-error").textContent !== ""
      && get("command-state").textContent.includes("no new command was prepared"),
    "unpreparable ID preserves editor, clears stale result, never truncates");
  }
  for (const [id, event] of [["command", "input"], ["assist-key", "input"],
    ["assist-operation", "change"], ["cognitive-fallback", "change"], ["prepare-browse", "click"]]) {
    show([summary()]); fire(get(id), event);
    check("stale-results", cleared(), `${id} clears previous result`);
  }
  check("no-fetch", calls.length === 0, "all preparation/edit/selection/rejection is local");

  show([summary()]);
  const stale = button();
  const manual = '  knowledge read :: {"record_id":"manual"}  ';
  get("command").value = manual;
  get("proof").value = "synthetic-s38-proof";
  get("cognitive-fallback").checked = true;
  fire(get("command-form"), "submit"); fire(get("command-form"), "submit");
  fire(get("prepare-browse")); fire(stale); fire(get("prepare-command"));
  const sent = JSON.parse(calls[0].options.body);
  check("send", calls.length === 1 && sent.text === manual && sent.proof === "synthetic-s38-proof"
    && sent.allow_cognitive_fallback === true && calls[0].url === "/local/command"
    && calls[0].options.method === "POST", "one activation sends exact editor through existing transport");
  const controls = ["send-command", "prepare-browse", "prepare-command", "command", "proof", "cognitive-fallback", "assist-operation"];
  check("pending", controls.every((id) => get(id).disabled) && stale.disabled && cleared()
    && get("status").textContent === "Pending" && get("command").value === manual,
  "pending blocks preparation, selection and resubmission");
  reply.resolve({ json: async () => ({ success: true, route: "local", response: "Browsed",
    projection: { kind: "knowledge", operation: "browse", records: [summary()], truncated: false } }) });
  await flush();
  check("pending", controls.every((id) => !get(id).disabled) && !button().disabled, "controls and new selections recover");
  fire(button());
  check("send", calls.length === 1 && cleared(), "selection after response does not send READ");
  get("proof").value = "synthetic-s38-proof";
  fire(get("command-form"), "submit");
  check("send", calls.length === 2 && JSON.parse(calls[1].options.body).text === 'knowledge read :: {"record_id":"id"}',
    "separate explicit Send for READ");
  reply.reject(new Error("synthetic failure")); await flush();
  check("pending", controls.every((id) => !get(id).disabled) && get("status").textContent === "Failed"
    && get("error").textContent !== "" && get("knowledge-projection").hidden, "recover from request error");

  // Existing FIND messages must be restored after BROWSE changes shared elements.
  show([], false);
  scope.result = { success: true, route: "local", response: "Found", projection: {
    kind: "knowledge", operation: "find", records: [], truncated: false } };
  vm.runInContext("renderResult(result)", context);
  check("regression", get("knowledge-empty").textContent === "No matching knowledge records."
    && get("knowledge-truncated").textContent === "Showing the first 50 matching records.", "FIND messages restored");
  const fullRecord = { ...summary(), value: "literal <value>" };
  for (const operation of ["store", "read", "find"]) {
    show(fifty, true);
    scope.result = { success: true, route: "local", response: "Canonical", projection: {
      kind: "knowledge", operation, record: fullRecord, created: false,
      records: [fullRecord], truncated: false } };
    vm.runInContext("renderResult(result)", context);
    check("regression", !get("knowledge-projection").hidden && get("knowledge-truncated").hidden
      && get("response").textContent === "Canonical", `${operation} replaces browse state`);
    if (operation === "find") {
      const article = get("knowledge-records").children[0];
      check("regression", article.children.length === 1
        && article.children[0].children[3].children[1].textContent === fullRecord.value,
      "FIND keeps full records without READ selection buttons");
    } else {
      check("regression", get("knowledge-value").textContent === fullRecord.value
        && get("knowledge-created-row").hidden === (operation !== "store"),
      "STORE guard and READ value preserved");
    }
  }
  for (const operation of ["add", "read"]) {
    show([summary()]);
    scope.result = { success: true, route: "local", response: "List", projection: {
      kind: "list", operation, list_id: "list", added: ["a"], already_present: [], items: ["a"] } };
    vm.runInContext("renderResult(result)", context);
    check("regression", !get("list-projection").hidden && get("knowledge-projection").hidden
      && get("knowledge-records").children.length === 0, "list projection replaces browse");
  }
  show([summary()]);
  scope.result = { success: false, route: "local", response: null,
    error: { code: "local_permission_denied", message: "Denied" } };
  vm.runInContext("renderResult(result)", context);
  check("states", get("knowledge-projection").hidden && get("knowledge-records").children.length === 0
    && get("status").textContent === "Failed" && get("error").textContent === "Denied", "error clears browse");
  fire(get("prepare-browse"));
  check("states", get("error").textContent === "" && get("preparation-error").textContent === ""
    && get("command").value === "knowledge browse :: {}", "new preparation recovers from error");
  for (const records of [[{ ...summary(), value: "private" }], Array(51).fill(summary())]) {
    show(records);
    check("invalid-projection", get("knowledge-projection").hidden
      && get("knowledge-records").children.length === 0, "no partial invalid projection");
  }
  return { environment: "node-dom-double", categories: [...categories], passed, vectors, actualRequests: 0 };
}

if (require.main === module) runBrowse().then((result) => process.stdout.write(JSON.stringify(result)))
  .catch((error) => { process.stderr.write(String(error)); process.exitCode = 1; });
module.exports = { runBrowse };
