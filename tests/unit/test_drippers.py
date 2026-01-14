from smart_irrigation_system.node.core.drippers import Drippers


# ---------------------- Tests ----------------------

def test_consumption_is_zero_on_init():
    # Arrange
    drippers = Drippers()

    # Assert
    assert drippers.get_consumption() == 0


def test_zero_consumption_on_removed_all():
    # Arrange
    drippers = Drippers()
    drippers.add_dripper(12)
    drippers.add_dripper(12)
    drippers.add_dripper(2)

    # Act
    drippers.remove_dripper(12)
    drippers.remove_dripper(12)
    drippers.remove_dripper(2)

    # Assert
    assert drippers.get_consumption() == 0


def test_correct_consumption_after_adding_and_removing():
    # Arrange
    drippers = Drippers()

    # Act
    drippers.add_dripper(12)
    drippers.add_dripper(12)
    drippers.add_dripper(2)
    drippers.add_dripper(3.5)
    drippers.remove_dripper(2)
    drippers.remove_dripper(12)

    # Assert
    assert drippers.get_consumption() == 15.5


def test_minimum_dripper_flow_returns_lowest_dripper_flow():
    # Arrange
    drippers = Drippers()
    drippers.add_dripper(12)
    drippers.add_dripper(12)
    drippers.add_dripper(1.5)
    drippers.add_dripper(2.5)
    drippers.remove_dripper(1.5)
    drippers.add_dripper(4)

    # Act
    min_flow = drippers.get_minimum_dripper_flow()

    # Assert
    assert min_flow == 2.5


def test_minimum_dripper_flow_is_zero_when_no_drippers():
    # Arrange
    drippers = Drippers()

    # Act
    min_flow = drippers.get_minimum_dripper_flow()

    # Assert
    assert min_flow == 0