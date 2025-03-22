# SmallMachine Helpers: Copyright © 2025 Benjamin Holt - MIT License

from functools import update_wrapper
import inspect
import re
#####


###  Helpers  ###
class in_test(object):
    """Callable to test if input is in a collection and format a nice __str/repr__."""
    def __init__(self, *in_list):
        self.in_list = in_list

    def __call__(self, input, **_):
        return input in self.in_list

    def __str__(self):
        return f"input in {self.in_list}"

    def __repr__(self):
        return f"<test input in {self.in_list}>"


class match_test(object):
    """Thin wrapper around re.match to format a nice __str/repr__."""
    def __init__(self, test_re_str):
        self.test_re = re.compile(test_re_str)

    def __call__(self, input, **_):
        return self.test_re.match(input)

    def __str__(self):
        return f"'{self.test_re.pattern}'.match(input)"

    def __repr__(self):
        return f"<test '{self.test_re.pattern}'.match(input)>"


class search_test(object):
    """Thin wrapper around re.search to format a nice __str/repr__."""
    def __init__(self, test_re_str):
        self.test_re = re.compile(test_re_str)

    def __call__(self, input, **_):
        return self.test_re.search(input)

    def __str__(self):
        return f"'{self.test_re.pattern}'.search(input)"

    def __repr__(self):
        return f"<test '{self.test_re.pattern}'.search(input)>"


class pretty:
    """Wrap a callable and give it a nice __str/repr__; not needed if it already prints nicely"""
    def __init__(self, c, name=None):
        self._callable = c
        self._name = name or c.__name__
        self._sig = inspect.signature(c)
        update_wrapper(self, c)

    def __call__(self, *args, **kwargs):
        return self._callable(*args, **kwargs)

    def __str__(self):
        return f"{self._name}{self._sig}"

    def __repr__(self):
        return f"<callable {self._name}{self._sig}>"
#####
