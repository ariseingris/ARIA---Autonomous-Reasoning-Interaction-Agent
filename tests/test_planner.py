from aria.planner.react import ReActPlanner


def test_browser_use_task_creates_browser_fetch_step():
    plan = ReActPlanner().create_plan("Research browser-use and produce a report")
    assert plan.steps[0].tool_name == "browser.fetch"
    assert "browser-use" in plan.steps[0].args["url"]
