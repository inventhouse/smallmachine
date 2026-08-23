# SmallMachine: Copyright © 2021-2026 Benjamin Holt - MIT License

from collections import deque
from itertools import chain
#####


###  State Machine Core  ###
class StateMachine(object):
    """A small state machine engine with powerful flexibility and a few nice conveniences.
    """

    def __init__(self, rules, state, tracer=False, history=10):
        """Create a state machine instance which can be called with an event and returns output from evaluating the rules for the current state.

        The rules dictionary maps each state to a list of rule tuples, each of which includes a label, a test, an action, and a destination.

        State is simply the starting state for the machine.

        Tracer can enable built-in printing of machine transitions; `True` enables tracing with a default prefix `T>`, anything else "truish" is used as a custom prefix.  Or if it is a callable it will be called a format and context arguments at the end of each transition.

        History is the number of state-changing transitions to retain for traceback; can be None for unlimited or 0 to disable.
        """
        # rules dict looks like { state: [(label, test, action, new_state), ...], ...}
        self.rules = rules
        self.state = state
        self.tracer = tracer
        self.history = deque(maxlen=history)
        self._event_count = 0


    @property
    def state(self):
        return self._state


    @state.setter
    def state(self, s):
        if s not in self.rules:
            raise RuntimeError(f"State '{s}' is not in the ruleset")
        self._state = s


    def __call__(self, event, /, **context):
        """Tests an event against the explicit rules for the current state plus the implicit rules from the ... (Ellipsis) state.  Any additional context arguments are passed on to rule components and tracers.

        As the rules are evaluated, the context dictionary is updated; all these keys and values are available to callable rule components as keyword arguments.  When a rule's test succeeds, its action is evaluated, the machine transitions, and the response is returned; if no rule succeeds, `ValueError` is raised.

        At the end of a successful transition, the internal and any custom tracer is called with a transition format and context arguments.
        """
        self._event_count += 1
        context.update({
            "machine": self, "state": self.state,
            "event_count": self._event_count, "event": event,
        })
        try:
            for l,t,a,d in chain(self.rules[self.state], self.rules.get(..., [])):
                context.update({"label": l, "test": t, "action": a, "destination": d})
                result = t(**context) if callable(t) else t == event
                if result:
                    response = a(result=result, **context) if callable(a) else a
                    if d is not ...:
                        self.state = d
                    self._trace(result=result, response=response, new_state=self.state, **context)
                    return response
            else:
                raise ValueError(f"State '{self.state}' did not recognize event {self._event_count}: '{event}'")
        except Exception as e:
            if self.history:
                trace_lines = "\n  ".join(self.build_trace())
                e.add_note(f"StateMachine Traceback (most recent last):\n  {trace_lines}")
            e.add_note(f"  {self._event_count}: {self.state}('{event}') > {context['label']} >> 💥\n{type(e).__name__}: {e}")
            raise


    _transition_fmt = "{event_count}: {state}('{event}') > {label}: {result} -- {response} --> {new_state}"
    def _trace(self, **transition):
        """Built-in tracing of transitions or calling of optional custom tracer, and building traceback history."""
        if self.tracer:
            if callable(self.tracer):
                self.tracer(self._transition_fmt, **transition)
            else:
                prefix = self.tracer if self.tracer is not True else "T>"
                print(f"{prefix} {self._transition_fmt.format(**transition)}")

        # History and Loop-Folding
        if self.history and transition["state"] == transition["new_state"]:
            transition["loop_count"] = 1
            prev = self.history[-1]
            if "loop_count" in prev and prev["state"] == transition["state"]:
                transition["loop_count"] += prev["loop_count"]
                self.history.pop()
        self.history.append(transition)


    def build_trace(self):
        """Returns formatted trace lines from the history of transitions."""
        for transition in self.history:
            lc = transition.get("loop_count", 0)
            if lc > 1:
                yield f"    ({lc - 1} loops in {transition['state']} elided)"
            yield self._transition_fmt.format(**transition)


    def status_dict(self):
        """Returns a dictionary of the machine's current status for inspecting or pretty-printing."""
        return {
            "Rules": self.rules,
            "State": self.state,
            "Trace": tuple(self.build_trace()),
        }
#####
