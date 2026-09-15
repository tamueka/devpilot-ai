from uuid import uuid4

from app.db.models import (
    Project,
    User,
)


def test_user_has_projects_relationship() -> None:
    user = User(
        email="user@devpilot.local",
        password_hash="hashed-password",
    )

    project = Project(
        name="DevPilot",
        status="CREATED",
    )

    user.projects.append(
        project,
    )

    assert project.owner is user
    assert project in user.projects


def test_project_can_have_owner() -> None:
    user = User(
        id=uuid4(),
        email="owner@devpilot.local",
        password_hash="hashed-password",
    )

    project = Project(
        name="DevPilot",
        status="CREATED",
        owner=user,
    )

    assert project.owner is user


def test_project_owner_id_column_exists() -> None:
    owner_id_column = (
        Project.__table__.c.owner_id
    )

    assert owner_id_column is not None


def test_project_owner_is_temporarily_nullable() -> None:
    owner_id_column = (
        Project.__table__.c.owner_id
    )

    assert owner_id_column.nullable is True


def test_project_owner_foreign_key_points_to_users() -> None:
    owner_id_column = (
        Project.__table__.c.owner_id
    )

    foreign_keys = list(
        owner_id_column.foreign_keys
    )

    assert len(
        foreign_keys,
    ) == 1

    foreign_key = foreign_keys[0]

    assert (
        foreign_key.target_fullname
        == "users.id"
    )

    assert (
        foreign_key.ondelete
        == "RESTRICT"
    )


def test_user_email_is_unique() -> None:
    email_column = (
        User.__table__.c.email
    )

    assert email_column.unique is True


def test_user_is_active_by_default() -> None:
    user = User(
        email="active@devpilot.local",
        password_hash="hashed-password",
    )

    assert (
        user.is_active is None
        or user.is_active is True
    )