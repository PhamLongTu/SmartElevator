"""Smart Elevator - game entry point.

Launches the Pygame UI: builds the :class:`~views.app.App`, registers every
screen from the screen registry, and starts on the Main Menu.

Run with::

    python main.py
"""

from __future__ import annotations

from views.app import App
from views.screens import SCREEN_REGISTRY


def main() -> None:
    """Create the app, register all screens, and run the main loop."""
    app = App()
    for name, screen_cls in SCREEN_REGISTRY.items():
        app.register(name, screen_cls)
    app.go_to("main")
    app.run()


if __name__ == "__main__":
    main()
