# Verified Blueprint Coverage Rubric

## Primary Metric

```text
VBC = passed required checks / total required checks * 100
```

Both the one-prompt baseline and ArchitectOS must return the same structured blueprint envelope. Each check produces `pass`, `fail`, or `invalid`. Invalid checks count as failures.

## Core Checks

| ID | Verification rule | Pass condition |
|---|---|---|
| VBC-01 | Requirement implementation coverage | Every functional requirement links to at least one architecture component or API operation. |
| VBC-02 | Requirement test coverage | Every functional requirement links to at least one test case. |
| VBC-03 | Protected-operation coverage | Every non-public operation declares authentication and an authorization rule. |
| VBC-04 | Entity reference integrity | Every entity referenced by an API operation or component exists in the data model. |
| VBC-05 | Measurable NFR coverage | Every NFR contains a numeric or objectively decidable target and a verification method. |
| VBC-06 | Reference validity | Every referenced requirement, component, entity, operation, and test ID resolves. |
| VBC-07 | Negative-test coverage | Authentication, authorization, validation, and relevant conflict paths have negative tests. |
| VBC-08 | Case-obligation coverage | The blueprint represents each obligation declared for its evaluation case. |

## Critical Findings

The following conditions create a critical finding and prevent a `ready` verdict regardless of the aggregate score:

- A protected write operation has no authentication.
- A multi-user operation has no authorization boundary.
- A payment or state-changing retry path has no idempotency strategy when the case requires it.
- A multi-tenant case has no tenant-isolation rule.
- A sensitive-data case lacks access control or retention handling required by the case.

## Case Scoring

For each case:

1. Run VBC-01 through VBC-07.
2. Run one VBC-08 check for every case-specific obligation.
3. Report passed checks, total checks, VBC percentage, and critical findings.
4. Record structured-output validity, runtime, model calls, and approximate cost separately.

## Aggregate Reporting

Report:

- Macro-average VBC across all ten cases
- Per-case VBC without exclusions
- Total unresolved critical findings
- Structured-output validity rate
- Median runtime and approximate cost
- The challenging case as a separate result

No claim of superiority should be made solely from the aggregate score if the agent solution introduces more unresolved critical findings than the baseline.
