"""Migration stairway test — upgrade → downgrade → upgrade for every revision.

Based on: https://github.com/alvassin/alembic-quickstart
Pattern: Walk through every migration step, verify each is reversible.

Catches:
    - Missing downgrade() implementations
    - Foreign key violations on downgrade
    - Data-dependent migration failures
    - Migrations that don't compose cleanly

Marked as ``slow`` — excluded from default CI loop, run explicitly::

    pytest -m slow
    pytest tests/migrations/
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


@pytest.fixture(scope="module")
def alembic_config() -> Config:
    """Load Alembic configuration from alembic.ini."""
    config = Config("alembic.ini")
    return config


def _get_revisions(config: Config) -> list[str]:
    """Return all revision identifiers in upgrade order."""
    script = ScriptDirectory.from_config(config)
    revisions: list[str] = []
    for revision in script.walk_revisions("base", "heads"):
        revisions.append(revision.revision)
    # walk_revisions goes head→base, reverse for upgrade order
    revisions.reverse()
    return revisions


@pytest.mark.slow
def test_stairway(alembic_config: Config) -> None:
    """Walk every migration: upgrade one step, downgrade one step, re-upgrade.

    If any migration fails to downgrade cleanly, this test fails — catching
    the issue before it reaches production where rollbacks matter most.
    """
    revisions = _get_revisions(alembic_config)

    if not revisions:
        pytest.skip("No migration revisions found")

    for revision in revisions:
        command.upgrade(alembic_config, revision)
        command.downgrade(alembic_config, "-1")
        command.upgrade(alembic_config, revision)

    # Leave DB at head for any subsequent tests
    command.upgrade(alembic_config, "head")
