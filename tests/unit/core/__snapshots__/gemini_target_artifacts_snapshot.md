<!-- markdownlint-disable -->

## GEMINI.md
# Sample Project

Project-level instructions.

## AGENTS.md
# AGENTS

Agent usage guide.

## .gemini/agents/test-writer-fixer.md
# test-writer-fixer

## Scope
Specialized context for test-writer-fixer work.

## Guidance
Fix tests.

## .gemini/commands/test-writer-fixer.toml
name = "test-writer-fixer"
description = "Use the test-writer-fixer specialist guidance for this repository."
prompt = "Read `.gemini/agents/test-writer-fixer.md` and `GEMINI.md`, then apply that guidance.\n\nFix tests."

## .gemini/agents/backend-architect.md
# backend-architect

## Scope
Specialized context for backend-architect work.

## Guidance
Design backend systems.

## .gemini/commands/backend-architect.toml
name = "backend-architect"
description = "Use the backend-architect specialist guidance for this repository."
prompt = "Read `.gemini/agents/backend-architect.md` and `GEMINI.md`, then apply that guidance.\n\nDesign backend systems."

## .gemini/settings.json.example
{
  "context": {
    "fileName": [
      "GEMINI.md",
      "AGENTS.md"
    ]
  }
}
