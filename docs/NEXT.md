# Next implementation and activation steps

1. Complete hosted validation of the experimental `bima-infra` Dagger module and retain the combined evidence plus native/Dagger parity result. Keep local Dagger, Azure Pipelines, and GitLab CI deferred.
2. Exercise `repository-audit.yml` from a separate fixture repository using the same reviewed SHA for both pins. Do not label the module stable before this evidence exists.
3. Activate the `main` ruleset after the final hosted run. Require workflow lint and both platform audit checks, prevent force pushes/deletion, and choose a solo-maintainer review/bypass policy. Add repository-level SHA pin enforcement after verifying Actions compatibility.
4. Decide the license for this infrastructure repository. A public repository does not by itself provide an explicit reusable code license. Do not inherit another project's license without an owner decision.
5. Implement `research-update` and `workflow-audit` skills described in the retained governance research, with bounded procedures and validators. A procedure document must not claim to enforce repository settings.
6. Integrate one real consumer through pinned workflow plus policy, retain its evidence, and add a lightweight project registry entry. Keep project source and application-specific architecture in that project.
7. Choose the next reusable module from a demonstrated consumer need: build/test adapter, benchmark result processing, or release evidence. Review current research and contracts before expanding architecture. Keep the general evidence schema open until at least one additional module supplies concrete requirements.
