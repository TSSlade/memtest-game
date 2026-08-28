"""Documentation drift is what produced most of the defects this suite covers:
the restructure moved files and the prose kept describing the old layout.

Mechanical checks only -- these catch dead links and stale invocations, not
inaccurate reasoning.
"""

import re

import pytest

from memtest.paths import MEMTEST_DIR

REPO_ROOT = MEMTEST_DIR.parent
DOCS = ("README.md", "MODIFICATIONS.md", "AGENTS.md", "CLAUDE.md")

# [text](target) where target is not a URL, an anchor, or a mailto.
LINK = re.compile(r"\[[^\]]*\]\((?!https?://|#|mailto:)([^)]+)\)")


@pytest.mark.parametrize("name", DOCS)
def test_document_exists(name):
    assert (REPO_ROOT / name).is_file()


@pytest.mark.parametrize("name", DOCS)
def test_relative_links_resolve(name):
    """A dead link in MODIFICATIONS.md is how the generator became unfindable."""
    text = (REPO_ROOT / name).read_text(encoding="utf-8")
    broken = []
    for target in LINK.findall(text):
        path = target.split("#", 1)[0].strip()
        if not path:
            continue
        if not (REPO_ROOT / path).exists():
            broken.append(target)
    assert not broken, f"{name} links to missing paths: {broken}"


@pytest.mark.parametrize("name", DOCS)
def test_no_references_to_the_pre_restructure_layout(name):
    """Everything lives under memtest/ now.

    Catches the flat-layout paths the docs kept after the restructure, such as
    `tools/generate_alerts.py` and `game/session_record.py`.
    """
    text = (REPO_ROOT / name).read_text(encoding="utf-8")
    stale = re.findall(
        r"(?<![\w/.-])(?:tools|game|config|ui|user|assets)/[\w./-]+",
        text,
    )
    # A path is fine when it is already qualified with the package directory.
    unqualified = [
        match
        for match in stale
        if not re.search(rf"memtest/{re.escape(match)}", text)
    ]
    assert not unqualified, f"{name} refers to pre-restructure paths: {unqualified}"


@pytest.mark.parametrize("name", DOCS)
def test_no_removed_module_invocations(name):
    """`python -m game.main_game` has not worked since the restructure."""
    text = (REPO_ROOT / name).read_text(encoding="utf-8")
    assert "python -m game.main_game" not in text
    assert "python tools/generate_alerts.py" not in text


def test_guide_fa_is_not_referenced():
    """It was dropped; nothing should still point at it."""
    for name in DOCS:
        assert "guide_fa" not in (REPO_ROOT / name).read_text(encoding="utf-8")


def test_task_init_docstring_matches_its_signature():
    """The docstring spent a long time naming parameters that did not exist.

    Three of the names were near-misses of the real ones -- close enough to read
    as correct, wrong enough to be useless to anyone matching them against the
    signature -- and the two parameters this fork added were absent entirely.
    The docstring is written in signature order so the agreement is checked here
    rather than trusted.
    """
    import inspect

    from memtest.game.task import Task

    signature = [
        name
        for name in inspect.signature(Task.__init__).parameters
        if name != "self"
    ]
    doc = Task.__init__.__doc__ or ""
    documented = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", doc, re.M)

    assert documented == signature, (
        f"docstring lists {documented}, signature has {signature}"
    )


def test_constitution_is_present_and_attributed():
    """An unchanged mirror must retain its provenance and attribution."""
    text = (REPO_ROOT / "CONSTITUTION.md").read_text(encoding="utf-8")
    assert "Clanker Constitution" in text
    assert "github.com/kenn-io/constitution" in text
    assert "CC BY 4.0" in text


def test_agents_md_is_referenced_by_claude_md():
    """Both agents must reach the same project guidance."""
    text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "@AGENTS.md" in text
    assert "@CONSTITUTION.md" in text
