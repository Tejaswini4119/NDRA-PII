# NSRL Invariants

Safety properties that must hold true for ALL valid NSRL deployments.

1.  **Termination Guarantee**: All rule evaluations must complete in finite time $O(N)$ where N is number of conditions. No infinite loops.
2.  **Isolation**: Rules cannot read/write files, access network, or call external APIs.
3.  **Traceability**: Every output must contain the ID of the rule that produced it.
4.  **Schema Compliance**: All inputs and outputs must validate strictly against the contracts.
5.  **Version Stability**: A rule engine version $X$ must consistently interpret rules of version $X$.

