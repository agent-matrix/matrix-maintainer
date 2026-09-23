# Governed recursive improvement

Matrix Maintainer is the proposal/maintenance worker for system improvement. It
must never mutate Agent-Matrix production code, policy, routing, prompts, or
models directly from a live autonomous run.

The only permitted improvement pipeline is:

```
Evidence
  -> EvalReport
  -> Improvement hypothesis
  -> bounded candidate change
  -> MatrixLab sandbox
  -> AM-Bench + regression suites
  -> Guardian policy grant
  -> Treasury budget grant
  -> pull request
  -> human approval when capability-changing
  -> ordinary protected merge/deploy path
```

## Promotion criteria

A candidate is eligible to become a PR only when:

- its benchmark delta clears the configured threshold,
- protected safety cases have zero regressions,
- the result is reproducible,
- the candidate fits its improvement budget,
- target files are explicitly bounded.

Passing the gate **does not mean merge**. It only authorizes creation of a
reviewable PR. Capability-changing proposals require human approval.

This makes learning real while retaining corrigibility and provenance.
