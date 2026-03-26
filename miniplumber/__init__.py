"""
miniplumber — a minimal functional pipeline for Python

    from miniplumber import pipe, flatten, field, sort

    result = records > (
        pipe
        @ having(status="active")
        // field("name")
        / sort()
        / " ".join
    )

Operators  (/ // @ + are same precedence — always left-to-right):

    /   pass whole value to func, or compose two pipelines
    //  map func over each element, dict value, or scalar
    @   filter elements  (keep where func(x) is truthy)
    +   fork into parallel pipelines        /  (pipe_a + pipe_b)  /
    >   fire the pipeline, return raw value

See README.md for full documentation.
"""

from miniplumber.core import pipe, Pipeline

from miniplumber.utils import (
    # flatten
    flatten,
    flatten_deep,
    # sequence
    sort,
    unique,
    keep,
    twist,
    named,
    chunk,
    window,
    group,
    # dict and object access
    field,
    attr,
    # predicates
    matching,
    having,
    # debugging
    tap,
)

__all__ = [
    # core
    'pipe',
    'Pipeline',
    # flatten
    'flatten',
    'flatten_deep',
    # sequence
    'sort',
    'unique',
    'keep',
    'twist',
    'named',
    'chunk',
    'window',
    'group',
    # dict and object access
    'field',
    'attr',
    # predicates
    'matching',
    'having',
    # debugging
    'tap',
]
