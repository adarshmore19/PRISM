"""CLI script to provision or elevate the initial Administrator in PRISM.

Usage:
    python -m scripts.bootstrap_admin --email admin@example.com --role ADMIN
"""

import argparse
import sys
from uuid import uuid4

from backend.db.session import get_session
from backend.db.models import User, Role, UserRoleAssignment, AUTH_ROLES
from backend.services.authorization import create_user, assign_role


def bootstrap_admin(email: str, role_name: str = "ADMINISTRATOR", username: str | None = None, display_name: str | None = None):
    email = email.strip().lower()
    if not username:
        username = email.split("@")[0]
    if not display_name:
        display_name = f"PRISM {role_name.title()}"
    if role_name not in AUTH_ROLES:
        print(f"Error: Role '{role_name}' is not in known roles: {sorted(AUTH_ROLES)}")
        sys.exit(1)

    with get_session() as db:
        user = db.query(User).filter(User.email == email).one_or_none()
        if user is None:
            print(f"Creating user {username} <{email}>...")
            user = create_user(
                db,
                username=username,
                email=email,
                display_name=display_name,
                identity_provider="supabase",
                external_subject=str(uuid4()),
            )
            print(f"User created with ID: {user.id}")
        else:
            print(f"User already exists with ID: {user.id}")

        role = db.query(Role).filter(Role.name == role_name).one_or_none()
        if not role:
            print(f"Role '{role_name}' not found in database. Run 'alembic upgrade head' first.")
            sys.exit(1)

        existing_assignment = (
            db.query(UserRoleAssignment)
            .filter(UserRoleAssignment.user_id == user.id, UserRoleAssignment.role_id == role.id)
            .one_or_none()
        )
        if existing_assignment:
            print(f"User already has role '{role_name}'.")
        else:
            print(f"Assigning role '{role_name}' to user...")
            assign_role(db, user_id=str(user.id), role_name=role_name)
            print(f"Successfully assigned '{role_name}' to {email}.")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap PRISM Admin Account")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--role", default="ADMINISTRATOR", choices=list(AUTH_ROLES), help="Role to grant")
    parser.add_argument("--username", help="Username (defaults to email handle)")
    parser.add_argument("--display-name", help="Display name")
    args = parser.parse_args()

    bootstrap_admin(
        email=args.email,
        role_name=args.role,
        username=args.username,
        display_name=args.display_name,
    )


if __name__ == "__main__":
    main()
