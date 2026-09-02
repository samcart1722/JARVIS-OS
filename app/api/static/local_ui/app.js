"use strict";

const form = document.querySelector("#command-form");
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearAllProjections();

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

  form.querySelector("button").disabled = true;
  errorOutput.textContent = "";

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
    form.querySelector("button").disabled = false;
  }
});
