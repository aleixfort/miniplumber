# miniplumber

A minimal functional pipeline for Python.

```python
from miniplumber import pipe, sort, field

scores > pipe // field("score") / sort(reverse=True)

words = sentences >  pipe // str.split / flatten // str.lower @ str.isalpha / unique / sort()


```

---

## Quick reference

```
value > pipe               fire pipeline, return raw value

/   func                   pass whole value to func
/   pipeline               compose two pipelines sequentially
//  func                   map over each element
@   func                   filter — keep where func(x) is truthy
+   pipeline               fork — always inside parens: / (a + b) /

All of  / // @ +  share the same precedence — left-to-right, no exceptions.
>  is lower precedence — pipeline always builds fully before firing.
```

---

## Philosophy

Every data pipeline is a combination of three operations:

```
//   map     — transform each element       (same number of inputs in and out)
@    filter  — select elements              (less or equal)
/    pass    — send the whole value to a function as-is
```

`/` does not imply a single output. It passes whatever you have — a list, a dict, a string — to the next function whole. The function decides what comes out:

```python
pipe / sorted          # list → list (reordered)
pipe / len             # list → int  (counted)
pipe / " ".join        # list → str  (joined)
```

miniplumber gives these three operations clean operator syntax and one rule: **all operators share the same precedence, always left-to-right**. No brackets to manage precedence. No surprises.

Everything else — flatten, sort, group, twist — is a plain function you pass with `/` or `//`. The library is the glue, not the logic. Any function that takes one value and returns one value is a valid step. No wrappers, no base classes, no registration.

The pipeline is lazy. Nothing executes until `>` fires it. This means pipelines are values — name them, compose them, pass them around, reuse them anywhere.

---

## Operators

### `/` — pass

Pass the whole value to a function:

```python
["hello", "world"] > pipe / len          # → 2
["hello", "world"] > pipe / " ".join     # → "hello world"
["hello", "world"] > pipe / sorted       # → ["hello", "world"]
```

Compose two named pipelines sequentially:

```python
clean   = pipe // str.strip // str.lower
shout   = pipe // str.upper
process = clean / shout
```

### `//` — map

Apply a function to each element. Always same length in, same length out:

```python
[1, 2, 3]          > pipe // double      # → [2, 4, 6]
["hello", "world"] > pipe // len         # → [5, 5]
["hello", "world"] > pipe // str.upper   # → ["HELLO", "WORLD"]
```

`//` is polymorphic — it works on dicts too, mapping over values and preserving keys:

```python
{"a": 1, "b": 2, "c": 3} > pipe // double
# → {"a": 2, "b": 4, "c": 6}
```

### `@` — filter

Keep elements where `func(x)` is truthy:

```python
[3, 0, 1, -1] > pipe @ bool              # → [3, 1]
words         > pipe @ having(pos="noun")# → [only nouns]
```

`@` also works on scalars — returns the value if truthy, `None` if not:

```python
3 > pipe @ bool    # → 3
0 > pipe @ bool    # → None
```

### `+` — fork

Split one input into parallel pipelines. Always wrap in parentheses:

```python
import statistics

data > pipe / (
    pipe / statistics.mean   +
    pipe / statistics.median +
    pipe / statistics.stdev
)
# → [mean, median, stdev]
```

Fork then merge — the step after `)` receives the list of branch results:

```python
"photo.jpg" > load / preproc / (edges + blurred) / np.hstack / save("compare.jpg")
```

### `>` — fire

Fires the pipeline and returns the raw value:

```python
result = data > pipe // str.upper / " ".join
```

---

## Named pipelines

Pipelines are values. Name them, reuse them, compose them with `/`:

```python
tokenize = pipe // str.split / flatten
clean    = pipe // str.strip // str.lower
join     = pipe / " ".join

process  = tokenize / clean / join

["  Hello World  "] > process    # → "hello world"
["  FOO BAR BAZ  "] > process    # → "foo bar baz"
```

Test each piece independently. Compose freely.

---

## Writing steps

Any `def` function works as a pipeline step:

```python
def remove_stopwords(words):
    stopwords = {"the", "a", "an"}
    return [w for w in words if w not in stopwords]

sentences > pipe // str.split / flatten / remove_stopwords
```

When a step needs configuration, use a closure. The outer call captures configuration at build time; the inner function receives the value at fire time:

```python
def blur(sigma):
    def _blur(img):
        k = max(3, int(6 * sigma) | 1)
        return cv2.GaussianBlur(img, (k, k), sigma)
    return _blur

def above(threshold):
    return lambda x: x > threshold

pipe / blur(5.0)      # pre-configured step
pipe @ above(100)     # pre-configured predicate
```

---

## Utils

### Sequence

```python
pipe / flatten                     # one level: [[1,2],[3,4]] → [1,2,3,4]
pipe / flatten_deep                # any depth: [1,[2,[3]]]   → [1,2,3]
pipe / sort()                      # alphabetical
pipe / sort(key=len, reverse=True) # by length descending
pipe / unique                      # deduplicate preserving order
pipe / take(3)                     # [:3]  first 3 elements
pipe / take(3, None)               # [3:]  skip first 3
pipe / take(1, 5)                  # [1:5] elements 1 to 4
pipe / take(None, None, -1)        # [::-1] reverse
pipe / chunk(2)                    # [[1,2],[3,4],[5]]
pipe / window(2)                   # [(1,2),(2,3),(3,4)]
pipe / group(key)                  # → dict grouped by key function
```

### Dict and object access

```python
users   > pipe // field("name")            # extract dict key
users   > pipe // field("age", default=0)  # with fallback
objects > pipe // attr("created_at")       # extract object attribute
```

### Fork utilities

```python
pipe / twist(2)                            # branch-major → item-major
pipe / named(["micro", "meso", "macro"])   # flat list → named dict
```

### Predicates for `@`

```python
pipe @ instance(str)               # isinstance check
pipe @ matching("^[A-Z]")          # substring or regex match
pipe @ having(status="active")     # dict key/value match
```

### Debug

```python
pipe / tap(print)                           # print and pass through
pipe / tap(lambda x: print("after:", x))   # with label
pipe / tap(log_to_file)                     # any side effect
```

---

## Patterns

### Growing state with dicts

For pipelines where each step enriches a shared state, pass a dict and grow it at each step. The convention: every step returns `{**state, "new_key": value}`.

```python
def load(state):
    return {**state, "img": cv2.imread(state["path"])}

def preprocess(state):
    gray = cv2.cvtColor(state["img"], cv2.COLOR_BGR2GRAY)
    return {**state, "gray": gray}

def segment(state):
    return {**state, "letters": find_letters(state["gray"])}

{"path": "image.jpg"} > pipe / load / preprocess / segment
# → {"path": ..., "img": ..., "gray": ..., "letters": [...]}
```

Each step reads what it needs, adds what it produces, passes everything forward. Nothing is lost. For type safety and autocomplete, use a dataclass with `dataclasses.replace` instead — same pattern, typed.

### Fork → twist → named

A fork produces results in branch-major order: all results of branch A, then all of branch B. `twist` reorders them to item-major: all branch results for item 0, then item 1, and so on. `named` then restores meaning to the flat list.

```python
energy_before = pipe // sobel_energy
energy_after  = pipe // (probe_blur / sobel_energy)

bands > pipe / dict.values / list
      / (energy_before + energy_after)
      / twist(2)                          # [[e0,pe0], [e1,pe1], [e2,pe2]]
      // divide                           # [ratio0, ratio1, ratio2]
      / named(["micro", "meso", "macro"]) # {"micro": r0, "meso": r1, "macro": r2}
```

The physical model lives in the operator structure — two energy measurements per band, one ratio each.

### Preserving a value across a transformation

Use `pipe` as the identity branch in a fork to carry a value forward untouched:

```python
result = data > pipe / step1 / (transform + pipe) / merge
#                                            ↑ value after step1, unchanged
```

### Error handling

Handle errors where they belong — inside the function that knows what failure means, or around the whole pipeline:

```python
# inside the function — owns its own error contract
def parse(x):
    try:
        return int(x)
    except ValueError:
        return 0

# around the pipeline — one place for the whole flow
try:
    result = data > pipe / step1 / step2 / step3
except ValueError as e:
    result = fallback
```

---

## Installation

```
pip install miniplumber
```

```python
from miniplumber import pipe                              # minimum
from miniplumber import pipe, flatten, sort, field, tap  # with utilities
from miniplumber import *                                 # everything
```

### Package structure

```
miniplumber/
    __init__.py     # re-exports everything
    core.py         # Pipeline class and pipe sentinel — zero dependencies
    utils.py        # flatten, sort, twist, named, field, and friends
```

`core.py` is self-contained. Copy just that file if you want the pipeline with no utilities.