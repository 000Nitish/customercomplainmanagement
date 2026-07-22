from app.agents.graph import build_intake_graph, build_investigation_graph


def test_graphs_build():
    assert build_intake_graph() is not None
    assert build_investigation_graph() is not None
