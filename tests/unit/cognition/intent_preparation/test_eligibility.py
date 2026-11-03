"""Frozen safety parity and Amendment 01 guard-complement eligibility."""

from itertools import product

import pytest

from app.cognition.intent_preparation.eligibility import (
    assess_eligibility,
    has_multiple_actions,
    keyword_text,
    quoted_spans,
)
from app.cognition.intent_preparation.models import (
    EDGE_WHITESPACE,
    EligibilityDecision,
)


def assert_protected(text: object, reason: str) -> None:
    result = assess_eligibility(text)
    assert result.decision is EligibilityDecision.PROTECTED
    assert result.reason == reason
    assert assess_eligibility(text) == result


def test_keyword_mapping_is_only_the_frozen_length_preserving_mapping():
    original = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑİKÉ e\u0301 😀"
    compared = keyword_text(original)
    assert compared == "abcdefghijklmnopqrstuvwxyzáéíóúüñİKé e\u0301 😀"
    assert len(compared) == len(original)


_PREPARED_CORPUS = (
    "Recuerda que MedSupply entrega los martes.",
    "Guarda que MedSupply entrega los martes.",
    "Anota que MedSupply entrega los martes.",
    "Qué te dije sobre MedSupply",
    "Qué sabes de MedSupply",
    "Agrega llamar a MedSupply a la lista tareas",
    "Añade llamar a MedSupply a la lista tareas",
    "Qué hay en la lista tareas",
    "Muéstrame la lista tareas",
)


@pytest.mark.parametrize("text", _PREPARED_CORPUS)
@pytest.mark.parametrize("uppercase", (False, True))
def test_exact_sprint_41_recognition_is_protected(text, uppercase):
    # Capture may require explicit controls; recognizing it still forbids a model.
    assert_protected(text.upper() if uppercase else text, "deterministic_recognized")


@pytest.mark.parametrize(
    "prefix", ("Qué te dije sobre", "Qué sabes de", "Qué hay en la lista")
)
@pytest.mark.parametrize("left,right", tuple(product(("", "¿"), ("", "?"))))
def test_exact_question_wrappers_remain_recognized(prefix, left, right):
    assert_protected(f"{left}{prefix} K{right}", "deterministic_recognized")


@pytest.mark.parametrize(
    "text",
    (
        "Recuerda que",
        "Guarda que",
        "Anota que",
        "Qué te dije sobre",
        "¿Qué te dije sobre?",
        "Qué sabes de",
        "Qué hay en la lista",
        "Muéstrame la lista",
        "Agrega  a la lista L",
        "Añade X a la lista ",
        "Agrega  a la lista ",
        "Agrega X a mis pendientes",
        "Añade X a mis pendientes",
        "Qué tengo pendiente",
        "¿Qué tengo pendiente?",
        "Qué tengo pendiente?",
        "¿Qué tengo pendiente",
        "Agrega X | Y a la lista L",
        "Muéstrame la lista dos palabras",
        "Agrega X a la lista a::b",
        "Agrega X a la lista a la lista L",
    ),
)
def test_recognized_missing_or_invalid_semantics_remain_protected(text):
    assert_protected(text, "deterministic_clarification")


@pytest.mark.parametrize("edge", tuple(EDGE_WHITESPACE))
def test_outer_whitespace_matches_the_frozen_set(edge):
    assert_protected(f"{edge}Qué sabes de K{edge}", "deterministic_recognized")
    assert_protected(edge, "invalid_input")


@pytest.mark.parametrize("text", (None, False, 3, [], {}, "", "\ud800", "x\udfff"))
def test_invalid_input_protected_without_interpreting_it(text):
    assert_protected(text, "invalid_input")


def test_code_point_budget_includes_original_outer_whitespace():
    prefix = "Recuerda que "
    text = prefix + "😀" * (8192 - len(prefix))
    assert_protected(text, "deterministic_recognized")
    assert_protected(text + "😀", "invalid_input")
    assert_protected(" " + text, "invalid_input")


@pytest.mark.parametrize(
    "text",
    (
        "Si recuerda que X",
        "si",
        "SI",
        "cuando",
        "Cuando agrega X a la lista L",
        "si: X",
        "cuando(X)",
    ),
)
def test_bounded_top_level_conditions_are_protected(text):
    assert_protected(text, "unsupported_request")


@pytest.mark.parametrize(
    "text", ("notable", "noche", "sin", "silencio", "cuando2", "si²", "noél")
)
def test_bounded_prefix_does_not_broaden_into_other_words(text):
    assert_eligible(text)


@pytest.mark.parametrize(
    "text",
    (
        "Recuerda que si X",
        "Guarda que CUANDO X",
        "Qué sabes de si",
        "Recuerda que X si Y y agrega Z",
        "texto (si) X",
        "texto cuando X",
        "texto_si_X",
        "texto-si-X",
    ),
)
def test_standalone_conditions_are_protected_including_unknown_text(text):
    assert_protected(text, "conditional_request")


def test_negative_capture_payload_remains_deterministically_recognized():
    assert_protected("Recuerda que No entrega", "deterministic_recognized")
    assert_protected("Recuerda que X siembra cuando2", "deterministic_recognized")


@pytest.mark.parametrize(
    "text",
    (
        '"Recuerda que X"',
        "“Recuerda que X”",
        '"unmatched',
        "“unmatched",
        "Por ejemplo: Recuerda que X",
        "POR EJEMPLO: Recuerda que X",
    ),
)
def test_whole_quote_and_example_framing_are_protected(text):
    assert_protected(text, "unsupported_request")


_BOUNDARIES = (
    " y ",
    " y también ",
    " luego ",
    " después ",
    " entonces ",
    "; ",
    ". ",
    "! ",
    "? ",
    "\n",
    "\r\n",
    "\r",
    "\n \t",
    "\r\n\t ",
    "\r  ",
)
_INTRODUCERS = (
    "recuerda",
    "guarda",
    "anota",
    "agrega",
    "añade",
    "agrégalo",
    "añádelo",
    "muéstrame",
    "qué",
    "¿qué",
)


@pytest.mark.parametrize(
    "boundary,introducer", tuple(product(_BOUNDARIES, _INTRODUCERS))
)
def test_exact_multi_action_matrix_and_balanced_quote_suppression(boundary, introducer):
    pair = boundary + introducer + " Y"
    for variant in (pair, pair.upper()):
        text = "Recuerda que X" + variant
        assert has_multiple_actions(text)
        assert_protected(text, "multiple_actions")
    for left, right in (('"', '"'), ("“", "”")):
        text = f"Recuerda que X{left}{pair}{right}"
        assert not has_multiple_actions(text)
        assert_protected(text, "deterministic_recognized")


@pytest.mark.parametrize(
    "payload",
    (
        'X " y agrega Y',
        r"X \" y agrega Y",
        r"X \" y agrega Y \"",
        "X “ y agrega Y",
        'X "literal" y agrega Y',
    ),
)
def test_unmatched_and_escaped_quotes_do_not_hide_a_second_action(payload):
    assert has_multiple_actions(payload)
    assert_protected("Recuerda que " + payload, "multiple_actions")


@pytest.mark.parametrize(
    "payload",
    (
        r'X "literal \" y agrega Y"',
        r'X \\" y agrega Y"',
        "X “ y agrega Y”",
        'X " y agrega Y"',
    ),
)
def test_balanced_quotes_and_even_backslash_openers_suppress_the_detector(payload):
    assert not has_multiple_actions(payload)
    assert_protected("Recuerda que " + payload, "deterministic_recognized")


@pytest.mark.parametrize(
    "payload",
    (
        "X, agrega Y",
        "X;agrega Y",
        "X y busca Y",
        "X Y\tagrega Y",
        "X y agregamos Y",
        "X y anota\tY",
        "ir a mis pendientes favoritos",
    ),
)
def test_unlisted_boundaries_and_introducers_are_not_added(payload):
    assert not has_multiple_actions(payload)
    assert_protected("Recuerda que " + payload, "deterministic_recognized")


def test_quote_spans_are_inclusive_non_nested_and_unmatched_is_ordinary():
    assert quoted_spans('x "ab" y “cd”') == ((2, 5), (9, 12))
    assert quoted_spans('x "ab') == ()
    assert quoted_spans('x “ab"cd”') == ((2, 8),)
    assert quoted_spans(r"x \"ab\"") == ()
    assert quoted_spans(r'x \\"ab"') == ((4, 7),)


@pytest.mark.parametrize(
    "word", ("esto", "eso", "aquello", "ello", "él", "ella", "ellos", "ellas")
)
def test_exact_context_words_are_protected_in_payload_and_unrecognized_text(word):
    for text in (f"Recuerda que ({word.upper()})", f"texto ({word})", f"texto_{word}_"):
        assert_protected(text, "context_reference")


@pytest.mark.parametrize(
    "key", ("camellos", "xesto9", "eso²", "²eso", "𝒜esto", "esto𝟙")
)
def test_unicode_letter_number_boundaries_do_not_create_context_references(key):
    assert_protected("Qué sabes de " + key, "deterministic_recognized")


@pytest.mark.parametrize(
    "text",
    (
        "Agrega X a la lista L a la lista Q",
        "Agrega X a la lista L a mis pendientes",
        "Añade X a la lista L a la lista",
        "Agrega X a la lista A a la lista L",
    ),
)
def test_multiple_add_destination_structures_are_protected(text):
    assert_protected(text, "ambiguous_structure")


@pytest.mark.parametrize(
    "text",
    (
        "Agrega ir a mis pendientes favoritos a la lista L",
        "Añade X a mis pendientes a la lista L",
    ),
)
def test_non_terminal_generic_phrase_is_not_an_extra_destination(text):
    assert_protected(text, "deterministic_recognized")


@pytest.mark.parametrize("namespace", ("knowledge", "list", "KNOWLEDGE", "LIST"))
@pytest.mark.parametrize("suffix", ("", " bad", "\tbad", "\nmalformed", "\u0085bad"))
def test_direct_namespace_even_malformed_is_protected(namespace, suffix):
    assert_protected(namespace + suffix, "direct_command_namespace")


@pytest.mark.parametrize("text", ("knowledgeable", "listing", "knowledge: x", "list-x"))
def test_namespace_is_bounded_by_whitespace_or_end_only(text):
    assert_eligible(text)


@pytest.mark.parametrize(
    "text",
    (
        "Recuerda",
        "Agrega",
        "Añade",
        "Recuerda  que X",
        "Qué  sabes de K",
        "Que sabes de K",
        "Muestrame la lista L",
        "Anota\tque X",
        "Guardar que X",
        "Que\u0301 sabes de K",
        "Qué sabes de K??",
        "Qué sabes de ?K",
        "Qué sabes de ¿K",
        "¿Muéstrame la lista L?",
        "¿Recuerda que X?",
        "Dime qué sabes de K",
        "\ufeffQué sabes de K\u200b",
    ),
)
def test_semantic_non_recognition_alone_does_not_protect_text(text):
    assert_eligible(text)


def test_safety_precedence_keeps_stronger_guards_before_unrecognized_negation():
    assert_protected("Recuerda que si X y agrega Y", "conditional_request")
    assert_protected('"Recuerda que esto y agrega Y"', "unsupported_request")
    assert_protected("Recuerda que esto y agrega Y", "multiple_actions")
    assert_protected("Agrega esto a la lista L a la lista Q", "context_reference")
    assert_protected("No X y agrega Y", "multiple_actions")


def assert_eligible(text: str) -> None:
    result = assess_eligibility(text)
    assert result.decision is EligibilityDecision.ELIGIBLE_UNRECOGNIZED
    assert result.reason == "safe_unrecognized"
    assert assess_eligibility(text) == result


@pytest.mark.parametrize(
    "text",
    (
        "Conserva café molido",
        "Busca Tema Ágil",
        "Incorpora pan a la lista Compras",
        "Consulta la lista Compras",
        "Hola",
    ),
)
def test_amendment_examples_are_eligible_without_recognizing_an_intent(text):
    # Amendment 01 sections 4-8: these illustrate guard complement, not templates.
    assert_eligible(text)


@pytest.mark.parametrize("edge", tuple(EDGE_WHITESPACE))
def test_positive_eligibility_uses_frozen_outer_whitespace(edge):
    assert_eligible(f"{edge}Hola{edge}")


@pytest.mark.parametrize(
    "text",
    (
        "Nunca recuerdes X",
        "Jamás guardes X",
        "Tampoco conserves X",
        "No quiero que recuerdes X",
        "Evita guardar X",
        "Omite recordar X",
        "Ignora conservar X",
        "Deja de guardar X",
        "No recuerdes que X",
        "NO",
        "no!",
        "texto no demostrado",
        'Conserva la palabra "nunca"',
        "Conserva la palabra “jamás”",
    ),
)
def test_amendment_unrecognized_negation_is_protected(text):
    assert_protected(text, "negation_guard")


@pytest.mark.parametrize("word", ("no", "nunca", "jamás", "tampoco"))
@pytest.mark.parametrize("boundary", ("", " ", "_", "-", "(", "\u0301"))
def test_negation_standalone_boundaries_use_unicode_letters_and_numbers(word, boundary):
    assert_protected(f"Conserva {boundary}{word.upper()}{boundary}", "negation_guard")


@pytest.mark.parametrize("word", ("no", "nunca", "jamás", "tampoco"))
@pytest.mark.parametrize("adjacent", ("X", "é", "𝒜", "2", "²", "𝟙"))
@pytest.mark.parametrize("side", ("left", "right"))
def test_negation_does_not_match_inside_unicode_letter_or_number_words(
    word, adjacent, side
):
    value = adjacent + word if side == "left" else word + adjacent
    assert_eligible(f"Conserva {value}")


@pytest.mark.parametrize("phrase", ("evita", "omite", "ignora", "deja de"))
@pytest.mark.parametrize("suffix", ("", " X", ":X", "_X", "(X)", "\u0301X"))
def test_inhibitory_phrases_use_bounded_leading_matching(phrase, suffix):
    assert_protected(f"\u3000{phrase.upper()}{suffix}\u0085", "negation_guard")


@pytest.mark.parametrize(
    "text",
    (
        "notable",
        "nunca2",
        "jamásX",
        "tampoco9",
        "evitable",
        "omitente",
        "ignorado",
        "dejadero",
        "deja de2",
        "deja deX",
        "deja  de guardar X",
        "deja\tde guardar X",
        "deja\u00a0de guardar X",
        "deja\nde guardar X",
        "Conserva evita guardar X",
        "Conserva omite recordar X",
        "Conserva ignora conservar X",
        "Conserva deja de guardar X",
        "jamas guardes X",
        "jama\u0301s guardes X",
        "sin",
        "ni",
    ),
)
def test_no_stems_normalization_or_additional_negation_vocabulary(text):
    assert_eligible(text)


@pytest.mark.parametrize("word", ("No", "Nunca", "Jamás", "Tampoco"))
def test_recognized_capture_payload_is_not_scanned_for_unrecognized_negation(word):
    assert_protected(f"Recuerda que {word} entrega", "deterministic_recognized")


@pytest.mark.parametrize(
    "text,reason",
    (
        ("Nunca esto", "context_reference"),
        ("Nunca X y agrega Y", "multiple_actions"),
        ('"Nunca conserves X"', "unsupported_request"),
        ("Por ejemplo: Nunca conserves X", "unsupported_request"),
        ("Nunca conserva X si Y", "conditional_request"),
        ("knowledge no", "direct_command_namespace"),
        ("list nunca", "direct_command_namespace"),
        ("Recuerda que no", "deterministic_recognized"),
        ("Agrega no a mis pendientes", "deterministic_clarification"),
    ),
)
def test_existing_guards_and_recognition_precede_new_negation(text, reason):
    assert_protected(text, reason)


@pytest.mark.parametrize(
    "text",
    (
        "Incorpora pan a la lista Compras a la lista Hogar",
        "Incorpora pan a la lista Compras a mis pendientes",
        "Incorpora pan a la lista Compras a la lista",
        "Consulta la lista Compras y la lista Hogar",
    ),
)
def test_unrecognized_verbs_cannot_bypass_frozen_destination_ambiguity(text):
    assert_protected(text, "ambiguous_structure")


@pytest.mark.parametrize(
    "text",
    (
        'Conserva " y agrega pan"',
        "Conserva “ y agrega pan”",
    ),
)
def test_quoted_multi_action_suppression_can_reach_positive_eligibility(text):
    assert_eligible(text)


def test_original_code_point_limit_applies_before_positive_eligibility():
    assert_eligible("😀" * 8192)
    assert_protected("😀" * 8193, "invalid_input")
    assert_protected(" " + "😀" * 8192, "invalid_input")


@pytest.mark.parametrize("left,right", tuple(product(("", "¿"), ("", "?"))))
def test_read_destination_ambiguity_preserves_optional_question_wrappers(left, right):
    assert_protected(
        f"{left}la lista Compras y la lista Hogar{right}", "ambiguous_structure"
    )


@pytest.mark.parametrize("left,right", tuple(product(("", "¿"), ("", "?"))))
def test_single_read_destination_remains_eligible_with_question_wrappers(left, right):
    assert_eligible(f"{left}la lista Compras{right}")


@pytest.mark.parametrize(
    "text",
    (
        "¿¿la lista Compras y la lista Hogar?",
        "texto¿la lista Compras y la lista Hogar?",
        "?la lista Compras y la lista Hogar?",
        "¿la\tlista Compras y la lista Hogar?",
        "¿la listas Compras y la lista Hogar?",
    ),
)
def test_read_wrapper_correction_does_not_broaden_destination_boundaries(text):
    assert_eligible(text)


@pytest.mark.parametrize(
    "text,reason",
    (
        ("¿la lista Compras y la lista?", "ambiguous_structure"),
        ("\u3000¿LA LISTA Compras y LA LISTA Hogar?\u0085", "ambiguous_structure"),
        ('"¿la lista Compras y la lista Hogar?"', "unsupported_request"),
        ("Por ejemplo: ¿la lista Compras y la lista Hogar?", "unsupported_request"),
        ("¿la lista Compras y la lista Hogar? y agrega pan", "multiple_actions"),
        ("¿la lista Compras y la lista Hogar esto?", "context_reference"),
        ("¿la lista Compras y la lista Hogar si X?", "conditional_request"),
        (
            "Recuerda que ¿la lista Compras y la lista Hogar?",
            "deterministic_recognized",
        ),
        ("knowledge ¿la lista Compras y la lista Hogar?", "direct_command_namespace"),
    ),
)
def test_read_destination_wrapper_correction_preserves_frozen_precedence(text, reason):
    assert_protected(text, reason)
