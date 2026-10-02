# V232 Persistent Worker

The project cannot honestly promise that one ChatGPT turn, one process, or one GitHub Actions job will run forever. GitHub-hosted jobs have a six-hour execution limit, while a workflow run has a larger overall limit. These are platform limits, not something project code should bypass.

V232 solves the engineering problem differently: make progress durable.

## Model

TASK QUEUE -> CHECKPOINT -> JOURNAL -> CLEAN STOP -> RESUME

Every task has a stable ID, kind, payload, status, attempt count, timestamps, and result/error.

The worker loads the previous checkpoint, adds tasks, works only until a configurable wall-clock budget, checkpoints before and after every task, stops cleanly, and resumes unfinished work on the next invocation.

A crash therefore loses at most the currently executing atomic task, not the entire research session.

## Brain-project use

The future pipeline can split expensive work into independent tasks: source acquisition, schema inspection, target extraction, topology verification, exact-coordinate verification, morphology matching, circuit construction, simulation, and regression/evidence checks.

V232 gives all of those stages one durable execution substrate.

## Safety boundary

Unknown task types fail closed. The worker never marks unavailable work DONE.

## Expansion

New source adapters can register task kinds without changing the checkpoint format. The same worker can therefore grow from four target neurons to larger circuits while preserving historical evidence and restartability.
