"use strict";

// Python str.strip() whitespace in the governed knowledge models.
const KNOWLEDGE_WHITESPACE_ONLY = /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u;
const KNOWLEDGE_FIELDS = Object.freeze({
  store: ["record_id", "kind", "key", "value", "source_type", "source_reference"],
  read: ["record_id"],
  find: ["key", "kind"],
});

function prepareKnowledgeCommand(operation, fields) {
  if (!Object.hasOwn(KNOWLEDGE_FIELDS, operation)) {
    throw new Error("Select STORE, READ or FIND.");
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

const form = document.querySelector("#command-form");
const sendButton = document.querySelector("#send-command");
const assistance = document.querySelector("#knowledge-assistance");
const operationInput = document.querySelector("#assist-operation");
const prepareButton = document.querySelector("#prepare-command");
const preparationStatus = document.querySelector("#preparation-status");
const preparationError = document.querySelector("#preparation-error");
const commandState = document.querySelector("#command-state");
const assistanceInputs = Object.fromEntries(
  KNOWLEDGE_FIELDS.store.map((field) => [
    field, document.querySelector(`#assist-${field.replaceAll("_", "-")}`),
  ]),
);
let requestPending = false;
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

function renderKnowledgeRecord(record) {
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
  knowledgeRecords.appendChild(article);
}

function renderKnowledgeProjection(projection) {
  clearKnowledgeProjection();
  if (projection?.kind !== "knowledge") {
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
    knowledgeCount.textContent = String(projection.records.length);
    knowledgeCountRow.hidden = false;
    for (const record of projection.records) {
      renderKnowledgeRecord(record);
    }
    knowledgeEmpty.hidden = projection.records.length !== 0;
    knowledgeTruncated.hidden = projection.truncated !== true;
    knowledgeProjection.hidden = false;
  }
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
  updateAssistanceFields();
}

operationInput.addEventListener("change", () => {
  if (requestPending) return;
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
  clearDraftResults();
  preparationError.textContent = "";
  preparationStatus.textContent = "Field changes have not been applied to the editor.";
  updatePreparationButton();
});

commandInput.addEventListener("input", () => {
  if (requestPending) return;
  clearDraftResults();
  commandState.textContent = "Manually edited. Send uses this exact text; fields are not reapplied.";
  updatePreparationButton();
});

fallbackInput.addEventListener("change", () => {
  if (!requestPending) clearDraftResults();
});

prepareButton.addEventListener("click", () => {
  if (requestPending) return;
  clearDraftResults();
  preparationError.textContent = "";
  const fields = Object.fromEntries(
    Object.entries(assistanceInputs).map(([field, input]) => [field, input.value]),
  );
  try {
    commandInput.value = prepareKnowledgeCommand(operationInput.value, fields);
    preparationStatus.textContent = "Command prepared. No operation has been executed.";
    commandState.textContent = "Review or edit the prepared command, then explicitly Send.";
    commandInput.focus();
  } catch (error) {
    preparationError.textContent = error.message;
    preparationStatus.textContent = "Preparation failed. Editor unchanged.";
    commandState.textContent = "Previous editor text retained; no new command was prepared.";
  }
  updatePreparationButton();
});

updateAssistanceFields();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (requestPending) return;
  clearDraftResults("Pending");

  const csrfMeta = document.querySelector("meta[name=\"luxiom-csrf\"]");
  const csrfToken = csrfMeta?.getAttribute("content") || "";
  if (!csrfToken) {
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
    renderResult(result);
  } catch {
    renderLocalFailure();
  } finally {
    setRequestPending(false);
  }
});
