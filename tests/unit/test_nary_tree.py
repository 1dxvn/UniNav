import pytest

from data_structures.nary_tree import NaryTree


@pytest.fixture()
def tree():
    campus = NaryTree("University")
    campus.add_child("University", "Engineering")
    campus.add_child("University", "Health")
    campus.add_child("Engineering", "Building A", {"floors": 4})
    campus.add_child("Building A", "Room 101")
    return campus


def test_size_and_height(tree):
    assert len(tree) == 5
    assert tree.height() == 4


def test_dfs_visits_parents_before_children_in_insertion_order(tree):
    names = [node.name for node in tree.dfs()]
    assert names == ["University", "Engineering", "Building A", "Room 101", "Health"]


def test_find_and_path_to_root(tree):
    room = tree.find("Room 101")
    assert [n.name for n in tree.path_to_root(room)] == [
        "University", "Engineering", "Building A", "Room 101",
    ]
    assert room.depth() == 3 and room.is_leaf()
    assert tree.find("Gym") is None


def test_unknown_parent_raises(tree):
    with pytest.raises(KeyError):
        tree.add_child("Nowhere", "X")


def test_empty_name_is_rejected():
    with pytest.raises(ValueError):
        NaryTree("")


def test_to_text_indents_by_depth(tree):
    lines = tree.to_text().splitlines()
    assert lines[0] == "University"
    assert lines[2] == "        Building A"
