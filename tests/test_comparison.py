"""Tests for multi-project comparison."""

from irr_terminal.comparison import compare_projects


def test_multi_project_ranking_uses_balanced_score() -> None:
    projects = {"Large": [-1000, 800, 800], "Small": [-100, 90, 90]}
    frame = compare_projects(projects, 0.10, 0.10)
    assert "Score" in frame.columns
    assert "Rank" in frame.columns
    assert frame.iloc[0]["Project Name"] == "Large"
