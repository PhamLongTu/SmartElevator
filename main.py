"""Điểm khởi chạy game Smart Elevator."""

from __future__ import annotations

from views.app import App
from views.screens import SCREEN_REGISTRY


def main() -> None:
    """Tạo app, đăng ký màn hình và chạy vòng lặp chính."""
    app = App()
    for name, screen_cls in SCREEN_REGISTRY.items():
        app.register(name, screen_cls)
    app.go_to("main")
    app.run()


if __name__ == "__main__":
    main()
