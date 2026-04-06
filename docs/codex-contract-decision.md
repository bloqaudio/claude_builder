# Codex contract decision

Keep repo skills; do not replace them with subagent TOMLs.

Date checked: 2026-04-06
Scope: Codex de-provisionalization milestone, task 1 keep-or-replace gate

## Decision

Keep the current repository skill layout:

- `AGENTS.md`
- `.agents/skills/<skill>/SKILL.md`

Do **not** replace repo skills with `.codex/agents/*.toml` as the
primary Codex contract for this milestone.

Instead, narrow the contract language:

1. Treat `.agents/skills/*/SKILL.md` as **Codex skills**.
2. Stop treating those files as if they were Codex **custom subagents**.
3. If the product later needs project-scoped custom agents, add
   `.codex/agents/*.toml` **alongside** repo skills, not instead of them.

## Why this is the correct contract

### Repository evidence

Current implementation already aligns around repo skills:

- `src/claude_builder/core/output_renderers.py`
  - `CodexTargetRenderer.render(..., agents_dir=".agents/skills")`
  - emits `AGENTS.md`
  - emits `.agents/skills/<slug>/SKILL.md`
- `src/claude_builder/cli/generate_commands.py`
  - Codex target resolves agents dir to `.agents/skills`
- `src/claude_builder/cli/main.py`
  - Codex summaries already direct users to `.agents/skills/`
- `tests/unit/core/test_output_renderers.py`
  - asserts Codex output paths are `AGENTS.md` plus `.agents/skills/*/SKILL.md`
- `tests/integration/test_cli_target_workflows.py`
  - integration coverage checks generated Codex `SKILL.md` files
    under `.agents/skills`
- `README.md`
  - documents Codex output as `AGENTS.md` and `.agents/skills/<agent>/SKILL.md`

### Official Codex-facing guidance checked on 2026-04-06

#### AGENTS discovery

OpenAI Codex docs say Codex reads `AGENTS.md` files before doing work and
builds an instruction chain from layered locations.

Source:

- <https://developers.openai.com/codex/guides/agents-md>

#### Skill authoring and discovery

OpenAI Codex skills docs say:

- skills are directories with `SKILL.md`
- Codex reads repo-scoped skills from `.agents/skills`
- for repositories, Codex scans `.agents/skills` from the current
  working directory up to the repository root
- explicit discovery works through `/skills` or `$skill`
- implicit discovery works by matching the skill description

Source:

- <https://developers.openai.com/codex/skills>

#### Custom agents / subagents are a different contract

OpenAI Codex subagents docs say project-scoped custom agents live under:

- `.codex/agents/` for project-scoped agents
- `~/.codex/agents/` for personal agents

Those are standalone TOML files and belong to Codex
custom-agent/subagent workflows, not repo skill folders.

Source:

- <https://developers.openai.com/codex/subagents>

## Keep-or-replace verdict

### Keep

Keep `.agents/skills/*/SKILL.md` because it is not a provisional hack
anymore; it is an officially documented Codex repo-skill location.

### Replace only the claim, not the layout

Replace any wording that implies `.agents/skills/*/SKILL.md` are
Codex custom subagents.

That wording is the risky part, not the file layout.

## Downstream contract for delivery/test lanes

To count as non-provisional, downstream changes should lock in all of
the following:

1. Generated `AGENTS.md` explicitly points Codex users to the generated
   repo skills.
2. Generated `AGENTS.md` explains discoverability in Codex-native terms:
   - skills are available from `.agents/skills`
   - users can inspect them with `/skills`
   - users can invoke them with `$skill-name`
3. Codex output quality should be judged as:
   - meaningful `AGENTS.md`
   - meaningful repo skills
   - no false claim that repo skills are custom subagent TOMLs
4. Tests should fail if Codex output regresses to shallow renaming or
   loses the discoverability story.

## Practical implication

For this milestone, the safest contract is:

- **primary Codex artifact contract:** `AGENTS.md` + repo skills in
  `.agents/skills/*/SKILL.md`
- **possible future additive contract:** `.codex/agents/*.toml` only if
  the product later decides to generate Codex custom agents explicitly

This keeps the milestone bounded while matching current official Codex behavior.
