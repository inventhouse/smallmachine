SmallMachine
============

SmallMachine is a state machine engine that aims to be simple, powerful, and debuggable; these state machine instances work from a dictionary of states and associated rule lists.

States
------
States are simply dictionary keys (i.e. hashable), so they can be pretty much anything you want from simple strings to custom classes.  Instances only require a rules dictionary and a starting state.

The rules dictionary maps each state to a list of rule tuples, each of which includes a label, a test, an action, and a destination.  Rules associated with the special `...` (Ellipsis) state are implicitly added to all states' rules, and evaluated after explicit rules.

Rules and Evaluation
--------------------
Input is tested against the explicit rules for the current state plus the implicit rules from the `...` (Ellipsis) state.

As the rules are evaluated, a context dictionary is built; these keys and values are available to callable rule components as keyword arguments.  Context arguments available when rules are evaluated are: `machine`, `state`, `input_count`, `input`, and elements of the currently evaluating rule: `label`, `test`, `action`, and `dest`.

Each rule consists of a label, test, action, and destination, which work as follows:

- **Label:** Usually a string, used for identifying the "successful" rule when tracing.

- **Test:** Called with context arguments; if the result is truish, the rule succeeds, no other rules are tested.  If the test is not callable, it is compared (equal) to the input.

- **Action:** When a test succeeds, the action is called with context arguments, including `result` from the test above; the action's `response` will be included in the context arguments for the tracer and returned by this call.  If the action is not callable, it is returned as the response.

- **Destination:** Finally, the machine will transition to the destination state unless the destination is `...` (Ellipsis), usually used for self-transitions, but for advanced use-cases the action could modify the state directly (via `machine` in the context) to push/pop states, implement non-deterministic transitions, etc.

At the end of a successful transition, the internal and any custom tracer is called with a transition format and context arguments; if no rule succeeds, `ValueError` will be raised.

Tracing
-------
State machines can be very hard to debug if you can't track their operation and transitions, so the engine automatically traces each transition.  By default it keeps a `history` of 10 transitions that changed state ("loops" within a state are counted but only the last transition is retained); this is formatted into a traceback and added to any exceptions that may be raised to help understand "where the machine was."

State machine instances can also take a `tracer` argument that either enables built-in real-time printing of the transitions, or if it is callable, it will be called with a format and the transition context keyword arguments.

---

To Do
-----
- [x] Finish README
    - [x] Move most documentation here instead
- [ ] Examples
    - [x] sailing game
    - [ ] build zoom chat parser step-by-step
- [ ] Unit tests
- [ ] Package for PyPI

### Doneyard

---