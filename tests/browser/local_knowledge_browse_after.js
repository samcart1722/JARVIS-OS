"use strict";

// Runs actual app.js in the established DOM double. Not native browser acceptance.
const vm = require("node:vm");
const { createEnvironment } = require("./local_knowledge_command_assistance.js");

async function runBrowseAfter() {
  const { scope, context } = createEnvironment();
  const get = (id) => scope.document.querySelector(`#${id}`);
  const fire = (element, type = "click") => element.dispatchEvent(
    new scope.Event(type, { bubbles: true, cancelable: true }),
  );
  const next = () => get("knowledge-projection").children[0].children[0];
  const read = () => get("knowledge-records").children[0].children[1];
  const summary = (record_id) => ({ record_id, kind: "fact", key: "literal <key>" });
  const page = (records, truncated, operation = "browse_after") => ({
    success: true, route: "local", response: "Knowledge records browsed locally.", error: null,
    projection: { kind: "knowledge", operation, records, truncated },
  });
  const show = (result) => { scope.result = result; vm.runInContext("renderResult(result)", context); };
  const full = (anchor, operation = "browse_after") => page(
    [...Array.from({ length: 49 }, (_, i) => summary(`id-${i}`)), summary(anchor)], true, operation,
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
  let focused = 0;
  get("command").focus = () => { focused += 1; };
  const send = () => { get("proof").value = "synthetic-s39-proof"; fire(get("command-form"), "submit"); };
  const resolve = async (result) => { reply.resolve({ json: async () => result }); await flush(); };

  // 101 records, three explicit sends, two prepares; no hidden navigation request.
  const dataset = Array.from({ length: 101 }, (_, i) => summary(`id-${String(i).padStart(3, "0")}`));
  fire(get("prepare-browse"));
  check("initial-browse", get("command").value === "knowledge browse :: {}" && calls.length === 0,
    "historical initial preparation unchanged");
  const seen = [];
  for (let i = 0; i < 3; i += 1) {
    const command = get("command").value;
    send();
    check("explicit-send", calls.length === i + 1 && JSON.parse(calls[i].options.body).text === command,
      "Send transmits exact editor");
    const records = dataset.slice(i * 50, (i + 1) * 50);
    await resolve(page(records, i < 2, i === 0 ? "browse" : "browse_after"));
    seen.push(...records.map((r) => r.record_id));
    check("continuation-render", get("knowledge-records").children.length === records.length
      && get("knowledge-operation").textContent === (i === 0 ? "Browse" : "Browse after"), "explicit operation rendering");
    if (i < 2) {
      const action = next();
      const staleRead = read();
      check("next-page", action.type === "button" && !action.disabled && !action.hidden
        && action.textContent === "Prepare next page", "native nonsubmit control available");
      const priorFocus = focused;
      fire(action);
      check("prepare-no-fetch", calls.length === i + 1, "Prepare must not execute");
      check("next-page", get("command").value === `knowledge browse-after :: ${JSON.stringify({ after_record_id: records[49].record_id })}`,
        "last visible record is exact anchor");
      check("keyboard-focus", focused === priorFocus + 1
        && get("preparation-status").textContent.includes("No operation has been executed")
        && get("command-state").textContent.includes("explicitly Send"), "focus call and accessible prepared announcement");
      const prepared = get("command").value;
      fire(action); fire(staleRead);
      check("stale-controls", action.disabled && staleRead.disabled && !next()
        && get("command").value === prepared, "both detached actions inert after preparation");
    } else {
      check("final-page", !next() && get("knowledge-truncated").hidden, "final page has no continuation control");
      fire(read());
      check("read-continuation", get("command").value === 'knowledge read :: {"record_id":"id-100"}'
        && calls.length === 3, "READ prepared independently without Send");
    }
  }
  check("flow-101", seen.length === 101 && new Set(seen).size === 101
    && seen.join() === dataset.map((r) => r.record_id).join(), "50/50/1, no skipped or duplicate IDs");

  show(page([], false));
  check("empty", get("knowledge-empty").textContent === "No knowledge records after this ID in this workspace."
    && !get("knowledge-empty").hidden && !next(), "empty continuation succeeds without navigation");

  const whitespace = "\t\n\v\f\r\u001c\u001d\u001e\u001f \u0085\u00a0\u1680"
    + "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    + "\u2028\u2029\u202f\u205f\u3000";
  const valid = ['Z"\\<img src=x>', "e\u0301 \u00c9  A\tB", "\u200b", "\ufeff", "\u{1f600}", "x\u0000y",
    ...Array.from(whitespace, (w) => `${w}Ab${w}`)];
  const overhead = Array.from('knowledge browse-after :: {"after_record_id":""}').length;
  for (const size of [8191, 8192]) valid.push("\u{1f600}".repeat(size - overhead));
  // Control/quote/backslash escaping is counted in the final serialized string.
  for (const escape of ['"', "\\", "\u0000", "\n"]) {
    const cost = JSON.stringify(escape).length - 2;
    for (const size of [8191, 8192]) {
      const budget = size - overhead - 2;
      valid.push("a" + escape.repeat(Math.floor(budget / cost)) + "x".repeat(budget % cost) + "z");
    }
  }
  for (const anchor of valid) {
    const result = full(anchor);
    show(result);
    const action = next();
    // Tampering with rendered text or the original object cannot change capture.
    get("knowledge-records").children[49].children[0].children[0].children[1].textContent = "DOM LIE";
    result.projection.records[49].record_id = "OBJECT LIE";
    const before = calls.length;
    fire(action);
    const command = get("command").value;
    check("unicode-escaping", command === `knowledge browse-after :: ${JSON.stringify({ after_record_id: anchor })}`
      && get("preparation-error").textContent === "" && calls.length === before, "original captured Unicode serialized without rewriting");
    vectors.push({ anchor, command });
    const size = Array.from(command).length;
    if (size >= 8191) check("length-boundaries", [8191, 8192].includes(size), "exact accepted serialized boundary");
  }
  const oversized = ["\u{1f600}".repeat(8193 - overhead)];
  for (const escape of ['"', "\\", "\u0000", "\n"]) {
    const cost = JSON.stringify(escape).length - 2;
    const budget = 8193 - overhead - 2;
    oversized.push("a" + escape.repeat(Math.floor(budget / cost)) + "x".repeat(budget % cost) + "z");
  }
  for (const anchor of oversized) {
    check("length-boundaries", Array.from(`knowledge browse-after :: ${JSON.stringify({ after_record_id: anchor })}`).length === 8193,
      "rejected boundary is exactly 8193 after escaping");
  }
  for (const anchor of ["", ...whitespace, ...oversized, "\ud800", "a\udfff", "\ud800a\udc00",
    "\u{1f600}".repeat(8193 - overhead), '"'.repeat(4096), "\\".repeat(4096), "a" + "\u0000".repeat(1360)]) {
    const previous = "  manual editor\n\tuntouched  ";
    get("command").value = previous;
    show(full(anchor));
    const before = calls.length;
    fire(next());
    check("failure-preservation", get("command").value === previous && get("preparation-error").textContent !== ""
      && get("command-state").textContent.includes("no new command was prepared") && calls.length === before,
      "invalid/unrepresentable anchor preserves editor exactly and cannot send");
  }
  // Successful READ invalidates next-page action as well.
  show(full("last"));
  const staleNext = next(); fire(read());
  const readCommand = get("command").value; fire(staleNext);
  check("read-continuation", staleNext.disabled && get("command").value === readCommand && !next(), "READ invalidates next");
  for (const [id, event] of [["command", "input"], ["assist-key", "input"],
    ["assist-operation", "change"], ["cognitive-fallback", "change"], ["prepare-browse", "click"]]) {
    show(full("last")); const stale = next(); fire(get(id), event);
    const retained = get("command").value; fire(stale);
    check("stale-controls", stale.disabled && !next() && get("command").value === retained, `${id} invalidates next`);
  }
  show(full("last")); const stale = next(); const staleRead = read();
  const edited = ' \nknowledge browse-after :: {"after_record_id":"USER EDIT"}  ';
  get("command").value = edited;
  const count = calls.length; send(); send(); fire(stale); fire(staleRead); fire(get("prepare-command")); fire(get("prepare-browse"));
  check("pending", calls.length === count + 1 && JSON.parse(calls[count].options.body).text === edited
    && get("command").value === edited && stale.disabled && staleRead.disabled && !next()
    && ["send-command", "prepare-command", "prepare-browse", "command"].every((id) => get(id).disabled), "Pending blocks all actions and sends only edited text once");
  reply.reject(new Error("Disconnected")); await flush();
  check("disconnect-recovery", calls.length === count + 1 && get("command").value === edited
    && get("status").textContent === "Failed" && !get("send-command").disabled && !get("prepare-browse").disabled
    && !next(), "failure releases Pending without retry or preparation");
  fire(get("prepare-browse")); send(); await resolve(page([], false, "browse"));
  check("initial-browse", get("knowledge-empty").textContent === "No knowledge records in this workspace."
    && !next(), "recovered initial browse");

  for (const projection of [
    { kind: "knowledge", operation: "browse_after", records: [], truncated: true },
    { kind: "knowledge", operation: "browse_after", records: [summary("x")], truncated: "true" },
    { ...full("last").projection, records: [{ ...summary("x"), value: "private" }] },
    { ...full("last").projection, records: Array(51).fill(summary("x")) },
    ...["read", "find", "store", "unknown"].map((operation) => ({ ...full("last").projection, operation })),
    { ...full("last").projection, kind: "list" },
  ]) {
    show({ success: true, route: "local", projection });
    check("visibility", !next(), "no continuation control on malformed or other operation");
  }
  return { environment: "node-dom-double", categories: [...categories], passed, vectors,
    mockedFetchCalls: calls.length, actualRequests: 0, nativeKeyboardVerified: false };
}
if (require.main === module) runBrowseAfter().then((result) => process.stdout.write(JSON.stringify(result)))
  .catch((error) => { process.stderr.write(String(error)); process.exitCode = 1; });
module.exports = { runBrowseAfter };
