from mathfoundry.subareas import detect_ag_subareas


def test_detect_subareas_moduli():
    t = "We study moduli stacks of stable maps and geometric invariant theory quotients."
    tags = detect_ag_subareas(t)
    assert "moduli_and_stacks" in tags


def test_detect_subareas_derived():
    t = "Derived categories, t-structures, and stability conditions in algebraic geometry."
    tags = detect_ag_subareas(t)
    assert "derived_and_homological_ag" in tags
