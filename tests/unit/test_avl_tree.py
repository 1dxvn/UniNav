from data_structures.avl_tree import AVLTree


def build(keys):
    tree = AVLTree()
    for key in keys:
        tree.insert(key, f"v{key}")
    return tree


def test_in_order_is_sorted_and_reverse_is_descending():
    tree = build([5, 3, 8, 1, 4, 7, 9])
    assert [key for key, _ in tree.in_order()] == [1, 3, 4, 5, 7, 8, 9]
    assert [key for key, _ in tree.reverse_in_order()] == [9, 8, 7, 5, 4, 3, 1]


def test_stays_balanced_with_sorted_input():
    tree = build(range(1, 129))
    assert tree.height() <= 9
    assert len(tree) == 128


def test_rotation_cases_put_the_median_at_the_root():
    for keys in ([30, 20, 10], [10, 20, 30], [30, 10, 20], [10, 30, 20]):
        assert build(keys).root.key == 20


def test_duplicate_keys_share_a_node():
    tree = AVLTree()
    tree.insert(5, "a")
    tree.insert(5, "b")
    assert tree.search(5) == ["a", "b"]
    assert len(tree) == 2


def test_search_and_contains():
    tree = build([1, 2, 3])
    assert 2 in tree and tree.contains(3)
    assert tree.search(99) is None
    assert 99 not in tree


def test_empty_tree():
    tree = AVLTree()
    assert tree.is_empty() and tree.height() == 0 and tree.in_order() == []
