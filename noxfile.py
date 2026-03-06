import nox

nox.options.sessions = ["lint", "typecheck", "test"]


@nox.session(python="3.11", venv_backend="uv")
def lint(session: nox.Session) -> None:
    """Run ruff linter and formatter check."""
    session.run("ruff", "check", ".", external=True)
    session.run("ruff", "format", "--check", ".", external=True)


@nox.session(python="3.11", venv_backend="uv")
def typecheck(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.run("mypy", "app/", "--ignore-missing-imports", external=True)


@nox.session(python="3.11", venv_backend="uv")
def test(session: nox.Session) -> None:
    """Run the test suite (model, database, and health tests)."""
    session.env["OPENAI_API_KEY"] = "mock-key-for-testing"
    session.run(
        "pytest",
        "tests/test_models/",
        "tests/test_database.py",
        "tests/test_health.py",
        "-v",
        external=True,
    )
