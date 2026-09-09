# Next implementation and activation steps

1. Complete the bounded action-validator increment from Issue #3 by merging PR #6 after its final hosted run.
2. Continue Issue #3 P0 sequentially with pinact, then zizmor, canonical evidence, and the agent packet. Add one bounded tool increment at a time with measured value.
3. Keep closed PR #2 Dagger work deferred on its retained branch until the deterministic baseline is stable and a portability need is demonstrated.
4. Exercise `repository-audit.yml` from a separate fixture repository using the same reviewed SHA for both pins. Do not label the module stable before this evidence exists.
5. Activate the `main` ruleset after the final hosted run. Require workflow lint and both platform audit checks, prevent force pushes/deletion, and choose a solo-maintainer review/bypass policy. Add repository-level SHA pin enforcement after verifying Actions compatibility.
6. Decide the license for this infrastructure repository. A public repository does not by itself provide an explicit reusable code license. Do not inherit another project's license without an owner decision.
7. Integrate one real consumer through pinned workflow plus policy, retain its evidence, and add a lightweight project registry entry. Keep project source and application-specific architecture in that project.
