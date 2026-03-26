# pylint: disable=pointless-statement
# pylint: disable=expression-not-assigned
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring



"""Tests for pype/utils.py — all utility functions."""

from miniplumber import pipe
from miniplumber.utils import (
    flatten, flatten_deep,
    sort, unique, keep, twist, named, chunk, window, group,
    field, attr,
    matching, having,
    tap,
)


# ── Flatten ───────────────────────────────────────────────────────────────────

def test_flatten_one_level():
    assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]

def test_flatten_does_not_go_deep():
    assert flatten([[1, [2]], [3]]) == [1, [2], 3]

def test_flatten_empty():
    assert flatten([]) == [] #pylint: disable=use-implicit-booleaness-not-comparison

def test_flatten_deep_arbitrary_nesting():
    assert flatten_deep([1, [2, [3, [4]]]]) == [1, 2, 3, 4]

def test_flatten_deep_mixed():
    assert flatten_deep([[1, 2], [3, [4, 5]]]) == [1, 2, 3, 4, 5]

def test_flatten_in_pipeline():
    result = ["hello world", "foo bar"] > pipe // str.split / flatten
    assert result == ["hello", "world", "foo", "bar"]


# ── Sort ─────────────────────────────────────────────────────────────────────

def test_sort_default():
    assert sort()([3, 1, 2]) == [1, 2, 3]

def test_sort_by_key():
    assert sort(key=len)(["bb", "a", "ccc"]) == ["a", "bb", "ccc"]

def test_sort_reverse():
    assert sort(reverse=True)([1, 2, 3]) == [3, 2, 1]

def test_sort_does_not_mutate():
    original = [3, 1, 2]
    sort()(original)
    assert original == [3, 1, 2]


# ── Unique ────────────────────────────────────────────────────────────────────

def test_unique_removes_duplicates():
    assert unique([1, 2, 1, 3, 2]) == [1, 2, 3]

def test_unique_preserves_order():
    assert unique(["b", "a", "b", "c"]) == ["b", "a", "c"]

def test_unique_empty():
    assert unique([]) == []


# ── Keep ──────────────────────────────────────────────────────────────────────

def test_keep_first_n():
    assert keep(3)([1, 2, 3, 4, 5]) == [1, 2, 3]

def test_keep_more_than_length():
    assert keep(10)([1, 2, 3]) == [1, 2, 3]

def test_keep_zero():
    assert keep(0)([1, 2, 3]) == []

def test_keep_skip_first_n():
    assert keep(2, None)([1, 2, 3, 4, 5]) == [3, 4, 5]

def test_keep_skip_more_than_length():
    assert keep(10, None)([1, 2, 3]) == []

def test_keep_slice_range():
    assert keep(1, 4)([1, 2, 3, 4, 5]) == [2, 3, 4]

def test_keep_step():
    assert keep(None, None, 2)([1, 2, 3, 4, 5]) == [1, 3, 5]

def test_keep_reverse():
    assert keep(None, None, -1)([1, 2, 3]) == [3, 2, 1]


# ── Twist ─────────────────────────────────────────────────────────────────────

def test_twist_two_branches():
    assert twist([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]

def test_twist_three_branches():
    assert twist([[1, 2], [3, 4], [5, 6]]) == [[1, 3, 5], [2, 4, 6]]

def test_twist_in_pipeline():
    result = [1, 2, 3] > pipe / (pipe / list + pipe / list) / twist
    assert result == [[1, 1], [2, 2], [3, 3]]

def test_twist_then_flatten():
    result = twist([[1, 2], [3, 4]])
    assert flatten(result) == [1, 3, 2, 4]


# ── Named ─────────────────────────────────────────────────────────────────────

def test_named_basic():
    assert named(["a", "b", "c"])([1, 2, 3]) == {"a": 1, "b": 2, "c": 3}

def test_named_in_pipeline():
    result = [0.73, 0.61, 0.44] > pipe / named(["micro", "meso", "macro"])
    assert result == {"micro": 0.73, "meso": 0.61, "macro": 0.44}

def test_named_after_fork():
    result = [1, 2, 3] > pipe / (pipe / min + pipe / max) / named(["lo", "hi"])
    assert result == {"lo": 1, "hi": 3}


# ── Chunk / Window ────────────────────────────────────────────────────────────

def test_chunk_even():
    assert chunk(2)([1, 2, 3, 4]) == [[1, 2], [3, 4]]

def test_chunk_with_remainder():
    assert chunk(2)([1, 2, 3, 4, 5]) == [[1, 2], [3, 4], [5]]

def test_window_size_two():
    assert window(2)([1, 2, 3, 4]) == [(1, 2), (2, 3), (3, 4)]

def test_window_size_three():
    assert window(3)([1, 2, 3, 4]) == [(1, 2, 3), (2, 3, 4)]

def test_window_exact_size():
    assert window(3)([1, 2, 3]) == [(1, 2, 3)]


# ── Group ─────────────────────────────────────────────────────────────────────

def test_group_by_len():
    result = group(len)(["a", "bb", "cc", "ddd"])
    assert result == {1: ["a"], 2: ["bb", "cc"], 3: ["ddd"]}

def test_group_preserves_order():
    result = group(lambda x: x % 2)([1, 2, 3, 4, 5])
    assert result == {1: [1, 3, 5], 0: [2, 4]}


# ── Field / Attr ──────────────────────────────────────────────────────────────

def test_field_extracts_key():
    users = [{"name": "Alice"}, {"name": "Bob"}]
    assert list(map(field("name"), users)) == ["Alice", "Bob"]

def test_field_missing_key_returns_default():
    users = [{"name": "Alice"}, {}]
    assert list(map(field("name", default="unknown"), users)) == ["Alice", "unknown"]

def test_field_default_is_none():
    assert field("x")({"y": 1}) is None

def test_field_in_pipeline():
    users = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    result = users > pipe // field("name")
    assert result == ["Alice", "Bob"]

def test_attr_extracts_attribute():
    class Obj:
        def __init__(self, x):
            self.x = x
    objs = [Obj(1), Obj(2)]
    assert list(map(attr("x"), objs)) == [1, 2]

def test_attr_missing_returns_default():
    class Obj:
        pass
    assert attr("x", default=0)(Obj()) == 0


# ── Predicates ────────────────────────────────────────────────────────────────

def test_matching_substring():
    pred = matching("ing")
    assert pred("running") is True
    assert pred("walked") is False

def test_matching_regex():
    import re # pylint: disable=import-outside-toplevel
    pred = matching(re.compile(r"^\d+$"))
    assert pred("123") is True
    assert pred("abc") is False

def test_having_single_kwarg():
    pred = having(status="active")
    assert pred({"status": "active", "name": "Alice"}) is True
    assert pred({"status": "inactive"}) is False

def test_having_multiple_kwargs():
    pred = having(status="active", role="admin")
    assert pred({"status": "active", "role": "admin"}) is True
    assert pred({"status": "active", "role": "user"}) is False


# ── Tap ───────────────────────────────────────────────────────────────────────

def test_tap_calls_func_as_side_effect():
    calls = []
    result = [1, 2, 3] > pipe / tap(calls.append)
    assert calls == [[1, 2, 3]]
    assert result == [1, 2, 3]

def test_tap_passes_value_unchanged():
    result = "hello" > pipe / tap(lambda x: None)
    assert result == "hello"
