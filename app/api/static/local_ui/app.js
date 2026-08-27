"use strict";

const form = document.querySelector("#command-form");
const proofInput = document.querySelector("#proof");
const commandInput = document.querySelector("#command");
const fallbackInput = document.querySelector("#cognitive-fallback");
const statusOutput = document.querySelector("#status");
const routeOutput = document.querySelector("#route");
const responseOutput = document.querySelector("#response");
const errorOutput = document.querySelector("#error");

function renderResult(result) {
  statusOutput.textContent = result.success ? "Success" : "Failed";
  routeOutput.textContent = result.route || "—";
  responseOutput.textContent = result.response || "";
  errorOutput.textContent = result.error?.message || "";
}

function renderLocalFailure() {
  statusOutput.textContent = "Failed";
  routeOutput.textContent = "—";
  responseOutput.textContent = "";
  errorOutput.textContent = "The local request could not be completed.";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

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
