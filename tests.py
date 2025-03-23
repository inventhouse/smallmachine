#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SmallMachine Tests: Copyright © 2025 Benjamin Holt - MIT License

from unittest import main, TestCase
from unittest.mock import Mock

from smallmachine import StateMachine
from helpers import in_test, match_test, search_test, pretty
#####


###  StateMachine Tests  ###
class TestStateMachine(TestCase):
    def setUp(self):
        self.trace_line = None
        self.rules = {
            "A": [
                ("move to b", "b", "A-B", "B"),
            ],
            "B": [
                ("match 1", "1", "one", ...),
                ("match 2", "2", "two", ...),
                ("move to c", "c", "B-C", "C"),
            ],
            "C": [
                ("move to a", "a", "C-A", "A"),
            ],
        }
        self.machine = StateMachine(self.rules, "A", tracer=self.tracer, history=5)


    def tracer(self, _, **t):
        f = "{input_count}: {state}('{input}') > {label}: {result} -- {response} --> {new_state}"  # Copied the format so the tests don't depend on the implementation
        self.trace_line = f.format(**t)


    def test_state_machine(self):
        self.assertEqual(self.machine.state, "A")
        self.assertEqual(self.trace_line, None)

        response = self.machine("b")
        self.assertEqual(response, "A-B")
        self.assertEqual(self.machine.state, "B")
        expected = "1: A('b') > move to b: True -- A-B --> B"
        self.assertEqual(self.trace_line, expected)

        response = self.machine("1")
        self.assertEqual(response, "one")
        self.assertEqual(self.machine.state, "B")
        expected = "2: B('1') > match 1: True -- one --> B"
        self.assertEqual(self.trace_line, expected)

        response = self.machine("2")
        self.assertEqual(response, "two")
        self.assertEqual(self.machine.state, "B")
        expected = "3: B('2') > match 2: True -- two --> B"
        self.assertEqual(self.trace_line, expected)

        response = self.machine("c")
        self.assertEqual(response, "B-C")
        self.assertEqual(self.machine.state, "C")
        expected = "4: B('c') > move to c: True -- B-C --> C"
        self.assertEqual(self.trace_line, expected)

        response = self.machine("a")
        self.assertEqual(response, "C-A")
        self.assertEqual(self.machine.state, "A")
        expected = "5: C('a') > move to a: True -- C-A --> A"
        self.assertEqual(self.trace_line, expected)


    def test_state_machine_state_check(self):
        with self.assertRaises(RuntimeError):
            self.machine.state = "invalid state"
        self.machine.state = "B"  # Assigning valid state should work
        self.assertEqual(self.machine.state, "B")


    def test_state_machine_unrecognized(self):
        with self.assertRaises(ValueError):
            self.machine("invalid input")


    def test_state_machine_history(self):
        self.machine("b")
        self.machine("1")
        self.machine("2")
        self.machine("c")
        self.machine("a")
        self.assertEqual(len(self.machine.history), 4)  # One loop in B should be folded
        expected_history = [
            {"input_count": 1, "state": "A", "input": "b", "label": "move to b", "result": True, "response": "A-B", "new_state": "B"},
            # {"input_count": 2, "state": "B", "input": "1", "label": "match 1", "result": True, "response": "one", "new_state": "B"},  # Folded away
            {"input_count": 3, "state": "B", "input": "2", "label": "match 2", "result": True, "response": "two", "new_state": "B", "loop_count": 2},
            {"input_count": 4, "state": "B", "input": "c", "label": "move to c", "result": True, "response": "B-C", "new_state": "C"},
            {"input_count": 5, "state": "C", "input": "a", "label": "move to a", "result": True, "response": "C-A", "new_state": "A"},
        ]
        for i, expected in enumerate(expected_history):
            transition = self.machine.history[i]
            transition = {k: v for k, v in transition.items() if k in expected}
            self.assertEqual(transition, expected, f"History transition {i} does not match expected.")


    def test_state_machine_callables(self):
        a_test = Mock(return_value=True)
        a_action = Mock(return_value="A-B")
        trace = Mock()
        rules = {
            "A": [
                ("test a", a_test, a_action, "B"),
            ],
            "B": [],
        }
        machine = StateMachine(rules, "A", tracer=trace)
        machine("a")

        expected = dict(
            machine=machine,
            state="A",
            input_count=1,
            input="a",
            label="test a",
            test=a_test,
            action=a_action,
            destination="B",
        )
        a_test.assert_called_once_with(**expected)

        expected = dict(
            result=True,
            machine=machine,
            state="A",
            input_count=1,
            input="a",
            label="test a",
            test=a_test,
            action=a_action,
            destination="B",
        )
        a_action.assert_called_once_with(**expected)

        expected = dict(
            result=True,
            response="A-B",
            new_state='B',
            machine=machine,
            state="A",
            input_count=1,
            input="a",
            label="test a",
            test=a_test,
            action=a_action,
            destination="B",
        )
        trace.assert_called_once_with(StateMachine._transition_fmt, **expected)
#####


###  Main  ###
if __name__ == "__main__":
    main()
#####