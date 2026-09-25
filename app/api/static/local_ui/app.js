"use strict";

// Python str.strip() whitespace in the governed knowledge models.
const KNOWLEDGE_WHITESPACE_ONLY = /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u;
const KNOWLEDGE_LEADING_WHITESPACE = /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/u;
const KNOWLEDGE_TRAILING_WHITESPACE = /[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/u;

function stripKnowledgeWhitespace(value) {
  return value
    .replace(KNOWLEDGE_LEADING_WHITESPACE, "")
    .replace(KNOWLEDGE_TRAILING_WHITESPACE, "");
}
const KNOWLEDGE_FIELDS = Object.freeze({
  store: ["record_id", "kind", "key", "value", "source_type", "source_reference"],
  read: ["record_id"],
  find: ["key", "kind"],
  browse: [],
  "browse-after": ["after_record_id"],
});

function prepareKnowledgeCommand(operation, fields) {
  if (!Object.hasOwn(KNOWLEDGE_FIELDS, operation)) {
    throw new Error("Select STORE, READ, FIND or BROWSE.");
  }
  const payload = {};
  for (const field of KNOWLEDGE_FIELDS[operation]) {
    const value = fields[field];
    if (operation === "find" && field === "kind" && value === "") {
      continue;
    }
    if (typeof value !== "string" || KNOWLEDGE_WHITESPACE_ONLY.test(value)) {
      throw new Error(`${field} must contain non-whitespace text.`);
    }
    if (field === "kind" && !["fact", "concept", "state"].includes(value)) {
      throw new Error("kind must be exactly fact, concept or state.");
    }
    // Iteration combines valid UTF-16 pairs, leaving isolated surrogates visible.
    for (const character of value) {
      const point = character.codePointAt(0);
      if (point >= 0xd800 && point <= 0xdfff) {
        throw new Error(`${field} contains an isolated Unicode surrogate.`);
      }
    }
    payload[field] = value;
  }
  const command = `knowledge ${operation} :: ${JSON.stringify(payload)}`;
  if (Array.from(command).length > 8192) {
    throw new Error("The complete command exceeds 8192 Unicode code points.");
  }
  return command;
}

const GUIDE_STAGES = Object.freeze([
  "capture",
  "recall",
  "follow-up",
  "verify",
]);
const GUIDE_STATES = Object.freeze([
  "not-started",
  "ready",
  "prepared",
  "pending",
  "completed",
  "failed",
]);
const GUIDE_INITIAL_STATES = Object.freeze({
  capture: "ready",
  recall: "not-started",
  "follow-up": "not-started",
  verify: "not-started",
});
const GUIDE_STATE_LABELS = Object.freeze({
  "not-started": "Not started",
  ready: "Ready",
  prepared: "Prepared",
  pending: "Pending",
  completed: "Completed",
  failed: "Needs retry",
});

const guidedStatus = document.querySelector("#guided-status");
const guidedResetButton = document.querySelector("#guided-reset");
const guidedStageElements = Object.fromEntries(
  GUIDE_STAGES.map((stage) => [
    stage,
    document.querySelector(`#guided-${stage}`),
  ]),
);
const guidedStageOutputs = Object.fromEntries(
  GUIDE_STAGES.map((stage) => [
    stage,
    document.querySelector(`#guided-${stage}-state`),
  ]),
);

const form = document.querySelector("#command-form");
const sendButton = document.querySelector("#send-command");
const assistance = document.querySelector("#knowledge-assistance");
const operationInput = document.querySelector("#assist-operation");
const prepareButton = document.querySelector("#prepare-command");
const browseButton = document.querySelector("#prepare-browse");
let browseReadButtons = [];
let nextPageButton = null;
const preparationStatus = document.querySelector("#preparation-status");
const preparationError = document.querySelector("#preparation-error");
const commandState = document.querySelector("#command-state");
const assistanceInputs = Object.fromEntries(
  KNOWLEDGE_FIELDS.store.map((field) => [
    field, document.querySelector(`#assist-${field.replaceAll("_", "-")}`),
  ]),
);
const followUpListInput = document.querySelector("#follow-up-list-id");
const followUpItemInput = document.querySelector("#follow-up-item");
const followUpPrepareButton = document.querySelector("#prepare-follow-up");
const followUpError = document.querySelector("#follow-up-error");
let requestPending = false;
let guidedState = {
  stages: { ...GUIDE_INITIAL_STATES },
  correlation: null,
  retainedFollowUp: null,
};

function updateFollowUpControls() {
  const disabled = requestPending || guidedState.stages.recall !== "completed";
  followUpListInput.disabled = disabled;
  followUpItemInput.disabled = disabled;
  followUpPrepareButton.disabled = disabled;
}

function renderGuidedState(message = null) {
  updateFollowUpControls();
  for (const stage of GUIDE_STAGES) {
    const state = guidedState.stages[stage];
    guidedStageElements[stage].setAttribute("data-guide-state", state);
    guidedStageOutputs[stage].textContent = GUIDE_STATE_LABELS[state];
  }

  if (message !== null) {
    guidedStatus.textContent = message;
    return;
  }

  const currentStage = GUIDE_STAGES.find(
    (stage) => guidedState.stages[stage] !== "not-started"
      && guidedState.stages[stage] !== "completed",
  );
  if (currentStage) {
    guidedStatus.textContent =
      `${GUIDE_STATE_LABELS[guidedState.stages[currentStage]]}: `
      + `${currentStage}. Send remains explicit.`;
    return;
  }

  guidedStatus.textContent = "Guided workflow state is ready for the next step.";
}

function setGuidedStageState(stage, state, message = null) {
  if (!GUIDE_STAGES.includes(stage)) {
    throw new Error(`Unknown guided stage: ${stage}`);
  }
  if (!GUIDE_STATES.includes(state)) {
    throw new Error(`Unknown guided state: ${state}`);
  }
  guidedState.stages[stage] = state;
  renderGuidedState(message);
}

function resetGuidedExperience() {
  followUpError.textContent = "";
  guidedState = {
    stages: { ...GUIDE_INITIAL_STATES },
    correlation: null,
    retainedFollowUp: null,
  };
  renderGuidedState(
    "Guide reset. Capture is ready; no command was prepared or executed.",
  );
}

guidedResetButton.addEventListener("click", () => {
  if (requestPending) return;
  resetGuidedExperience();
});

renderGuidedState(
  "Capture is ready. No guided operation has been executed.",
);

function guidedStageLabel(stage) {
  return { capture: "Capture", recall: "Recall", "follow-up": "Follow-up" }[stage];
}

function guidedStageAvailable(stage) {
  if (stage === "capture") {
    return guidedState.stages.capture !== "completed";
  }
  if (stage === "recall") {
    return (
      guidedState.stages.capture === "completed"
      && guidedState.stages.recall !== "completed"
    );
  }
  return false;
}

function invalidateGuidedStage(stage) {
  if (requestPending || !["capture", "recall", "follow-up"].includes(stage)) return;
  const affected = GUIDE_STAGES.slice(GUIDE_STAGES.indexOf(stage));
  for (const dependent of affected) {
    guidedState.stages[dependent] = "not-started";
  }
  const prerequisite = stage === "recall" ? "capture" : "recall";
  guidedState.stages[stage] = stage === "capture"
    || guidedState.stages[prerequisite] === "completed" ? "ready" : "not-started";
  guidedState.retainedFollowUp = null;
  followUpError.textContent = "";
  if (affected.includes(guidedState.correlation?.stage)) {
    guidedState.correlation = null;
  }
  renderGuidedState(
    `${guidedStageLabel(stage)} inputs or preparation changed. `
      + "Previous progress for this step and dependent steps was cleared. Nothing was executed.",
  );
}

function invalidateGuidedOperation(operation) {
  if (operation === "store") invalidateGuidedStage("capture");
  else if (["find", "read", "browse", "browse-after"].includes(operation)) {
    invalidateGuidedStage("recall");
  }
}

function clearGuidedCorrelationForReplacement() {
  const correlation = guidedState.correlation;
  guidedState.correlation = null;
  if (!correlation) return;

  const stage = correlation.stage;
  if (
    ["capture", "recall", "follow-up"].includes(stage)
    && guidedState.stages[stage] !== "completed"
  ) {
    invalidateGuidedStage(stage);
  }
}

function setGuidedPreparation(stage, correlation, message) {
  guidedState.correlation = correlation;
  setGuidedStageState(stage, "prepared", message);
}

function prepareGuidedCapture(fields) {
  if (requestPending) return;
  invalidateGuidedStage("capture");
  const prepared = prepareEditorCommand("store", fields);
  if (!prepared) {
    if (guidedStageAvailable("capture")) {
      setGuidedStageState(
        "capture",
        "failed",
        "Capture preparation failed. Correct the fields and prepare again.",
      );
    }
    return;
  }

  if (!guidedStageAvailable("capture")) return;

  setGuidedPreparation(
    "capture",
    {
      stage: "capture",
      type: "capture-store",
      recordId: stripKnowledgeWhitespace(fields.record_id),
    },
    "Capture prepared. Review the editor, then explicitly Send.",
  );
}

function prepareGuidedRecallQuery(operation, fields) {
  if (requestPending) return;
  invalidateGuidedStage("recall");
  const prepared = prepareEditorCommand(operation, fields);
  if (!prepared) {
    if (guidedStageAvailable("recall")) {
      setGuidedStageState(
        "recall",
        "failed",
        "Recall preparation failed. Correct the fields and prepare again.",
      );
    }
    return;
  }

  if (!guidedStageAvailable("recall")) return;

  const projectionOperation = operation === "browse-after"
    ? "browse_after"
    : operation;

  setGuidedPreparation(
    "recall",
    {
      stage: "recall",
      type: "recall-query",
      operation: projectionOperation,
    },
    "Recall query prepared. Review the editor, then explicitly Send.",
  );
}

function prepareGuidedRecallRead(recordId) {
  if (requestPending) return;
  invalidateGuidedStage("recall");
  const prepared = prepareEditorCommand(
    "read",
    { record_id: recordId },
  );
  if (!prepared) {
    if (guidedStageAvailable("recall")) {
      setGuidedStageState(
        "recall",
        "failed",
        "READ preparation failed. Select the record again.",
      );
    }
    return;
  }

  if (!guidedStageAvailable("recall")) return;

  setGuidedPreparation(
    "recall",
    {
      stage: "recall",
      type: "recall-read",
      recordId: stripKnowledgeWhitespace(recordId),
    },
    "READ prepared for the selected record. Explicit Send is still required.",
  );
}

function isValidGuidedRecallQueryProjection(projection, operation) {
  if (
    projection?.kind !== "knowledge"
    || projection.operation !== operation
  ) {
    return false;
  }

  if (operation === "find") {
    return (
      Array.isArray(projection.records)
      && projection.records.every(isKnowledgeRecord)
      && typeof projection.truncated === "boolean"
    );
  }

  if (!["browse", "browse_after"].includes(operation)) {
    return false;
  }

  return (
    Array.isArray(projection.records)
    && projection.records.length <= 50
    && typeof projection.truncated === "boolean"
    && (!projection.truncated || projection.records.length === 50)
    && projection.records.every(isKnowledgeSummary)
  );
}

function beginGuidedRequest() {
  const correlation = guidedState.correlation;
  if (!correlation) return;

  const stage = correlation.stage;
  if (!["capture", "recall", "follow-up"].includes(stage)) return;
  if (guidedState.stages[stage] === "completed") return;

  setGuidedStageState(
    stage,
    "pending",
    `${guidedStageLabel(stage)} request pending. `
      + "Completion still depends on the governed result.",
  );
}

function failGuidedRequest(message) {
  const correlation = guidedState.correlation;
  if (!correlation) return;

  const stage = correlation.stage;
  if (!["capture", "recall", "follow-up"].includes(stage)) return;
  if (guidedState.stages[stage] === "completed") return;

  setGuidedStageState(stage, "failed", message);
}

function applyGuidedResult(result) {
  const correlation = guidedState.correlation;
  if (!correlation) return;

  if (result?.success !== true) {
    failGuidedRequest(
      "The governed request did not succeed. The guided step remains incomplete.",
    );
    return;
  }

  const projection = result.projection;

  if (correlation.type === "follow-up-add") {
    const strings = (value) => Array.isArray(value)
      && value.every((item) => typeof item === "string");
    if (
      projection?.kind !== "list"
      || projection.operation !== "add"
      || projection.list_id !== correlation.listId
      || !strings(projection.added)
      || !strings(projection.already_present)
      || !strings(projection.items)
      || !(projection.added.includes(correlation.expectedItem)
        || projection.already_present.includes(correlation.expectedItem))
    ) {
      failGuidedRequest(
        "The returned ADD did not match the prepared follow-up. Prepare again to retry.",
      );
      return;
    }
    guidedState.retainedFollowUp = {
      listId: correlation.listId,
      expectedItem: correlation.expectedItem,
    };
    guidedState.correlation = null;
    guidedState.stages["follow-up"] = "completed";
    guidedState.stages.verify = "ready";
    renderGuidedState(
      "Follow-up recorded from the governed ADD result. "
        + "Verify is ready; nothing else was executed.",
    );
    return;
  }

  if (correlation.type === "capture-store") {
    const matches = (
      projection?.kind === "knowledge"
      && projection.operation === "store"
      && isKnowledgeRecord(projection.record)
      && typeof projection.created === "boolean"
      && projection.record.record_id === correlation.recordId
    );

    if (!matches) {
      failGuidedRequest(
        "The returned result did not match the prepared Capture record.",
      );
      return;
    }

    guidedState.correlation = null;
    guidedState.stages.capture = "completed";
    guidedState.stages.recall = "ready";
    renderGuidedState(
      "Capture completed from the governed STORE result. Recall is ready.",
    );
    return;
  }

  if (correlation.type === "recall-query") {
    if (
      !isValidGuidedRecallQueryProjection(
        projection,
        correlation.operation,
      )
    ) {
      failGuidedRequest(
        "The returned result did not match the prepared Recall query.",
      );
      return;
    }

    guidedState.correlation = null;
    guidedState.stages.recall = "ready";
    renderGuidedState(
      "Recall results returned. Select a record to prepare READ; "
      + "selection does not execute it.",
    );
    return;
  }

  if (correlation.type === "recall-read") {
    const matches = (
      projection?.kind === "knowledge"
      && projection.operation === "read"
      && isKnowledgeRecord(projection.record)
      && projection.record.record_id === correlation.recordId
    );

    if (!matches) {
      failGuidedRequest(
        "The returned READ did not match the selected record. "
        + "Recall remains incomplete.",
      );
      return;
    }

    guidedState.correlation = null;
    guidedState.stages.recall = "completed";
    guidedState.stages["follow-up"] = "ready";
    renderGuidedState(
      "Recall completed from the selected READ result. Follow-up is ready.",
    );
  }
}

const proofInput = document.querySelector("#proof");
const commandInput = document.querySelector("#command");
const fallbackInput = document.querySelector("#cognitive-fallback");
const statusOutput = document.querySelector("#status");
const routeOutput = document.querySelector("#route");
const responseOutput = document.querySelector("#response");
const errorOutput = document.querySelector("#error");
const listProjection = document.querySelector("#list-projection");
const projectionListId = document.querySelector("#projection-list-id");
const projectionAddedRow = document.querySelector("#projection-added-row");
const projectionAdded = document.querySelector("#projection-added");
const projectionAlreadyPresentRow = document.querySelector(
  "#projection-already-present-row",
);
const projectionAlreadyPresent = document.querySelector(
  "#projection-already-present",
);
const projectionItems = document.querySelector("#projection-items");
const knowledgeProjection = document.querySelector("#knowledge-projection");
const knowledgeOperation = document.querySelector("#knowledge-operation");
const knowledgeRecordDetails = document.querySelector(
  "#knowledge-record-details",
);
const knowledgeRecordId = document.querySelector("#knowledge-record-id");
const knowledgeKind = document.querySelector("#knowledge-kind");
const knowledgeKey = document.querySelector("#knowledge-key");
const knowledgeValue = document.querySelector("#knowledge-value");
const knowledgeCreatedRow = document.querySelector("#knowledge-created-row");
const knowledgeCreated = document.querySelector("#knowledge-created");
const knowledgeCountRow = document.querySelector("#knowledge-count-row");
const knowledgeCount = document.querySelector("#knowledge-count");
const knowledgeRecords = document.querySelector("#knowledge-records");
const knowledgeEmpty = document.querySelector("#knowledge-empty");
const knowledgeTruncated = document.querySelector("#knowledge-truncated");
const continuationActions = document.createElement("div");
knowledgeProjection.appendChild(continuationActions);

function clearListProjection() {
  listProjection.hidden = true;
  projectionListId.textContent = "";
  projectionAdded.replaceChildren();
  projectionAlreadyPresent.replaceChildren();
  projectionItems.replaceChildren();
  projectionAddedRow.hidden = true;
  projectionAlreadyPresentRow.hidden = true;
}

function clearKnowledgeProjection() {
  if (nextPageButton) nextPageButton.disabled = true;
  nextPageButton = null;
  continuationActions.replaceChildren();
  for (const button of browseReadButtons) button.disabled = true;
  browseReadButtons = [];
  knowledgeProjection.hidden = true;
  knowledgeOperation.textContent = "";
  knowledgeRecordId.textContent = "";
  knowledgeKind.textContent = "";
  knowledgeKey.textContent = "";
  knowledgeValue.textContent = "";
  knowledgeCreated.textContent = "";
  knowledgeCount.textContent = "";
  knowledgeRecords.replaceChildren();
  knowledgeRecordDetails.hidden = true;
  knowledgeCreatedRow.hidden = true;
  knowledgeCountRow.hidden = true;
  knowledgeEmpty.hidden = true;
  knowledgeTruncated.hidden = true;
}

function clearAllProjections() {
  clearListProjection();
  clearKnowledgeProjection();
}

function renderCollection(output, values) {
  output.replaceChildren();
  if (values.length === 0) {
    output.textContent = "—";
    return;
  }

  const list = document.createElement("ul");
  for (const value of values) {
    const item = document.createElement("li");
    item.textContent = value;
    list.appendChild(item);
  }
  output.appendChild(list);
}

function renderListProjection(projection) {
  clearListProjection();
  if (
    projection?.kind !== "list"
    || typeof projection.list_id !== "string"
  ) {
    return;
  }

  const stringArray = (value) => (
    Array.isArray(value) && value.every((item) => typeof item === "string")
  );

  if (
    projection.operation === "add"
    && stringArray(projection.added)
    && stringArray(projection.already_present)
    && stringArray(projection.items)
  ) {
    projectionListId.textContent = projection.list_id;
    projectionAddedRow.hidden = false;
    projectionAlreadyPresentRow.hidden = false;
    renderCollection(projectionAdded, projection.added);
    renderCollection(
      projectionAlreadyPresent,
      projection.already_present,
    );
    renderCollection(projectionItems, projection.items);
    listProjection.hidden = false;
    return;
  }

  if (
    projection.operation === "read"
    && stringArray(projection.items)
  ) {
    projectionListId.textContent = projection.list_id;
    renderCollection(projectionItems, projection.items);
    listProjection.hidden = false;
  }
}

function isKnowledgeRecord(record) {
  if (record === null || typeof record !== "object" || Array.isArray(record)) {
    return false;
  }
  const keys = Object.keys(record);
  const expectedKeys = ["record_id", "kind", "key", "value"];
  return (
    keys.length === expectedKeys.length
    && expectedKeys.every((key) => keys.includes(key))
    && typeof record.record_id === "string"
    && ["fact", "concept", "state"].includes(record.kind)
    && typeof record.key === "string"
    && typeof record.value === "string"
  );
}

function renderKnowledgeRecord(record, selectable = false) {
  const recordId = record.record_id;
  const article = document.createElement("article");
  article.className = "knowledge-record";
  const details = document.createElement("dl");
  for (const [label, value] of [
    ["Record ID", record.record_id],
    ["Kind", record.kind],
    ["Key", record.key],
    ["Value", record.value],
  ]) {
    const row = document.createElement("div");
    row.className = "projection-row";
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    row.append(term, description);
    details.appendChild(row);
  }
  article.appendChild(details);

  if (selectable) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = commandInput.value
      ? "Prepare READ and replace editor command"
      : "Prepare READ";
    button.disabled = requestPending;
    button.addEventListener("click", () => {
      if (requestPending || button.disabled) return;
      prepareGuidedRecallRead(recordId);
    });
    browseReadButtons.push(button);
    article.appendChild(button);
  }

  knowledgeRecords.appendChild(article);
}

function renderKnowledgeProjection(projection) {
  clearKnowledgeProjection();
  if (projection?.kind !== "knowledge") {
    return;
  }

  if (["browse", "browse_after"].includes(projection.operation)) {
    if (
      !Array.isArray(projection.records)
      || projection.records.length > 50
      || typeof projection.truncated !== "boolean"
      || (projection.truncated && projection.records.length !== 50)
      || !projection.records.every(isKnowledgeSummary)
    ) return;
    knowledgeOperation.textContent = projection.operation === "browse_after"
      ? "Browse after" : "Browse";
    for (const record of projection.records) renderKnowledgeSummary(record);
    knowledgeEmpty.textContent = projection.operation === "browse_after"
      ? "No knowledge records after this ID in this workspace."
      : "No knowledge records in this workspace.";
    knowledgeTruncated.textContent = "Showing up to 50 records by ID. More records exist; prepare the next page to continue.";
    knowledgeEmpty.hidden = projection.records.length !== 0;
    knowledgeTruncated.hidden = !projection.truncated;
    if (projection.truncated) renderNextPageAction(projection.records);
    knowledgeProjection.hidden = false;
    return;
  }

  if (
    projection.operation === "store"
    && isKnowledgeRecord(projection.record)
    && typeof projection.created === "boolean"
  ) {
    knowledgeOperation.textContent = "Stored";
    knowledgeRecordId.textContent = projection.record.record_id;
    knowledgeKind.textContent = projection.record.kind;
    knowledgeKey.textContent = projection.record.key;
    knowledgeValue.textContent = projection.record.value;
    knowledgeCreated.textContent = projection.created ? "Yes" : "No";
    knowledgeRecordDetails.hidden = false;
    knowledgeCreatedRow.hidden = false;
    knowledgeProjection.hidden = false;
    return;
  }

  if (
    projection.operation === "read"
    && isKnowledgeRecord(projection.record)
  ) {
    knowledgeCreated.textContent = "";
    knowledgeCreatedRow.hidden = true;
    knowledgeOperation.textContent = "Read";
    knowledgeRecordId.textContent = projection.record.record_id;
    knowledgeKind.textContent = projection.record.kind;
    knowledgeKey.textContent = projection.record.key;
    knowledgeValue.textContent = projection.record.value;
    knowledgeRecordDetails.hidden = false;
    knowledgeProjection.hidden = false;
    return;
  }

  if (
    projection.operation === "find"
    && Array.isArray(projection.records)
    && projection.records.every(isKnowledgeRecord)
    && typeof projection.truncated === "boolean"
  ) {
    knowledgeOperation.textContent = "Find";
    knowledgeEmpty.textContent = "No matching knowledge records.";
    knowledgeTruncated.textContent = "Showing the first 50 matching records.";
    knowledgeCount.textContent = String(projection.records.length);
    knowledgeCountRow.hidden = false;
    for (const record of projection.records) {
      renderKnowledgeRecord(record, true);
    }
    knowledgeEmpty.hidden = projection.records.length !== 0;
    knowledgeTruncated.hidden = projection.truncated !== true;
    knowledgeProjection.hidden = false;
  }
}

function isKnowledgeSummary(record) {
  return record !== null && typeof record === "object" && !Array.isArray(record)
    && Object.keys(record).length === 3
    && ["record_id", "kind", "key"].every((key) => Object.hasOwn(record, key))
    && typeof record.record_id === "string"
    && ["fact", "concept", "state"].includes(record.kind)
    && typeof record.key === "string";
}

function renderResult(result) {
  clearAllProjections();
  statusOutput.textContent = result.success ? "Success" : "Failed";
  routeOutput.textContent = result.route || "—";
  responseOutput.textContent = result.response || "";
  errorOutput.textContent = result.error?.message || "";
  if (result.projection?.kind === "list") {
    renderListProjection(result.projection);
  } else if (result.projection?.kind === "knowledge") {
    renderKnowledgeProjection(result.projection);
  }
}

function renderLocalFailure() {
  clearAllProjections();
  statusOutput.textContent = "Failed";
  routeOutput.textContent = "—";
  responseOutput.textContent = "";
  errorOutput.textContent = "The local request could not be completed.";
}

function renderKnowledgeSummary(record) {
  // Capture the original data now; selection clears and detaches this article.
  const recordId = record.record_id;
  const article = document.createElement("article");
  article.className = "knowledge-record knowledge-summary";
  const details = document.createElement("dl");
  for (const [label, value] of [["Record ID", recordId], ["Kind", record.kind], ["Key", record.key]]) {
    const row = document.createElement("div");
    row.className = "projection-row";
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    row.append(term, description);
    details.appendChild(row);
  }
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = commandInput.value ? "Prepare READ and replace editor command" : "Prepare READ";
  button.disabled = requestPending;
  button.addEventListener("click", () => {
    if (requestPending || button.disabled) return;
    prepareGuidedRecallRead(recordId);
  });
  browseReadButtons.push(button);
  article.append(details, button);
  knowledgeRecords.appendChild(article);
}

function renderNextPageAction(records) {
  // Capture structured data before any preparation invalidates this result.
  const anchor = records[records.length - 1].record_id;
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Prepare next page";
  button.disabled = requestPending;
  button.hidden = requestPending;
  button.addEventListener("click", () => {
    if (requestPending || button.disabled || nextPageButton !== button) return;
    prepareGuidedRecallQuery(
      "browse-after",
      { after_record_id: anchor },
    );
  });
  nextPageButton = button;
  continuationActions.appendChild(button);
}

function clearDraftResults(status = "Ready") {
  clearAllProjections();
  statusOutput.textContent = status;
  routeOutput.textContent = "—";
  responseOutput.textContent = "";
  errorOutput.textContent = "";
}

function updatePreparationButton() {
  prepareButton.textContent = commandInput.value
    ? "Prepare and replace editor command"
    : "Prepare command";
  browseButton.textContent = commandInput.value
    ? "Prepare browse and replace editor command"
    : "Prepare browse";
}

function updateAssistanceFields() {
  const visibleFields = KNOWLEDGE_FIELDS[operationInput.value];
  for (const [field, input] of Object.entries(assistanceInputs)) {
    const visible = visibleFields.includes(field);
    input.parentElement.hidden = !visible;
    input.disabled = requestPending || !visible;
  }
}

function setRequestPending(pending) {
  requestPending = pending;
  sendButton.disabled = pending;
  proofInput.disabled = pending;
  commandInput.disabled = pending;
  fallbackInput.disabled = pending;
  operationInput.disabled = pending;
  prepareButton.disabled = pending;
  browseButton.disabled = pending;
  guidedResetButton.disabled = pending;
  for (const button of browseReadButtons) button.disabled = pending;
  if (nextPageButton) {
    nextPageButton.disabled = pending;
    nextPageButton.hidden = pending;
  }
  updateAssistanceFields();
  updateFollowUpControls();
}

operationInput.addEventListener("change", () => {
  if (requestPending) return;
  clearGuidedCorrelationForReplacement();
  invalidateGuidedOperation(operationInput.value);
  for (const input of Object.values(assistanceInputs)) input.value = "";
  updateAssistanceFields();
  clearDraftResults();
  preparationError.textContent = "";
  preparationStatus.textContent = "Operation changed. Fields reset; prepare again.";
  commandState.textContent = "Editor unchanged. The selected operation is not prepared.";
  updatePreparationButton();
});

assistance.addEventListener("input", (event) => {
  if (requestPending || event.target === operationInput) return;
  invalidateGuidedOperation(operationInput.value);
  clearDraftResults();
  preparationError.textContent = "";
  preparationStatus.textContent = "Field changes have not been applied to the editor.";
  updatePreparationButton();
});

commandInput.addEventListener("input", () => {
  if (requestPending) return;
  if (guidedState.correlation?.stage === "follow-up") {
    invalidateGuidedStage("follow-up");
  }
  clearDraftResults();
  commandState.textContent = "Manually edited. Send uses this exact text; fields are not reapplied.";
  updatePreparationButton();
});

fallbackInput.addEventListener("change", () => {
  if (!requestPending) clearDraftResults();
});

function prepareFollowUpCommand(listId, item) {
  const whitespace = /[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/u;
  if (typeof listId !== "string" || !listId || whitespace.test(listId)
    || listId.includes("::")) {
    throw new Error("List ID must be one nonblank token with no whitespace or ::.");
  }
  if (typeof item !== "string" || KNOWLEDGE_WHITESPACE_ONLY.test(item)
    || item.includes("|")) {
    throw new Error("Supply one nonblank item without |.");
  }
  const expectedItem = stripKnowledgeWhitespace(item);
  const command = `list add ${listId} :: ${expectedItem}`;
  for (const character of command) {
    const point = character.codePointAt(0);
    if (point >= 0xd800 && point <= 0xdfff) {
      throw new Error("Follow-up contains an isolated Unicode surrogate.");
    }
  }
  if (Array.from(command).length > 8192) {
    throw new Error("The complete command exceeds 8192 Unicode code points.");
  }
  return { command, listId, expectedItem };
}

for (const input of [followUpListInput, followUpItemInput]) {
  input.addEventListener("input", () => {
    if (requestPending || guidedState.stages.recall !== "completed") return;
    invalidateGuidedStage("follow-up");
    clearDraftResults();
  });
}

followUpPrepareButton.addEventListener("click", () => {
  if (requestPending || guidedState.stages.recall !== "completed") return;
  invalidateGuidedStage("follow-up");
  clearDraftResults();
  try {
    const prepared = prepareFollowUpCommand(
      followUpListInput.value, followUpItemInput.value,
    );
    clearGuidedCorrelationForReplacement();
    commandInput.value = prepared.command;
    preparationError.textContent = "";
    preparationStatus.textContent = "Follow-up command prepared. No operation has been executed.";
    commandState.textContent = "Review or edit the prepared command, then explicitly Send.";
    setGuidedPreparation("follow-up", {
      stage: "follow-up", type: "follow-up-add",
      listId: prepared.listId, expectedItem: prepared.expectedItem,
    }, "Follow-up prepared. Review the editor, then explicitly Send.");
    commandInput.focus();
    updatePreparationButton();
  } catch (error) {
    followUpError.textContent = error.message;
    setGuidedStageState(
      "follow-up", "failed",
      "Follow-up preparation failed. Editor unchanged; correct the fields and prepare again.",
    );
  }
});

function prepareEditorCommand(operation, fields) {
  if (requestPending) return;
  clearDraftResults();
  preparationError.textContent = "";
  const replaced = commandInput.value !== "";
  try {
    const preparedCommand = prepareKnowledgeCommand(operation, fields);
    clearGuidedCorrelationForReplacement();
    commandInput.value = preparedCommand;
    preparationStatus.textContent = `${operation === "read" ? "READ command" : "Command"} prepared. ${replaced ? "Previous editor command replaced. " : ""}No operation has been executed.`;
    commandState.textContent = "Review or edit the prepared command, then explicitly Send.";
    commandInput.focus();
    updatePreparationButton();
    return true;
  } catch (error) {
    preparationError.textContent = error.message;
    preparationStatus.textContent = "Preparation failed. Editor unchanged.";
    commandState.textContent = "Previous editor text retained; no new command was prepared.";
  }
  updatePreparationButton();
  return false;
}

prepareButton.addEventListener("click", () => {
  const fields = Object.fromEntries(
    Object.entries(assistanceInputs).map(([field, input]) => [field, input.value]),
  );

  if (operationInput.value === "store") {
    prepareGuidedCapture(fields);
    return;
  }

  if (operationInput.value === "find") {
    prepareGuidedRecallQuery("find", fields);
    return;
  }

  prepareEditorCommand(operationInput.value, fields);
});

browseButton.addEventListener(
  "click",
  () => prepareGuidedRecallQuery("browse", {}),
);

updateAssistanceFields();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (requestPending) return;
  clearDraftResults("Pending");
  beginGuidedRequest();

  const csrfMeta = document.querySelector("meta[name=\"luxiom-csrf\"]");
  const csrfToken = csrfMeta?.getAttribute("content") || "";
  if (!csrfToken) {
    failGuidedRequest(
      "The request could not start. The guided step remains incomplete.",
    );
    renderLocalFailure();
    return;
  }

  const proof = proofInput.value;
  const requestBody = JSON.stringify({
    proof: proof,
    requested_workspace_id: "luxiom-local-dev-workspace",
    text: commandInput.value,
    allow_cognitive_fallback: fallbackInput.checked,
  });
  proofInput.value = "";

  setRequestPending(true);

  try {
    const response = await fetch("/local/command", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Luxiom-CSRF": csrfToken,
      },
      body: requestBody,
    });
    const result = await response.json();
    applyGuidedResult(result);
    renderResult(result);
  } catch {
    failGuidedRequest(
      "The local request could not be completed. The guided step remains incomplete.",
    );
    renderLocalFailure();
  } finally {
    setRequestPending(false);
  }
});
