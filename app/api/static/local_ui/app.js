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

// Sprint 41 Block A: callable preparation only; no browser state or authority.
function boundedKeywordText(text) {
  return text.replace(/[A-ZÁÉÍÓÚÜÑ]/gu, (letter) =>
    String.fromCodePoint(letter.codePointAt(0) + 32));
}

function boundedHasSurrogate(text) {
  return Array.from(text).some((character) => {
    const point = character.codePointAt(0);
    return point >= 0xd800 && point <= 0xdfff;
  });
}

function boundedStandalone(text, words) {
  return new RegExp(`(^|[^\\p{L}\\p{N}])(${words})(?=$|[^\\p{L}\\p{N}])`, "u")
    .test(text);
}

function boundedMultipleActions(text) {
  // Only balanced, non-nested spans suppress the lexical guard. Unmatched
  // openers remain ordinary text. Odd backslash counts escape ASCII quotes.
  const spans = [];
  let opener = null;
  let start = 0;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (character === '"') {
      let slashes = 0;
      for (let at = index - 1; at >= 0 && text[at] === "\\"; at -= 1) slashes += 1;
      if (slashes % 2) continue;
    }
    if (opener === null && (character === '"' || character === "“")) {
      opener = character;
      start = index;
    } else if ((opener === '"' && character === '"')
      || (opener === "“" && character === "”")) {
      spans.push([start, index]);
      opener = null;
    }
  }
  const pairs = /( y también | y | luego | después | entonces |; |\. |! |\? |\r\n[ \t]*|[\r\n][ \t]*)(recuerda|guarda|anota|agrega|añade|agrégalo|añádelo|muéstrame|¿?qué) /gu;
  return Array.from(text.matchAll(pairs)).some((match) =>
    !spans.some(([left, right]) => match.index <= right
      && match.index + match[0].length > left));
}

// Recognition retains original slices; keyword mapping is length preserving.
function recognizeBoundedNaturalLanguageIntent(text) {
  const compared = boundedKeywordText(text);
  const prefixes = [
    ["recuerda que", "CAPTURE_KNOWLEDGE", "value"],
    ["guarda que", "CAPTURE_KNOWLEDGE", "value"],
    ["anota que", "CAPTURE_KNOWLEDGE", "value"],
    ["qué te dije sobre", "RECALL_KNOWLEDGE", "key"],
    ["qué sabes de", "RECALL_KNOWLEDGE", "key"],
    ["qué hay en la lista", "READ_FOLLOW_UP", "list_id"],
    ["muéstrame la lista", "READ_FOLLOW_UP", "list_id"],
  ];
  const question = compared.startsWith("¿") ? text.slice(1) : text;
  const unwrapped = question.endsWith("?") ? question.slice(0, -1) : question;
  for (const [prefix, intent, field] of prefixes) {
    const candidate = prefix.startsWith("qué") ? unwrapped : text;
    const lower = boundedKeywordText(candidate);
    if (lower === prefix || lower.startsWith(prefix + " ")) {
      const payload = candidate.slice(prefix.length + 1);
      if (intent === "RECALL_KNOWLEDGE"
        && /^[¿?]|[¿?]$/u.test(stripKnowledgeWhitespace(payload))) {
        return null;
      }
      return { intent, extractedFields: { [field]: payload } };
    }
  }
  if (boundedKeywordText(unwrapped) === "qué tengo pendiente") {
    return { intent: "READ_FOLLOW_UP", extractedFields: {} };
  }
  for (const prefix of ["agrega ", "añade "]) {
    if (!compared.startsWith(prefix)) continue;
    const body = text.slice(prefix.length);
    const lower = boundedKeywordText(body);
    const separators = Array.from(lower.matchAll(/ a la lista | a mis pendientes$/gu));
    // Outer strip removes the final separator space for an empty list ID.
    if (lower.endsWith(" a la lista")) {
      separators.push({ index: lower.length - " a la lista".length, 0: " a la lista" });
    }
    if (separators.length > 1) return { reason: "ambiguous_structure" };
    if (separators.length !== 1) continue;
    const separator = separators[0];
    const item = body.slice(0, separator.index);
    if (separator[0] === " a mis pendientes") {
      if (separator.index + separator[0].length !== body.length) continue;
      return { intent: "ADD_FOLLOW_UP", extractedFields: { item } };
    }
    return { intent: "ADD_FOLLOW_UP", extractedFields: {
      item, list_id: body.slice(separator.index + separator[0].length),
    } };
  }
  return null;
}

function prepareBoundedNaturalLanguageIntent(naturalText, explicitFields = {}) {
  const result = {
    outcome: "unsupported", intent: null, extractedFields: {}, fields: {},
    missingFields: [], invalidFields: [], conflictingFields: [],
    reason: null, clarification: null, command: null,
  };
  const unsupported = (reason) => ({
    ...result, outcome: "unsupported", intent: null, command: null,
    missingFields: [], invalidFields: [], conflictingFields: [], reason,
    clarification: "Solicitud fuera del contrato acotado; no se preparó un comando.",
  });
  if (typeof naturalText !== "string" || boundedHasSurrogate(naturalText)
    || Array.from(naturalText).length > 8192
    || KNOWLEDGE_WHITESPACE_ONLY.test(naturalText)) return unsupported("invalid_input");
  const text = stripKnowledgeWhitespace(naturalText);
  const lower = boundedKeywordText(text);
  const candidate = recognizeBoundedNaturalLanguageIntent(text);
  if (boundedStandalone(lower, "si|cuando") && candidate?.intent) {
    return unsupported("conditional_request");
  }
  // Anchored recognition excludes top-level negation, quotes and examples.
  if (/^(no|si|cuando)(?=$|[^\p{L}\p{N}])/u.test(lower)
    || /^["“]/u.test(lower) || lower.startsWith("por ejemplo:")) {
    return unsupported("unsupported_request");
  }
  if (boundedMultipleActions(lower)) return unsupported("multiple_actions");
  if (boundedStandalone(lower, "esto|eso|aquello|ello|él|ella|ellos|ellas")) {
    return unsupported("context_reference");
  }
  if (!candidate?.intent) return unsupported(candidate?.reason || "unsupported_request");
  result.intent = candidate.intent;
  result.extractedFields = candidate.extractedFields;
  return finishBoundedNaturalLanguageIntent(result, explicitFields, unsupported);
}

// One shared explicit-field validator and existing deterministic builders.
function finishBoundedNaturalLanguageIntent(result, explicitFields, unsupported) {
  const orders = {
    CAPTURE_KNOWLEDGE: KNOWLEDGE_FIELDS.store,
    RECALL_KNOWLEDGE: ["key", "kind"],
    ADD_FOLLOW_UP: ["list_id", "item"],
    READ_FOLLOW_UP: ["list_id"],
  };
  const ownFields = explicitFields !== null && typeof explicitFields === "object"
    ? explicitFields : {};
  for (const field of orders[result.intent]) {
    const extracted = Object.hasOwn(result.extractedFields, field)
      ? stripKnowledgeWhitespace(result.extractedFields[field]) : "";
    const supplied = Object.hasOwn(ownFields, field) ? ownFields[field] : "";
    const explicit = typeof supplied === "string" ? stripKnowledgeWhitespace(supplied) : supplied;
    if (typeof explicit !== "string") {
      result.invalidFields.push(field);
      continue;
    }
    if (extracted && explicit && extracted !== explicit) {
      result.conflictingFields.push(field);
      continue;
    }
    const value = explicit || extracted;
    if (!value) {
      if (!(result.intent === "RECALL_KNOWLEDGE" && field === "kind")) {
        result.missingFields.push(field);
      }
      continue;
    }
    const whitespace = /[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/u;
    if (boundedHasSurrogate(value)
      || (field === "kind" && !["fact", "concept", "state"].includes(value))
      || (field === "list_id" && (whitespace.test(value) || value.includes("::")))
      || (field === "item" && value.includes("|"))) {
      result.invalidFields.push(field);
      continue;
    }
    result.fields[field] = value;
  }
  if (result.missingFields.length || result.invalidFields.length || result.conflictingFields.length) {
    return { ...result, outcome: "clarification_required",
      clarification: "Completa o corrige los campos indicados; no se preparó un comando." };
  }
  try {
    if (result.intent === "CAPTURE_KNOWLEDGE") {
      result.command = prepareKnowledgeCommand("store", result.fields);
    } else if (result.intent === "RECALL_KNOWLEDGE") {
      result.command = prepareKnowledgeCommand("find", { ...result.fields, kind: result.fields.kind || "" });
    } else if (result.intent === "ADD_FOLLOW_UP") {
      result.command = prepareFollowUpCommand(result.fields.list_id, result.fields.item).command;
    } else {
      result.command = `list read ${result.fields.list_id}`;
    }
    if (boundedHasSurrogate(result.command) || Array.from(result.command).length > 8192) {
      return unsupported("unrepresentable");
    }
  } catch {
    return unsupported("unrepresentable");
  }
  return { ...result, outcome: "prepared" };
}

// Sprint 42: independent Amendment 01 gate, never inferred from UI reasons.
// Unicode 16.0 L/N categories are frozen below, independent of browser Unicode.
const LOCAL_LETTER_NUMBER_RANGES = Object.freeze([
  [0x30, 0x39],
  [0x41, 0x5a],
  [0x61, 0x7a],
  [0xaa, 0xaa],
  [0xb2, 0xb3],
  [0xb5, 0xb5],
  [0xb9, 0xba],
  [0xbc, 0xbe],
  [0xc0, 0xd6],
  [0xd8, 0xf6],
  [0xf8, 0x2c1],
  [0x2c6, 0x2d1],
  [0x2e0, 0x2e4],
  [0x2ec, 0x2ec],
  [0x2ee, 0x2ee],
  [0x370, 0x374],
  [0x376, 0x377],
  [0x37a, 0x37d],
  [0x37f, 0x37f],
  [0x386, 0x386],
  [0x388, 0x38a],
  [0x38c, 0x38c],
  [0x38e, 0x3a1],
  [0x3a3, 0x3f5],
  [0x3f7, 0x481],
  [0x48a, 0x52f],
  [0x531, 0x556],
  [0x559, 0x559],
  [0x560, 0x588],
  [0x5d0, 0x5ea],
  [0x5ef, 0x5f2],
  [0x620, 0x64a],
  [0x660, 0x669],
  [0x66e, 0x66f],
  [0x671, 0x6d3],
  [0x6d5, 0x6d5],
  [0x6e5, 0x6e6],
  [0x6ee, 0x6fc],
  [0x6ff, 0x6ff],
  [0x710, 0x710],
  [0x712, 0x72f],
  [0x74d, 0x7a5],
  [0x7b1, 0x7b1],
  [0x7c0, 0x7ea],
  [0x7f4, 0x7f5],
  [0x7fa, 0x7fa],
  [0x800, 0x815],
  [0x81a, 0x81a],
  [0x824, 0x824],
  [0x828, 0x828],
  [0x840, 0x858],
  [0x860, 0x86a],
  [0x870, 0x887],
  [0x889, 0x88e],
  [0x8a0, 0x8c9],
  [0x904, 0x939],
  [0x93d, 0x93d],
  [0x950, 0x950],
  [0x958, 0x961],
  [0x966, 0x96f],
  [0x971, 0x980],
  [0x985, 0x98c],
  [0x98f, 0x990],
  [0x993, 0x9a8],
  [0x9aa, 0x9b0],
  [0x9b2, 0x9b2],
  [0x9b6, 0x9b9],
  [0x9bd, 0x9bd],
  [0x9ce, 0x9ce],
  [0x9dc, 0x9dd],
  [0x9df, 0x9e1],
  [0x9e6, 0x9f1],
  [0x9f4, 0x9f9],
  [0x9fc, 0x9fc],
  [0xa05, 0xa0a],
  [0xa0f, 0xa10],
  [0xa13, 0xa28],
  [0xa2a, 0xa30],
  [0xa32, 0xa33],
  [0xa35, 0xa36],
  [0xa38, 0xa39],
  [0xa59, 0xa5c],
  [0xa5e, 0xa5e],
  [0xa66, 0xa6f],
  [0xa72, 0xa74],
  [0xa85, 0xa8d],
  [0xa8f, 0xa91],
  [0xa93, 0xaa8],
  [0xaaa, 0xab0],
  [0xab2, 0xab3],
  [0xab5, 0xab9],
  [0xabd, 0xabd],
  [0xad0, 0xad0],
  [0xae0, 0xae1],
  [0xae6, 0xaef],
  [0xaf9, 0xaf9],
  [0xb05, 0xb0c],
  [0xb0f, 0xb10],
  [0xb13, 0xb28],
  [0xb2a, 0xb30],
  [0xb32, 0xb33],
  [0xb35, 0xb39],
  [0xb3d, 0xb3d],
  [0xb5c, 0xb5d],
  [0xb5f, 0xb61],
  [0xb66, 0xb6f],
  [0xb71, 0xb77],
  [0xb83, 0xb83],
  [0xb85, 0xb8a],
  [0xb8e, 0xb90],
  [0xb92, 0xb95],
  [0xb99, 0xb9a],
  [0xb9c, 0xb9c],
  [0xb9e, 0xb9f],
  [0xba3, 0xba4],
  [0xba8, 0xbaa],
  [0xbae, 0xbb9],
  [0xbd0, 0xbd0],
  [0xbe6, 0xbf2],
  [0xc05, 0xc0c],
  [0xc0e, 0xc10],
  [0xc12, 0xc28],
  [0xc2a, 0xc39],
  [0xc3d, 0xc3d],
  [0xc58, 0xc5a],
  [0xc5d, 0xc5d],
  [0xc60, 0xc61],
  [0xc66, 0xc6f],
  [0xc78, 0xc7e],
  [0xc80, 0xc80],
  [0xc85, 0xc8c],
  [0xc8e, 0xc90],
  [0xc92, 0xca8],
  [0xcaa, 0xcb3],
  [0xcb5, 0xcb9],
  [0xcbd, 0xcbd],
  [0xcdd, 0xcde],
  [0xce0, 0xce1],
  [0xce6, 0xcef],
  [0xcf1, 0xcf2],
  [0xd04, 0xd0c],
  [0xd0e, 0xd10],
  [0xd12, 0xd3a],
  [0xd3d, 0xd3d],
  [0xd4e, 0xd4e],
  [0xd54, 0xd56],
  [0xd58, 0xd61],
  [0xd66, 0xd78],
  [0xd7a, 0xd7f],
  [0xd85, 0xd96],
  [0xd9a, 0xdb1],
  [0xdb3, 0xdbb],
  [0xdbd, 0xdbd],
  [0xdc0, 0xdc6],
  [0xde6, 0xdef],
  [0xe01, 0xe30],
  [0xe32, 0xe33],
  [0xe40, 0xe46],
  [0xe50, 0xe59],
  [0xe81, 0xe82],
  [0xe84, 0xe84],
  [0xe86, 0xe8a],
  [0xe8c, 0xea3],
  [0xea5, 0xea5],
  [0xea7, 0xeb0],
  [0xeb2, 0xeb3],
  [0xebd, 0xebd],
  [0xec0, 0xec4],
  [0xec6, 0xec6],
  [0xed0, 0xed9],
  [0xedc, 0xedf],
  [0xf00, 0xf00],
  [0xf20, 0xf33],
  [0xf40, 0xf47],
  [0xf49, 0xf6c],
  [0xf88, 0xf8c],
  [0x1000, 0x102a],
  [0x103f, 0x1049],
  [0x1050, 0x1055],
  [0x105a, 0x105d],
  [0x1061, 0x1061],
  [0x1065, 0x1066],
  [0x106e, 0x1070],
  [0x1075, 0x1081],
  [0x108e, 0x108e],
  [0x1090, 0x1099],
  [0x10a0, 0x10c5],
  [0x10c7, 0x10c7],
  [0x10cd, 0x10cd],
  [0x10d0, 0x10fa],
  [0x10fc, 0x1248],
  [0x124a, 0x124d],
  [0x1250, 0x1256],
  [0x1258, 0x1258],
  [0x125a, 0x125d],
  [0x1260, 0x1288],
  [0x128a, 0x128d],
  [0x1290, 0x12b0],
  [0x12b2, 0x12b5],
  [0x12b8, 0x12be],
  [0x12c0, 0x12c0],
  [0x12c2, 0x12c5],
  [0x12c8, 0x12d6],
  [0x12d8, 0x1310],
  [0x1312, 0x1315],
  [0x1318, 0x135a],
  [0x1369, 0x137c],
  [0x1380, 0x138f],
  [0x13a0, 0x13f5],
  [0x13f8, 0x13fd],
  [0x1401, 0x166c],
  [0x166f, 0x167f],
  [0x1681, 0x169a],
  [0x16a0, 0x16ea],
  [0x16ee, 0x16f8],
  [0x1700, 0x1711],
  [0x171f, 0x1731],
  [0x1740, 0x1751],
  [0x1760, 0x176c],
  [0x176e, 0x1770],
  [0x1780, 0x17b3],
  [0x17d7, 0x17d7],
  [0x17dc, 0x17dc],
  [0x17e0, 0x17e9],
  [0x17f0, 0x17f9],
  [0x1810, 0x1819],
  [0x1820, 0x1878],
  [0x1880, 0x1884],
  [0x1887, 0x18a8],
  [0x18aa, 0x18aa],
  [0x18b0, 0x18f5],
  [0x1900, 0x191e],
  [0x1946, 0x196d],
  [0x1970, 0x1974],
  [0x1980, 0x19ab],
  [0x19b0, 0x19c9],
  [0x19d0, 0x19da],
  [0x1a00, 0x1a16],
  [0x1a20, 0x1a54],
  [0x1a80, 0x1a89],
  [0x1a90, 0x1a99],
  [0x1aa7, 0x1aa7],
  [0x1b05, 0x1b33],
  [0x1b45, 0x1b4c],
  [0x1b50, 0x1b59],
  [0x1b83, 0x1ba0],
  [0x1bae, 0x1be5],
  [0x1c00, 0x1c23],
  [0x1c40, 0x1c49],
  [0x1c4d, 0x1c7d],
  [0x1c80, 0x1c8a],
  [0x1c90, 0x1cba],
  [0x1cbd, 0x1cbf],
  [0x1ce9, 0x1cec],
  [0x1cee, 0x1cf3],
  [0x1cf5, 0x1cf6],
  [0x1cfa, 0x1cfa],
  [0x1d00, 0x1dbf],
  [0x1e00, 0x1f15],
  [0x1f18, 0x1f1d],
  [0x1f20, 0x1f45],
  [0x1f48, 0x1f4d],
  [0x1f50, 0x1f57],
  [0x1f59, 0x1f59],
  [0x1f5b, 0x1f5b],
  [0x1f5d, 0x1f5d],
  [0x1f5f, 0x1f7d],
  [0x1f80, 0x1fb4],
  [0x1fb6, 0x1fbc],
  [0x1fbe, 0x1fbe],
  [0x1fc2, 0x1fc4],
  [0x1fc6, 0x1fcc],
  [0x1fd0, 0x1fd3],
  [0x1fd6, 0x1fdb],
  [0x1fe0, 0x1fec],
  [0x1ff2, 0x1ff4],
  [0x1ff6, 0x1ffc],
  [0x2070, 0x2071],
  [0x2074, 0x2079],
  [0x207f, 0x2089],
  [0x2090, 0x209c],
  [0x2102, 0x2102],
  [0x2107, 0x2107],
  [0x210a, 0x2113],
  [0x2115, 0x2115],
  [0x2119, 0x211d],
  [0x2124, 0x2124],
  [0x2126, 0x2126],
  [0x2128, 0x2128],
  [0x212a, 0x212d],
  [0x212f, 0x2139],
  [0x213c, 0x213f],
  [0x2145, 0x2149],
  [0x214e, 0x214e],
  [0x2150, 0x2189],
  [0x2460, 0x249b],
  [0x24ea, 0x24ff],
  [0x2776, 0x2793],
  [0x2c00, 0x2ce4],
  [0x2ceb, 0x2cee],
  [0x2cf2, 0x2cf3],
  [0x2cfd, 0x2cfd],
  [0x2d00, 0x2d25],
  [0x2d27, 0x2d27],
  [0x2d2d, 0x2d2d],
  [0x2d30, 0x2d67],
  [0x2d6f, 0x2d6f],
  [0x2d80, 0x2d96],
  [0x2da0, 0x2da6],
  [0x2da8, 0x2dae],
  [0x2db0, 0x2db6],
  [0x2db8, 0x2dbe],
  [0x2dc0, 0x2dc6],
  [0x2dc8, 0x2dce],
  [0x2dd0, 0x2dd6],
  [0x2dd8, 0x2dde],
  [0x2e2f, 0x2e2f],
  [0x3005, 0x3007],
  [0x3021, 0x3029],
  [0x3031, 0x3035],
  [0x3038, 0x303c],
  [0x3041, 0x3096],
  [0x309d, 0x309f],
  [0x30a1, 0x30fa],
  [0x30fc, 0x30ff],
  [0x3105, 0x312f],
  [0x3131, 0x318e],
  [0x3192, 0x3195],
  [0x31a0, 0x31bf],
  [0x31f0, 0x31ff],
  [0x3220, 0x3229],
  [0x3248, 0x324f],
  [0x3251, 0x325f],
  [0x3280, 0x3289],
  [0x32b1, 0x32bf],
  [0x3400, 0x4dbf],
  [0x4e00, 0xa48c],
  [0xa4d0, 0xa4fd],
  [0xa500, 0xa60c],
  [0xa610, 0xa62b],
  [0xa640, 0xa66e],
  [0xa67f, 0xa69d],
  [0xa6a0, 0xa6ef],
  [0xa717, 0xa71f],
  [0xa722, 0xa788],
  [0xa78b, 0xa7cd],
  [0xa7d0, 0xa7d1],
  [0xa7d3, 0xa7d3],
  [0xa7d5, 0xa7dc],
  [0xa7f2, 0xa801],
  [0xa803, 0xa805],
  [0xa807, 0xa80a],
  [0xa80c, 0xa822],
  [0xa830, 0xa835],
  [0xa840, 0xa873],
  [0xa882, 0xa8b3],
  [0xa8d0, 0xa8d9],
  [0xa8f2, 0xa8f7],
  [0xa8fb, 0xa8fb],
  [0xa8fd, 0xa8fe],
  [0xa900, 0xa925],
  [0xa930, 0xa946],
  [0xa960, 0xa97c],
  [0xa984, 0xa9b2],
  [0xa9cf, 0xa9d9],
  [0xa9e0, 0xa9e4],
  [0xa9e6, 0xa9fe],
  [0xaa00, 0xaa28],
  [0xaa40, 0xaa42],
  [0xaa44, 0xaa4b],
  [0xaa50, 0xaa59],
  [0xaa60, 0xaa76],
  [0xaa7a, 0xaa7a],
  [0xaa7e, 0xaaaf],
  [0xaab1, 0xaab1],
  [0xaab5, 0xaab6],
  [0xaab9, 0xaabd],
  [0xaac0, 0xaac0],
  [0xaac2, 0xaac2],
  [0xaadb, 0xaadd],
  [0xaae0, 0xaaea],
  [0xaaf2, 0xaaf4],
  [0xab01, 0xab06],
  [0xab09, 0xab0e],
  [0xab11, 0xab16],
  [0xab20, 0xab26],
  [0xab28, 0xab2e],
  [0xab30, 0xab5a],
  [0xab5c, 0xab69],
  [0xab70, 0xabe2],
  [0xabf0, 0xabf9],
  [0xac00, 0xd7a3],
  [0xd7b0, 0xd7c6],
  [0xd7cb, 0xd7fb],
  [0xf900, 0xfa6d],
  [0xfa70, 0xfad9],
  [0xfb00, 0xfb06],
  [0xfb13, 0xfb17],
  [0xfb1d, 0xfb1d],
  [0xfb1f, 0xfb28],
  [0xfb2a, 0xfb36],
  [0xfb38, 0xfb3c],
  [0xfb3e, 0xfb3e],
  [0xfb40, 0xfb41],
  [0xfb43, 0xfb44],
  [0xfb46, 0xfbb1],
  [0xfbd3, 0xfd3d],
  [0xfd50, 0xfd8f],
  [0xfd92, 0xfdc7],
  [0xfdf0, 0xfdfb],
  [0xfe70, 0xfe74],
  [0xfe76, 0xfefc],
  [0xff10, 0xff19],
  [0xff21, 0xff3a],
  [0xff41, 0xff5a],
  [0xff66, 0xffbe],
  [0xffc2, 0xffc7],
  [0xffca, 0xffcf],
  [0xffd2, 0xffd7],
  [0xffda, 0xffdc],
  [0x10000, 0x1000b],
  [0x1000d, 0x10026],
  [0x10028, 0x1003a],
  [0x1003c, 0x1003d],
  [0x1003f, 0x1004d],
  [0x10050, 0x1005d],
  [0x10080, 0x100fa],
  [0x10107, 0x10133],
  [0x10140, 0x10178],
  [0x1018a, 0x1018b],
  [0x10280, 0x1029c],
  [0x102a0, 0x102d0],
  [0x102e1, 0x102fb],
  [0x10300, 0x10323],
  [0x1032d, 0x1034a],
  [0x10350, 0x10375],
  [0x10380, 0x1039d],
  [0x103a0, 0x103c3],
  [0x103c8, 0x103cf],
  [0x103d1, 0x103d5],
  [0x10400, 0x1049d],
  [0x104a0, 0x104a9],
  [0x104b0, 0x104d3],
  [0x104d8, 0x104fb],
  [0x10500, 0x10527],
  [0x10530, 0x10563],
  [0x10570, 0x1057a],
  [0x1057c, 0x1058a],
  [0x1058c, 0x10592],
  [0x10594, 0x10595],
  [0x10597, 0x105a1],
  [0x105a3, 0x105b1],
  [0x105b3, 0x105b9],
  [0x105bb, 0x105bc],
  [0x105c0, 0x105f3],
  [0x10600, 0x10736],
  [0x10740, 0x10755],
  [0x10760, 0x10767],
  [0x10780, 0x10785],
  [0x10787, 0x107b0],
  [0x107b2, 0x107ba],
  [0x10800, 0x10805],
  [0x10808, 0x10808],
  [0x1080a, 0x10835],
  [0x10837, 0x10838],
  [0x1083c, 0x1083c],
  [0x1083f, 0x10855],
  [0x10858, 0x10876],
  [0x10879, 0x1089e],
  [0x108a7, 0x108af],
  [0x108e0, 0x108f2],
  [0x108f4, 0x108f5],
  [0x108fb, 0x1091b],
  [0x10920, 0x10939],
  [0x10980, 0x109b7],
  [0x109bc, 0x109cf],
  [0x109d2, 0x10a00],
  [0x10a10, 0x10a13],
  [0x10a15, 0x10a17],
  [0x10a19, 0x10a35],
  [0x10a40, 0x10a48],
  [0x10a60, 0x10a7e],
  [0x10a80, 0x10a9f],
  [0x10ac0, 0x10ac7],
  [0x10ac9, 0x10ae4],
  [0x10aeb, 0x10aef],
  [0x10b00, 0x10b35],
  [0x10b40, 0x10b55],
  [0x10b58, 0x10b72],
  [0x10b78, 0x10b91],
  [0x10ba9, 0x10baf],
  [0x10c00, 0x10c48],
  [0x10c80, 0x10cb2],
  [0x10cc0, 0x10cf2],
  [0x10cfa, 0x10d23],
  [0x10d30, 0x10d39],
  [0x10d40, 0x10d65],
  [0x10d6f, 0x10d85],
  [0x10e60, 0x10e7e],
  [0x10e80, 0x10ea9],
  [0x10eb0, 0x10eb1],
  [0x10ec2, 0x10ec4],
  [0x10f00, 0x10f27],
  [0x10f30, 0x10f45],
  [0x10f51, 0x10f54],
  [0x10f70, 0x10f81],
  [0x10fb0, 0x10fcb],
  [0x10fe0, 0x10ff6],
  [0x11003, 0x11037],
  [0x11052, 0x1106f],
  [0x11071, 0x11072],
  [0x11075, 0x11075],
  [0x11083, 0x110af],
  [0x110d0, 0x110e8],
  [0x110f0, 0x110f9],
  [0x11103, 0x11126],
  [0x11136, 0x1113f],
  [0x11144, 0x11144],
  [0x11147, 0x11147],
  [0x11150, 0x11172],
  [0x11176, 0x11176],
  [0x11183, 0x111b2],
  [0x111c1, 0x111c4],
  [0x111d0, 0x111da],
  [0x111dc, 0x111dc],
  [0x111e1, 0x111f4],
  [0x11200, 0x11211],
  [0x11213, 0x1122b],
  [0x1123f, 0x11240],
  [0x11280, 0x11286],
  [0x11288, 0x11288],
  [0x1128a, 0x1128d],
  [0x1128f, 0x1129d],
  [0x1129f, 0x112a8],
  [0x112b0, 0x112de],
  [0x112f0, 0x112f9],
  [0x11305, 0x1130c],
  [0x1130f, 0x11310],
  [0x11313, 0x11328],
  [0x1132a, 0x11330],
  [0x11332, 0x11333],
  [0x11335, 0x11339],
  [0x1133d, 0x1133d],
  [0x11350, 0x11350],
  [0x1135d, 0x11361],
  [0x11380, 0x11389],
  [0x1138b, 0x1138b],
  [0x1138e, 0x1138e],
  [0x11390, 0x113b5],
  [0x113b7, 0x113b7],
  [0x113d1, 0x113d1],
  [0x113d3, 0x113d3],
  [0x11400, 0x11434],
  [0x11447, 0x1144a],
  [0x11450, 0x11459],
  [0x1145f, 0x11461],
  [0x11480, 0x114af],
  [0x114c4, 0x114c5],
  [0x114c7, 0x114c7],
  [0x114d0, 0x114d9],
  [0x11580, 0x115ae],
  [0x115d8, 0x115db],
  [0x11600, 0x1162f],
  [0x11644, 0x11644],
  [0x11650, 0x11659],
  [0x11680, 0x116aa],
  [0x116b8, 0x116b8],
  [0x116c0, 0x116c9],
  [0x116d0, 0x116e3],
  [0x11700, 0x1171a],
  [0x11730, 0x1173b],
  [0x11740, 0x11746],
  [0x11800, 0x1182b],
  [0x118a0, 0x118f2],
  [0x118ff, 0x11906],
  [0x11909, 0x11909],
  [0x1190c, 0x11913],
  [0x11915, 0x11916],
  [0x11918, 0x1192f],
  [0x1193f, 0x1193f],
  [0x11941, 0x11941],
  [0x11950, 0x11959],
  [0x119a0, 0x119a7],
  [0x119aa, 0x119d0],
  [0x119e1, 0x119e1],
  [0x119e3, 0x119e3],
  [0x11a00, 0x11a00],
  [0x11a0b, 0x11a32],
  [0x11a3a, 0x11a3a],
  [0x11a50, 0x11a50],
  [0x11a5c, 0x11a89],
  [0x11a9d, 0x11a9d],
  [0x11ab0, 0x11af8],
  [0x11bc0, 0x11be0],
  [0x11bf0, 0x11bf9],
  [0x11c00, 0x11c08],
  [0x11c0a, 0x11c2e],
  [0x11c40, 0x11c40],
  [0x11c50, 0x11c6c],
  [0x11c72, 0x11c8f],
  [0x11d00, 0x11d06],
  [0x11d08, 0x11d09],
  [0x11d0b, 0x11d30],
  [0x11d46, 0x11d46],
  [0x11d50, 0x11d59],
  [0x11d60, 0x11d65],
  [0x11d67, 0x11d68],
  [0x11d6a, 0x11d89],
  [0x11d98, 0x11d98],
  [0x11da0, 0x11da9],
  [0x11ee0, 0x11ef2],
  [0x11f02, 0x11f02],
  [0x11f04, 0x11f10],
  [0x11f12, 0x11f33],
  [0x11f50, 0x11f59],
  [0x11fb0, 0x11fb0],
  [0x11fc0, 0x11fd4],
  [0x12000, 0x12399],
  [0x12400, 0x1246e],
  [0x12480, 0x12543],
  [0x12f90, 0x12ff0],
  [0x13000, 0x1342f],
  [0x13441, 0x13446],
  [0x13460, 0x143fa],
  [0x14400, 0x14646],
  [0x16100, 0x1611d],
  [0x16130, 0x16139],
  [0x16800, 0x16a38],
  [0x16a40, 0x16a5e],
  [0x16a60, 0x16a69],
  [0x16a70, 0x16abe],
  [0x16ac0, 0x16ac9],
  [0x16ad0, 0x16aed],
  [0x16b00, 0x16b2f],
  [0x16b40, 0x16b43],
  [0x16b50, 0x16b59],
  [0x16b5b, 0x16b61],
  [0x16b63, 0x16b77],
  [0x16b7d, 0x16b8f],
  [0x16d40, 0x16d6c],
  [0x16d70, 0x16d79],
  [0x16e40, 0x16e96],
  [0x16f00, 0x16f4a],
  [0x16f50, 0x16f50],
  [0x16f93, 0x16f9f],
  [0x16fe0, 0x16fe1],
  [0x16fe3, 0x16fe3],
  [0x17000, 0x187f7],
  [0x18800, 0x18cd5],
  [0x18cff, 0x18d08],
  [0x1aff0, 0x1aff3],
  [0x1aff5, 0x1affb],
  [0x1affd, 0x1affe],
  [0x1b000, 0x1b122],
  [0x1b132, 0x1b132],
  [0x1b150, 0x1b152],
  [0x1b155, 0x1b155],
  [0x1b164, 0x1b167],
  [0x1b170, 0x1b2fb],
  [0x1bc00, 0x1bc6a],
  [0x1bc70, 0x1bc7c],
  [0x1bc80, 0x1bc88],
  [0x1bc90, 0x1bc99],
  [0x1ccf0, 0x1ccf9],
  [0x1d2c0, 0x1d2d3],
  [0x1d2e0, 0x1d2f3],
  [0x1d360, 0x1d378],
  [0x1d400, 0x1d454],
  [0x1d456, 0x1d49c],
  [0x1d49e, 0x1d49f],
  [0x1d4a2, 0x1d4a2],
  [0x1d4a5, 0x1d4a6],
  [0x1d4a9, 0x1d4ac],
  [0x1d4ae, 0x1d4b9],
  [0x1d4bb, 0x1d4bb],
  [0x1d4bd, 0x1d4c3],
  [0x1d4c5, 0x1d505],
  [0x1d507, 0x1d50a],
  [0x1d50d, 0x1d514],
  [0x1d516, 0x1d51c],
  [0x1d51e, 0x1d539],
  [0x1d53b, 0x1d53e],
  [0x1d540, 0x1d544],
  [0x1d546, 0x1d546],
  [0x1d54a, 0x1d550],
  [0x1d552, 0x1d6a5],
  [0x1d6a8, 0x1d6c0],
  [0x1d6c2, 0x1d6da],
  [0x1d6dc, 0x1d6fa],
  [0x1d6fc, 0x1d714],
  [0x1d716, 0x1d734],
  [0x1d736, 0x1d74e],
  [0x1d750, 0x1d76e],
  [0x1d770, 0x1d788],
  [0x1d78a, 0x1d7a8],
  [0x1d7aa, 0x1d7c2],
  [0x1d7c4, 0x1d7cb],
  [0x1d7ce, 0x1d7ff],
  [0x1df00, 0x1df1e],
  [0x1df25, 0x1df2a],
  [0x1e030, 0x1e06d],
  [0x1e100, 0x1e12c],
  [0x1e137, 0x1e13d],
  [0x1e140, 0x1e149],
  [0x1e14e, 0x1e14e],
  [0x1e290, 0x1e2ad],
  [0x1e2c0, 0x1e2eb],
  [0x1e2f0, 0x1e2f9],
  [0x1e4d0, 0x1e4eb],
  [0x1e4f0, 0x1e4f9],
  [0x1e5d0, 0x1e5ed],
  [0x1e5f0, 0x1e5fa],
  [0x1e7e0, 0x1e7e6],
  [0x1e7e8, 0x1e7eb],
  [0x1e7ed, 0x1e7ee],
  [0x1e7f0, 0x1e7fe],
  [0x1e800, 0x1e8c4],
  [0x1e8c7, 0x1e8cf],
  [0x1e900, 0x1e943],
  [0x1e94b, 0x1e94b],
  [0x1e950, 0x1e959],
  [0x1ec71, 0x1ecab],
  [0x1ecad, 0x1ecaf],
  [0x1ecb1, 0x1ecb4],
  [0x1ed01, 0x1ed2d],
  [0x1ed2f, 0x1ed3d],
  [0x1ee00, 0x1ee03],
  [0x1ee05, 0x1ee1f],
  [0x1ee21, 0x1ee22],
  [0x1ee24, 0x1ee24],
  [0x1ee27, 0x1ee27],
  [0x1ee29, 0x1ee32],
  [0x1ee34, 0x1ee37],
  [0x1ee39, 0x1ee39],
  [0x1ee3b, 0x1ee3b],
  [0x1ee42, 0x1ee42],
  [0x1ee47, 0x1ee47],
  [0x1ee49, 0x1ee49],
  [0x1ee4b, 0x1ee4b],
  [0x1ee4d, 0x1ee4f],
  [0x1ee51, 0x1ee52],
  [0x1ee54, 0x1ee54],
  [0x1ee57, 0x1ee57],
  [0x1ee59, 0x1ee59],
  [0x1ee5b, 0x1ee5b],
  [0x1ee5d, 0x1ee5d],
  [0x1ee5f, 0x1ee5f],
  [0x1ee61, 0x1ee62],
  [0x1ee64, 0x1ee64],
  [0x1ee67, 0x1ee6a],
  [0x1ee6c, 0x1ee72],
  [0x1ee74, 0x1ee77],
  [0x1ee79, 0x1ee7c],
  [0x1ee7e, 0x1ee7e],
  [0x1ee80, 0x1ee89],
  [0x1ee8b, 0x1ee9b],
  [0x1eea1, 0x1eea3],
  [0x1eea5, 0x1eea9],
  [0x1eeab, 0x1eebb],
  [0x1f100, 0x1f10c],
  [0x1fbf0, 0x1fbf9],
  [0x20000, 0x2a6df],
  [0x2a700, 0x2b739],
  [0x2b740, 0x2b81d],
  [0x2b820, 0x2cea1],
  [0x2ceb0, 0x2ebe0],
  [0x2ebf0, 0x2ee5d],
  [0x2f800, 0x2fa1d],
  [0x30000, 0x3134a],
  [0x31350, 0x323af],
]);
function localLetterOrNumber(point) {
  if (point === undefined) return false;
  let low = 0, high = LOCAL_LETTER_NUMBER_RANGES.length - 1;
  while (low <= high) {
    const middle = (low + high) >> 1;
    const [start, end] = LOCAL_LETTER_NUMBER_RANGES[middle];
    if (point < start) high = middle - 1;
    else if (point > end) low = middle + 1;
    else return true;
  }
  return false;
}

function localPointBefore(text, index) {
  if (!index) return undefined;
  const last = text.charCodeAt(index - 1);
  return last >= 0xdc00 && last <= 0xdfff && index > 1
    ? text.codePointAt(index - 2) : last;
}

function localStandalone(text, words) {
  return words.some((word) => {
    let from = 0, index;
    while ((index = text.indexOf(word, from)) !== -1) {
      const end = index + word.length;
      if (!localLetterOrNumber(localPointBefore(text, index))
        && !localLetterOrNumber(text.codePointAt(end))) return true;
      from = index + 1;
    }
    return false;
  });
}

function localStartsBounded(text, words) {
  return words.some((word) => text.startsWith(word)
    && !localLetterOrNumber(text.codePointAt(word.length)));
}

function assessLocalIntentEligibility(original) {
  const protectedResult = (reason) => ({ decision: "protected", reason });
  if (typeof original !== "string" || boundedHasSurrogate(original)
    || Array.from(original).length > 8192 || KNOWLEDGE_WHITESPACE_ONLY.test(original)) {
    return protectedResult("invalid_input");
  }
  const text = stripKnowledgeWhitespace(original);
  const lower = boundedKeywordText(text);
  const recognized = recognizeBoundedNaturalLanguageIntent(text);
  const conditional = localStandalone(lower, ["si", "cuando"]);
  if (recognized?.intent && conditional) return protectedResult("conditional_request");
  if (localStartsBounded(lower, ["si", "cuando"]) || /^["“]/u.test(lower)
    || lower.startsWith("por ejemplo:")) return protectedResult("unsupported_request");
  if (boundedMultipleActions(lower)) return protectedResult("multiple_actions");
  if (localStandalone(lower, ["esto", "eso", "aquello", "ello", "él", "ella", "ellos", "ellas"])) {
    return protectedResult("context_reference");
  }
  if (recognized?.reason) return protectedResult(recognized.reason);
  if (recognized?.intent) {
    const required = {
      CAPTURE_KNOWLEDGE: ["value"], RECALL_KNOWLEDGE: ["key"],
      ADD_FOLLOW_UP: ["item", "list_id"], READ_FOLLOW_UP: ["list_id"],
    }[recognized.intent];
    const fields = Object.fromEntries(Object.entries(recognized.extractedFields)
      .map(([key, value]) => [key, stripKnowledgeWhitespace(value)]));
    const badList = fields.list_id !== undefined && (fields.list_id.includes("::")
      || Array.from(fields.list_id).some((c) => KNOWLEDGE_WHITESPACE_ONLY.test(c)));
    return protectedResult(required.some((key) => !fields[key]) || badList
      || fields.item?.includes("|") ? "deterministic_clarification" : "deterministic_recognized");
  }
  if (["knowledge", "list"].some((word) => lower === word || (lower.startsWith(word)
    && KNOWLEDGE_WHITESPACE_ONLY.test(lower.slice(word.length, word.length + 1))))) {
    return protectedResult("direct_command_namespace");
  }
  if (conditional) return protectedResult("conditional_request");
  const addCount = Array.from(lower.matchAll(/ a la lista | a mis pendientes$/gu)).length
    + Number(lower.endsWith(" a la lista"));
  let read = lower.startsWith("¿") ? lower.slice(1) : lower;
  if (read.endsWith("?")) read = read.slice(0, -1);
  if (addCount > 1 || Array.from(read.matchAll(/(?<![^ ])la lista(?= |$)/gu)).length > 1) {
    return protectedResult("ambiguous_structure");
  }
  if (localStandalone(lower, ["no", "nunca", "jamás", "tampoco"])
    || localStartsBounded(lower, ["evita", "omite", "ignora", "deja de"])) {
    return protectedResult("negation_guard");
  }
  return { decision: "eligible_unrecognized", reason: "safe_unrecognized" };
}

function emptyLocalPreparation(outcome) {
  return { outcome, intent: null, extractedFields: {}, fields: {},
    missingFields: [], invalidFields: [], conflictingFields: [], reason: null,
    clarification: null, command: null };
}

function closedLocalObject(value, keys, exact = true) {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).every((key) => keys.includes(key))
    && (!exact || Object.keys(value).length === keys.length);
}

function parseLocalPreparationResponse(raw) {
  if (typeof raw !== "string" || raw.length > 262144) throw new Error("Invalid response");
  const result = JSON.parse(raw);
  // JSON.parse checks syntax; the token walk additionally rejects duplicate keys
  // (including escaped spellings) before any envelope or semantic use.
  const tokens = raw.match(/"(?:\\.|[^"\\])*"|[{}\[\]:,]/gu) || [];
  const stack = [];
  for (let at = 0; at < tokens.length; at += 1) {
    const token = tokens[at];
    if (token === "{") stack.push(new Set());
    else if (token === "[") stack.push(null);
    else if (token === "}" || token === "]") stack.pop();
    else if (token.startsWith('"') && tokens[at + 1] === ":") {
      const key = JSON.parse(token), keys = stack.at(-1);
      if (!keys || keys.has(key)) throw new Error("Invalid response");
      keys.add(key);
    }
  }
  if (!closedLocalObject(result, ["state", "candidate"])) throw new Error("Invalid response");
  if (!["candidate_accepted", "unsupported", "provider_unavailable", "provider_failure"]
    .includes(result.state)) throw new Error("Invalid response");
  if (result.state !== "candidate_accepted" && result.candidate !== null) {
    throw new Error("Invalid response");
  }
  return result;
}

function localQuotedOverlap(text, start, end) {
  let opener = null, left = 0;
  for (let at = 0; at < text.length; at += 1) {
    const c = text[at];
    if (c === '"') {
      let slashes = 0;
      for (let i = at - 1; i >= 0 && text[i] === "\\"; i -= 1) slashes += 1;
      if (slashes % 2) continue;
    }
    if (opener === null && (c === '"' || c === "“")) { opener = c; left = at; }
    else if ((opener === '"' && c === '"') || (opener === "“" && c === "”")) {
      if (left < end && at >= start) return true;
      opener = null;
    }
  }
  return false;
}

function localListRoles(intent, fields, original) {
  if (!["ADD_FOLLOW_UP", "READ_FOLLOW_UP"].includes(intent)) return true;
  let source = stripKnowledgeWhitespace(original);
  if (intent === "READ_FOLLOW_UP") {
    if (source.startsWith("¿")) source = source.slice(1);
    if (source.endsWith("?")) source = source.slice(0, -1);
  }
  const lower = boundedKeywordText(source);
  const pattern = intent === "ADD_FOLLOW_UP" ? / a la lista(?= |$)/gu
    : /(?<![^ ])la lista(?= |$)/gu;
  const destinations = Array.from(lower.matchAll(pattern));
  if (destinations.length + Number(intent === "ADD_FOLLOW_UP"
    && lower.endsWith(" a mis pendientes")) > 1) return false;
  if (!destinations.length) return fields.list_id === undefined;
  const destination = destinations[0];
  const end = destination.index + destination[0].length;
  const identifier = stripKnowledgeWhitespace(source.slice(end + 1));
  if (fields.list_id !== undefined && (!identifier || identifier !== fields.list_id
    || localQuotedOverlap(source, destination.index, source.length))) return false;
  return fields.item === undefined || source.slice(0, destination.index).includes(fields.item);
}

function prepareLocalSemanticCandidate(candidate, original, explicitFields) {
  const allowed = { CAPTURE_KNOWLEDGE: ["value"], RECALL_KNOWLEDGE: ["key"],
    ADD_FOLLOW_UP: ["item", "list_id"], READ_FOLLOW_UP: ["list_id"] };
  if (assessLocalIntentEligibility(original).decision !== "eligible_unrecognized"
    || !closedLocalObject(candidate, ["intent", "fields", "provenance"])
    || typeof candidate.intent !== "string"
    || !Object.hasOwn(allowed, candidate.intent)
    || candidate.provenance !== "local_model_assisted"
    || !closedLocalObject(candidate.fields, allowed[candidate.intent], false)) {
    throw new Error("Invalid candidate");
  }
  const result = emptyLocalPreparation("unsupported");
  result.intent = candidate.intent;
  for (const [name, raw] of Object.entries(candidate.fields)) {
    if (typeof raw !== "string" || boundedHasSurrogate(raw)
      || Array.from(raw).length > 8192 || KNOWLEDGE_WHITESPACE_ONLY.test(raw)) {
      throw new Error("Invalid candidate");
    }
    const value = stripKnowledgeWhitespace(raw);
    if (!original.includes(value)) throw new Error("Invalid candidate");
    result.extractedFields[name] = value;
  }
  if (!localListRoles(result.intent, result.extractedFields, original)) {
    throw new Error("Invalid candidate");
  }
  const unsupported = (reason) => ({ ...emptyLocalPreparation("unsupported"), reason,
    clarification: "Solicitud fuera del contrato acotado; no se preparó un comando." });
  const completed = finishBoundedNaturalLanguageIntent(result, explicitFields, unsupported);
  if (completed.outcome === "prepared"
    && !localListRoles(result.intent, completed.fields, original)) {
    return { ...completed, outcome: "clarification_required", command: null,
      invalidFields: ["list_id"], clarification: "An explicit original list destination is required." };
  }
  return completed;
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
const verifyPrepareButton = document.querySelector("#prepare-verification");
const followUpError = document.querySelector("#follow-up-error");
// Initialized before guided rendering, which also invalidates assistance.
let localAssistanceRevision = 0;
let localAssistanceIdentity = 0;
let localAssistancePending = null;
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
  verifyPrepareButton.disabled = requestPending
    || guidedState.stages["follow-up"] !== "completed"
    || !guidedState.retainedFollowUp;
}

function renderGuidedState(message = null) {
  invalidateLocalAssistance("guided");
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
  invalidateLocalAssistance("replacement");
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
  return { capture: "Capture", recall: "Recall", "follow-up": "Follow-up", verify: "Verify" }[stage];
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
  if (requestPending || !["capture", "recall", "follow-up", "verify"].includes(stage)) return;
  const affected = GUIDE_STAGES.slice(GUIDE_STAGES.indexOf(stage));
  for (const dependent of affected) {
    guidedState.stages[dependent] = "not-started";
  }
  const prerequisite = GUIDE_STAGES[GUIDE_STAGES.indexOf(stage) - 1];
  guidedState.stages[stage] = stage === "capture"
    || guidedState.stages[prerequisite] === "completed" ? "ready" : "not-started";
  if (stage !== "verify") guidedState.retainedFollowUp = null;
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
  if (correlation) invalidateLocalAssistance("guided");
  guidedState.correlation = null;
  if (!correlation) return;

  const stage = correlation.stage;
  if (
    ["capture", "recall", "follow-up", "verify"].includes(stage)
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
  if (!["capture", "recall", "follow-up", "verify"].includes(stage)) return;
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
  if (!["capture", "recall", "follow-up", "verify"].includes(stage)) return;
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

  if (correlation.type === "verify-read") {
    if (
      projection?.kind !== "list"
      || projection.operation !== "read"
      || projection.list_id !== correlation.listId
      || !Array.isArray(projection.items)
      || !projection.items.every((item) => typeof item === "string")
      || !projection.items.some((item) => casefoldEquivalent(item, correlation.expectedItem))
    ) {
      failGuidedRequest("The returned list did not verify the expected follow-up. Prepare again to retry.");
      return;
    }
    guidedState.correlation = null;
    setGuidedStageState("verify", "completed",
      "Follow-up verified from the governed list READ result. Nothing else was executed.");
    return;
  }

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

// Sprint 41 browser-only proposal lifecycle; execution remains governed by Send.
const naturalIntentInput = document.querySelector("#natural-intent-input");
const naturalPrepareButton = document.querySelector("#natural-intent-prepare");
const naturalRejectButton = document.querySelector("#natural-intent-reject");
const naturalIntentStatus = document.querySelector("#natural-intent-status");
const naturalIntentResult = document.querySelector("#natural-intent-result");
const localModelConsent = document.querySelector("#local-model-consent");
const localModelConsentStatus = document.querySelector("#local-model-consent-status");
const naturalFieldNames = [
  "record_id", "kind", "key", "value", "source_type", "source_reference", "list_id", "item",
];
const naturalFields = Object.fromEntries(naturalFieldNames.map((field) => {
  const id = `natural-field-${field.replaceAll("_", "-")}`;
  return [field, { input: document.querySelector(`#${id}`), row: document.querySelector(`#${id}-row`) }];
}));
const naturalOutputs = Object.fromEntries([
  "outcome", "detected-intent", "extracted-fields", "final-fields", "missing-fields",
  "invalid-fields", "conflicting-fields", "reason", "clarification", "provenance",
].map((name) => [name, document.querySelector(`#natural-intent-${name}`)]));
let naturalProposal = null;

function markNaturalProposalStale(cause) {
  if (requestPending || naturalProposal === null) return;
  naturalProposal.stale = true;
  naturalProposal.uiState = "stale";
  naturalIntentResult.setAttribute("data-natural-state", "stale");
  const reasons = {
    inputs: "Inputs changed.",
    manual: "The command editor was manually edited.",
    replacement: "Another preparation replaced the command editor.",
    consent: "Local assistance consent changed.",
    interpretation: "A new interpretation was initiated.",
    send: "An explicit Send was initiated.",
    controls: "Auxiliary preparation controls changed.",
    guided: "Guided preparation state changed.",
  };
  naturalIntentStatus.textContent = "Proposal is stale. " + reasons[cause]
    + " Re-Interpret / Prepare is required to make the proposal current."
    + " Editor retained; Send still uses the exact visible editor text.";
}

function markNaturalProposalReplaced() {
  invalidateLocalAssistance("replacement");
  if (naturalProposal?.result.outcome === "prepared") {
    markNaturalProposalStale("replacement");
  }
}

function submitNaturalProposal() {
  if (naturalProposal === null) return;
  if (naturalProposal.result.outcome === "prepared"
    && commandInput.value !== naturalProposal.generatedCommand) markNaturalProposalReplaced();
  naturalProposal.uiState = "submitted";
  naturalIntentResult.setAttribute("data-natural-state", "submitted");
  naturalIntentStatus.textContent = naturalProposal.stale || naturalProposal.manuallyEdited
    ? "The stale/manual editor text was submitted exactly as visible through governed Send. See Result for the authoritative outcome."
    : "The exact visible editor was submitted through governed Send. Preparation does not determine the outcome; see Result.";
}

naturalIntentInput.addEventListener("input", () => {
  if (requestPending) return;
  invalidateLocalAssistance("inputs");
  markNaturalProposalStale("inputs");
});
for (const { input, row } of Object.values(naturalFields)) {
  const changed = () => {
    if (requestPending) return;
    invalidateLocalAssistance("inputs");
    if (!row.hidden && !input.disabled) markNaturalProposalStale("inputs");
  };
  input.addEventListener("input", changed);
  input.addEventListener("change", changed);
}

function updateNaturalIntentControls() {
  naturalIntentInput.disabled = requestPending;
  localModelConsent.disabled = requestPending;
  naturalPrepareButton.disabled = requestPending;
  naturalRejectButton.disabled = requestPending || naturalProposal === null;
  for (const { input, row } of Object.values(naturalFields)) {
    input.disabled = requestPending || row.hidden;
  }
}

function showNaturalClarificationFields(result) {
  const needed = new Set(result?.outcome === "clarification_required"
    ? [...result.missingFields, ...result.invalidFields, ...result.conflictingFields] : []);
  if (result?.intent === "RECALL_KNOWLEDGE") needed.add("kind");
  for (const [field, { input, row }] of Object.entries(naturalFields)) {
    row.hidden = !needed.has(field);
    if (row.hidden) input.value = "";
  }
  updateNaturalIntentControls();
}

function renderNaturalIntentResult(result, provenance = "Deterministic") {
  naturalIntentResult.hidden = false;
  naturalIntentResult.setAttribute("data-natural-state", "current");
  naturalOutputs.outcome.textContent = result.outcome;
  naturalOutputs.provenance.textContent = provenance;
  naturalOutputs["detected-intent"].textContent = result.intent || "—";
  naturalOutputs["extracted-fields"].textContent = JSON.stringify(result.extractedFields, null, 2);
  naturalOutputs["final-fields"].textContent = JSON.stringify(result.fields, null, 2);
  naturalOutputs["missing-fields"].textContent = result.missingFields.join(", ") || "—";
  naturalOutputs["invalid-fields"].textContent = result.invalidFields.join(", ") || "—";
  naturalOutputs["conflicting-fields"].textContent = result.conflictingFields.join(", ") || "—";
  naturalOutputs.reason.textContent = result.reason || "—";
  naturalOutputs.clarification.textContent = result.clarification || "";
  const messages = {
    prepared: "Prepared for review. Review or edit the command; explicit Send remains required.",
    clarification_required: "Clarification required. Complete the indicated fields and Interpret / Prepare again. No new command prepared.",
    unsupported: "Unsupported by the bounded preparer. No new command prepared.",
    pending: "Pending local assistance. You may edit or reject; no command is sent.",
    provider_unavailable: "Local assistance is unavailable. Editor retained; no new command prepared.",
    provider_failure: "Local assistance failed. Editor retained; no new command prepared.",
  };
  naturalIntentStatus.textContent = provenance + ": " + messages[result.outcome];
  if (result.outcome !== "pending") showNaturalClarificationFields(result);
}


// Independent of governed Send. One logical assistance slot lasts until settlement
// or the absolute client deadline. Expiration never queues or retries a request.
// This is a client policy, not a frozen contract constant: Block B allows 30 seconds
// for provider work; 5 additional seconds accommodate local transport/body overhead.
// Abort requests transport cancellation; it does not prove server work has stopped.
const LOCAL_ASSISTANCE_TIMEOUT_MS = 35000;

function invalidateLocalAssistance(cause) {
  if (requestPending) return;
  localAssistanceRevision += 1;
  if (!localAssistancePending || !localAssistancePending.valid) return;
  localAssistancePending.valid = false;
  markNaturalProposalStale(cause);
}

function localAssistanceSnapshot() {
  return JSON.stringify([naturalIntentInput.value, localModelConsent.checked,
    commandInput.value, naturalIntentResult.getAttribute("data-natural-state"),
    Object.values(naturalFields).map(({ input, row }) =>
      [input.value, row.hidden, input.disabled]),
    operationInput.value, Object.values(assistanceInputs).map((input) =>
      [input.value, input.disabled, input.parentElement?.hidden]),
    [followUpListInput.value, followUpItemInput.value,
      followUpListInput.disabled, followUpItemInput.disabled], guidedState]);
}

function localAssistanceCurrent(attempt) {
  return localAssistancePending === attempt && attempt.valid
    && attempt.identity === localAssistanceIdentity
    && attempt.revision === localAssistanceRevision
    && attempt.proposal === naturalProposal && !requestPending
    && localModelConsent.checked && attempt.snapshot === localAssistanceSnapshot();
}

function applyNaturalPreparation(result, provenance = "Deterministic") {
  if (result.outcome === "prepared") {
    clearGuidedCorrelationForReplacement();
    clearDraftResults();
    commandInput.value = result.command;
    commandState.textContent = "Natural-language command prepared. Review or edit; explicit Send remains required.";
    updatePreparationButton();
  }
  naturalProposal = { result, generatedCommand: result.command, manuallyEdited: false,
    stale: false, uiState: "current" };
  renderNaturalIntentResult(result, provenance);
}

async function requestLocalIntentAssistance(original, explicitFields) {
  applyNaturalPreparation(emptyLocalPreparation("pending"), "Local-model assistance");
  naturalIntentResult.setAttribute("data-natural-state", "pending");
  const attempt = { identity: ++localAssistanceIdentity, revision: localAssistanceRevision,
    valid: true, proposal: naturalProposal, snapshot: localAssistanceSnapshot(),
    deadlineAt: performance.now() + LOCAL_ASSISTANCE_TIMEOUT_MS };
  localAssistancePending = attempt;
  updateNaturalIntentControls();
  let timer, controller;
  const expired = Symbol("assistance deadline");
  try {
    controller = new AbortController();
    // One deadline covers connection AND body reading. Promise.race attaches
    // rejection handlers even if a transport ignores abort and settles much later.
    const deadline = new Promise((resolve) => {
      timer = setTimeout(() => resolve(expired), LOCAL_ASSISTANCE_TIMEOUT_MS);
    });
    const transport = (async () => {
      const csrfMeta = document.querySelector("meta[name=\"luxiom-csrf\"]");
      const csrfToken = csrfMeta?.getAttribute("content") || "";
      if (!csrfToken) throw new Error("Preparation unavailable");
      const response = await fetch("/local/intent-preparation", {
        method: "POST", mode: "same-origin", credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-Luxiom-CSRF": csrfToken },
        body: JSON.stringify({ text: original }), signal: controller.signal,
      });
      if (!localAssistanceCurrent(attempt)) return null;
      if (performance.now() >= attempt.deadlineAt) return expired;
      if (!response.ok || response.headers.get("Content-Type")?.split(";")[0] !== "application/json") {
        throw new Error("Preparation failed");
      }
      return await response.text();
    })();
    const raw = await Promise.race([transport, deadline]);
    if (raw === expired || performance.now() >= attempt.deadlineAt) {
      const current = localAssistanceCurrent(attempt);
      // Invalidate before releasing the logical slot or notifying abort listeners.
      attempt.valid = false;
      if (current) {
        applyNaturalPreparation(emptyLocalPreparation("provider_failure"), "Local-model assistance");
      }
      controller.abort();
      return;
    }
    if (!localAssistanceCurrent(attempt)) return;
    const envelope = parseLocalPreparationResponse(raw);
    const result = envelope.state === "candidate_accepted"
      ? prepareLocalSemanticCandidate(envelope.candidate, original, explicitFields)
      : emptyLocalPreparation(envelope.state);
    applyNaturalPreparation(result, envelope.state === "candidate_accepted"
      ? "Local-model assisted (local_model_assisted)" : "Local-model assistance");
  } catch {
    if (localAssistanceCurrent(attempt)) {
      applyNaturalPreparation(emptyLocalPreparation("provider_failure"), "Local-model assistance");
    }
  } finally {
    if (timer !== undefined) clearTimeout(timer);
    attempt.valid = false;
    if (localAssistancePending === attempt) {
      localAssistancePending = null;
      updateNaturalIntentControls();
    }
  }
}

localModelConsent.checked = false;
function updateLocalModelConsent() {
  if (requestPending) return;
  invalidateLocalAssistance("consent");
  localModelConsentStatus.textContent = localModelConsent.checked
    ? "Local model assistance is ON for this page session. Interpretation only; Send remains explicit."
    : "Local model assistance is OFF for this page session.";
}
localModelConsent.addEventListener("input", updateLocalModelConsent);
localModelConsent.addEventListener("change", updateLocalModelConsent);
updateLocalModelConsent();

naturalPrepareButton.addEventListener("click", () => {
  if (requestPending) return;
  const explicitFields = {};
  for (const [field, { input, row }] of Object.entries(naturalFields)) {
    if (!row.hidden && !input.disabled) explicitFields[field] = input.value;
  }
  // Always run the unchanged Sprint 41 recognition/safety path first.
  const result = prepareBoundedNaturalLanguageIntent(naturalIntentInput.value, explicitFields);
  if (localAssistancePending && localAssistanceCurrent(localAssistancePending)) return;
  invalidateLocalAssistance("interpretation");
  if (result.outcome !== "unsupported" || !localModelConsent.checked
    || assessLocalIntentEligibility(naturalIntentInput.value).decision !== "eligible_unrecognized") {
    applyNaturalPreparation(result);
    return;
  }
  if (localAssistancePending) {
    applyNaturalPreparation(emptyLocalPreparation("pending"), "Local-model assistance");
    naturalIntentStatus.textContent = "Previous assistance is still settling. No request queued. Interpret again when ready.";
    return;
  }
  // The async handler contains every failure; no fire-and-forget rejection.
  void requestLocalIntentAssistance(naturalIntentInput.value, explicitFields);
});

naturalRejectButton.addEventListener("click", () => {
  if (requestPending || naturalProposal === null) return;
  invalidateLocalAssistance("replacement");
  if (naturalProposal.result.outcome === "prepared") {
    if (!naturalProposal.manuallyEdited && commandInput.value === naturalProposal.generatedCommand) {
      commandInput.value = "";
      commandState.textContent = "Natural-language proposal rejected. No command prepared.";
    } else {
      commandState.textContent = "Manual text retained. Send uses the exact text in this editor.";
    }
  }
  naturalProposal = null;
  naturalIntentResult.hidden = true;
  naturalIntentResult.setAttribute("data-natural-state", "inactive");
  for (const output of Object.values(naturalOutputs)) output.textContent = "";
  for (const { input } of Object.values(naturalFields)) input.value = "";
  showNaturalClarificationFields(null);
  naturalIntentStatus.textContent = "Proposal rejected. No natural-language proposal is active.";
  updatePreparationButton();
});

showNaturalClarificationFields(null);

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
  updateNaturalIntentControls();
}

operationInput.addEventListener("input", () => invalidateLocalAssistance("controls"));
operationInput.addEventListener("change", () => {
  if (requestPending) return;
  invalidateLocalAssistance("controls");
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

assistance.addEventListener("change", () => invalidateLocalAssistance("controls"));
assistance.addEventListener("input", (event) => {
  if (requestPending || event.target === operationInput) return;
  invalidateLocalAssistance("controls");
  invalidateGuidedOperation(operationInput.value);
  clearDraftResults();
  preparationError.textContent = "";
  preparationStatus.textContent = "Field changes have not been applied to the editor.";
  updatePreparationButton();
});

commandInput.addEventListener("input", () => {
  if (requestPending) return;
  invalidateLocalAssistance("manual");
  // Sticky even after edit-back-to-original: the visible editor is authoritative.
  if (naturalProposal?.result.outcome === "prepared") {
    naturalProposal.manuallyEdited = true;
    markNaturalProposalStale("manual");
  }
  if (["follow-up", "verify"].includes(guidedState.correlation?.stage)) {
    invalidateGuidedStage(guidedState.correlation.stage);
  }
  clearDraftResults();
  commandState.textContent = "Manually edited. Send uses this exact text; fields are not reapplied.";
  updatePreparationButton();
});

fallbackInput.addEventListener("change", () => {
  if (!requestPending) clearDraftResults();
});

// Generated from CPython 3.14.6, Unicode 16.0.0.
// All non-identity str.casefold mappings; unmapped code points remain exact.
// No normalization, trimming, locale rules, or browser casing.
const PYTHON_CASEFOLD = Object.freeze({
  "65": "a",
  "66": "b",
  "67": "c",
  "68": "d",
  "69": "e",
  "70": "f",
  "71": "g",
  "72": "h",
  "73": "i",
  "74": "j",
  "75": "k",
  "76": "l",
  "77": "m",
  "78": "n",
  "79": "o",
  "80": "p",
  "81": "q",
  "82": "r",
  "83": "s",
  "84": "t",
  "85": "u",
  "86": "v",
  "87": "w",
  "88": "x",
  "89": "y",
  "90": "z",
  "181": "\u03bc",
  "192": "\u00e0",
  "193": "\u00e1",
  "194": "\u00e2",
  "195": "\u00e3",
  "196": "\u00e4",
  "197": "\u00e5",
  "198": "\u00e6",
  "199": "\u00e7",
  "200": "\u00e8",
  "201": "\u00e9",
  "202": "\u00ea",
  "203": "\u00eb",
  "204": "\u00ec",
  "205": "\u00ed",
  "206": "\u00ee",
  "207": "\u00ef",
  "208": "\u00f0",
  "209": "\u00f1",
  "210": "\u00f2",
  "211": "\u00f3",
  "212": "\u00f4",
  "213": "\u00f5",
  "214": "\u00f6",
  "216": "\u00f8",
  "217": "\u00f9",
  "218": "\u00fa",
  "219": "\u00fb",
  "220": "\u00fc",
  "221": "\u00fd",
  "222": "\u00fe",
  "223": "ss",
  "256": "\u0101",
  "258": "\u0103",
  "260": "\u0105",
  "262": "\u0107",
  "264": "\u0109",
  "266": "\u010b",
  "268": "\u010d",
  "270": "\u010f",
  "272": "\u0111",
  "274": "\u0113",
  "276": "\u0115",
  "278": "\u0117",
  "280": "\u0119",
  "282": "\u011b",
  "284": "\u011d",
  "286": "\u011f",
  "288": "\u0121",
  "290": "\u0123",
  "292": "\u0125",
  "294": "\u0127",
  "296": "\u0129",
  "298": "\u012b",
  "300": "\u012d",
  "302": "\u012f",
  "304": "i\u0307",
  "306": "\u0133",
  "308": "\u0135",
  "310": "\u0137",
  "313": "\u013a",
  "315": "\u013c",
  "317": "\u013e",
  "319": "\u0140",
  "321": "\u0142",
  "323": "\u0144",
  "325": "\u0146",
  "327": "\u0148",
  "329": "\u02bcn",
  "330": "\u014b",
  "332": "\u014d",
  "334": "\u014f",
  "336": "\u0151",
  "338": "\u0153",
  "340": "\u0155",
  "342": "\u0157",
  "344": "\u0159",
  "346": "\u015b",
  "348": "\u015d",
  "350": "\u015f",
  "352": "\u0161",
  "354": "\u0163",
  "356": "\u0165",
  "358": "\u0167",
  "360": "\u0169",
  "362": "\u016b",
  "364": "\u016d",
  "366": "\u016f",
  "368": "\u0171",
  "370": "\u0173",
  "372": "\u0175",
  "374": "\u0177",
  "376": "\u00ff",
  "377": "\u017a",
  "379": "\u017c",
  "381": "\u017e",
  "383": "s",
  "385": "\u0253",
  "386": "\u0183",
  "388": "\u0185",
  "390": "\u0254",
  "391": "\u0188",
  "393": "\u0256",
  "394": "\u0257",
  "395": "\u018c",
  "398": "\u01dd",
  "399": "\u0259",
  "400": "\u025b",
  "401": "\u0192",
  "403": "\u0260",
  "404": "\u0263",
  "406": "\u0269",
  "407": "\u0268",
  "408": "\u0199",
  "412": "\u026f",
  "413": "\u0272",
  "415": "\u0275",
  "416": "\u01a1",
  "418": "\u01a3",
  "420": "\u01a5",
  "422": "\u0280",
  "423": "\u01a8",
  "425": "\u0283",
  "428": "\u01ad",
  "430": "\u0288",
  "431": "\u01b0",
  "433": "\u028a",
  "434": "\u028b",
  "435": "\u01b4",
  "437": "\u01b6",
  "439": "\u0292",
  "440": "\u01b9",
  "444": "\u01bd",
  "452": "\u01c6",
  "453": "\u01c6",
  "455": "\u01c9",
  "456": "\u01c9",
  "458": "\u01cc",
  "459": "\u01cc",
  "461": "\u01ce",
  "463": "\u01d0",
  "465": "\u01d2",
  "467": "\u01d4",
  "469": "\u01d6",
  "471": "\u01d8",
  "473": "\u01da",
  "475": "\u01dc",
  "478": "\u01df",
  "480": "\u01e1",
  "482": "\u01e3",
  "484": "\u01e5",
  "486": "\u01e7",
  "488": "\u01e9",
  "490": "\u01eb",
  "492": "\u01ed",
  "494": "\u01ef",
  "496": "j\u030c",
  "497": "\u01f3",
  "498": "\u01f3",
  "500": "\u01f5",
  "502": "\u0195",
  "503": "\u01bf",
  "504": "\u01f9",
  "506": "\u01fb",
  "508": "\u01fd",
  "510": "\u01ff",
  "512": "\u0201",
  "514": "\u0203",
  "516": "\u0205",
  "518": "\u0207",
  "520": "\u0209",
  "522": "\u020b",
  "524": "\u020d",
  "526": "\u020f",
  "528": "\u0211",
  "530": "\u0213",
  "532": "\u0215",
  "534": "\u0217",
  "536": "\u0219",
  "538": "\u021b",
  "540": "\u021d",
  "542": "\u021f",
  "544": "\u019e",
  "546": "\u0223",
  "548": "\u0225",
  "550": "\u0227",
  "552": "\u0229",
  "554": "\u022b",
  "556": "\u022d",
  "558": "\u022f",
  "560": "\u0231",
  "562": "\u0233",
  "570": "\u2c65",
  "571": "\u023c",
  "573": "\u019a",
  "574": "\u2c66",
  "577": "\u0242",
  "579": "\u0180",
  "580": "\u0289",
  "581": "\u028c",
  "582": "\u0247",
  "584": "\u0249",
  "586": "\u024b",
  "588": "\u024d",
  "590": "\u024f",
  "837": "\u03b9",
  "880": "\u0371",
  "882": "\u0373",
  "886": "\u0377",
  "895": "\u03f3",
  "902": "\u03ac",
  "904": "\u03ad",
  "905": "\u03ae",
  "906": "\u03af",
  "908": "\u03cc",
  "910": "\u03cd",
  "911": "\u03ce",
  "912": "\u03b9\u0308\u0301",
  "913": "\u03b1",
  "914": "\u03b2",
  "915": "\u03b3",
  "916": "\u03b4",
  "917": "\u03b5",
  "918": "\u03b6",
  "919": "\u03b7",
  "920": "\u03b8",
  "921": "\u03b9",
  "922": "\u03ba",
  "923": "\u03bb",
  "924": "\u03bc",
  "925": "\u03bd",
  "926": "\u03be",
  "927": "\u03bf",
  "928": "\u03c0",
  "929": "\u03c1",
  "931": "\u03c3",
  "932": "\u03c4",
  "933": "\u03c5",
  "934": "\u03c6",
  "935": "\u03c7",
  "936": "\u03c8",
  "937": "\u03c9",
  "938": "\u03ca",
  "939": "\u03cb",
  "944": "\u03c5\u0308\u0301",
  "962": "\u03c3",
  "975": "\u03d7",
  "976": "\u03b2",
  "977": "\u03b8",
  "981": "\u03c6",
  "982": "\u03c0",
  "984": "\u03d9",
  "986": "\u03db",
  "988": "\u03dd",
  "990": "\u03df",
  "992": "\u03e1",
  "994": "\u03e3",
  "996": "\u03e5",
  "998": "\u03e7",
  "1000": "\u03e9",
  "1002": "\u03eb",
  "1004": "\u03ed",
  "1006": "\u03ef",
  "1008": "\u03ba",
  "1009": "\u03c1",
  "1012": "\u03b8",
  "1013": "\u03b5",
  "1015": "\u03f8",
  "1017": "\u03f2",
  "1018": "\u03fb",
  "1021": "\u037b",
  "1022": "\u037c",
  "1023": "\u037d",
  "1024": "\u0450",
  "1025": "\u0451",
  "1026": "\u0452",
  "1027": "\u0453",
  "1028": "\u0454",
  "1029": "\u0455",
  "1030": "\u0456",
  "1031": "\u0457",
  "1032": "\u0458",
  "1033": "\u0459",
  "1034": "\u045a",
  "1035": "\u045b",
  "1036": "\u045c",
  "1037": "\u045d",
  "1038": "\u045e",
  "1039": "\u045f",
  "1040": "\u0430",
  "1041": "\u0431",
  "1042": "\u0432",
  "1043": "\u0433",
  "1044": "\u0434",
  "1045": "\u0435",
  "1046": "\u0436",
  "1047": "\u0437",
  "1048": "\u0438",
  "1049": "\u0439",
  "1050": "\u043a",
  "1051": "\u043b",
  "1052": "\u043c",
  "1053": "\u043d",
  "1054": "\u043e",
  "1055": "\u043f",
  "1056": "\u0440",
  "1057": "\u0441",
  "1058": "\u0442",
  "1059": "\u0443",
  "1060": "\u0444",
  "1061": "\u0445",
  "1062": "\u0446",
  "1063": "\u0447",
  "1064": "\u0448",
  "1065": "\u0449",
  "1066": "\u044a",
  "1067": "\u044b",
  "1068": "\u044c",
  "1069": "\u044d",
  "1070": "\u044e",
  "1071": "\u044f",
  "1120": "\u0461",
  "1122": "\u0463",
  "1124": "\u0465",
  "1126": "\u0467",
  "1128": "\u0469",
  "1130": "\u046b",
  "1132": "\u046d",
  "1134": "\u046f",
  "1136": "\u0471",
  "1138": "\u0473",
  "1140": "\u0475",
  "1142": "\u0477",
  "1144": "\u0479",
  "1146": "\u047b",
  "1148": "\u047d",
  "1150": "\u047f",
  "1152": "\u0481",
  "1162": "\u048b",
  "1164": "\u048d",
  "1166": "\u048f",
  "1168": "\u0491",
  "1170": "\u0493",
  "1172": "\u0495",
  "1174": "\u0497",
  "1176": "\u0499",
  "1178": "\u049b",
  "1180": "\u049d",
  "1182": "\u049f",
  "1184": "\u04a1",
  "1186": "\u04a3",
  "1188": "\u04a5",
  "1190": "\u04a7",
  "1192": "\u04a9",
  "1194": "\u04ab",
  "1196": "\u04ad",
  "1198": "\u04af",
  "1200": "\u04b1",
  "1202": "\u04b3",
  "1204": "\u04b5",
  "1206": "\u04b7",
  "1208": "\u04b9",
  "1210": "\u04bb",
  "1212": "\u04bd",
  "1214": "\u04bf",
  "1216": "\u04cf",
  "1217": "\u04c2",
  "1219": "\u04c4",
  "1221": "\u04c6",
  "1223": "\u04c8",
  "1225": "\u04ca",
  "1227": "\u04cc",
  "1229": "\u04ce",
  "1232": "\u04d1",
  "1234": "\u04d3",
  "1236": "\u04d5",
  "1238": "\u04d7",
  "1240": "\u04d9",
  "1242": "\u04db",
  "1244": "\u04dd",
  "1246": "\u04df",
  "1248": "\u04e1",
  "1250": "\u04e3",
  "1252": "\u04e5",
  "1254": "\u04e7",
  "1256": "\u04e9",
  "1258": "\u04eb",
  "1260": "\u04ed",
  "1262": "\u04ef",
  "1264": "\u04f1",
  "1266": "\u04f3",
  "1268": "\u04f5",
  "1270": "\u04f7",
  "1272": "\u04f9",
  "1274": "\u04fb",
  "1276": "\u04fd",
  "1278": "\u04ff",
  "1280": "\u0501",
  "1282": "\u0503",
  "1284": "\u0505",
  "1286": "\u0507",
  "1288": "\u0509",
  "1290": "\u050b",
  "1292": "\u050d",
  "1294": "\u050f",
  "1296": "\u0511",
  "1298": "\u0513",
  "1300": "\u0515",
  "1302": "\u0517",
  "1304": "\u0519",
  "1306": "\u051b",
  "1308": "\u051d",
  "1310": "\u051f",
  "1312": "\u0521",
  "1314": "\u0523",
  "1316": "\u0525",
  "1318": "\u0527",
  "1320": "\u0529",
  "1322": "\u052b",
  "1324": "\u052d",
  "1326": "\u052f",
  "1329": "\u0561",
  "1330": "\u0562",
  "1331": "\u0563",
  "1332": "\u0564",
  "1333": "\u0565",
  "1334": "\u0566",
  "1335": "\u0567",
  "1336": "\u0568",
  "1337": "\u0569",
  "1338": "\u056a",
  "1339": "\u056b",
  "1340": "\u056c",
  "1341": "\u056d",
  "1342": "\u056e",
  "1343": "\u056f",
  "1344": "\u0570",
  "1345": "\u0571",
  "1346": "\u0572",
  "1347": "\u0573",
  "1348": "\u0574",
  "1349": "\u0575",
  "1350": "\u0576",
  "1351": "\u0577",
  "1352": "\u0578",
  "1353": "\u0579",
  "1354": "\u057a",
  "1355": "\u057b",
  "1356": "\u057c",
  "1357": "\u057d",
  "1358": "\u057e",
  "1359": "\u057f",
  "1360": "\u0580",
  "1361": "\u0581",
  "1362": "\u0582",
  "1363": "\u0583",
  "1364": "\u0584",
  "1365": "\u0585",
  "1366": "\u0586",
  "1415": "\u0565\u0582",
  "4256": "\u2d00",
  "4257": "\u2d01",
  "4258": "\u2d02",
  "4259": "\u2d03",
  "4260": "\u2d04",
  "4261": "\u2d05",
  "4262": "\u2d06",
  "4263": "\u2d07",
  "4264": "\u2d08",
  "4265": "\u2d09",
  "4266": "\u2d0a",
  "4267": "\u2d0b",
  "4268": "\u2d0c",
  "4269": "\u2d0d",
  "4270": "\u2d0e",
  "4271": "\u2d0f",
  "4272": "\u2d10",
  "4273": "\u2d11",
  "4274": "\u2d12",
  "4275": "\u2d13",
  "4276": "\u2d14",
  "4277": "\u2d15",
  "4278": "\u2d16",
  "4279": "\u2d17",
  "4280": "\u2d18",
  "4281": "\u2d19",
  "4282": "\u2d1a",
  "4283": "\u2d1b",
  "4284": "\u2d1c",
  "4285": "\u2d1d",
  "4286": "\u2d1e",
  "4287": "\u2d1f",
  "4288": "\u2d20",
  "4289": "\u2d21",
  "4290": "\u2d22",
  "4291": "\u2d23",
  "4292": "\u2d24",
  "4293": "\u2d25",
  "4295": "\u2d27",
  "4301": "\u2d2d",
  "5112": "\u13f0",
  "5113": "\u13f1",
  "5114": "\u13f2",
  "5115": "\u13f3",
  "5116": "\u13f4",
  "5117": "\u13f5",
  "7296": "\u0432",
  "7297": "\u0434",
  "7298": "\u043e",
  "7299": "\u0441",
  "7300": "\u0442",
  "7301": "\u0442",
  "7302": "\u044a",
  "7303": "\u0463",
  "7304": "\ua64b",
  "7305": "\u1c8a",
  "7312": "\u10d0",
  "7313": "\u10d1",
  "7314": "\u10d2",
  "7315": "\u10d3",
  "7316": "\u10d4",
  "7317": "\u10d5",
  "7318": "\u10d6",
  "7319": "\u10d7",
  "7320": "\u10d8",
  "7321": "\u10d9",
  "7322": "\u10da",
  "7323": "\u10db",
  "7324": "\u10dc",
  "7325": "\u10dd",
  "7326": "\u10de",
  "7327": "\u10df",
  "7328": "\u10e0",
  "7329": "\u10e1",
  "7330": "\u10e2",
  "7331": "\u10e3",
  "7332": "\u10e4",
  "7333": "\u10e5",
  "7334": "\u10e6",
  "7335": "\u10e7",
  "7336": "\u10e8",
  "7337": "\u10e9",
  "7338": "\u10ea",
  "7339": "\u10eb",
  "7340": "\u10ec",
  "7341": "\u10ed",
  "7342": "\u10ee",
  "7343": "\u10ef",
  "7344": "\u10f0",
  "7345": "\u10f1",
  "7346": "\u10f2",
  "7347": "\u10f3",
  "7348": "\u10f4",
  "7349": "\u10f5",
  "7350": "\u10f6",
  "7351": "\u10f7",
  "7352": "\u10f8",
  "7353": "\u10f9",
  "7354": "\u10fa",
  "7357": "\u10fd",
  "7358": "\u10fe",
  "7359": "\u10ff",
  "7680": "\u1e01",
  "7682": "\u1e03",
  "7684": "\u1e05",
  "7686": "\u1e07",
  "7688": "\u1e09",
  "7690": "\u1e0b",
  "7692": "\u1e0d",
  "7694": "\u1e0f",
  "7696": "\u1e11",
  "7698": "\u1e13",
  "7700": "\u1e15",
  "7702": "\u1e17",
  "7704": "\u1e19",
  "7706": "\u1e1b",
  "7708": "\u1e1d",
  "7710": "\u1e1f",
  "7712": "\u1e21",
  "7714": "\u1e23",
  "7716": "\u1e25",
  "7718": "\u1e27",
  "7720": "\u1e29",
  "7722": "\u1e2b",
  "7724": "\u1e2d",
  "7726": "\u1e2f",
  "7728": "\u1e31",
  "7730": "\u1e33",
  "7732": "\u1e35",
  "7734": "\u1e37",
  "7736": "\u1e39",
  "7738": "\u1e3b",
  "7740": "\u1e3d",
  "7742": "\u1e3f",
  "7744": "\u1e41",
  "7746": "\u1e43",
  "7748": "\u1e45",
  "7750": "\u1e47",
  "7752": "\u1e49",
  "7754": "\u1e4b",
  "7756": "\u1e4d",
  "7758": "\u1e4f",
  "7760": "\u1e51",
  "7762": "\u1e53",
  "7764": "\u1e55",
  "7766": "\u1e57",
  "7768": "\u1e59",
  "7770": "\u1e5b",
  "7772": "\u1e5d",
  "7774": "\u1e5f",
  "7776": "\u1e61",
  "7778": "\u1e63",
  "7780": "\u1e65",
  "7782": "\u1e67",
  "7784": "\u1e69",
  "7786": "\u1e6b",
  "7788": "\u1e6d",
  "7790": "\u1e6f",
  "7792": "\u1e71",
  "7794": "\u1e73",
  "7796": "\u1e75",
  "7798": "\u1e77",
  "7800": "\u1e79",
  "7802": "\u1e7b",
  "7804": "\u1e7d",
  "7806": "\u1e7f",
  "7808": "\u1e81",
  "7810": "\u1e83",
  "7812": "\u1e85",
  "7814": "\u1e87",
  "7816": "\u1e89",
  "7818": "\u1e8b",
  "7820": "\u1e8d",
  "7822": "\u1e8f",
  "7824": "\u1e91",
  "7826": "\u1e93",
  "7828": "\u1e95",
  "7830": "h\u0331",
  "7831": "t\u0308",
  "7832": "w\u030a",
  "7833": "y\u030a",
  "7834": "a\u02be",
  "7835": "\u1e61",
  "7838": "ss",
  "7840": "\u1ea1",
  "7842": "\u1ea3",
  "7844": "\u1ea5",
  "7846": "\u1ea7",
  "7848": "\u1ea9",
  "7850": "\u1eab",
  "7852": "\u1ead",
  "7854": "\u1eaf",
  "7856": "\u1eb1",
  "7858": "\u1eb3",
  "7860": "\u1eb5",
  "7862": "\u1eb7",
  "7864": "\u1eb9",
  "7866": "\u1ebb",
  "7868": "\u1ebd",
  "7870": "\u1ebf",
  "7872": "\u1ec1",
  "7874": "\u1ec3",
  "7876": "\u1ec5",
  "7878": "\u1ec7",
  "7880": "\u1ec9",
  "7882": "\u1ecb",
  "7884": "\u1ecd",
  "7886": "\u1ecf",
  "7888": "\u1ed1",
  "7890": "\u1ed3",
  "7892": "\u1ed5",
  "7894": "\u1ed7",
  "7896": "\u1ed9",
  "7898": "\u1edb",
  "7900": "\u1edd",
  "7902": "\u1edf",
  "7904": "\u1ee1",
  "7906": "\u1ee3",
  "7908": "\u1ee5",
  "7910": "\u1ee7",
  "7912": "\u1ee9",
  "7914": "\u1eeb",
  "7916": "\u1eed",
  "7918": "\u1eef",
  "7920": "\u1ef1",
  "7922": "\u1ef3",
  "7924": "\u1ef5",
  "7926": "\u1ef7",
  "7928": "\u1ef9",
  "7930": "\u1efb",
  "7932": "\u1efd",
  "7934": "\u1eff",
  "7944": "\u1f00",
  "7945": "\u1f01",
  "7946": "\u1f02",
  "7947": "\u1f03",
  "7948": "\u1f04",
  "7949": "\u1f05",
  "7950": "\u1f06",
  "7951": "\u1f07",
  "7960": "\u1f10",
  "7961": "\u1f11",
  "7962": "\u1f12",
  "7963": "\u1f13",
  "7964": "\u1f14",
  "7965": "\u1f15",
  "7976": "\u1f20",
  "7977": "\u1f21",
  "7978": "\u1f22",
  "7979": "\u1f23",
  "7980": "\u1f24",
  "7981": "\u1f25",
  "7982": "\u1f26",
  "7983": "\u1f27",
  "7992": "\u1f30",
  "7993": "\u1f31",
  "7994": "\u1f32",
  "7995": "\u1f33",
  "7996": "\u1f34",
  "7997": "\u1f35",
  "7998": "\u1f36",
  "7999": "\u1f37",
  "8008": "\u1f40",
  "8009": "\u1f41",
  "8010": "\u1f42",
  "8011": "\u1f43",
  "8012": "\u1f44",
  "8013": "\u1f45",
  "8016": "\u03c5\u0313",
  "8018": "\u03c5\u0313\u0300",
  "8020": "\u03c5\u0313\u0301",
  "8022": "\u03c5\u0313\u0342",
  "8025": "\u1f51",
  "8027": "\u1f53",
  "8029": "\u1f55",
  "8031": "\u1f57",
  "8040": "\u1f60",
  "8041": "\u1f61",
  "8042": "\u1f62",
  "8043": "\u1f63",
  "8044": "\u1f64",
  "8045": "\u1f65",
  "8046": "\u1f66",
  "8047": "\u1f67",
  "8064": "\u1f00\u03b9",
  "8065": "\u1f01\u03b9",
  "8066": "\u1f02\u03b9",
  "8067": "\u1f03\u03b9",
  "8068": "\u1f04\u03b9",
  "8069": "\u1f05\u03b9",
  "8070": "\u1f06\u03b9",
  "8071": "\u1f07\u03b9",
  "8072": "\u1f00\u03b9",
  "8073": "\u1f01\u03b9",
  "8074": "\u1f02\u03b9",
  "8075": "\u1f03\u03b9",
  "8076": "\u1f04\u03b9",
  "8077": "\u1f05\u03b9",
  "8078": "\u1f06\u03b9",
  "8079": "\u1f07\u03b9",
  "8080": "\u1f20\u03b9",
  "8081": "\u1f21\u03b9",
  "8082": "\u1f22\u03b9",
  "8083": "\u1f23\u03b9",
  "8084": "\u1f24\u03b9",
  "8085": "\u1f25\u03b9",
  "8086": "\u1f26\u03b9",
  "8087": "\u1f27\u03b9",
  "8088": "\u1f20\u03b9",
  "8089": "\u1f21\u03b9",
  "8090": "\u1f22\u03b9",
  "8091": "\u1f23\u03b9",
  "8092": "\u1f24\u03b9",
  "8093": "\u1f25\u03b9",
  "8094": "\u1f26\u03b9",
  "8095": "\u1f27\u03b9",
  "8096": "\u1f60\u03b9",
  "8097": "\u1f61\u03b9",
  "8098": "\u1f62\u03b9",
  "8099": "\u1f63\u03b9",
  "8100": "\u1f64\u03b9",
  "8101": "\u1f65\u03b9",
  "8102": "\u1f66\u03b9",
  "8103": "\u1f67\u03b9",
  "8104": "\u1f60\u03b9",
  "8105": "\u1f61\u03b9",
  "8106": "\u1f62\u03b9",
  "8107": "\u1f63\u03b9",
  "8108": "\u1f64\u03b9",
  "8109": "\u1f65\u03b9",
  "8110": "\u1f66\u03b9",
  "8111": "\u1f67\u03b9",
  "8114": "\u1f70\u03b9",
  "8115": "\u03b1\u03b9",
  "8116": "\u03ac\u03b9",
  "8118": "\u03b1\u0342",
  "8119": "\u03b1\u0342\u03b9",
  "8120": "\u1fb0",
  "8121": "\u1fb1",
  "8122": "\u1f70",
  "8123": "\u1f71",
  "8124": "\u03b1\u03b9",
  "8126": "\u03b9",
  "8130": "\u1f74\u03b9",
  "8131": "\u03b7\u03b9",
  "8132": "\u03ae\u03b9",
  "8134": "\u03b7\u0342",
  "8135": "\u03b7\u0342\u03b9",
  "8136": "\u1f72",
  "8137": "\u1f73",
  "8138": "\u1f74",
  "8139": "\u1f75",
  "8140": "\u03b7\u03b9",
  "8146": "\u03b9\u0308\u0300",
  "8147": "\u03b9\u0308\u0301",
  "8150": "\u03b9\u0342",
  "8151": "\u03b9\u0308\u0342",
  "8152": "\u1fd0",
  "8153": "\u1fd1",
  "8154": "\u1f76",
  "8155": "\u1f77",
  "8162": "\u03c5\u0308\u0300",
  "8163": "\u03c5\u0308\u0301",
  "8164": "\u03c1\u0313",
  "8166": "\u03c5\u0342",
  "8167": "\u03c5\u0308\u0342",
  "8168": "\u1fe0",
  "8169": "\u1fe1",
  "8170": "\u1f7a",
  "8171": "\u1f7b",
  "8172": "\u1fe5",
  "8178": "\u1f7c\u03b9",
  "8179": "\u03c9\u03b9",
  "8180": "\u03ce\u03b9",
  "8182": "\u03c9\u0342",
  "8183": "\u03c9\u0342\u03b9",
  "8184": "\u1f78",
  "8185": "\u1f79",
  "8186": "\u1f7c",
  "8187": "\u1f7d",
  "8188": "\u03c9\u03b9",
  "8486": "\u03c9",
  "8490": "k",
  "8491": "\u00e5",
  "8498": "\u214e",
  "8544": "\u2170",
  "8545": "\u2171",
  "8546": "\u2172",
  "8547": "\u2173",
  "8548": "\u2174",
  "8549": "\u2175",
  "8550": "\u2176",
  "8551": "\u2177",
  "8552": "\u2178",
  "8553": "\u2179",
  "8554": "\u217a",
  "8555": "\u217b",
  "8556": "\u217c",
  "8557": "\u217d",
  "8558": "\u217e",
  "8559": "\u217f",
  "8579": "\u2184",
  "9398": "\u24d0",
  "9399": "\u24d1",
  "9400": "\u24d2",
  "9401": "\u24d3",
  "9402": "\u24d4",
  "9403": "\u24d5",
  "9404": "\u24d6",
  "9405": "\u24d7",
  "9406": "\u24d8",
  "9407": "\u24d9",
  "9408": "\u24da",
  "9409": "\u24db",
  "9410": "\u24dc",
  "9411": "\u24dd",
  "9412": "\u24de",
  "9413": "\u24df",
  "9414": "\u24e0",
  "9415": "\u24e1",
  "9416": "\u24e2",
  "9417": "\u24e3",
  "9418": "\u24e4",
  "9419": "\u24e5",
  "9420": "\u24e6",
  "9421": "\u24e7",
  "9422": "\u24e8",
  "9423": "\u24e9",
  "11264": "\u2c30",
  "11265": "\u2c31",
  "11266": "\u2c32",
  "11267": "\u2c33",
  "11268": "\u2c34",
  "11269": "\u2c35",
  "11270": "\u2c36",
  "11271": "\u2c37",
  "11272": "\u2c38",
  "11273": "\u2c39",
  "11274": "\u2c3a",
  "11275": "\u2c3b",
  "11276": "\u2c3c",
  "11277": "\u2c3d",
  "11278": "\u2c3e",
  "11279": "\u2c3f",
  "11280": "\u2c40",
  "11281": "\u2c41",
  "11282": "\u2c42",
  "11283": "\u2c43",
  "11284": "\u2c44",
  "11285": "\u2c45",
  "11286": "\u2c46",
  "11287": "\u2c47",
  "11288": "\u2c48",
  "11289": "\u2c49",
  "11290": "\u2c4a",
  "11291": "\u2c4b",
  "11292": "\u2c4c",
  "11293": "\u2c4d",
  "11294": "\u2c4e",
  "11295": "\u2c4f",
  "11296": "\u2c50",
  "11297": "\u2c51",
  "11298": "\u2c52",
  "11299": "\u2c53",
  "11300": "\u2c54",
  "11301": "\u2c55",
  "11302": "\u2c56",
  "11303": "\u2c57",
  "11304": "\u2c58",
  "11305": "\u2c59",
  "11306": "\u2c5a",
  "11307": "\u2c5b",
  "11308": "\u2c5c",
  "11309": "\u2c5d",
  "11310": "\u2c5e",
  "11311": "\u2c5f",
  "11360": "\u2c61",
  "11362": "\u026b",
  "11363": "\u1d7d",
  "11364": "\u027d",
  "11367": "\u2c68",
  "11369": "\u2c6a",
  "11371": "\u2c6c",
  "11373": "\u0251",
  "11374": "\u0271",
  "11375": "\u0250",
  "11376": "\u0252",
  "11378": "\u2c73",
  "11381": "\u2c76",
  "11390": "\u023f",
  "11391": "\u0240",
  "11392": "\u2c81",
  "11394": "\u2c83",
  "11396": "\u2c85",
  "11398": "\u2c87",
  "11400": "\u2c89",
  "11402": "\u2c8b",
  "11404": "\u2c8d",
  "11406": "\u2c8f",
  "11408": "\u2c91",
  "11410": "\u2c93",
  "11412": "\u2c95",
  "11414": "\u2c97",
  "11416": "\u2c99",
  "11418": "\u2c9b",
  "11420": "\u2c9d",
  "11422": "\u2c9f",
  "11424": "\u2ca1",
  "11426": "\u2ca3",
  "11428": "\u2ca5",
  "11430": "\u2ca7",
  "11432": "\u2ca9",
  "11434": "\u2cab",
  "11436": "\u2cad",
  "11438": "\u2caf",
  "11440": "\u2cb1",
  "11442": "\u2cb3",
  "11444": "\u2cb5",
  "11446": "\u2cb7",
  "11448": "\u2cb9",
  "11450": "\u2cbb",
  "11452": "\u2cbd",
  "11454": "\u2cbf",
  "11456": "\u2cc1",
  "11458": "\u2cc3",
  "11460": "\u2cc5",
  "11462": "\u2cc7",
  "11464": "\u2cc9",
  "11466": "\u2ccb",
  "11468": "\u2ccd",
  "11470": "\u2ccf",
  "11472": "\u2cd1",
  "11474": "\u2cd3",
  "11476": "\u2cd5",
  "11478": "\u2cd7",
  "11480": "\u2cd9",
  "11482": "\u2cdb",
  "11484": "\u2cdd",
  "11486": "\u2cdf",
  "11488": "\u2ce1",
  "11490": "\u2ce3",
  "11499": "\u2cec",
  "11501": "\u2cee",
  "11506": "\u2cf3",
  "42560": "\ua641",
  "42562": "\ua643",
  "42564": "\ua645",
  "42566": "\ua647",
  "42568": "\ua649",
  "42570": "\ua64b",
  "42572": "\ua64d",
  "42574": "\ua64f",
  "42576": "\ua651",
  "42578": "\ua653",
  "42580": "\ua655",
  "42582": "\ua657",
  "42584": "\ua659",
  "42586": "\ua65b",
  "42588": "\ua65d",
  "42590": "\ua65f",
  "42592": "\ua661",
  "42594": "\ua663",
  "42596": "\ua665",
  "42598": "\ua667",
  "42600": "\ua669",
  "42602": "\ua66b",
  "42604": "\ua66d",
  "42624": "\ua681",
  "42626": "\ua683",
  "42628": "\ua685",
  "42630": "\ua687",
  "42632": "\ua689",
  "42634": "\ua68b",
  "42636": "\ua68d",
  "42638": "\ua68f",
  "42640": "\ua691",
  "42642": "\ua693",
  "42644": "\ua695",
  "42646": "\ua697",
  "42648": "\ua699",
  "42650": "\ua69b",
  "42786": "\ua723",
  "42788": "\ua725",
  "42790": "\ua727",
  "42792": "\ua729",
  "42794": "\ua72b",
  "42796": "\ua72d",
  "42798": "\ua72f",
  "42802": "\ua733",
  "42804": "\ua735",
  "42806": "\ua737",
  "42808": "\ua739",
  "42810": "\ua73b",
  "42812": "\ua73d",
  "42814": "\ua73f",
  "42816": "\ua741",
  "42818": "\ua743",
  "42820": "\ua745",
  "42822": "\ua747",
  "42824": "\ua749",
  "42826": "\ua74b",
  "42828": "\ua74d",
  "42830": "\ua74f",
  "42832": "\ua751",
  "42834": "\ua753",
  "42836": "\ua755",
  "42838": "\ua757",
  "42840": "\ua759",
  "42842": "\ua75b",
  "42844": "\ua75d",
  "42846": "\ua75f",
  "42848": "\ua761",
  "42850": "\ua763",
  "42852": "\ua765",
  "42854": "\ua767",
  "42856": "\ua769",
  "42858": "\ua76b",
  "42860": "\ua76d",
  "42862": "\ua76f",
  "42873": "\ua77a",
  "42875": "\ua77c",
  "42877": "\u1d79",
  "42878": "\ua77f",
  "42880": "\ua781",
  "42882": "\ua783",
  "42884": "\ua785",
  "42886": "\ua787",
  "42891": "\ua78c",
  "42893": "\u0265",
  "42896": "\ua791",
  "42898": "\ua793",
  "42902": "\ua797",
  "42904": "\ua799",
  "42906": "\ua79b",
  "42908": "\ua79d",
  "42910": "\ua79f",
  "42912": "\ua7a1",
  "42914": "\ua7a3",
  "42916": "\ua7a5",
  "42918": "\ua7a7",
  "42920": "\ua7a9",
  "42922": "\u0266",
  "42923": "\u025c",
  "42924": "\u0261",
  "42925": "\u026c",
  "42926": "\u026a",
  "42928": "\u029e",
  "42929": "\u0287",
  "42930": "\u029d",
  "42931": "\uab53",
  "42932": "\ua7b5",
  "42934": "\ua7b7",
  "42936": "\ua7b9",
  "42938": "\ua7bb",
  "42940": "\ua7bd",
  "42942": "\ua7bf",
  "42944": "\ua7c1",
  "42946": "\ua7c3",
  "42948": "\ua794",
  "42949": "\u0282",
  "42950": "\u1d8e",
  "42951": "\ua7c8",
  "42953": "\ua7ca",
  "42955": "\u0264",
  "42956": "\ua7cd",
  "42960": "\ua7d1",
  "42966": "\ua7d7",
  "42968": "\ua7d9",
  "42970": "\ua7db",
  "42972": "\u019b",
  "42997": "\ua7f6",
  "43888": "\u13a0",
  "43889": "\u13a1",
  "43890": "\u13a2",
  "43891": "\u13a3",
  "43892": "\u13a4",
  "43893": "\u13a5",
  "43894": "\u13a6",
  "43895": "\u13a7",
  "43896": "\u13a8",
  "43897": "\u13a9",
  "43898": "\u13aa",
  "43899": "\u13ab",
  "43900": "\u13ac",
  "43901": "\u13ad",
  "43902": "\u13ae",
  "43903": "\u13af",
  "43904": "\u13b0",
  "43905": "\u13b1",
  "43906": "\u13b2",
  "43907": "\u13b3",
  "43908": "\u13b4",
  "43909": "\u13b5",
  "43910": "\u13b6",
  "43911": "\u13b7",
  "43912": "\u13b8",
  "43913": "\u13b9",
  "43914": "\u13ba",
  "43915": "\u13bb",
  "43916": "\u13bc",
  "43917": "\u13bd",
  "43918": "\u13be",
  "43919": "\u13bf",
  "43920": "\u13c0",
  "43921": "\u13c1",
  "43922": "\u13c2",
  "43923": "\u13c3",
  "43924": "\u13c4",
  "43925": "\u13c5",
  "43926": "\u13c6",
  "43927": "\u13c7",
  "43928": "\u13c8",
  "43929": "\u13c9",
  "43930": "\u13ca",
  "43931": "\u13cb",
  "43932": "\u13cc",
  "43933": "\u13cd",
  "43934": "\u13ce",
  "43935": "\u13cf",
  "43936": "\u13d0",
  "43937": "\u13d1",
  "43938": "\u13d2",
  "43939": "\u13d3",
  "43940": "\u13d4",
  "43941": "\u13d5",
  "43942": "\u13d6",
  "43943": "\u13d7",
  "43944": "\u13d8",
  "43945": "\u13d9",
  "43946": "\u13da",
  "43947": "\u13db",
  "43948": "\u13dc",
  "43949": "\u13dd",
  "43950": "\u13de",
  "43951": "\u13df",
  "43952": "\u13e0",
  "43953": "\u13e1",
  "43954": "\u13e2",
  "43955": "\u13e3",
  "43956": "\u13e4",
  "43957": "\u13e5",
  "43958": "\u13e6",
  "43959": "\u13e7",
  "43960": "\u13e8",
  "43961": "\u13e9",
  "43962": "\u13ea",
  "43963": "\u13eb",
  "43964": "\u13ec",
  "43965": "\u13ed",
  "43966": "\u13ee",
  "43967": "\u13ef",
  "64256": "ff",
  "64257": "fi",
  "64258": "fl",
  "64259": "ffi",
  "64260": "ffl",
  "64261": "st",
  "64262": "st",
  "64275": "\u0574\u0576",
  "64276": "\u0574\u0565",
  "64277": "\u0574\u056b",
  "64278": "\u057e\u0576",
  "64279": "\u0574\u056d",
  "65313": "\uff41",
  "65314": "\uff42",
  "65315": "\uff43",
  "65316": "\uff44",
  "65317": "\uff45",
  "65318": "\uff46",
  "65319": "\uff47",
  "65320": "\uff48",
  "65321": "\uff49",
  "65322": "\uff4a",
  "65323": "\uff4b",
  "65324": "\uff4c",
  "65325": "\uff4d",
  "65326": "\uff4e",
  "65327": "\uff4f",
  "65328": "\uff50",
  "65329": "\uff51",
  "65330": "\uff52",
  "65331": "\uff53",
  "65332": "\uff54",
  "65333": "\uff55",
  "65334": "\uff56",
  "65335": "\uff57",
  "65336": "\uff58",
  "65337": "\uff59",
  "65338": "\uff5a",
  "66560": "\ud801\udc28",
  "66561": "\ud801\udc29",
  "66562": "\ud801\udc2a",
  "66563": "\ud801\udc2b",
  "66564": "\ud801\udc2c",
  "66565": "\ud801\udc2d",
  "66566": "\ud801\udc2e",
  "66567": "\ud801\udc2f",
  "66568": "\ud801\udc30",
  "66569": "\ud801\udc31",
  "66570": "\ud801\udc32",
  "66571": "\ud801\udc33",
  "66572": "\ud801\udc34",
  "66573": "\ud801\udc35",
  "66574": "\ud801\udc36",
  "66575": "\ud801\udc37",
  "66576": "\ud801\udc38",
  "66577": "\ud801\udc39",
  "66578": "\ud801\udc3a",
  "66579": "\ud801\udc3b",
  "66580": "\ud801\udc3c",
  "66581": "\ud801\udc3d",
  "66582": "\ud801\udc3e",
  "66583": "\ud801\udc3f",
  "66584": "\ud801\udc40",
  "66585": "\ud801\udc41",
  "66586": "\ud801\udc42",
  "66587": "\ud801\udc43",
  "66588": "\ud801\udc44",
  "66589": "\ud801\udc45",
  "66590": "\ud801\udc46",
  "66591": "\ud801\udc47",
  "66592": "\ud801\udc48",
  "66593": "\ud801\udc49",
  "66594": "\ud801\udc4a",
  "66595": "\ud801\udc4b",
  "66596": "\ud801\udc4c",
  "66597": "\ud801\udc4d",
  "66598": "\ud801\udc4e",
  "66599": "\ud801\udc4f",
  "66736": "\ud801\udcd8",
  "66737": "\ud801\udcd9",
  "66738": "\ud801\udcda",
  "66739": "\ud801\udcdb",
  "66740": "\ud801\udcdc",
  "66741": "\ud801\udcdd",
  "66742": "\ud801\udcde",
  "66743": "\ud801\udcdf",
  "66744": "\ud801\udce0",
  "66745": "\ud801\udce1",
  "66746": "\ud801\udce2",
  "66747": "\ud801\udce3",
  "66748": "\ud801\udce4",
  "66749": "\ud801\udce5",
  "66750": "\ud801\udce6",
  "66751": "\ud801\udce7",
  "66752": "\ud801\udce8",
  "66753": "\ud801\udce9",
  "66754": "\ud801\udcea",
  "66755": "\ud801\udceb",
  "66756": "\ud801\udcec",
  "66757": "\ud801\udced",
  "66758": "\ud801\udcee",
  "66759": "\ud801\udcef",
  "66760": "\ud801\udcf0",
  "66761": "\ud801\udcf1",
  "66762": "\ud801\udcf2",
  "66763": "\ud801\udcf3",
  "66764": "\ud801\udcf4",
  "66765": "\ud801\udcf5",
  "66766": "\ud801\udcf6",
  "66767": "\ud801\udcf7",
  "66768": "\ud801\udcf8",
  "66769": "\ud801\udcf9",
  "66770": "\ud801\udcfa",
  "66771": "\ud801\udcfb",
  "66928": "\ud801\udd97",
  "66929": "\ud801\udd98",
  "66930": "\ud801\udd99",
  "66931": "\ud801\udd9a",
  "66932": "\ud801\udd9b",
  "66933": "\ud801\udd9c",
  "66934": "\ud801\udd9d",
  "66935": "\ud801\udd9e",
  "66936": "\ud801\udd9f",
  "66937": "\ud801\udda0",
  "66938": "\ud801\udda1",
  "66940": "\ud801\udda3",
  "66941": "\ud801\udda4",
  "66942": "\ud801\udda5",
  "66943": "\ud801\udda6",
  "66944": "\ud801\udda7",
  "66945": "\ud801\udda8",
  "66946": "\ud801\udda9",
  "66947": "\ud801\uddaa",
  "66948": "\ud801\uddab",
  "66949": "\ud801\uddac",
  "66950": "\ud801\uddad",
  "66951": "\ud801\uddae",
  "66952": "\ud801\uddaf",
  "66953": "\ud801\uddb0",
  "66954": "\ud801\uddb1",
  "66956": "\ud801\uddb3",
  "66957": "\ud801\uddb4",
  "66958": "\ud801\uddb5",
  "66959": "\ud801\uddb6",
  "66960": "\ud801\uddb7",
  "66961": "\ud801\uddb8",
  "66962": "\ud801\uddb9",
  "66964": "\ud801\uddbb",
  "66965": "\ud801\uddbc",
  "68736": "\ud803\udcc0",
  "68737": "\ud803\udcc1",
  "68738": "\ud803\udcc2",
  "68739": "\ud803\udcc3",
  "68740": "\ud803\udcc4",
  "68741": "\ud803\udcc5",
  "68742": "\ud803\udcc6",
  "68743": "\ud803\udcc7",
  "68744": "\ud803\udcc8",
  "68745": "\ud803\udcc9",
  "68746": "\ud803\udcca",
  "68747": "\ud803\udccb",
  "68748": "\ud803\udccc",
  "68749": "\ud803\udccd",
  "68750": "\ud803\udcce",
  "68751": "\ud803\udccf",
  "68752": "\ud803\udcd0",
  "68753": "\ud803\udcd1",
  "68754": "\ud803\udcd2",
  "68755": "\ud803\udcd3",
  "68756": "\ud803\udcd4",
  "68757": "\ud803\udcd5",
  "68758": "\ud803\udcd6",
  "68759": "\ud803\udcd7",
  "68760": "\ud803\udcd8",
  "68761": "\ud803\udcd9",
  "68762": "\ud803\udcda",
  "68763": "\ud803\udcdb",
  "68764": "\ud803\udcdc",
  "68765": "\ud803\udcdd",
  "68766": "\ud803\udcde",
  "68767": "\ud803\udcdf",
  "68768": "\ud803\udce0",
  "68769": "\ud803\udce1",
  "68770": "\ud803\udce2",
  "68771": "\ud803\udce3",
  "68772": "\ud803\udce4",
  "68773": "\ud803\udce5",
  "68774": "\ud803\udce6",
  "68775": "\ud803\udce7",
  "68776": "\ud803\udce8",
  "68777": "\ud803\udce9",
  "68778": "\ud803\udcea",
  "68779": "\ud803\udceb",
  "68780": "\ud803\udcec",
  "68781": "\ud803\udced",
  "68782": "\ud803\udcee",
  "68783": "\ud803\udcef",
  "68784": "\ud803\udcf0",
  "68785": "\ud803\udcf1",
  "68786": "\ud803\udcf2",
  "68944": "\ud803\udd70",
  "68945": "\ud803\udd71",
  "68946": "\ud803\udd72",
  "68947": "\ud803\udd73",
  "68948": "\ud803\udd74",
  "68949": "\ud803\udd75",
  "68950": "\ud803\udd76",
  "68951": "\ud803\udd77",
  "68952": "\ud803\udd78",
  "68953": "\ud803\udd79",
  "68954": "\ud803\udd7a",
  "68955": "\ud803\udd7b",
  "68956": "\ud803\udd7c",
  "68957": "\ud803\udd7d",
  "68958": "\ud803\udd7e",
  "68959": "\ud803\udd7f",
  "68960": "\ud803\udd80",
  "68961": "\ud803\udd81",
  "68962": "\ud803\udd82",
  "68963": "\ud803\udd83",
  "68964": "\ud803\udd84",
  "68965": "\ud803\udd85",
  "71840": "\ud806\udcc0",
  "71841": "\ud806\udcc1",
  "71842": "\ud806\udcc2",
  "71843": "\ud806\udcc3",
  "71844": "\ud806\udcc4",
  "71845": "\ud806\udcc5",
  "71846": "\ud806\udcc6",
  "71847": "\ud806\udcc7",
  "71848": "\ud806\udcc8",
  "71849": "\ud806\udcc9",
  "71850": "\ud806\udcca",
  "71851": "\ud806\udccb",
  "71852": "\ud806\udccc",
  "71853": "\ud806\udccd",
  "71854": "\ud806\udcce",
  "71855": "\ud806\udccf",
  "71856": "\ud806\udcd0",
  "71857": "\ud806\udcd1",
  "71858": "\ud806\udcd2",
  "71859": "\ud806\udcd3",
  "71860": "\ud806\udcd4",
  "71861": "\ud806\udcd5",
  "71862": "\ud806\udcd6",
  "71863": "\ud806\udcd7",
  "71864": "\ud806\udcd8",
  "71865": "\ud806\udcd9",
  "71866": "\ud806\udcda",
  "71867": "\ud806\udcdb",
  "71868": "\ud806\udcdc",
  "71869": "\ud806\udcdd",
  "71870": "\ud806\udcde",
  "71871": "\ud806\udcdf",
  "93760": "\ud81b\ude60",
  "93761": "\ud81b\ude61",
  "93762": "\ud81b\ude62",
  "93763": "\ud81b\ude63",
  "93764": "\ud81b\ude64",
  "93765": "\ud81b\ude65",
  "93766": "\ud81b\ude66",
  "93767": "\ud81b\ude67",
  "93768": "\ud81b\ude68",
  "93769": "\ud81b\ude69",
  "93770": "\ud81b\ude6a",
  "93771": "\ud81b\ude6b",
  "93772": "\ud81b\ude6c",
  "93773": "\ud81b\ude6d",
  "93774": "\ud81b\ude6e",
  "93775": "\ud81b\ude6f",
  "93776": "\ud81b\ude70",
  "93777": "\ud81b\ude71",
  "93778": "\ud81b\ude72",
  "93779": "\ud81b\ude73",
  "93780": "\ud81b\ude74",
  "93781": "\ud81b\ude75",
  "93782": "\ud81b\ude76",
  "93783": "\ud81b\ude77",
  "93784": "\ud81b\ude78",
  "93785": "\ud81b\ude79",
  "93786": "\ud81b\ude7a",
  "93787": "\ud81b\ude7b",
  "93788": "\ud81b\ude7c",
  "93789": "\ud81b\ude7d",
  "93790": "\ud81b\ude7e",
  "93791": "\ud81b\ude7f",
  "125184": "\ud83a\udd22",
  "125185": "\ud83a\udd23",
  "125186": "\ud83a\udd24",
  "125187": "\ud83a\udd25",
  "125188": "\ud83a\udd26",
  "125189": "\ud83a\udd27",
  "125190": "\ud83a\udd28",
  "125191": "\ud83a\udd29",
  "125192": "\ud83a\udd2a",
  "125193": "\ud83a\udd2b",
  "125194": "\ud83a\udd2c",
  "125195": "\ud83a\udd2d",
  "125196": "\ud83a\udd2e",
  "125197": "\ud83a\udd2f",
  "125198": "\ud83a\udd30",
  "125199": "\ud83a\udd31",
  "125200": "\ud83a\udd32",
  "125201": "\ud83a\udd33",
  "125202": "\ud83a\udd34",
  "125203": "\ud83a\udd35",
  "125204": "\ud83a\udd36",
  "125205": "\ud83a\udd37",
  "125206": "\ud83a\udd38",
  "125207": "\ud83a\udd39",
  "125208": "\ud83a\udd3a",
  "125209": "\ud83a\udd3b",
  "125210": "\ud83a\udd3c",
  "125211": "\ud83a\udd3d",
  "125212": "\ud83a\udd3e",
  "125213": "\ud83a\udd3f",
  "125214": "\ud83a\udd40",
  "125215": "\ud83a\udd41",
  "125216": "\ud83a\udd42",
  "125217": "\ud83a\udd43"
});

function pythonCasefold(value) {
  return Array.from(value, (character) =>
    PYTHON_CASEFOLD[character.codePointAt(0)] ?? character).join("");
}

function casefoldEquivalent(left, right) {
  return pythonCasefold(left) === pythonCasefold(right);
}

verifyPrepareButton.addEventListener("click", () => {
  if (requestPending || guidedState.stages["follow-up"] !== "completed"
    || !guidedState.retainedFollowUp) return;
  invalidateGuidedStage("verify");
  clearGuidedCorrelationForReplacement();
  clearDraftResults();
  const { listId, expectedItem } = guidedState.retainedFollowUp;
  markNaturalProposalReplaced();
  commandInput.value = `list read ${listId}`;
  preparationError.textContent = "";
  preparationStatus.textContent = "Verification prepared. No operation has been executed.";
  commandState.textContent = "Review or edit the prepared command, then explicitly Send.";
  setGuidedPreparation("verify", {
    stage: "verify", type: "verify-read", listId, expectedItem,
  }, "Verification prepared for the recorded follow-up. Review the editor, then explicitly Send.");
  commandInput.focus();
  updatePreparationButton();
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
  for (const type of ["input", "change"]) input.addEventListener(type, () => {
    if (requestPending || guidedState.stages.recall !== "completed") return;
    invalidateLocalAssistance("controls");
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
    markNaturalProposalReplaced();
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
  invalidateLocalAssistance("controls");
  clearDraftResults();
  preparationError.textContent = "";
  const replaced = commandInput.value !== "";
  try {
    const preparedCommand = prepareKnowledgeCommand(operation, fields);
    clearGuidedCorrelationForReplacement();
    markNaturalProposalReplaced();
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
  invalidateLocalAssistance("send");
  clearDraftResults("Pending");
  beginGuidedRequest();

  const csrfMeta = document.querySelector("meta[name=\"luxiom-csrf\"]");
  const csrfToken = csrfMeta?.getAttribute("content") || "";
  if (!csrfToken) {
    failGuidedRequest(
      "The request could not start. The guided step remains incomplete.",
    );
    renderLocalFailure();
    if (naturalProposal !== null) {
      naturalIntentStatus.textContent = "Governed Send could not start; see Result. Editor retained.";
    }
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

  submitNaturalProposal();
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
    if (naturalProposal?.uiState === "submitted") {
      naturalIntentStatus.textContent = "Governed request settled; see Result for the authoritative execution outcome.";
    }
  }
});
