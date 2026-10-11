"""Verify the installed wheel's public scaffold greeting."""

import pokie


def main() -> None:
    """Check the installed package and print its verified greeting.

    Run ``python scripts/wheel_smoke.py`` in the
    wheel's virtual environment; success prints ``hello from Python``.

    Raises
    ------
    RuntimeError
        If the wheel's public greeting differs from the scaffold contract.
    """
    greeting = pokie.hello()
    if greeting != "hello from Python":
        message = f"Unexpected wheel greeting: {greeting!r}"
        raise RuntimeError(message)
    print(greeting)


if __name__ == "__main__":
    main()
