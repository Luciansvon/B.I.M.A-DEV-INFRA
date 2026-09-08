# Source Ledger — Agent Governance / Skills — 2026-09-08

**Scope:** `AGENTS.md`, Agent Skills / `SKILL.md`, repository instructions, hooks, deterministic enforcement, context management, skill evaluation, multi-agent structure, and cross-agent portability for B.I.M.A-DEV-INFRA.

**Retained relevant sources:** **69**

The list intentionally mixes community reports with official specifications/docs and real repositories. Community reports are evidence of practical behavior and failure modes, not authoritative platform specifications.

---

# Search themes

- AGENTS.md vs SKILL.md
- Claude Code CLAUDE.md vs Skills
- GitHub Copilot Agent Skills
- Codex `.agents/skills`
- Agent Skills open standard
- repository instruction best practices
- context bloat / progressive disclosure
- skill testing / skill evals
- hooks vs prompt rules
- deterministic agent governance
- prompt instruction compliance failures
- coding agent security and least privilege
- real repositories combining AGENTS.md and skills
- GitHub Copilot hook lifecycle and preToolUse

---

# A. Community / Reddit — 37 sources

**C01 — ClaudeWorkflows: SKILL.md for repeatable git/development workflows**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1uo4b0h/workflow_streamlining_agentic_coding_with_skillmd/

**C02 — ClaudeCode: Agent Engineering 101 — AGENTS.md, Skills, MCP**  
https://www.reddit.com/r/ClaudeCode/comments/1rwkbkm/agent_engineering_101_a_visual_guide_agentsmd/

**C03 — GitHubCopilot: custom Copilot Agent Skill generator discussion and quality criticism**  
https://www.reddit.com/r/GithubCopilot/comments/1q8oad6/made_a_generator_for_custom_copilot_agent_skills/

**C04 — ClaudeWorkflows: delegating coding work to Codex through AGENTS.md**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1v1xfhh/workflow_claude_code_workflow_delegating_coding/

**C05 — GitHubCopilot: Agent Skills support in VS Code / agentskills.io**  
https://www.reddit.com/r/GithubCopilot/comments/1ppzu5v/agent_skills_now_in_vs_code/

**C06 — GitHubCopilot: practical first skills; code review skill as recurring workflow**  
https://www.reddit.com/r/GithubCopilot/comments/1vnyvi0/just_built_my_first_ai_agent_skill_in_vs_code/

**C07 — GitHubCopilot: discussion seeking a standardized agentic repository blueprint**  
https://www.reddit.com/r/GithubCopilot/comments/1u7oidr/is_there_a_proven_blueprint_or_standardized/

**C08 — GitHubCopilot: testing Agent Instructions, Skills and Custom Agents with evals**  
https://www.reddit.com/r/GithubCopilot/comments/1t8cp8a/testing_agent_instructions_agent_skills_and/

**C09 — ClaudeWorkflows: structured development workflow with AGENTS.md and rigorous testing**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1vcmmd2/workflow_structured_development_workflow_for_ai/

**C10 — ClaudeWorkflows: phase-wise AI-assisted development and architectural integrity**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1vcpi9w/workflow_structured_aiassisted_development/

**C11 — GitHubCopilot: skill preloading/frontmatter semantics discussion**  
https://www.reddit.com/r/GithubCopilot/comments/1ur0zaq/does_the_skills_field_in_agent_frontmatter/

**C12 — ClaudeAI: Agent Engineering 101 cross-agent framing**  
https://www.reddit.com/r/ClaudeAI/comments/1rwkjo7/agent_engineering_101_a_visual_guide_agentsmd/

**C13 — ClaudeCode: differences between hooks, skills, plugins, CLAUDE.md and agents.md**  
https://www.reddit.com/r/ClaudeCode/comments/1tmq9kz/can_someone_explain_the_real_difference_between/

**C14 — ClaudeCode: community rule of thumb for CLAUDE.md vs skills vs MCP vs subagents**  
https://www.reddit.com/r/ClaudeCode/comments/1so9lme/skills_mcp_subagents_what_to_use_when/

**C15 — ClaudeAI: CLAUDE.md vs Skills vs slash commands vs plugins**  
https://www.reddit.com/r/ClaudeAI/comments/1ped515/understanding_claudemd_vs_skills_vs_slash/

**C16 — ClaudeCode: difference between Skills, subagents, CLAUDE.md and slash commands**  
https://www.reddit.com/r/ClaudeCode/comments/1o8t6xe

**C17 — ClaudeCode: CLAUDE.md best-practice discussion; keeping it lean**  
https://www.reddit.com/r/ClaudeCode/comments/1riwy13/claudemd_best_practices/

**C18 — ClaudeCode: community context/prompt engineering discussion**  
https://www.reddit.com/r/ClaudeCode/comments/1v88lap/question_to_community_can_we_share_some_more_tips/

**C19 — ClaudeAI: September 2026 CLAUDE.md vs skills questions**  
https://www.reddit.com/r/ClaudeAI/comments/1w8gadi/claude_md_and_skills_questions/

**C20 — LocalLLaMA: coding agents wasting context while orienting in codebases**  
https://www.reddit.com/r/LocalLLaMA/comments/1rr5fo5/why_ai_coding_agents_waste_half_their_context/

**C21 — ClaudeCode: CLAUDE.md compliance failures; recommendation for deterministic mechanisms**  
https://www.reddit.com/r/ClaudeCode/comments/1t3fvf9/whats_even_the_point_of_claudemd/

**C22 — LLM: AGENTS.md / CLAUDE.md as persistent context vs skills as dynamic context**  
https://www.reddit.com/r/LLM/comments/1qtlizp/whats_the_difference_between_skillsmd_agentsmd/

**C23 — ClaudeCode: best practices; warning against very long CLAUDE.md files**  
https://www.reddit.com/r/ClaudeCode/comments/1nris9w

**C24 — ClaudeCode: why skills vs putting everything in AGENTS.md; context/reuse discussion**  
https://www.reddit.com/r/ClaudeCode/comments/1prjg62/why_are_skills_way_better_than_putting_them_in/

**C25 — ClaudeWorkflows: deterministic PreToolUse hooks to prevent agent drift**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1v06i54/workflow_enforce_claude_code_rules_with/

**C26 — ClaudeWorkflows: leaner CLAUDE.md plus deterministic hooks**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1vylfly/workflow_leveraging_hooks_for_deterministic/

**C27 — ClaudeAI: moving strict rules from CLAUDE.md into hooks**  
https://www.reddit.com/r/ClaudeAI/comments/1ucnasw/i_stopped_writing_rules_in_claudemd_and_started/

**C28 — ClaudeCode: hook fired but model still ignored non-blocking guidance**  
https://www.reddit.com/r/ClaudeCode/comments/1uzwqnb/help_with_claude_not_complying_with_hooks/

**C29 — ClaudeWorkflows: self-correcting PreToolUse / Stop hook enforcement**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1v205k3/workflow_enforcing_claudemd_rules_with/

**C30 — ClaudeWorkflows: deterministic blocking of unwanted code writes**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1ushoju/workflow_deterministic_code_enforcement_blocking/

**C31 — ClaudeWorkflows: separating mandatory rules (hooks) from contextual guidance (skills)**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1vq05ol/workflow_designing_robust_claude_code_agents/

**C32 — ClaudeWorkflows: blocking file access and dangerous commands with PreToolUse**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1volx5w/workflow_enforcing_deterministic_control_using/

**C33 — ClaudeWorkflows: why blocking hooks beat CLAUDE.md for strict control**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1ud4x3k/workflow_enforcing_rules_with_claude_why_hooks/

**C34 — ClaudeWorkflows: external scripted hooks and verification instead of self-assessment**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1uf0c7r/workflow_enforcing_claude_code_rules_with/

**C35 — ClaudeWorkflows: data-driven conversion of frequently violated rules into hooks**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1vz90jc/workflow_enforcing_claude_code_rules_with/

**C36 — ClaudeWorkflows: blocking hooks + structured verification + durable memory**  
https://www.reddit.com/r/ClaudeWorkflows/comments/1vw25g5/workflow_claude_code_enforcement_shifting_from/

**C37 — AgentAuthorization: agentjacking, over-privileged tools, least privilege as runtime policy**  
https://gl.reddit.com/r/AgentAuthorization/comments/1ucbmt4/agentjacking_is_the_loud_failure_overprivileged/

---

# B. Specifications, official docs, and real repositories — 32 sources

**O01 — GitHub awesome-copilot: guidelines for high-quality Agent Skills**  
https://github.com/github/awesome-copilot/blob/main/instructions/agent-skills.instructions.md

**O02 — GitHub awesome-copilot: Agent Skills catalog and usage**  
https://github.com/github/awesome-copilot/blob/main/docs/README.skills.md

**O03 — Agent Skills open specification**  
https://agentskills.io/specification

**O04 — GitHub Copilot Learning Hub: Agents vs Skills vs Instructions**  
https://github.com/github/awesome-copilot/blob/main/website/src/content/docs/learning-hub/what-are-agents-skills-instructions.md

**O05 — GitHub Docs: adding agent skills for GitHub Copilot**  
https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills

**O06 — Anthropic public Agent Skills repository**  
https://github.com/anthropics/skills

**O07 — GitHub awesome-copilot AGENTS.md: repository standards for agents/instructions/skills/hooks**  
https://github.com/github/awesome-copilot/blob/main/AGENTS.md

**O08 — GitHub Docs: repository custom instructions and AGENTS.md precedence**  
https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide

**O09 — GitHub awesome-copilot repository**  
https://github.com/github/awesome-copilot

**O10 — GitHub Docs: support matrix for instruction types**  
https://docs.github.com/en/copilot/reference/custom-instructions-support

**O11 — VS Code Docs: Use Agent Skills in VS Code**  
https://code.visualstudio.com/docs/agent-customization/agent-skills

**O12 — OpenAI Agents Python: real AGENTS.md with mandatory skill routing**  
https://github.com/openai/openai-agents-python/blob/main/AGENTS.md

**O13 — OpenAI: Introducing the Codex app; skills used beyond coding and shared through repositories**  
https://openai.com/index/introducing-the-codex-app/

**O14 — OpenAI: Introducing Codex; AGENTS.md guidance and verification expectations**  
https://openai.com/index/introducing-codex/

**O15 — catalyst-cooperative/agent-skills: AGENTS.md as single repository-level source of truth**  
https://github.com/catalyst-cooperative/agent-skills/blob/main/AGENTS.md

**O16 — zazencodes/agent-skills: cross-tool canonical/mirror strategy**  
https://github.com/zazencodes/agent-skills/blob/main/AGENTS.md

**O17 — kky42/agent_skills: skill repository as canonical global skill selection**  
https://github.com/kky42/agent_skills/blob/main/AGENTS.md

**O18 — compiler-graph: concise AGENTS.md plus task-specific skills, including benchmark**  
https://github.com/samchon/compiler-graph/blob/master/AGENTS.md

**O19 — amigoscode/skills: `.agents/skills` as cross-agent standard in a skill repository**  
https://github.com/amigoscode/skills/blob/main/AGENTS.md

**O20 — OpenAI Codex source: skill loader and `.agents/skills` implementation details**  
https://github.com/openai/codex/blob/main/codex-rs/core-skills/src/loader.rs

**O21 — gohypergiant/agent-skills: canonical skill source + local harness wiring + docs**  
https://github.com/gohypergiant/agent-skills/

**O22 — joshuadavidthomas/agent-skills: source-of-truth and skill documentation conventions**  
https://github.com/joshuadavidthomas/agent-skills/blob/main/AGENTS.md

**O23 — typia AGENTS.md: small agent entry point + conditional skill documents**  
https://github.com/samchon/typia/blob/master/AGENTS.md

**O24 — GitHub awesome-copilot: hook catalog and examples**  
https://github.com/github/awesome-copilot/blob/main/docs/README.hooks.md

**O25 — GitHub Docs: Copilot hooks reference, including preToolUse decisions**  
https://docs.github.com/en/copilot/reference/hooks-reference

**O26 — GitHub Docs: customize Copilot agent workflows with hooks**  
https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/use-hooks

**O27 — GitHub Docs: conceptual overview of hooks and security/validation uses**  
https://docs.github.com/en/copilot/concepts/agents/hooks?hl=en-US

**O28 — GitHub awesome-copilot CONTRIBUTING: hook and agentic workflow structure/validation**  
https://github.com/github/awesome-copilot/blob/main/CONTRIBUTING.md

**O29 — GitHub Copilot Learning Hub: plugins bundle agents, skills, hooks and integrations**  
https://github.com/github/awesome-copilot/blob/main/website/src/content/docs/learning-hub/installing-and-using-plugins.md

**O30 — GitHub Copilot Learning Hub: agents/subagents and hook interaction**  
https://github.com/github/awesome-copilot/blob/main/website/src/content/docs/learning-hub/agents-and-subagents.md

**O31 — GitHub awesome-copilot: real session-end hook implementation example**  
https://github.com/github/awesome-copilot/blob/main/hooks/session-auto-commit/README.md

**O32 — OpenAI: broader use of agents for long-horizon work outside software engineering**  
https://openai.com/index/how-agents-are-transforming-work/

---

# Research interpretation rules

1. Reddit/community sources are used to identify practical failure modes, conventions, and lived experience.
2. GitHub/VS Code/Agent Skills/OpenAI sources are preferred for current capability and format claims.
3. Real repositories show architecture patterns, not universal standards.
4. Markdown instructions cannot be treated as deterministic authorization or enforcement.
5. Skill descriptions, discovery behavior, hooks, and agent products are evolving quickly; revalidate before making major infrastructure changes.
6. Future research passes should append or supersede findings with dates rather than silently deleting prior evidence.
