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


def _normalize_snapshot_text(text: str) -> str:
    """Normalize whitespace for stable snapshot assertions."""
    normalized_lines = [line.rstrip() for line in text.splitlines()]
    collapsed: list[str] = []
    previous_blank = False

    for line in normalized_lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank

    return "\n".join(collapsed).strip() + "\n"


def _read_snapshot(name: str) -> str:
    """Read an integration snapshot file."""
    path = Path(__file__).parent / "__snapshots__" / name
    return _normalize_snapshot_text(path.read_text(encoding="utf-8"))


def _extract_listed_skill_paths(agents_text: str) -> list[str]:
    """Extract listed skill paths from the generated AGENTS guide."""
    return re.findall(r"`([^`]+/SKILL\.md)`", agents_text)


def _render_codex_contract_snapshot(project_path: Path) -> str:
    """Render the contract-relevant Codex artifact summary for snapshotting."""
    agents_text = (project_path / "AGENTS.md").read_text(encoding="utf-8")
    listed_paths = _extract_listed_skill_paths(agents_text)
    actual_paths = [
        path.as_posix()
        for path in sorted(
            relative_path.relative_to(project_path)
            for relative_path in project_path.rglob("SKILL.md")
        )
    ]

    codex_section = ""
    if "## Codex Skills" in agents_text:
        codex_section = "## Codex Skills" + agents_text.split("## Codex Skills", 1)[1]

    return _normalize_snapshot_text(
        "\n".join(
            [
                "# Codex python_web contract snapshot",
                "",
                "## Actual skill files",
                *actual_paths,
                "",
                "## Listed skill files",
                *listed_paths,
                "",
                "## Codex section",
                codex_section,
            ]
        )
    )


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

    def test_top_level_codex_target_fixture_snapshot_catches_shallow_renames(
        self, tmp_path: Path
    ) -> None:
        """Codex contract snapshot should require Codex-native paths for fixture projects."""
        project_path = _copy_sample_project_fixture(tmp_path, "python_web")
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["--target", "codex", "--no-git", str(project_path)],
        )

        assert result.exit_code == 0, result.output
        agents_text = (project_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "Codex scans repository skills from `.agents/skills`" in agents_text
        assert "not custom agents from `.codex/agents/*.toml`" in agents_text
        expected = _read_snapshot("codex_python_web_contract_snapshot.md")
        assert _render_codex_contract_snapshot(project_path) == expected
