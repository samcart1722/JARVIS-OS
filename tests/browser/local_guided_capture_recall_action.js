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

if (require.main === module) {
  try {
    process.stdout.write(JSON.stringify(runGuidedCaptureRecallAction()));
  } catch (error) {
    process.stderr.write(String(error));
    process.exitCode = 1;
  }
}

module.exports = { runGuidedCaptureRecallAction };
