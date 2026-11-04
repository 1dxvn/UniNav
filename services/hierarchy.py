from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_structures.nary_tree import NaryNode, NaryTree
from models import Building
from schemas.campus import HierarchyNodeResponse, HierarchyResponse

UNASSIGNED_FACULTY: str = "Unassigned"


def build_campus_tree(database_session: Session, root_name: str = "University") -> NaryTree:
    tree = NaryTree(root_name)
    faculty_nodes: dict[str, NaryNode] = {}
    buildings = database_session.scalars(select(Building).order_by(Building.name))
    for building in buildings:
        faculty = building.faculty or UNASSIGNED_FACULTY
        if faculty not in faculty_nodes:
            faculty_nodes[faculty] = tree.add_child(tree.root, faculty)
        tree.add_child(
            faculty_nodes[faculty],
            building.name,
            {"id": building.id, "x": building.x, "y": building.y, "type": building.building_type},
        )
    return tree


def to_hierarchy_response(node: NaryNode) -> HierarchyNodeResponse:
    return HierarchyNodeResponse(
        name=node.name,
        data=node.data,
        children=[to_hierarchy_response(child) for child in node.children],
    )


def describe_campus(tree: NaryTree) -> HierarchyResponse:
    return HierarchyResponse(
        height=tree.height(),
        total_nodes=len(tree),
        root=to_hierarchy_response(tree.root),
    )
