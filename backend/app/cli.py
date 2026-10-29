"""Comandos administrativos (ADD §6.3: las cuentas se crean desde el backend, sin registro público).

Uso, desde backend/:
    uv run python -m app.cli create-user <usuario>
    uv run python -m app.cli set-password <usuario>
    uv run python -m app.cli deactivate-user <usuario>

La contraseña se pide por teclado sin mostrarla. Para scripts, pásala por la entrada
estándar con --password-stdin (nunca como argumento: quedaría en el historial).
"""

import argparse
import getpass
import sys

from sqlalchemy.exc import IntegrityError

from app.core.security import validate_password_strength
from app.db.session import get_sessionmaker
from app.repositories import users as users_repo


def _read_password(from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    password = getpass.getpass("Contraseña: ")
    if password != getpass.getpass("Repite la contraseña: "):
        raise SystemExit("Las contraseñas no coinciden.")
    return password


def create_user(username: str, from_stdin: bool) -> None:
    password = _read_password(from_stdin)
    validate_password_strength(password)
    with get_sessionmaker()() as session:
        try:
            user = users_repo.create_user(session, username, password)
            session.commit()
        except IntegrityError:
            raise SystemExit(f"Ya existe un usuario llamado {username!r}.") from None
        print(f"Usuario {user.username!r} creado (id={user.id}).")


def set_password(username: str, from_stdin: bool) -> None:
    password = _read_password(from_stdin)
    validate_password_strength(password)
    with get_sessionmaker()() as session:
        user = users_repo.get_by_username(session, username)
        if user is None:
            raise SystemExit(f"No existe el usuario {username!r}.")
        users_repo.set_password(session, user, password)
        session.commit()
        print(f"Contraseña de {user.username!r} actualizada.")


def deactivate_user(username: str) -> None:
    with get_sessionmaker()() as session:
        user = users_repo.get_by_username(session, username)
        if user is None:
            raise SystemExit(f"No existe el usuario {username!r}.")
        user.is_active = False
        session.commit()
        print(f"Usuario {user.username!r} desactivado; sus tokens dejan de ser válidos.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Administración GTIP")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("create-user", "set-password"):
        cmd = commands.add_parser(name)
        cmd.add_argument("username")
        cmd.add_argument("--password-stdin", action="store_true")
    commands.add_parser("deactivate-user").add_argument("username")

    args = parser.parse_args(argv)
    try:
        if args.command == "create-user":
            create_user(args.username, args.password_stdin)
        elif args.command == "set-password":
            set_password(args.username, args.password_stdin)
        else:
            deactivate_user(args.username)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
