from sqlmodel import SQLModel, create_engine, Session
import pytest

from smart_irrigation_system.server.configuration.models.node import Node
from smart_irrigation_system.server.configuration.repositories.node_repository import NodeRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_create_and_get_node(session: Session):
    repo = NodeRepository(session)

    node = Node(
        name="Test Node",
        location="Garden",
        hardware={"input_pins": [1], "output_pins": [2]},
        irrigation_limits={"min_percent": 30, "max_percent": 100},
        automation={"enabled": True},
        batch_strategy={"concurrent_irrigation": False},
        logging={"enabled": True, "log_level": "DEBUG"}
    )

    repo.create(node)
    session.commit()

    loaded = repo.get(node.id)

    assert loaded is not None
    assert loaded.name == "Test Node"
    assert loaded.location == "Garden"
    assert loaded.hardware == {"input_pins": [1], "output_pins": [2]}
    assert loaded.logging == {"enabled": True, "log_level": "DEBUG"}


def test_list_nodes(session: Session):
    repo = NodeRepository(session)

    repo.create(Node(name="A"))
    repo.create(Node(name="B"))
    session.commit()

    nodes = repo.list_all()

    assert len(nodes) == 2


def test_delete_node(session: Session):
    repo = NodeRepository(session)

    node = Node(name="Delete Me")
    repo.create(node)
    session.commit()

    result = repo.delete(node.id)
    session.commit()

    assert result is True
    assert repo.get(node.id) is None


