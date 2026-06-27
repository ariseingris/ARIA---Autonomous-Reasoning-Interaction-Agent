import pytest

from aria.tools.router import ToolRouter
from aria.tools.types import ToolResult


@pytest.mark.asyncio
async def test_router_executes_registered_tool():
    router = ToolRouter()

    async def ok() -> ToolResult:
        return ToolResult(name="ok", ok=True, content="done")

    router.register("ok", ok)
    result = await router.execute("ok")
    assert result.ok
    assert result.content == "done"


@pytest.mark.asyncio
async def test_router_reports_missing_tool():
    result = await ToolRouter().execute("missing")
    assert not result.ok
    assert result.error == "tool_not_found"
