from wordle import Constraint
import pytest


alphabet = set(map(chr, range(97, 123)))
parse_parameters = [
    (
        "+s_a-s_s_y",
        {"s": 2},
        [
            {"s"},
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "+s_a_s-s_y",
        {"s": 2},
        [
            {"s"},
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "-s_a+s_s_y",
        {"s": 2},
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            {"s"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "-s_a_s+s_y",
        {"s": 2},
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            {"s"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "_s_a+s-s_y",
        {"s": 2},
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            {"s"},
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
        ],
    ),
    (
        "_s_a-s+s_y",
        {"s": 2},
        [
            alphabet - {"a", "s", "y"},
            alphabet - {"a", "y"},
            alphabet - {"a", "s", "y"},
            {"s"},
            alphabet - {"a", "y"},
        ],
    ),
]


@pytest.mark.parametrize(
    "input,at_least,allows",
    parse_parameters,
)
def test_parse_constraints(input, at_least, allows):
    c = Constraint.parse(input)
    assert c.at_least == at_least
    assert c.allows[0] == allows[0]
    assert c.allows[1] == allows[1]
    assert c.allows[2] == allows[2]
    assert c.allows[3] == allows[3]
    assert c.allows[4] == allows[4]


diff_parameters = [
    (
        "shire",
        "cross",
        {"s": 1, "r": 1},
        [
            alphabet - {"o", "c"},
            alphabet - {"o", "c", "r"},
            alphabet - {"o", "c"},
            alphabet - {"o", "c", "s"},
            alphabet - {"o", "c", "s"},
        ],
    ),
    (
        "adage",
        "adiue",
        {"a": 1, "d": 1, "e": 1},
        [
            {"a"},
            {"d"},
            alphabet - {"i", "u"},
            alphabet - {"i", "u"},
            {"e"},
        ],
    ),
]


@pytest.mark.parametrize(
    "input_a,input_b,at_least,allows",
    diff_parameters,
)
def test_gen_constraints(input_a, input_b, at_least, allows):
    c = Constraint.diff(input_a, input_b)
    assert c.at_least == at_least
    assert c.allows[0] == allows[0]
    assert c.allows[1] == allows[1]
    assert c.allows[2] == allows[2]
    assert c.allows[3] == allows[3]
    assert c.allows[4] == allows[4]
