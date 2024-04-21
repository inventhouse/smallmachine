# SmallMachine: Copyright © 2021-2024 Benjamin Holt - MIT License

from collections import deque
from enum import Enum
import re


def statemachine(state=None, rules=None, debug=False, history=..., checkpoints=...):
    """Create a batteries-included state machine with convenience options.

    Returns a StateMachine pre-configured to reject unknown input and states; this is the most common way to set up a machine.  Optionally it can also have a verbose debugging tracer with configurable prefix added.

    History and checkpoints arguments will be passed on to the CheckpointTracer, see that for details.
    """

    tracers = []
    if debug is not False:
        dbg_args = {"prefix": debug} if debug is not True else {}
        dbg = PrefixTracer(**dbg_args)
        tracers.append(dbg)

    checkpoints_args = {"checkpoints": checkpoints} if checkpoints is not ... else {}
    history_args = {"history": history} if history is not ... else {}
    tracers.append(CheckpointTracer(**checkpoints_args, **history_args))
    tracer = MultiTracer(*tracers) if len(tracers) > 1 else tracers[0]
    return StateMachine(state, rules, tracer=tracer)
#####


###  Test Helpers  ###
class match_test(object):
    """Callable to match input with a regex and format a nice __str__."""
    def __init__(self, test_re_str):
        self.test_re = re.compile(test_re_str)

    def __call__(self, input, **_):
        return self.test_re.match(input)

    def __str__(self):
        return f"'{self.test_re.pattern}'.match(input)"


class search_test(object):
    """Callable to search input with a regex and format a nice __str__."""
    def __init__(self, test_re_str):
        self.test_re = re.compile(test_re_str)

    def __call__(self, input, **_):
        return self.test_re.search(input)

    def __str__(self):
        return f"'{self.test_re.pattern}'.search(input)"


class in_test(object):
    """Callable to test if input is in a collection and format a nice __str__."""
    def __init__(self, in_list):
        self.in_list = in_list

    def __call__(self, input, **_):
        return input in self.in_list

    def __str__(self):
        return f"input in {self.in_list}"
#####


###  Action Helpers  ###
class action_formatter:
    """Decorator to wrap an action callable and give it a nice __str__."""
    def __init__(self, action):
        self.action = action
    def __call__(self, *args, **kwds):
        return self.action(*args, **kwds)
    def __repr__(self):
        return f"{self.action.__name__}(**ctx)"
#####


###  State Machine Core  ###
class Tracepoint(Enum):
    # The formatter keys are all distinct so they can be aggregated with dict.update; StateMachine itself does this, or see CheckpointTracer for a more complex example
    INPUT = "{input_count}: {state}('{input}')"
    NO_RULES = "\t(No rules: {state})"  # Consider raising NoRulesError
    RULE = "  {label}: {test} -- {action} --> {dest}"
    RESULT = "  {label}: {result}"
    RESPONSE = "    {response}"
    NEW_STATE = "    --> {new_state}"
    UNRECOGNIZED = "\t(No match: '{input}')"  # Consider raising UnrecognizedInputError
    UNKNOWN_STATE = "\t(Unknown state: {new_state})"  # Consider raising UnknownStateError


class StateMachine(object):
    """State machine engine that makes minimal assumptions but includes some nice conveniences and powerful extensibitility.

    Public attributes can be manipulated after init; it is common to create the machine and set the rules after the ruleset has been defined, but more dynamic things are possible, for example a rule action could set the state machine's tracer to start or stop logging of the machine's operation.
    """

    def __init__(self, state=None, rules=None, tracer=None):
        """Create a state machine optionally with a starting state rules, and tracer; state and rules should be set before the machine is used.

        State is simply the starting state for the machine.

        The rules dictionary maps each state to a list of rule tuples, each of which includes a label, a test, an action, and a destination; more about rule elements in the __call__ documentation.

        Rules associated with the special '...' state are implicitly added to all states' rules, to be evaluated after explicit rules.

        Tracer is an optional callable that takes a tracepoint string and its associated values, and is called at critical points in the input processing to follow the internal operation of the machine.  A simple tracer can produce logs that are extremely helpful when debugging, see PrefixTracer for an example.  Tracepoints are distinct constants which can be used by more advanced tracers for selective verbosity, raising errors for unrecognized input or states, and other things.  Tracer values can be collected for later use; see ContextTracer.  Tracers can be stacked using MultiTracer.
        """
        # Starting state and rules can be set after init, but really should be set before using the machine
        self.state = state
        # rules dict looks like { state: [(label, test, action, new_state), ...], ...}
        self.rules = rules if rules is not None else {}
        self.tracer = tracer
        self.context = {}
        self._input_count = 0

    def _trace(self, tp, **vals):
        """Updates the context and calls an external tracer if one is set."""
        self.context["tracepoint"] = tp
        self.context.update(vals)
        if self.tracer:
            self.tracer(tp, **vals)

    def __call__(self, i):
        """Tests an input against the explicit rules for the current state plus the implicit rules from the '...' state.

        As the rules are evaluated, a context dictionary is built; these keys and values are available to callable rule components as keyword arguments.  Context arguments avalable when rules are evaluated are: input, input_count, state, and elements of the currently evaluating rule: label, test, action, and dest.

        Each rule consists of a label, test, action, and destination, which work as follows:

        - Label: string used for identifying the "successful" rule when tracing.

        - Test: if callable, it will be called with context arguments, otherwise it will be tested for equality with the input; if the result is truish, the rule succeeds and no other rules are tested and the result is added to the context.

        - Action: when a test succeeds, the action is evaluated and the response is added to the context and returned by this call.  If action callable, it will be called with context arguments, including 'result' from the test above; it is common for the action to have side-effects that are intended to happen when the test is met.  If it is not callable, the action literal will be the response.

        - Destination: finally, if destination is callable it will be called with context arguments, including 'result' and 'response' above, to get the destination state, otherwise the literal value will be the destination.  If the destination state is '...', the machine will remain in the same state (self-transition or "loop".)  Callable destinations can implement state push/pop for recursion, state exit/enter actions, non-deterministic state changes, and other interesting things.
        """
        self.context = {}
        self._input_count += 1
        self._trace(Tracepoint.INPUT, input_count=self._input_count, state=self.state, input=i)
        rule_list = self.rules.get(self.state, []) + self.rules.get(..., [])
        if not rule_list:
            self._trace(Tracepoint.NO_RULES, state=self.state)
        for l,t,a,d in rule_list:
            self._trace(Tracepoint.RULE, label=l, test=t, action=a, dest=d)
            result = t(**self.context) if callable(t) else t == i
            if result:
                self._trace(Tracepoint.RESULT, label=l, result=result)
                response = a(**self.context) if callable(a) else a
                self._trace(Tracepoint.RESPONSE, response=response)
                dest = d(**self.context) if callable(d) else d
                self._trace(Tracepoint.NEW_STATE, new_state=dest)
                if dest is not ...:
                    if dest not in self.rules:
                        self._trace(Tracepoint.UNKNOWN_STATE, new_state=dest)
                    self.state = dest
                return response
        else:
            self._trace(Tracepoint.UNRECOGNIZED, input=i)
            return None
#####


###  Exceptions  ###
class NoRulesError(RuntimeError):
    """Raised when when the current state has no explicit or implicit rules."""
    @classmethod
    def checkpoint(cls):
        def check(tracepoint, **ctx):
            if tracepoint == Tracepoint.NO_RULES:
                return "'{state}' does not have any explicit nor implicit rules".format(**ctx)

        return (check, cls)


class UnrecognizedInputError(ValueError):
    """Raised when input is not matched by any explicit or implicit rule in the current state."""
    @classmethod
    def checkpoint(cls):
        def check(tracepoint, **ctx):
            if tracepoint == Tracepoint.UNRECOGNIZED:
                return "'{state}' did not recognize {input_count}: '{input}'".format(**ctx)

        return (check, cls)


class UnknownStateError(RuntimeError):
    """Raised when a machine transitions to an unknown state."""
    @classmethod
    def checkpoint(cls):
        def check(tracepoint, **ctx):
            if tracepoint == Tracepoint.UNKNOWN_STATE:
                return "'{new_state}' is not in the ruleset".format(**ctx)

        return (check, cls)
#####


###  Tracing  ###
def PrefixTracer(prefix="T>", printer=print):
    """Prints tracepoints with a distinctive prefix and, optionally, to a separate destination than other output"""
    def t(tp, **vals):
        msg = f"{prefix} {tp.value.format(**vals)}" if prefix else tp.value.format(**vals)
        printer(msg)
    return t


class MultiTracer:
    """Combines multiple tracers; tracers list can be manipulated at any time to add or remove tracers."""
    def __init__(self, *tracers):
        self.tracers = list(tracers)

    def __call__(self, tp, **vals):
        for t in self.tracers:
            t(tp, **vals)


class CheckpointTracer(object):
    """Tracer that can check a wide variety of conditions and raise an error if one is met."""

    DEFAULT_CHECKPOINTS = (
        NoRulesError.checkpoint(), 
        UnrecognizedInputError.checkpoint(), 
        UnknownStateError.checkpoint(),
    )

    def __init__(self, checkpoints=(...,), history=10, compact=True):
        """Create a CheckpointTracer with customizable checkpoints, history depth, and compaction.

        Checkpoints is a list of tuples, each with a callable check function and an exception class to raise if the check function returns a message.  If ... is in checkpoints, the default checks will be inserted at that point in the list.  Defaults to check for the most common issues: NoRulesError, UnrecognizedInputError, and UnknownStateError.

        History is the number of previous transitions to keep in memory for context; if history is None or negative, the history will be unlimited.  Defaults to 10.

        Compact determines whether the tracer will compact loops in the trace history; if compact is True (default), the tracer will keep only the most recent transition in any state, and the number of loops will be noted in the traceback.
        """
        if not checkpoints:
            self.checkpoints = []
        elif ... in checkpoints:
            # Replace ... in checkpoints with the default checkpoints
            checkpoints = list(checkpoints)
            i = checkpoints.index(...)
            checkpoints[i:i+1] = self.DEFAULT_CHECKPOINTS
        self.checkpoints = list(checkpoints)  # List so it can be manipulated later if desired

        self.context = {}  # Simpler to keep our own context than to try to get a reference to the machine
        self.input_count = 0
        if history is None or history < 0:
            history = None  # Unlimited depth
        self.history = deque(maxlen=history)
        self.compact = compact

    ## Collect context & history
    def __call__(self, tracepoint, **values):
        values["tracepoint"] = tracepoint
        if tracepoint == Tracepoint.INPUT:
            if self.context:
                self.history.append(self.context)
            self.input_count += 1
            values["input_count"] = self.input_count
            self.context = values
        else:
            self.context.update(values)

        for check, err in self.checkpoints:
            msg = check(**self.context)
            if msg:
                trace_lines = "\n".join(self.format_trace())
                raise err(f"StateMachine Traceback (most recent last):\n{trace_lines}\n{err.__name__}: {msg}")

        if self.compact and tracepoint == Tracepoint.NEW_STATE:
            self._fold_loop()

    def _fold_loop(self):
        if not self.history:
            return

        latest = self.context
        previous = self.history[-1]
        if previous["state"] == latest["state"]:
            # We have looped
            if "loop_count" in previous:
                # If we are already compacting, fold
                latest["loop_count"] = previous["loop_count"] + 1
                self.history.pop()

            elif len(self.history) >= 2:
                p_previous = self.history[-2]
                if p_previous["state"] == latest["state"]:
                    # Start compacting loops on the third iteration
                    latest["loop_count"] = 2
                    self.history.pop()
                    self.history.pop()

    ## Formatting
    def format_trace(self):
        transitions = (*self.history, self.context)
        return [ self.format_transition(t) for t in transitions ]

    def format_transition(self, t):
        tp = t.get("tracepoint", "Tracepoint missing")
        if tp == Tracepoint.NEW_STATE:
            # Most transitions will be "complete"
            looped = "    ({loop_count} loops in '{state}' elided)\n".format_map(t) if "loop_count" in t else ""
            return looped + "{input_count}: {state}('{input}') > {label}: {result} -- {response} --> {new_state}".format(**t)
        if tp == Tracepoint.NO_RULES:
            # No rules has its own format
            return "{input_count}: {state} >> No rules".format(**t)
        if tp == Tracepoint.UNRECOGNIZED:
            # Unrecognized has its own format
            return "{input_count}: {state}('{input}') >> Unrecognized".format(**t)
        if tp == Tracepoint.UNKNOWN_STATE:
            # Unknown state has its own format
            return "{input_count}: {state}('{input}') >> Unknown state: {new_state}".format(**t)
        return f"PARTIAL: {str(t)}"  # If transition somehow does not have a known formatting, simply dump it for debugging  FIXME: do better
#####
