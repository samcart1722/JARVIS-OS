"use strict";

// Sprint 40 Block A: presentation-state shell only.
// This uses the established DOM double and proves zero requests, not native browser behavior.
const vm = require("node:vm");
const {
  createEnvironment,
} = require("./local_knowledge_command_assistance.js");

function runGuidedCaptureRecallAction() {
  const { scope, context } = createEnvironment();
  const get = (id) => scope.document.querySelector(`#${id}`);
  const fire = (element, type = "click") => element.dispatchEvent(
    new scope.Event(type, { bubbles: true, cancelable: true }),
  );

  const categories = new Set();
  let passed = 0;
  const check = (category, condition, message) => {
    if (!condition) throw new Error(`${category}: ${message}`);
    categories.add(category);
    passed += 1;
  };

  const calls = [];
  scope.fetch = (url, options) => {
    calls.push({ url, options });
    throw new Error("Guided Block A must not fetch");
  };

  const stateOf = (stage) => get(`guided-${stage}`).getAttribute("data-guide-state");
  const outputOf = (stage) => get(`guided-${stage}-state`).textContent;

  check(
    "initial",
    stateOf("capture") === "ready"
      && stateOf("recall") === "not-started"
      && stateOf("follow-up") === "not-started"
      && stateOf("verify") === "not-started",
    "initial guided states",
  );
  check(
    "initial",
    get("guided-status").textContent.includes("Capture is ready"),
    "initial status announcement",
  );

  const states = [
    "not-started",
    "ready",
    "prepared",
    "pending",
    "completed",
    "failed",
  ];
  for (const state of states) {
    scope.testState = state;
    vm.runInContext(
      'setGuidedStageState("capture", testState, `state:${testState}`)',
      context,
    );
    check(
      "states",
      stateOf("capture") === state
        && outputOf("capture") !== ""
        && get("guided-status").textContent === `state:${state}`,
      `render ${state}`,
    );
  }

  for (const expression of [
    'setGuidedStageState("unknown", "ready")',
    'setGuidedStageState("capture", "unknown")',
  ]) {
    let rejected = false;
    try {
      vm.runInContext(expression, context);
    } catch {
      rejected = true;
    }
    check("validation", rejected, `reject ${expression}`);
  }

  get("command").value = "  list read manual-list  ";
  fire(get("command"), "input");
  fire(get("guided-reset"));
  check(
    "reset",
    stateOf("capture") === "ready"
      && stateOf("recall") === "not-started"
      && stateOf("follow-up") === "not-started"
      && stateOf("verify") === "not-started",
    "reset restores initial presentation state",
  );
  check(
    "editor-authority",
    get("command").value === "  list read manual-list  ",
    "guide reset never rewrites editor",
  );
  check(
    "reset",
    get("guided-status").textContent.includes("no command was prepared or executed"),
    "reset truth is explicit",
  );
  check("no-fetch", calls.length === 0, "all Block A interactions are local presentation only");

  return {
    environment: "node-dom-double",
    categories: [...categories],
    passed,
    states,
    actualRequests: calls.length,
    nativeBrowserVerified: false,
  };
}

async function runGuidedCaptureRecall() {
  const { scope } = createEnvironment();
  const get = (id) => scope.document.querySelector(`#${id}`);
  const fire = (element, type = "click") => element.dispatchEvent(
    new scope.Event(type, { bubbles: true, cancelable: true }),
  );
  const flush = async () => {
    for (let i = 0; i < 12; i += 1) await Promise.resolve();
  };

  const categories = new Set();
  const vectors = [];
  let passed = 0;
  const check = (category, condition, message) => {
    if (!condition) throw new Error(`${category}: ${message}`);
    categories.add(category);
    passed += 1;
  };

  const calls = [];
  let reply;
  scope.fetch = (url, options) => {
    calls.push({ url, options });
    return new Promise((resolve) => {
      reply = { resolve };
    });
  };

  const resolve = async (result) => {
    reply.resolve({ json: async () => result });
    await flush();
  };

  const stateOf = (stage) => get(`guided-${stage}`).getAttribute(
    "data-guide-state",
  );

  const send = () => {
    get("proof").value = "synthetic-sprint40-proof";
    fire(get("command-form"), "submit");
  };

  const setField = (id, value) => {
    get(id).value = value;
    fire(get(id), "input");
  };

  // Capture: preparation is local only; Send remains explicit.
  setField("assist-record-id", "  memory-1  ");
  get("assist-kind").value = "fact";
  fire(get("assist-kind"), "input");
  setField("assist-key", "appointment");
  setField("assist-value", "Call tomorrow");
  setField("assist-source-type", "explicit-note");
  setField("assist-source-reference", "sprint40:block-b");

  fire(get("prepare-command"));
  const storeCommand = get("command").value;
  vectors.push({ operation: "store", command: storeCommand });

  check(
    "capture-prepare",
    stateOf("capture") === "prepared" && calls.length === 0,
    "STORE preparation must not execute",
  );

  send();
  check(
    "capture-send",
    calls.length === 1
      && JSON.parse(calls[0].options.body).text === storeCommand
      && stateOf("capture") === "pending",
    "explicit Send transmits exact prepared STORE",
  );

  await resolve({
    success: true,
    route: "local",
    response: "Knowledge stored locally.",
    error: null,
    projection: {
      kind: "knowledge",
      operation: "store",
      created: true,
      record: {
        record_id: "memory-1",
        kind: "fact",
        key: "appointment",
        value: "Call tomorrow",
      },
    },
  });

  check(
    "capture-result",
    stateOf("capture") === "completed"
      && stateOf("recall") === "ready",
    "matching STORE completes Capture only from governed projection",
  );

  // FIND: a successful query returns selectable records but does not complete Recall.
  get("assist-operation").value = "find";
  fire(get("assist-operation"), "change");
  setField("assist-key", "appointment");
  get("assist-kind").value = "fact";
  fire(get("assist-kind"), "input");
  fire(get("prepare-command"));

  const findCommand = get("command").value;
  vectors.push({ operation: "find", command: findCommand });

  check(
    "recall-query-prepare",
    stateOf("recall") === "prepared" && calls.length === 1,
    "FIND preparation remains zero request",
  );

  send();
  check(
    "recall-query-send",
    calls.length === 2
      && JSON.parse(calls[1].options.body).text === findCommand
      && stateOf("recall") === "pending",
    "FIND executes only on explicit Send",
  );

  const record = {
    record_id: "memory-1",
    kind: "fact",
    key: "appointment",
    value: "Call tomorrow",
  };

  await resolve({
    success: true,
    route: "local",
    response: "Knowledge records found locally.",
    error: null,
    projection: {
      kind: "knowledge",
      operation: "find",
      records: [record],
      truncated: false,
    },
  });

  check(
    "recall-query-result",
    stateOf("recall") === "ready"
      && get("knowledge-records").children.length === 1,
    "FIND result makes Recall selectable but incomplete",
  );

  const findReadButton = get("knowledge-records").children[0].children[1];
  const callsBeforeSelection = calls.length;
  fire(findReadButton);

  const selectedRead = get("command").value;
  vectors.push({ operation: "read", command: selectedRead });

  check(
    "selection",
    selectedRead === 'knowledge read :: {"record_id":"memory-1"}'
      && stateOf("recall") === "prepared"
      && calls.length === callsBeforeSelection,
    "record selection prepares READ without request",
  );

  // Manual editor remains authoritative; mismatched READ cannot complete Recall.
  get("command").value = 'knowledge read :: {"record_id":"other-record"}';
  fire(get("command"), "input");
  const editedRead = get("command").value;
  send();

  check(
    "manual-editor",
    calls.length === 3
      && JSON.parse(calls[2].options.body).text === editedRead,
    "manual editor text remains authoritative",
  );

  await resolve({
    success: true,
    route: "local",
    response: "Knowledge record read locally.",
    error: null,
    projection: {
      kind: "knowledge",
      operation: "read",
      record: {
        record_id: "other-record",
        kind: "fact",
        key: "other",
        value: "Other",
      },
    },
  });

  check(
    "mismatch",
    stateOf("recall") === "failed"
      && stateOf("follow-up") === "not-started",
    "mismatched structured READ cannot complete Recall",
  );

  // Re-render a governed FIND result and select again for a valid retry.
  scope.syntheticResult = {
    success: true,
    route: "local",
    response: "Knowledge records found locally.",
    error: null,
    projection: {
      kind: "knowledge",
      operation: "find",
      records: [record],
      truncated: false,
    },
  };
  const vm = require("node:vm");
  vm.runInContext("renderResult(syntheticResult)", scope);
  const retryButton = get("knowledge-records").children[0].children[1];
  fire(retryButton);

  check(
    "selection",
    get("command").value === selectedRead
      && stateOf("recall") === "prepared",
    "reselection restores guided READ correlation",
  );

  send();
  check(
    "recall-read-send",
    calls.length === 4
      && JSON.parse(calls[3].options.body).text === selectedRead,
    "selected READ still requires a separate Send",
  );

  await resolve({
    success: true,
    route: "local",
    response: "Knowledge record read locally.",
    error: null,
    projection: {
      kind: "knowledge",
      operation: "read",
      record,
    },
  });

  check(
    "recall-complete",
    stateOf("recall") === "completed"
      && stateOf("follow-up") === "ready",
    "matching selected READ completes Recall",
  );

  // Editing Recall fields immediately invalidates completion and dependents.
  setField("assist-key", "replacement query");
  check("recall-replacement", stateOf("capture") === "completed"
    && stateOf("recall") === "ready"
    && stateOf("follow-up") === "not-started"
    && stateOf("verify") === "not-started"
    && calls.length === 4,
  "Recall input changes clear prior success and dependents without requests");
  fire(get("prepare-command"));
  check("recall-replacement", stateOf("recall") === "prepared"
    && calls.length === 4, "replacement FIND only prepares");
  send();
  check("recall-replacement", calls.length === 5
    && stateOf("recall") === "pending"
    && JSON.parse(calls[4].options.body).text === get("command").value,
  "replacement FIND requires explicit exact-editor Send");
  await resolve({ success: false, error: { message: "Query rejected" } });
  check("recall-replacement", stateOf("recall") === "failed"
    && stateOf("follow-up") === "not-started"
    && !get("guided-status").textContent.includes("Recall completed"),
  "failed replacement FIND cannot restore prior completion");

  // Re-enter Capture through operation selection, then complete a fresh STORE.
  get("assist-operation").value = "store";
  fire(get("assist-operation"), "change");
  check("operation-replacement", stateOf("capture") === "ready"
    && stateOf("recall") === "not-started" && calls.length === 5,
  "operation re-entry invalidates completed Capture without sending");
  for (const [id, value] of Object.entries({
    "assist-record-id": "one", "assist-kind": "fact",
    "assist-key": "key", "assist-value": "value",
    "assist-source-type": "explicit-note", "assist-source-reference": "test",
  })) setField(id, value);
  fire(get("prepare-command"));
  send();
  check("capture-replacement", calls.length === 6
    && stateOf("capture") === "pending", "fresh Capture requires explicit Send");
  await resolve({ success: true, projection: {
    kind: "knowledge", operation: "store", created: true,
    record: { record_id: "one", kind: "fact", key: "key", value: "value" },
  } });
  check("capture-replacement", stateOf("capture") === "completed"
    && stateOf("recall") === "ready", "fresh Capture completed before replacement");
  setField("assist-record-id", "two");
  check("capture-replacement", stateOf("capture") === "ready"
    && stateOf("recall") === "not-started"
    && stateOf("follow-up") === "not-started"
    && stateOf("verify") === "not-started"
    && calls.length === 6,
  "Capture field edit immediately invalidates success and dependent progress");
  fire(get("prepare-command"));
  check("capture-replacement", stateOf("capture") === "prepared"
    && calls.length === 6, "replacement STORE prepares with zero requests");
  send();
  check("capture-replacement", calls.length === 7
    && stateOf("capture") === "pending"
    && JSON.parse(calls[6].options.body).text === get("command").value,
  "replacement STORE requires explicit exact-editor Send");
  await resolve({ success: false, error: { message: "Store rejected" } });
  check("capture-replacement", stateOf("capture") === "failed"
    && stateOf("recall") === "not-started"
    && !get("guided-status").textContent.includes("Capture completed"),
  "failed replacement STORE cannot restore previous Capture success");
  fire(get("guided-reset"));

  check(
    "no-hidden-send",
    calls.length === 7,
    "no guided preparation or selection introduced hidden requests",
  );

  return {
    environment: "node-dom-double",
    categories: [...categories],
    passed,
    vectors,
    actualRequests: calls.length,
    nativeBrowserVerified: false,
  };
}

async function runGuidedFollowUp() {
  const { scope, context } = createEnvironment();
  const get = (id) => scope.document.querySelector(`#${id}`);
  const fire = (id, type = "click") => get(id).dispatchEvent(
    new scope.Event(type, { bubbles: true, cancelable: true }),
  );
  const state = () => JSON.parse(vm.runInContext("JSON.stringify(guidedState)", context));
  const categories = new Set();
  const vectors = [];
  let passed = 0;
  const check = (category, condition, message) => {
    if (!condition) throw new Error(`${category}: ${message}`);
    categories.add(category);
    passed += 1;
  };
  const calls = [];
  let submissions = 0;
  let reply;
  scope.fetch = (url, options) => {
    calls.push({ url, options });
    check("no-hidden-send", calls.length === submissions, "fetch requires explicit submission");
    return new Promise((resolve, reject) => { reply = { resolve, reject }; });
  };
  const flush = async () => { for (let i = 0; i < 15; i += 1) await Promise.resolve(); };
  const send = () => {
    submissions += 1;
    const text = get("command").value;
    get("proof").value = "synthetic-block-c-proof";
    fire("command-form", "submit");
    check("exact-editor", calls.length === submissions
      && JSON.parse(calls.at(-1).options.body).text === text, "Send preserves exact editor text");
  };
  const finish = async (result) => {
    reply.resolve({ json: async () => result });
    await flush();
  };
  const field = (id, value) => { get(id).value = value; fire(id, "input"); };
  const stage = (name) => state().stages[name];
  const record = { record_id: "one", kind: "fact", key: "key", value: "value" };
  check("precondition", stage("follow-up") === "not-started"
    && get("prepare-follow-up").disabled, "Follow-up is unavailable before Recall");
  fire("prepare-follow-up");
  check("precondition", state().correlation === null && calls.length === 0, "early preparation ignored");
  for (const [id, value] of Object.entries({
    "assist-record-id": "one", "assist-kind": "fact", "assist-key": "key",
    "assist-value": "value", "assist-source-type": "explicit-note", "assist-source-reference": "test",
  })) field(id, value);
  fire("prepare-command");
  send();
  await finish({ success: true, projection: { kind: "knowledge", operation: "store", created: true, record } });
  check("precondition", get("prepare-follow-up").disabled, "Capture alone does not enable Follow-up");
  get("assist-operation").value = "find";
  fire("assist-operation", "change");
  field("assist-key", "key");
  fire("prepare-command");
  send();
  await finish({ success: true, projection: { kind: "knowledge", operation: "find", records: [record], truncated: false } });
  get("knowledge-records").children[0].children[1].dispatchEvent(new scope.Event("click"));
  send();
  await finish({ success: true, projection: { kind: "knowledge", operation: "read", record } });
  check("precondition", stage("follow-up") === "ready" && stage("verify") === "not-started"
    && !get("prepare-follow-up").disabled, "selected READ enables Follow-up");

  const prepare = (listId = "tasks", item = "  Call pharmacy tomorrow  ") => {
    const before = calls.length;
    field("follow-up-list-id", listId);
    field("follow-up-item", item);
    fire("prepare-follow-up");
    check("preparation", calls.length === before && stage("follow-up") === "prepared"
      && stage("verify") === "not-started", "preparation is local and incomplete");
    const correlation = state().correlation;
    vectors.push({ command: get("command").value, listId, expectedItem: correlation.expectedItem });
    return correlation;
  };
  const initial = prepare();
  check("whitespace", get("command").value === "list add tasks :: Call pharmacy tomorrow"
    && initial.listId === "tasks" && initial.expectedItem === "Call pharmacy tomorrow", "Python outer strip");
  for (const [listId, item, category] of [
    ["my tasks", "item", "list-id-whitespace"], [" tasks ", "item", "list-id-whitespace"],
    ["my\u0085tasks", "item", "list-id-whitespace"], ["my\u001ctasks", "item", "list-id-whitespace"],
    ["project::tasks", "item", "delimiter-collision"], ["", "item", "blank"],
    ["\u3000", "item", "blank"], ["tasks", " \u0085\u001c ", "blank"],
    ["tasks", "Call pharmacy | Send email", "item-separator"],
    ["tasks", "\ud800", "unicode-rejection"],
    ["tasks", "x".repeat(8192), "length"],
  ]) {
    const before = calls.length;
    const editor = get("command").value;
    field("follow-up-list-id", listId); field("follow-up-item", item); fire("prepare-follow-up");
    check(category, stage("follow-up") === "failed" && state().correlation === null
      && get("follow-up-error").textContent !== "" && get("command").value === editor
      && calls.length === before, "invalid input rejected without editor replacement or request");
  }
  for (const expression of ['prepareFollowUpCommand(null, "item")', 'prepareFollowUpCommand("tasks", null)']) {
    let rejected = false;
    try { vm.runInContext(expression, context); } catch { rejected = true; }
    check("types", rejected, "non-string input rejected");
  }
  prepare("t?ches", "\u001c\u0085  Appeler  Jos?\n?? ?? e\u0301 \u3000");
  check("unicode", state().correlation.expectedItem === "Appeler  Jos?\n?? ?? e\u0301", "interior whitespace and Unicode preserved");
  prepare("tasks", "\ufeffitem\ufeff");
  check("whitespace", state().correlation.expectedItem === "\ufeffitem\ufeff", "Python does not strip BOM");

  const add = (listId = "tasks", item = "Call pharmacy tomorrow") => ({
    success: true, projection: { kind: "list", operation: "add", list_id: listId,
      added: [item], already_present: [], items: [item] },
  });
  prepare(); send();
  check("pending", stage("follow-up") === "pending" && get("prepare-follow-up").disabled
    && get("follow-up-item").disabled && get("follow-up-list-id").disabled
    && get("guided-reset").disabled, "pending locks guided controls");
  const pendingCount = calls.length;
  fire("prepare-follow-up"); fire("guided-reset"); fire("command-form", "submit");
  check("pending", calls.length === pendingCount && stage("follow-up") === "pending", "no double execution");
  await finish(add());
  check("added", stage("follow-up") === "completed" && stage("verify") === "ready"
    && state().correlation === null && state().retainedFollowUp.listId === "tasks"
    && state().retainedFollowUp.expectedItem === "Call pharmacy tomorrow", "matching ADD retains future verification context");
  const completedCount = calls.length;
  field("follow-up-item", "replacement");
  check("replacement", stage("follow-up") === "ready" && stage("verify") === "not-started"
    && stage("capture") === "completed" && stage("recall") === "completed"
    && state().retainedFollowUp === null && calls.length === completedCount, "completed replacement clears only downstream truth");
  prepare("tasks", "replacement"); send(); await finish({ success: false });
  check("replacement", stage("follow-up") === "failed" && stage("verify") === "not-started"
    && state().retainedFollowUp === null, "failed replacement cannot restore old success");

  prepare("tasks", "GRAPES"); send();
  const duplicate = add("tasks", "GRAPES");
  duplicate.projection.added = [];
  duplicate.projection.already_present = ["GRAPES"];
  duplicate.projection.items = ["grapes"];
  await finish(duplicate);
  check("already-present", stage("follow-up") === "completed"
    && state().retainedFollowUp.expectedItem === "GRAPES", "submitted spelling in duplicate projection completes ADD");

  const mismatches = [
    ["wrong-list", add("other")], ["absent-item", add("tasks", "other")],
    ["exact-spelling", add("tasks", "call pharmacy tomorrow")],
    ["unrelated", { success: true, projection: { kind: "knowledge", operation: "read", record } }],
    ["wrong-operation", { success: true, projection: { ...add().projection, operation: "read" } }],
    ["failure", { success: false, projection: add().projection }],
    ["malformed", { success: true }],
  ];
  for (const key of ["added", "already_present", "items"]) {
    for (const invalid of [null, "not-array", [3]]) {
      mismatches.push(["malformed", { success: true, projection: { ...add().projection, [key]: invalid } }]);
    }
  }
  for (const [category, result] of mismatches) {
    prepare(); send(); await finish(result);
    check(category, stage("follow-up") === "failed" && stage("verify") === "not-started"
      && state().retainedFollowUp === null, "mismatch cannot complete Follow-up");
  }
  prepare();
  const oldCorrelation = vm.runInContext("guidedState.correlation", context);
  field("command", "list add tasks :: Call pharmacy tomorrow ");
  check("manual-edit", state().correlation === null && stage("follow-up") === "ready", "even equivalent manual edit invalidates ADD correlation");
  send(); await finish(add());
  check("manual-edit", stage("follow-up") === "ready" && stage("verify") === "not-started", "matching result after manual edit cannot advance");
  prepare();
  check("retry", vm.runInContext("guidedState.correlation", context) !== oldCorrelation, "re-prepare establishes fresh correlation");
  send(); reply.reject(new Error("offline")); await flush();
  check("network-failure", stage("follow-up") === "failed"
    && get("command").value === "list add tasks :: Call pharmacy tomorrow", "disconnect preserves editor and incomplete truth");
  prepare();
  const count = calls.length;
  field("follow-up-item", "new item");
  check("prepared-edit", state().correlation === null && stage("follow-up") === "ready"
    && calls.length === count, "editing prepared input invalidates correlation locally");
  send(); await finish(add());
  check("prepared-edit", stage("follow-up") === "ready", "old editor cannot complete invalidated preparation");
  prepare(); fire("prepare-browse");
  check("operation-replacement", state().correlation?.stage === "recall"
    && stage("follow-up") === "not-started" && state().retainedFollowUp === null, "earlier-stage replacement clears Follow-up");
  // Finish Recall again, then verify Reset clears successful retained context.
  send(); await finish({ success: true, projection: { kind: "knowledge", operation: "browse", records: [{ record_id: "one", kind: "fact", key: "key" }], truncated: false } });
  get("knowledge-records").children[0].children[1].dispatchEvent(new scope.Event("click"));
  send(); await finish({ success: true, projection: { kind: "knowledge", operation: "read", record } });
  prepare(); send(); await finish(add());
  const beforeReset = calls.length;
  fire("guided-reset");
  check("reset", state().correlation === null && state().retainedFollowUp === null
    && stage("capture") === "ready" && stage("recall") === "not-started"
    && stage("follow-up") === "not-started" && stage("verify") === "not-started"
    && get("prepare-follow-up").disabled && calls.length === beforeReset, "Reset clears all guide progress and retained context without requests");
  check("no-hidden-send", calls.length === submissions, "every mocked request came from explicit Send");
  return { environment: "node-dom-double", passed, categories: [...categories], vectors,
    actualRequests: 0, mockedFetchCalls: calls.length, explicitSubmissions: submissions,
    nativeBrowserVerified: false };
}

if (require.main === module) {
  const runner = process.argv.includes("--follow-up")
    ? runGuidedFollowUp
    : process.argv.includes("--capture-recall")
    ? runGuidedCaptureRecall
    : runGuidedCaptureRecallAction;

  Promise.resolve(runner()).then((result) => {
    process.stdout.write(JSON.stringify(result));
  }).catch((error) => {
    process.stderr.write(String(error));
    process.exitCode = 1;
  });
}

module.exports = {
  runGuidedCaptureRecallAction,
  runGuidedCaptureRecall,
  runGuidedFollowUp,
};
