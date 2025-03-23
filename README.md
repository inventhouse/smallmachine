SmallMachine
============

SmallMachine is a state machine engine that aims to be simple, powerful, and debuggable; these state machine instances work from a dictionary of states and associated rule lists.

States
------
States are simply dictionary keys, so they can be pretty much anything (hashable) you want from simple strings to custom classes.  Instances only require a rules dictionary and a starting state.

The rules dictionary maps each state to a list of rule tuples, each of which includes a label, a test, an action, and a destination.  Rules associated with the special `...` (Ellipsis) state are implicitly added to all states' rules, and evaluated after explicit rules.

Rules and Evaluation
--------------------
Input is tested against the explicit rules for the current state plus the implicit rules from the `...` (Ellipsis) state.

As the rules are evaluated, a context dictionary is built; these keys and values are available to callable rule components as keyword arguments.  Context arguments available when rules are evaluated are: `machine`, `state`, `input_count`, `input`, and elements of the currently evaluating rule: `label`, `test`, `action`, and `destination`.

Each rule consists of a label, test, action, and destination, which work as follows:

- **Label:** Usually a string, used for identifying the "successful" rule when tracing.

- **Test:** Called with context arguments; if the result is truish, the rule succeeds, and no other rules are tested.  If the test is not callable, it is compared (equal) to the input.

- **Action:** When a test succeeds, the action is called with context arguments, including `result` from the test above; the action's `response` will be included in the context arguments for the tracer and returned by this call.  If the action is not callable, it is returned as the response.

- **Destination:** Finally, the machine will transition to the destination state unless the destination is `...` (Ellipsis), usually used for self-transitions, but for advanced use-cases the action could modify the state directly (via `machine` in the context) to push/pop states, implement non-deterministic transitions, etc.

At the end of a successful transition, the internal and any custom tracer is called with a transition format and context arguments; if no rule succeeds, `ValueError` will be raised.

Tracing
-------
State machines can be very hard to debug if you can't track their operation, so the engine automatically traces each transition.  By default it keeps a `history` of the last 10 transitions that changed state ("loops" within a state are counted but only the last is retained); this is formatted into a traceback and added to any exceptions that may be raised to help understand "where the machine was" and how it got there.

State machine instances can also take a `tracer` argument that either enables built-in real-time printing of the transitions, or if it is callable, it will be called with a format and the transition context keyword arguments.

More
----
### Reading the Code
The best way to fully understand how it works is to read the code.  The implementation really is very small - just under 70 lines of code (plus another ~40 lines of comments and blanks) - and the core evaluation engine is under a dozen lines in the `try` block of `StateMachine.__call__`; I think most use-cases I've had for it were bigger than the StateMachine class itself.

The two trickiest aspects of Python I use are `for...else` to raise `ValueError` if no rule accepted the input, and `**context` to make a lot of different information available to tests and actions while allowing them to pluck out just what they need and ignore the rest.  For the second, it's important to understand how parameters in Python actually work; particularly how "required" and "optional" parameters in a definition are distinct from "positional" and "keyword" arguments in a call.  I definitely recommend looking at the helpers and examples to see how useful this can be.

Note that there is only the `StateMachine` class, I found no use for "State" nor "Rule/Transition" classes, they just made things more complicated and less powerful; frankly I'm puzzled that every other state machine module I've looked at on PyPI uses such constructs.

### Helpers
There is a `helpers.py` file with some useful "accessories", most of which help to make state machine traces and rulesets more readable when (pretty) printed; the `pretty` decorator is particularly interesting.

### Examples
#### Smooth Sailing Game
See [smooth-sailing](Examples/smooth-sailing)

I've mainly used this engine (and its predecessors) to write parsers, but it's capable of _many_ other things, so I thought it would be fun to write the smallest interactive fiction ("text-based adventure") game I could come up with that is in any sense playable.

It uses game locations as its primary states, and their associated rules implement the actions the player can take.  While StateMachine is primarily transition-action based, the `Location` class implements a simple enter-action pattern for room descriptions and `look`.

It also implements some actions for interacting with and testing the underlying machine.

(Aside, not really related to the state machine, but I'm quite pleased with the `adlib` function for templating descriptions and other messages so the game is a _little_ more dynamic, check it out while you're looking at this example.)

#### Zoom Chat Parser
One of the things state machines excel at is parsing data that has some sort of structure.  This engine in particular has features that really help make developing a parser easier, and dare I say, fun; let's write one together.

##### Saved Zoom Chats
The video-meeting platform Zoom allows participants to send text messages to the group and each other; there is an option to save the chat to a file, however the format of the chat log is _extremely_ verbose, for example emoji reactions to messages appear like messages themselves, message threads are flattened, and other issues.

Here we'll write a parser that will re-thread the messages, roll-up reactions, and even do some filtering as well.

##### Step 0: Format and Input Fixture
See [zoom-chat-parser-0](Examples/zoom-chat-parser-0)

The first thing to do is look at the format of the data: is it actually structured enough to write a parser for?  How are segments delimited?  How do they relate?  Start to get some ideas for how to take the data apart.

It can be helpful to collect and/or construct a snippet of the data to be parsed that exercises different aspects of the format to work from; once we're at the point of running full-sized "real" data through our parser, we can add to this as we find things it doesn't represent.

```python
chat_lines = """
15:01:39 From Michael M to Everyone:
    When are we going to have AI run team summit?
15:01:45 From Jared R to Everyone:
    Anyone still remember NFTs?
...
"""
```
Looks like messages are introduced with a line consisting of a timestamp, from, and to, and the messages themselves are indented; reactions and threaded messages tie back to earlier messages with a prefix, we can work with this.

##### Step 1: Null Parser
See [zoom-chat-parser-1](Examples/zoom-chat-parser-1)

`diff -u Examples/zoom-chat-parser-0 Examples/zoom-chat-parser-1`

To get started, we'll build a minimal scaffold around this fixture to easily run it through a state machine instance that does nothing but trace every line.  That's it.

```
T> 1: start('') > null: True -- None --> start
T> 2: start('15:01:39 From Michael M to Everyone:') > null: True -- None --> start
T> 3: start('    When are we going to have AI run team summit?') > null: True -- None --> start
T> 4: start('15:01:45 From Jared R to Everyone:') > null: True -- None --> start
T> 5: start('    Anyone still remember NFTs?') > null: True -- None --> start
...
```

##### Step 2: Develop Tests and States
See [zoom-chat-parser-2](Examples/zoom-chat-parser-2)

`diff -u Examples/zoom-chat-parser-1 Examples/zoom-chat-parser-2`

Now that we have some input, a machine, and a way to run it, we can start building the tests we need to parse the input and the states we need to organize those tests; our parser begins to take shape.

```
T> 1: start('') > blank: <re.Match object; span=(0, 0), match=''> -- None --> start
T> 2: start('15:01:39 From Michael M to Everyone:') > header: <re.Match object; span=(0, 36), match='15:01:39 From Michael M to Everyone:'> -- None --> message
T> 3: message('    When are we going to have AI run team summit?') > line: <re.Match object; span=(0, 49), match='    When are we going to have AI run team summit?> -- None --> message_lines
T> 4: message_lines('15:01:45 From Jared R to Everyone:') > header: <re.Match object; span=(0, 34), match='15:01:45 From Jared R to Everyone:'> -- None --> message
T> 5: message('    Anyone still remember NFTs?') > line: <re.Match object; span=(0, 31), match='    Anyone still remember NFTs?'> -- None --> message_lines
```

Once it runs successfully over our input snippet, we can start running it over full chat logs and find cases we missed, add them to our fixture, and make our parser robust enough to process the "real" data.

Already we have a parser!  Sure, it doesn't _do_ anything with the data it parses yet, but we can read through the trace and watch it navigating the input.

##### Step 3: Data Model and Actions
See [zoom-chat-parser-3](Examples/zoom-chat-parser-3)

`diff -u Examples/zoom-chat-parser-2 Examples/zoom-chat-parser-3`

Some parsers are pure transformers and don't need a data model, their actions will just return modified versions of the input; this one, however, needs a threaded message model, actions to build that model from the input, and some helpers.  This is, of course, is about the hardest part, but the real magic was being able to work through all of the data navigation first, and now we can just focus on modeling and plumbing.

```
(ChatMessage(time_str='15:01:39',
             sender='Michael M',
             recipient='Everyone',
             message_lines=['When are we going to have AI run team summit?'],
             replies=[ChatMessage(time_str='15:01:47',
...
```

##### Step 4: Do Things with Our Data
See [zoom-chat-parser-4](Examples/zoom-chat-parser-4)

`diff -u Examples/zoom-chat-parser-3 Examples/zoom-chat-parser-4`

At this point we have raw input parsing into our data model; we can do whatever we want with it!  Here, we're going to do some filtering and format the threaded messages so they'll look good when re-posted in Slack.

```
_(15:01) *Michael M*:_
    When are we going to have AI run team summit?
    _(15:01) *Aaron S*:_
        We already do
        😂 1
```

And that is how we can go from a raw data format we haven't seen before to a full-fledged parser-transformer in a one-evening hack.

---

To Do
-----
- [ ] FIXME: don't fold until the third loop (eliding a single loop is just losing information)
- [x] Unit tests
    - [ ] Tests for helpers
- [ ] Package for PyPI

### Doneyard
- [x] Finish README
    - [x] Move detailed documentation here instead
- [x] Examples dir
    - [x] README (in examples dir or a section in the main readme?)
    - [x] Sailing game
    - [x] Build zoom chat parser step-by-step
        - [x] Add links to files

---