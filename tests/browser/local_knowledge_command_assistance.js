"use strict";

/*
 * Run locally: node tests/browser/local_knowledge_command_assistance.js
 * This runs the ACTUAL app.js with a minimal DOM double, not a browser.
 * Python's UI tests consume the generated vectors through the real interpreter.
 *
 * Browser: in a disposable /local/ui test tab with no personal proof/data,
 * evaluate this file, then await runLocalKnowledgeCommandAssistance().
 * The suite replaces fetch before any action; it never sends an actual request.
 * Browser results must be reported separately from the Node evidence.
 */
async function runLocalKnowledgeCommandAssistance(environment) {
  const scope = environment || window;
  const document = scope.document;
  const get = (id) => document.querySelector(`#${id}`);
  let passed = 0;
  const vectors = [];
  const check = (condition, message) => {
    if (!condition) throw new Error(message);
    passed += 1;
  };
  const fire = (id, type) => get(id).dispatchEvent(
    new scope.Event(type, { bubbles: true, cancelable: true }),
  );
  const flush = async () => {
    for (let i = 0; i < 12; i += 1) await Promise.resolve();
  };
  const controls = ["send-command", "proof", "command", "cognitive-fallback",
    "assist-operation", "prepare-command"];
  const fields = ["record_id", "kind", "key", "value", "source_type", "source_reference"];
  const fieldId = (field) => `assist-${field.replaceAll("_", "-")}`;
  const base = {
    record_id: "record-1", kind: "fact", key: "greeting", value: "hello",
    source_type: "explicit-note", source_reference: "notebook:7",
  };
  const originalFetch = scope.fetch;
  const calls = [];
  let responseFactory = async () => ({
    json: async () => ({ success: true, route: "local", response: "Done", error: null }),
  });
  check(get("proof").value === "", "Use an isolated tab with no proof entered");
  scope.fetch = (url, options) => {
    calls.push({ url, options });
    return responseFactory();
  };
  function fill(operation, values) {
    get("assist-operation").value = operation;
    fire("assist-operation", "change");
    for (const [field, value] of Object.entries(values)) {
      get(fieldId(field)).value = value;
      fire(fieldId(field), "input");
    }
  }
  function prepare(name, operation, values) {
    fill(operation, values);
    fire("prepare-command", "click");
    check(get("preparation-error").textContent === "", `${name}: preparation failed`);
    const command = get("command").value;
    vectors.push({ name, operation, fields: values, command });
    return command;
  }
  function seedResults() {
    for (const id of ["response", "error", "knowledge-value", "projection-list-id"]) {
      get(id).textContent = "stale";
    }
    get("knowledge-projection").hidden = false;
    get("list-projection").hidden = false;
  }
  function checkCleared(label) {
    check(get("response").textContent === "" && get("error").textContent === ""
      && get("knowledge-value").textContent === "" && get("projection-list-id").textContent === ""
      && get("knowledge-projection").hidden && get("list-projection").hidden, label);
  }
  try {
    for (const kind of ["fact", "concept", "state"]) {
      const values = { ...base, kind };
      const command = prepare(`store-${kind}`, "store", values);
      check(command === `knowledge store :: ${JSON.stringify(values)}`, "Closed STORE payload");
    }
    const literal = { ...base, record_id: "  a  b  ", key: "é e\u0301 😀",
      value: '  "quoted" \\n C:\\notes\nline\t:: | <script>x</script>  ',
      source_type: " \u0085manual\u001c ", source_reference: "  notebook:7  " };
    check(prepare("literal-escapes", "store", literal)
      === `knowledge store :: ${JSON.stringify(literal)}`, "Preserve captured strings and escapes");
    const read = prepare("read-spaces", "read", { record_id: "  a  b  " });
    check(read === 'knowledge read :: {"record_id":"  a  b  "}', "READ fields closed");
    check(prepare("find-unfiltered", "find", { key: "greeting", kind: "" })
      === 'knowledge find :: {"key":"greeting"}', "FIND omits absent kind");
    for (const kind of ["fact", "concept", "state"]) {
      prepare(`find-${kind}`, "find", { key: "greeting", kind });
    }
    const whitespace = "\t\n\v\f\r\u001c\u001d\u001e\u001f \u0085\u00a0\u1680"
      + "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
      + "\u2028\u2029\u202f\u205f\u3000";
    for (const field of fields.filter((value) => value !== "kind")) {
      for (const value of ["", ...whitespace, "\ud800", "\udfff", "a\ud800b"]) {
        const previous = get("command").value;
        fill("store", { ...base, [field]: value });
        fire("prepare-command", "click");
        check(get("preparation-error").textContent !== "", `Reject invalid ${field}`);
        check(get("command").value === previous, "Rejected preparation preserves editor");
      }
    }
    for (const record_id of ["\u200b", "\ufeff", "a\u0000b", "😀"]) {
      prepare("non-whitespace-unicode", "read", { record_id });
    }
    const overhead = 'knowledge read :: {"record_id":""}'.length;
    const exact = "😀".repeat(8192 - overhead);
    check(Array.from(prepare("length-8192", "read", { record_id: exact })).length === 8192,
      "8192 counts code points, not UTF-16 units");
    fill("read", { record_id: exact + "x" });
    fire("prepare-command", "click");
    check(get("preparation-error").textContent.includes("8192"), "Reject 8193");
    // Escaped characters consume the serialized command budget.
    fill("read", { record_id: "\"".repeat(4096) });
    fire("prepare-command", "click");
    check(get("preparation-error").textContent.includes("8192"), "Count JSON escapes");
    prepare("state-transition", "store", base);
    seedResults();
    fire("assist-value", "input");
    checkCleared("Field edits clear prior results");
    check(get("preparation-status").textContent.includes("not been applied"), "Field dirty state");
    const prior = get("command").value;
    seedResults();
    get("assist-operation").value = "read";
    fire("assist-operation", "change");
    checkCleared("Operation changes clear results");
    check(get("command").value === prior, "Operation selection preserves editor");
    check(fields.every((field) => get(fieldId(field)).value === ""), "Operation resets all fields");
    check(get("assist-source-type").disabled && get("assist-source-type-row").hidden,
      "READ hides and disables provenance input");
    seedResults();
    const manual = '  list read manual-list  ';
    get("command").value = manual;
    fire("command", "input");
    checkCleared("Manual edits clear prior results");
    check(get("command-state").textContent.includes("Manually edited"), "Manual state visible");
    check(get("prepare-command").textContent.includes("replace"), "Replacement is explicit");
    seedResults();
    fill("read", { record_id: "replacement" });
    fire("prepare-command", "click");
    checkCleared("Explicit preparation clears results");
    check(get("command").value === 'knowledge read :: {"record_id":"replacement"}',
      "Explicit preparation replaces manual editor");
    get("command").value = manual;
    fire("command", "input");
    check(calls.length === 0, "Preparing, editing and changing operation make no calls");
    let release;
    responseFactory = () => new Promise((resolve) => { release = resolve; });
    get("proof").value = "synthetic-sprint37-proof";
    get("cognitive-fallback").checked = true;
    seedResults();
    fire("command-form", "submit");
    fire("command-form", "submit");
    check(calls.length === 1, "Double submit produces exactly one request");
    checkCleared("Submit synchronously clears old results");
    check(get("status").textContent === "Pending", "Pending state visible");
    check(controls.every((id) => get(id).disabled), "Controls locked during request");
    check(fields.every((field) => get(fieldId(field)).disabled), "All helper fields locked");
    fire("prepare-command", "click");
    fire("assist-operation", "change");
    check(get("command").value === manual && get("status").textContent === "Pending",
      "Pending guards prevent preparation and state changes");
    check(calls.length === 1, "Pending helper actions cannot send");
    check(get("proof").value === "", "Proof cleared before request");
    const sent = JSON.parse(calls[0].options.body);
    check(sent.text === manual && sent.allow_cognitive_fallback === true, "Exact editor and explicit fallback");
    check(sent.proof === "synthetic-sprint37-proof"
      && sent.requested_workspace_id === "luxiom-local-dev-workspace", "Existing request authority fields");
    check(Object.keys(sent).sort().join() === "allow_cognitive_fallback,proof,requested_workspace_id,text",
      "No new API fields");
    check(calls[0].url === "/local/command" && calls[0].options.method === "POST"
      && calls[0].options.headers["X-Luxiom-CSRF"], "Existing endpoint and CSRF");
    release({ json: async () => ({ success: true, route: "local", response: "Canonical",
      projection: { kind: "list", operation: "read", list_id: "manual-list", items: ["<b>literal</b>"] } }) });
    await flush();
    check(controls.every((id) => !get(id).disabled), "Controls restored on success");
    check(!get("list-projection").hidden && get("knowledge-projection").hidden, "List projection compatible");
    check(get("response").textContent === "Canonical", "Canonical response retained");
    for (const factory of [
      async () => { throw new Error("network failure"); },
      async () => ({ json: async () => { throw new Error("invalid JSON"); } }),
      async () => ({ json: async () => ({ success: false, route: "local", response: null,
        error: { code: "local_knowledge_conflict", message: "Conflict" } }) }),
    ]) {
      responseFactory = factory;
      get("proof").value = "synthetic-sprint37-proof";
      fire("command-form", "submit");
      await flush();
      check(controls.every((id) => !get(id).disabled), "Controls restored after failure");
      check(get("status").textContent === "Failed" && get("error").textContent !== "", "Failure visible");
      check(get("list-projection").hidden && get("knowledge-projection").hidden, "Failure hides projections");
      check(get("command").value === manual, "Failure retains editor");
    }
    const csrf = document.querySelector('meta[name="luxiom-csrf"]');
    const token = csrf.getAttribute("content");
    try {
      csrf.setAttribute("content", "");
      const before = calls.length;
      seedResults();
      fire("command-form", "submit");
      await flush();
      check(calls.length === before, "Missing CSRF sends no request");
      check(get("response").textContent === "" && get("knowledge-projection").hidden,
        "CSRF failure clears stale state");
      check(controls.every((id) => !get(id).disabled), "CSRF failure leaves controls usable");
    } finally {
      csrf.setAttribute("content", token);
    }
    return { environment: environment ? "node-dom-double" : "browser", passed, vectors,
      requests: calls.length, actualRequests: 0 };
  } finally {
    scope.fetch = originalFetch;
    get("proof").value = "";
    get("cognitive-fallback").checked = false;
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { runLocalKnowledgeCommandAssistance };
  if (require.main === module) {
    const fs = require("node:fs");
    const vm = require("node:vm");
    const path = require("node:path");
    const root = path.resolve(__dirname, "../..");
    // Minimal event/element fixture. It does NOT prove native browser behavior,
    // HTML constraint validation, focus, layout, accessibility, or transport.
    class Element {
      constructor() {
        this.value = ""; this.textContent = ""; this.hidden = false;
        this.disabled = false; this.checked = false; this.children = [];
        this.listeners = {}; this.attributes = {}; this.parentElement = null;
      }
      addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); }
      dispatchEvent(event) {
        event.target ||= this;
        for (const callback of this.listeners[event.type] || []) callback(event);
        if (event.bubbles && this.parentElement) this.parentElement.dispatchEvent(event);
        return true;
      }
      replaceChildren(...children) { this.children = children; this.textContent = ""; }
      appendChild(child) { this.children.push(child); }
      append(...children) { this.children.push(...children); }
      getAttribute(name) { return this.attributes[name]; }
      setAttribute(name, value) { this.attributes[name] = value; }
      focus() {}
    }
    const html = fs.readFileSync(path.join(root, "app/api/static/local_ui/index.html"), "utf8");
    const elements = Object.fromEntries([...html.matchAll(/\bid="([^"]+)"/g)]
      .map((match) => [match[1], new Element()]));
    for (const field of ["record-id", "kind", "key", "value", "source-type", "source-reference"]) {
      elements[`assist-${field}`].parentElement = elements[`assist-${field}-row`];
      elements[`assist-${field}-row`].parentElement = elements["knowledge-assistance"];
    }
    elements["assist-operation"].value = "store";
    const csrf = new Element();
    csrf.setAttribute("content", "synthetic-sprint37-csrf");
    const scope = {
      document: {
        querySelector: (selector) => selector.startsWith("#") ? elements[selector.slice(1)] : csrf,
        createElement: () => new Element(),
      },
      Event: class {
        constructor(type, options) { this.type = type; Object.assign(this, options); }
        preventDefault() {}
      },
      fetch: () => { throw new Error("Unexpected unmocked network call"); },
    };
    const context = vm.createContext(scope);
    const source = fs.readFileSync(path.join(root, "app/api/static/local_ui/app.js"), "utf8");
    vm.runInContext(source, context);
    runLocalKnowledgeCommandAssistance(scope).then((result) => {
      // Invalid kind cannot be selected in the real closed dropdown. Exercise
      // the actual serializer directly for strict kinds, types and operations.
      for (const expression of [
        'prepareKnowledgeCommand("read", {record_id: null})',
        'prepareKnowledgeCommand("read", {record_id: 1})',
        'prepareKnowledgeCommand("read", {record_id: []})',
        'prepareKnowledgeCommand("read", {record_id: true})',
        'prepareKnowledgeCommand("find", {key: "k", kind: "FACT"})',
        'prepareKnowledgeCommand("find", {key: "k", kind: " fact "})',
        'prepareKnowledgeCommand("find", {key: "k", kind: null})',
        'prepareKnowledgeCommand("delete", {})',
        'prepareKnowledgeCommand("__proto__", {})',
      ]) {
        let rejected = false;
        try { vm.runInContext(expression, context); } catch { rejected = true; }
        if (!rejected) throw new Error(`Expected rejection: ${expression}`);
        result.passed += 1;
      }
      process.stdout.write(JSON.stringify(result));
    }).catch((error) => { process.stderr.write(String(error)); process.exitCode = 1; });
  }
}
