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

As the rules are evaluated, a context dictionary is built; these keys and values are available to callable rule components as keyword arguments.  Context arguments available when rules are evaluated are: `machine`, `state`, `input_count`, `input`, and elements of the currently evaluating rule: `label`, `test`, `action`, and `destination`.

Each rule consists of a label, test, action, and destination, which work as follows:

- **Label:** Usually a string, used for identifying the "successful" rule when tracing.

- **Test:** Called with context arguments; if the result is truish, the rule succeeds, no other rules are tested.  If the test is not callable, it is compared (equal) to the input.

- **Action:** When a test succeeds, the action is called with context arguments, including `result` from the test above; the action's `response` will be included in the context arguments for the tracer and returned by this call.  If the action is not callable, it is returned as the response.

- **Destination:** Finally, the machine will transition to the destination state unless the destination is `...` (Ellipsis), usually used for self-transitions, but for advanced use-cases the action could modify the state directly (via `machine` in the context) to push/pop states, implement non-deterministic transitions, etc.

At the end of a successful transition, the internal and any custom tracer is called with a transition format and context arguments; if no rule succeeds, `ValueError` will be raised.

Tracing
-------
State machines can be very hard to debug if you can't track their operation and transitions, so the engine automatically traces each transition.  By default it keeps a `history` of the last 10 transitions that changed state ("loops" within a state are counted but only the last transition is retained); this is formatted into a traceback and added to any exceptions that may be raised to help understand "where the machine was" and how it got there.

State machine instances can also take a `tracer` argument that either enables built-in real-time printing of the transitions, or if it is callable, it will be called with a format and the transition context keyword arguments.

More
----
### Reading the Code
The best way to really understand how it works is to read the code.  The implementation really is very small - just under 70 lines of code (plus another ~40 lines of comments and blanks) - and the core evaluation engine is under a dozen lines in the `try` block of `StateMachine.__call__`; I think most use-cases I've had for it were bigger than the StateMachine class itself.

The two trickiest aspects of Python I use are `for...else` to raise `ValueError` if no rule accepted the input, and `**context` to make a lot of different information available to tests and actions while allowing them to pluck out just what they need and ignore the rest.  For the second, it's important to understand how parameters in Python really work, particularly how "required" and "optional" parameters in a definition are distinct from "positional" and "keyword" arguments in a call.  I definitely recommend looking at the helpers and examples to see how useful this can be.

Note that there is only the `StateMachine` class, I found no use for "State" nor "Rule/Transition" classes, they just made things more complicated and less powerful; I'm puzzled that every other state machine module I've looked at on PyPI uses such constructs.

### Helpers
There is a `helpers.py` file with some useful "accessories", most of which help to make state machine traces and rulesets more readable; the `pretty` decorator is particularly interesting.

### Examples
#### Sailing Game
I've mainly used this engine (and its predecessors) to write parsers, but it's capable of _many_ other things, so I thought it would be fun to write the smallest interactive fiction ("text-based adventure") game I could come up with that is in any sense playable.

It uses game locations as its primary states, and their associated rules implement the actions the player can take.  While the state machine is mostly transition-action based, the `Location` class implements a simple enter-action pattern for room descriptions.

It also implements some actions for interacting with and testing the underlying machine.

Aside, not really related to the state machine, but I'm quite pleased with the `adlib` function for templating descriptions and other messages so the game is a _little_ more dynamic, check it out while you're looking at this example.

---

To Do
-----
- [ ] Examples dir
    - [ ] README (in examples dir or a section in the main readme?)
    - [x] sailing game
    - [ ] build zoom chat parser step-by-step
- [ ] Unit tests
- [ ] Package for PyPI

### Doneyard
- [x] Finish README
    - [x] Move detailed documentation here instead

---