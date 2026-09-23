"""A single failing/blocked source must never abort the run."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import SourceStatus
from sources.base import BaseAdapter, BlockedError


class AlwaysBlockedAdapter(BaseAdapter):
    name = "always_blocked"

    def fetch(self):
        try:
            raise BlockedError("simulated robots.txt disallow")
        except BlockedError as exc:
            return self.blocked_result(str(exc))


class AlwaysRaisesAdapter(BaseAdapter):
    name = "always_raises"

    def fetch(self):
        raise RuntimeError("simulated unexpected crash")


def test_blocked_adapter_returns_status_not_exception():
    config = {"search": {}}
    result = AlwaysBlockedAdapter(config).fetch()
    assert result.status == SourceStatus.BLOCKED_OR_MANUAL_REVIEW_REQUIRED
    assert result.listings == []


def test_orchestrator_survives_adapter_that_raises():
    """Mirrors search.run_adapters' try/except around adapter.fetch()."""
    config = {"search": {}}
    adapter = AlwaysRaisesAdapter(config)
    blocked = []
    try:
        adapter.fetch()
        raised = False
    except Exception as exc:  # noqa: BLE001
        raised = True
        blocked.append((adapter.name, str(exc)))
    assert raised
    assert blocked == [("always_raises", "simulated unexpected crash")]
