"""Framework màn hình gồm lớp nền :class:`Screen` và vòng lặp :class:`App`."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from views import theme
from views.widgets import Marquee


@dataclass
class Session:
    """Trạng thái dùng chung giữa các màn hình."""

    passengers: int = 15
    seed: int = 7
    algorithm: str = "astar"
    last_engine: object | None = None
    last_score: int = 0
    last_label: str = ""
    last_mode: str = "manual"

    compare_engine: object | None = None
    compare_score: int = 0
    compare_label: str = ""

    ai_scenario_rows: list = field(default_factory=list)
    compare_scenario_rows: list = field(default_factory=list)

    extras: dict = field(default_factory=dict)


class Screen:
    """Lớp nền cho mọi màn hình."""

    def __init__(self, app: "App") -> None:
        self.app = app
        self.session = app.session

    def on_enter(self) -> None:
        """Được gọi mỗi khi màn hình trở thành màn hình hiện tại."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Xử lý một event của Pygame."""

    def update(self, dt: float) -> None:
        """Cập nhật trạng thái theo ``dt`` giây."""

    def draw(self, surface: pygame.Surface) -> None:
        """Vẽ màn hình."""


class App:
    """Quản lý cửa sổ, registry màn hình và vòng lặp chính."""

    def __init__(self, headless: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption(theme.TITLE)
        self.headless = headless
        if headless:
            self.screen_surface = pygame.Surface((theme.WIDTH, theme.HEIGHT))
        else:
            self.screen_surface = pygame.display.set_mode(
                (theme.WIDTH, theme.HEIGHT),
                pygame.SCALED | pygame.RESIZABLE
            )
        self.clock = pygame.time.Clock()
        self.session = Session()
        self.fullscreen = False
        self.running = True

        self.marquee = Marquee(
            "Nhóm 4: Phạm Long Tứ - 24110377, Nguyễn Lê Hoàng Chương - 24110172, Trần Minh Luân - 24110278"
        )

        self._registry: dict[str, type[Screen]] = {}
        self._current: Screen | None = None
        self._current_name = ""

    def register(self, name: str, screen_cls: type[Screen]) -> None:
        """Đăng ký một lớp màn hình theo tên."""
        self._registry[name] = screen_cls

    def go_to(self, name: str) -> None:
        """Chuyển sang màn hình đã đăng ký."""
        screen_cls = self._registry[name]
        self._current = screen_cls(self)
        self._current_name = name
        self._current.on_enter()

    @property
    def current_name(self) -> str:
        """Tên màn hình đang hoạt động."""
        return self._current_name

    def toggle_fullscreen(self) -> None:
        """Bật hoặc tắt chế độ toàn màn hình."""
        self.fullscreen = not self.fullscreen
        pygame.display.toggle_fullscreen()

    def step(self, dt: float, events: list[pygame.event.Event] | None = None) -> None:
        """Chạy một frame: xử lý event, cập nhật và vẽ."""
        if self._current is None:
            return
        for event in events if events is not None else pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
            else:
                self._current.handle_event(event)
        self._current.update(dt)
        self.marquee.update(dt)
        theme.draw_vgradient(
            self.screen_surface,
            pygame.Rect(0, 0, theme.WIDTH, theme.HEIGHT),
            theme.BG_TOP,
            theme.BG_BOTTOM
        )
        self._current.draw(self.screen_surface)
        self.marquee.draw(self.screen_surface)

    def run(self) -> None:
        """Chạy vòng lặp chính cho tới khi người dùng thoát."""
        while self.running:
            dt = self.clock.tick(theme.FPS) / 1000.0
            self.step(dt)
            if not self.headless:
                pygame.display.flip()
        pygame.quit()
