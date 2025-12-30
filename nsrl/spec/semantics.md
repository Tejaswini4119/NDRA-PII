# NSRL Semantics

## Deterministic Evaluation
NSRL guarantees that for any given Input $I$ and Rule Set $R$, the Output $O$ is always identical.  $f(I, R) \to O$.
There are no random seeds, race conditions, or external state dependencies.

## Precedence & Conflict Resolution
When multiple rules match the same input:
1.  **Priority Score**: The rule with the highest numeric `priority` wins.
2.  **Lexicographical Order**: If priorities are equal, the Rule ID is used for stable tie-breaking (e.g., `RULE-A` beats `RULE-B`).

## Immutability
Rule execution is side-effect free. It cannot modify the input object or change global system state. It only emits a new signal object.

## Input Scope
Rules operate on:
1.  **Target Object**: The specific PII entity being evaluated (e.g., a credit card number object).
2.  **Context**: Global metadata about the file/request (e.g., Document Classification, Source System).

## Failure Modes
*   **Missing Field**: Evaluates to `False` (safe fail).
*   **Type Mismatch**: Evaluates to `False`.
*   **Malformed Rule**: Rejected at load time (Static Analysis).

