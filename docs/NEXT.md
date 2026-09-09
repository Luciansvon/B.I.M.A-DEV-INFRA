# Next implementation and activation steps

1. Complete Issue #3 P0 with the agent packet schema and failure packet generator. Keep its input bounded to canonical evidence plus relevant excerpts.
2. Keep closed PR #2 Dagger work deferred on its retained branch until the deterministic baseline is stable and a portability need is demonstrated.
3. Exercise `repository-audit.yml` from a separate fixture repository using the same reviewed SHA for both pins. Do not label the module stable before this evidence exists.
4. Activate the `main` ruleset after the final hosted run. Require workflow lint and both platform audit checks, prevent force pushes/deletion, and choose a solo-maintainer review/bypass policy. Add repository-level SHA pin enforcement after verifying Actions compatibility.
5. Decide the license for this infrastructure repository. A public repository does not by itself provide an explicit reusable code license. Do not inherit another project's license without an owner decision.
6. Integrate one real consumer through pinned workflow plus policy, retain its evidence, and add a lightweight project registry entry. Keep project source and application-specific architecture in that project.
