"""Integration tests for top-level CLI target profile workflows."""

import re
import shutil

from pathlib import Path

from click.testing import CliRunner

from claude_builder.cli.main import cli


def _copy_sample_project_fixture(tmp_path: Path, fixture_name: str) -> Path:
    """Copy a representative sample project fixture into a temp directory."""
    source = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "sample_projects"
        / fixture_name
    )
    destination = tmp_path / fixture_name
    shutil.copytree(source, destination)
    return destination


def _extract_listed_skill_paths(agents_text: str) -> list[str]:
    """Extract listed skill paths from the generated AGENTS guide."""
    return re.findall(r"`([^`]+/SKILL\.md)`", agents_text)


class TestCLITargetWorkflows:
    """Integration coverage for target-aware top-level CLI execution."""

    def test_top_level_codex_target_generates_skill_artifacts(
        self, sample_python_project
    ):
        """Top-level CLI should generate Codex artifacts when --target codex is set."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["--target", "codex", "--no-git", str(sample_python_project)],
        )

        assert result.exit_code == 0, result.output
        assert (sample_python_project / "AGENTS.md").exists()
        assert not (sample_python_project / "CLAUDE.md").exists()

        agents_text = (sample_python_project / "AGENTS.md").read_text(encoding="utf-8")
        skills_root = sample_python_project / ".agents" / "skills"
        skill_files = sorted(
            path.relative_to(sample_python_project).as_posix()
            for path in skills_root.glob("*/SKILL.md")
        )
        listed_skill_files = _extract_listed_skill_paths(agents_text)

        assert (
            skills_root.exists()
        ), "Codex output should write skills under .agents/skills/"
        assert skill_files, "Codex target should emit at least one SKILL.md artifact"
        assert ".claude/agents/" not in agents_text
        assert "Codex scans repository skills from `.agents/skills`" in agents_text
        assert "not custom agents from `.codex/agents/*.toml`" in agents_text
        assert listed_skill_files == sorted(
            set(listed_skill_files)
        ), "AGENTS.md should list each generated repo skill exactly once"
        assert listed_skill_files == skill_files

    def test_top_level_codex_target_fixture_enforces_contract(
        self, tmp_path: Path
    ) -> None:
        """Codex fixture output should preserve the expected path contract."""
        project_path = _copy_sample_project_fixture(tmp_path, "python_web")
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["--target", "codex", "--no-git", str(project_path)],
        )

        assert result.exit_code == 0, result.output
        agents_text = (project_path / "AGENTS.md").read_text(encoding="utf-8")
        skill_files = sorted(
            path.relative_to(project_path).as_posix()
            for path in project_path.rglob("SKILL.md")
        )
        listed_skill_files = _extract_listed_skill_paths(agents_text)

        assert skill_files == [
            ".agents/skills/python-web-rapid-prototyper/SKILL.md",
            ".agents/skills/python-web-test-writer-fixer/SKILL.md",
        ]
        assert listed_skill_files == skill_files
        assert "Codex scans repository skills from `.agents/skills`" in agents_text
        assert "not custom agents from `.codex/agents/*.toml`" in agents_text
        assert "## Codex Skills" in agents_text
        assert ".claude/agents/" not in agents_text
