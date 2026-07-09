# Appendix: Token comparison between Hermes and our own QA agent service

## Purpose

This appendix summarizes the six comparison runs in which:

- Hermes was run with a stronger model environment, in the collected data `gpt-5.5`
- our own solution was run via `ai_agents` with `qa-agent-service` as the agent backend
- token consumption for our own solution was collected from exported JSON files per scenario

This appendix should be read together with [Hermes report scenarios 1-6](../hermes-report-scenarios-1-6/), which is left unchanged and serves as the source document for the Hermes side of the comparison.

## Data basis and scope

For Hermes, the measurable figures already compiled in [Hermes report scenarios 1-6](../hermes-report-scenarios-1-6/) are used:

- `Input tokens`
- `Output tokens`
- `Reasoning tokens`
- `Cache read`
- `API calls`
- `Tool calls`

For our own solution, the token fields now present in the JSON exports from `ai_agents` are used:

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`

This means that the comparison is not fully symmetric. The Hermes table describes session-level and orchestration-adjacent usage in the Hermes track, while our own table describes model tokens consumed in the `qa-agent-service` calls. Hermes cache reads, reasoning tokens, and other internal overhead therefore have no direct equivalent in our own export. Even so, the comparison is valuable because it shows order of magnitude, iteration patterns, and which parts of our own flow drive token cost.

## Scenario overview

All six runs of our own solution followed the same practical pattern:

- `max_rounds = 10`
- `max_feedback_messages = 12`
- `max_feedback_per_agent_pair = 4`
- actual `iterations = 5`
- actual `total_feedback_messages = 4`
- actual feedback direction: `Review Agent -> Test Design Agent`

This means that all runs stopped after four backtracking rounds between the Review Agent and the Test Design Agent, even though the global round limit was higher.

## Table 1: Hermes and our own solution per scenario

| Scenario | Hermes model | Hermes input + output | Our total tokens | Ratio our/Hermes I/O | Difference our - Hermes I/O |
|---|---|---:|---:|---:|---:|
| 1. Login and registration | gpt-5.5 | 123322 | 71362 | 0.579 | -51960 |
| 2. E-commerce checkout | gpt-5.5 | 125096 | 71430 | 0.571 | -53666 |
| 3. Password reset | gpt-5.5 | 65438 | 53451 | 0.817 | -11987 |
| 4. Support tickets | gpt-5.5 | 75112 | 66534 | 0.886 | -8578 |
| 5. Inventory management | gpt-5.5 | 139965 | 64305 | 0.459 | -75660 |
| 6. Course enrollment | gpt-5.5 | 122342 | 61162 | 0.500 | -61180 |
| **Total** | mixed | **651275** | **388244** | **0.596** | **-263031** |

### Interpretation

- Our own solution was below Hermes measurable input+output tokens in all six scenarios.
- This should not be interpreted as meaning that our solution is therefore "cheaper in every respect", because Hermes also reported reasoning tokens and very large cache reads that have no direct equivalent in our own export.
- What can be said, however, is that our `qa-agent-service` calls in this configuration were roughly 46 to 89 percent of Hermes measured input+output tokens depending on the scenario.

## Table 2: Our own solution per scenario

| Scenario | Run ID | Prompt tokens | Completion tokens | Total tokens | Token-carrying calls | Iterations | Feedback rounds |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1. Login and registration | 1 | 59211 | 12151 | 71362 | 11 | 5 | 4 |
| 2. E-commerce checkout | 2 | 59170 | 12260 | 71430 | 11 | 5 | 4 |
| 3. Password reset | 3 | 47185 | 6266 | 53451 | 11 | 5 | 4 |
| 4. Support tickets | 4 | 55585 | 10949 | 66534 | 11 | 5 | 4 |
| 5. Inventory management | 5 | 54502 | 9803 | 64305 | 11 | 5 | 4 |
| 6. Course enrollment | 6 | 51759 | 9403 | 61162 | 11 | 5 | 4 |

### Interpretation

- The run pattern was practically identical across all six scenarios.
- All runs reached the same number of iterations and the same number of feedback rounds.
- Token cost therefore varied mainly with scenario content and artifact size, not with different control settings.

## Table 3: Base round and extra cycles in our own solution

`Base round` refers to the first complete pass:

- Requirements Analyst
- first pass in Test Design Agent
- first pass in Review Agent

`Extra cycles` refers to the four subsequent loops between the Test Design Agent and the Review Agent.

| Scenario | Base round tokens | Extra cycles total | Average per extra cycle |
|---|---:|---:|---:|
| 1. Login and registration | 13127 | 58235 | 14558.75 |
| 2. E-commerce checkout | 13539 | 57891 | 14472.75 |
| 3. Password reset | 10505 | 42946 | 10736.50 |
| 4. Support tickets | 12648 | 53886 | 13471.50 |
| 5. Inventory management | 12199 | 52106 | 13026.50 |
| 6. Course enrollment | 11773 | 49389 | 12347.25 |

### Interpretation

- The first complete round cost roughly 10.5k to 13.5k tokens depending on scenario.
- The four extra cycles together cost roughly 43k to 58k tokens.
- One extra cycle cost on average roughly 10.7k to 14.6k tokens.
- In practice, it is therefore the backtracking loop between the Test Design Agent and the Review Agent that accounts for most of the cost growth.

## Table 4: Which steps cost the most in our own solution

Summed across scenarios 1 to 6:

| Part of the flow | Tokens | Share of total |
|---|---:|---:|
| Requirements Analyst | 11461 | 3.0% |
| Test Design Agent | 178868 | 46.1% |
| Review Agent | 197915 | 51.0% |
| **Total** | **388244** | **100%** |

### Interpretation

- The Requirements Analyst is relatively cheap and stable across scenarios.
- Almost the entire token cost lies in the Test Design Agent and Review Agent.
- The Review Agent is consistently the single most expensive part of the flow.

## Table 5: Growing cost within the same scenario

| Scenario | Test Design first -> last | Review first -> last |
|---|---|---|
| 1 | 4531 -> 7423 | 6714 -> 7879 |
| 2 | 4940 -> 7390 | 6693 -> 7827 |
| 3 | 3817 -> 5616 | 4715 -> 5891 |
| 4 | 4562 -> 6889 | 6192 -> 7369 |
| 5 | 4412 -> 6717 | 5878 -> 6955 |
| 6 | 4228 -> 6332 | 5648 -> 6742 |

### Interpretation

- Both the Test Design Agent and the Review Agent become more expensive with each additional cycle.
- This suggests that more context, more artifacts, and more prior feedback points are being sent into later prompts.
- The pattern fits the hypothesis of "growing context mass" better than the hypothesis of "loose agent chat" as the dominant cost cause.

## What is most likely costing tokens in our solution

Based on the six runs, the following conclusions can be drawn:

1. The orchestrator does not appear to be the major token cost.
   In these runs, orchestrator steps in the exported `stage_traces` have no token values and primarily function as routing and stop logic.

2. The large cost lies in repeated model calls in the Test Design Agent and Review Agent.
   Each extra cycle means those agents are called again, often with a larger input basis than in the previous round.

3. The initial requirements analysis is not the main problem.
   The Requirements Analyst accounts for only about 3 percent of total token consumption in the collected material.

4. Growing context seems to be a stronger explanation than "noisy agent dialogue".
   It is probably not free-form chat in itself that costs the most, but rather that requirements, test design, review findings, and earlier iterations are fed back into new prompts. Each new round therefore becomes slightly heavier than the previous one.

5. The feedback format is likely a key optimization point.
   Since all actual feedback in these runs went from the Review Agent to the Test Design Agent, this is the link that should be examined first if token cost is to be reduced.

## What more the collected data makes possible to analyze

The current data already makes several kinds of further analysis possible:

- compare token cost per scenario with scenario complexity
- measure how much each extra cycle costs in absolute terms
- analyze which agent roles drive the cost the most
- assess whether stop limits are mainly used as loop protection or whether they are more often reached as a "normal mode"
- compare total cost with end quality, for example Hermes total score versus our own total token sum
- compare how much observability our own solution provides in relation to its token cost

What still cannot be determined exactly from the current export is:

- exactly how much of the prompt consists of requirement text, prior test design, feedback, and other background data respectively
- exactly how much of it is "noise" compared with necessary working context

To go further on that question, the next step would be to log prompt size per component, for example:

- scenario text
- shared memory
- agent private memory
- prior test design
- review feedback
- system or agent directives

## Overall conclusion

The most interesting result from these six runs is that token consumption in our own solution does not primarily seem to be driven by the orchestrator or by general agent chat. It is instead driven by iterative rereading and reworking in the loop between the Test Design Agent and the Review Agent. This is also consistent with the literature's warning that multi-agent systems quickly become expensive when the same or growing context is passed between agents several times.

This means that the most important optimization question going forward is not only model choice, but context discipline:

- how much data is passed between steps
- how often it is passed
- and how much of that material is actually necessary in the next round

In practice, this suggests that the next improvement step should focus on better compression, more selective forwarding of feedback, and clearer boundaries around what the Test Design Agent and the Review Agent truly need to see in each new iteration.
