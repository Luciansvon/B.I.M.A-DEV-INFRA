# Earlier-Session Source Addendum — 2026-09-08

This file captures **30 additional unique sources** used in earlier turns of the same GitHub research session, before the 130-source deep pass documented in [`SOURCES-2026-09-08.md`](./SOURCES-2026-09-08.md).

**Session total:** 160 unique retained/reviewed sources.

- Main deep-pass ledger: 130
- Earlier-session addendum: 30

Duplicates already present in the 130-source ledger are intentionally not repeated here.

---

# Reddit / community additions — 17

**SR001** — GitHub community: using Actions for scheduled/general automation beyond build.  
https://www.reddit.com/r/github/comments/1s7zaw5/i_just_discovered_github_actions_and_i_love_it_3/

**SR002** — ClaudeWorkflows: adversarial AI code-review workflow using multiple models/agents.  
https://www.reddit.com/r/ClaudeWorkflows/comments/1vz22qx/workflow_adversarial_ai_code_review_workflow_for/

**SR003** — ClaudeWorkflows: automated proof gate for AI-generated work.  
https://www.reddit.com/r/ClaudeWorkflows/comments/1ubrr4i/workflow_automated_proof_gate_for_aigenerated/

**SR004** — DevOps: enforcing/version-bump automation through CI.  
https://www.reddit.com/r/devops/comments/1jayyg0/

**SR005** — GitHub community: scheduled Actions timing/delay limitations.  
https://www.reddit.com/r/github/comments/1s8ossx/is_there_any_way_to_triger_github_actions_faster/

**SR006** — CI/CD community: sending failed GitHub Actions workflow notifications to Discord.  
https://www.reddit.com/r/cicd/comments/1v1l8la/i_kept_missing_failed_github_actions_workflows_so/

**SR007** — DevOps: lesson on testing/promoting the same CI artifact rather than rebuilding it.  
https://www.reddit.com/r/devops/comments/1uaafd5/reddit_taught_me_why_my_ci_pipeline_was_wrong/

**SR008** — AI Eval community: what practitioners evaluate for LLMs in CI/CD.  
https://www.reddit.com/r/AIEval/comments/1qjtq3m/what_do_you_guys_test_llms_in_cicd/

**SR009** — GitHub Copilot community: practical experience assigning Issues/tasks to coding agents and reviewing resulting PRs.  
https://www.reddit.com/r/GithubCopilot/comments/1twyni7/with_all_the_talk_about_people_leaving_copilot/

**SR010** — GitHub community: Issues/Projects workflow and task granularity discussion.  
https://www.reddit.com/r/github/comments/1v4iglk/github_projects_workflow/

**SR011** — GitHub community: self-hosted Actions runners and persistent caching/build-time improvements.  
https://www.reddit.com/r/github/comments/1rhpavo/we_cut_github_actions_build_times_by_6x_with/

**SR012** — GitHub community: Codespaces usage/benefit discussion.  
https://www.reddit.com/r/github/comments/16bhsm2/

**SR013** — Self-hosted community: continuous deployment of Docker/self-hosted services from Git.  
https://www.reddit.com/r/selfhosted/comments/1lely9q/best_method_for_continuous_deployment_of_a_docker/

**SR014** — GitHub community: using GitHub for versioned Obsidian/notes/knowledge content and related caveats.  
https://www.reddit.com/r/github/comments/1f87fdj/

**SR015** — DevOps: centralized/reusable workflow versioning across many repositories.  
https://www.reddit.com/r/devops/comments/1qk63vg/how_do_you_version_independent_reusable_workflows/

**SR016** — GitHub community: large-file/Git-LFS limitations and pain points.  
https://www.reddit.com/r/github/comments/1bktp24/

**SR017** — GitHub community: repository backup strategies and why GitHub should not be the sole backup.  
https://www.reddit.com/r/github/comments/1rv49fi/github_backup_best_approach_suggestions/

---

# GitHub official additions — 10

**SG001** — Scheduling issue creation with GitHub Actions.  
https://docs.github.com/en/actions/tutorials/manage-your-work/schedule-issue-creation

**SG002** — GitHub Actions tutorials for managing work/Issues.  
https://docs.github.com/en/enterprise-cloud%40latest/actions/tutorials/manage-your-work

**SG003** — Automating Dependabot with GitHub Actions.  
https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/automate-dependabot-with-actions

**SG004** — GitHub Actions limits/reference, used when evaluating cache/job constraints.  
https://docs.github.com/en/actions/reference/limits

**SG005** — GitHub artifact attestations: provenance for build outputs.  
https://docs.github.com/en/actions/concepts/security/artifact-attestations

**SG006** — Repository rulesets.  
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets

**SG007** — Deployments and environments in GitHub Actions.  
https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

**SG008** — GitHub Codespaces prebuilds.  
https://docs.github.com/en/codespaces/prebuilding-your-codespaces/about-github-codespaces-prebuilds

**SG009** — Configuring Issue templates / Issue Forms.  
https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository

**SG010** — GitHub Pages documentation root.  
https://docs.github.com/en/pages

---

# External / ecosystem additions — 3

**SE001** — OpenAI Evals repository, used as an implementation reference for model/evaluation comparisons.  
https://github.com/openai/evals

**SE002** — Hugging Face Hub environment variables, including local cache configuration (`HF_HOME`, `HF_HUB_CACHE`).  
https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables

**SE003** — Hugging Face Hub cache management, used to verify that model snapshots can remain cached locally rather than being repeatedly uploaded/downloaded.  
https://huggingface.co/docs/huggingface_hub/guides/manage-cache

---

# Session accounting

```text
130  main deep-pass sources
+30  earlier-turn unique sources
---
160  total unique retained/reviewed sources in this session
```

The source files are intentionally split so the deep research pass remains auditable while the earlier conversation history is not silently rewritten after the fact.
