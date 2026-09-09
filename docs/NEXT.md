# Next implementation and activation steps

1. Review and merge the validated Task command contract in PR #4; retain its local and hosted evidence record.
2. Continue Issue #3 P0 sequentially: `prek`, action-validator, pinact, zizmor, then canonical evidence and the agent packet. Add one bounded tool increment at a time with measured value.
3. Keep PR #2 Dagger work draft/deferred until the deterministic baseline is stable and a portability need is demonstrated.
4. Exercise `repository-audit.yml` from a separate fixture repository using the same reviewed SHA for both pins. Do not label the module stable before this evidence exists.
5. Activate the `main` ruleset after the final hosted run. Require workflow lint and both platform audit checks, prevent force pushes/deletion, and choose a solo-maintainer review/bypass policy. Add repository-level SHA pin enforcement after verifying Actions compatibility.
6. Decide the license for this infrastructure repository. A public repository does not by itself provide an explicit reusable code license. Do not inherit another project's license without an owner decision.
7. Integrate one real consumer through pinned workflow plus policy, retain its evidence, and add a lightweight project registry entry. Keep project source and application-specific architecture in that project.
