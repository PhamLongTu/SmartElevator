"""Các widget Pygame dùng lại: Button, Dropdown, Tabs và Marquee."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pygame

from views import theme


_button_cache: dict[tuple, pygame.Surface] = {}

def get_glossy_button_surface(width: int, height: int, active: bool) -> pygame.Surface:
    """Tạo và cache bề mặt nút bóng."""
    key = (width, height, active)
    if key in _button_cache:
        return _button_cache[key]
        
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    radius = height // 2
    
    pygame.draw.rect(surf, theme.BTN_BORDER, (0, 0, width, height), border_radius=radius)
    
    bw = 4
    inner_rect = pygame.Rect(bw, bw, width - bw * 2, height - bw * 2)
    inner_rad = max(2, radius - bw)
    
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), inner_rect, border_radius=inner_rad)
    
    gradient = pygame.Surface((width, height), pygame.SRCALPHA)
    top_c = theme.BTN_HOVER_TOP if active else theme.BTN_TOP
    bot_c = theme.BTN_HOVER_BOT if active else theme.BTN_BOT
    
    for i in range(inner_rect.y, inner_rect.bottom):
        t = (i - inner_rect.y) / max(1, inner_rect.height - 1)
        r = int(top_c[0] + (bot_c[0] - top_c[0]) * t)
        g = int(top_c[1] + (bot_c[1] - top_c[1]) * t)
        b = int(top_c[2] + (bot_c[2] - top_c[2]) * t)
        pygame.draw.line(gradient, (r, g, b, 255), (0, i), (width, i))
        
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(gradient, (0, 0))
    
    hi_rect = pygame.Rect(bw, bw, width - bw * 2, (height - bw * 2) // 2)
    hi_mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(hi_mask, (255, 255, 255, 70), hi_rect, border_top_left_radius=inner_rad, border_top_right_radius=inner_rad)
    surf.blit(hi_mask, (0, 0))
    
    sh_rect = pygame.Rect(bw, height - bw - 8, width - bw * 2, 8)
    sh_mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(sh_mask, (0, 0, 0, 40), sh_rect, border_bottom_left_radius=inner_rad, border_bottom_right_radius=inner_rad)
    surf.blit(sh_mask, (0, 0))

    pygame.draw.rect(surf, (255, 255, 255, 120), inner_rect, width=2, border_radius=inner_rad)
    
    _button_cache[key] = surf
    return surf


class Button:
    """Nút bóng có thể click và focus bằng bàn phím."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        on_click: Callable[[], None],
        *,
        accent: tuple[int, int, int] = theme.HUMAN,
        icon: str = "",
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.accent = accent
        self.icon = icon
        self.hover = False
        self.focused = False

    def handle(self, event: pygame.event.Event) -> bool:
        """Xử lý một event và trả True nếu nút được kích hoạt."""
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        active = self.hover or self.focused
        bg_surf = get_glossy_button_surface(self.rect.width, self.rect.height, active)
        
        draw_rect = self.rect.copy()
        if active:
            draw_rect.y += 2
            
        surface.blit(bg_surf, draw_rect)
        
        text = f"{self.icon}  {self.label}" if self.icon else self.label
        theme.render_text(surface, text, draw_rect.center,
                         size=int(self.rect.height * 0.5), color=(255, 255, 255), center=True,
                         family="display", bold=True,
                         outline_color=theme.BTN_BORDER, outline_width=3)


class Dropdown:
    """Dropdown chọn một mục trong danh sách."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        options: Sequence[str],
        *,
        index: int = 0,
        on_change: Callable[[int], None] | None = None,
        accent: tuple[int, int, int] = theme.AI,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.options = list(options)
        self.index = index
        self.on_change = on_change
        self.accent = accent
        self.open = False

    @property
    def value(self) -> str:
        """Nhãn của lựa chọn hiện tại."""
        return self.options[self.index]

    def _option_rects(self) -> list[pygame.Rect]:
        return [
            pygame.Rect(self.rect.x, self.rect.bottom + 4 + i * self.rect.height,
                        self.rect.width, self.rect.height)
            for i in range(len(self.options))
        ]

    def handle(self, event: pygame.event.Event) -> bool:
        """Xử lý một event và trả True nếu lựa chọn thay đổi."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.open = not self.open
                return False
            if self.open:
                for i, r in enumerate(self._option_rects()):
                    if r.collidepoint(event.pos):
                        changed = i != self.index
                        self.index = i
                        self.open = False
                        if changed and self.on_change:
                            self.on_change(i)
                        return changed
                self.open = False
        return False

    def draw(self, surface: pygame.Surface) -> None:
        theme.draw_panel(surface, self.rect, fill=theme.SURFACE_HI, border=self.accent)
        theme.render_text(surface, self.value, (self.rect.x + 14, self.rect.centery),
                         size=18, color=theme.TEXT, bold=True,
                         midleft=True, max_width=self.rect.width - 44)
        cx, cy = self.rect.right - 22, self.rect.centery
        pts = [(cx - 6, cy - 3), (cx + 6, cy - 3), (cx, cy + 4)]
        pygame.draw.polygon(surface, self.accent, pts)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        """Vẽ danh sách lựa chọn đang mở."""
        if not self.open:
            return
        for i, r in enumerate(self._option_rects()):
            sel = i == self.index
            theme.draw_panel(surface, r,
                            fill=theme.SURFACE_HI if sel else theme.SURFACE,
                            border=self.accent if sel else theme.BORDER)
            theme.render_text(surface, self.options[i], (r.x + 14, r.centery),
                             size=18, color=theme.TEXT if sel else theme.TEXT_MUTED,
                             midleft=True, max_width=r.width - 28)


class Tabs:
    """Dãy tab ngang với một lựa chọn đang bật."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        labels: Sequence[str],
        *,
        index: int = 0,
        on_change: Callable[[int], None] | None = None,
        accent: tuple[int, int, int] = theme.WIN,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.labels = list(labels)
        self.index = index
        self.on_change = on_change
        self.accent = accent

    def _tab_rects(self) -> list[pygame.Rect]:
        n = len(self.labels)
        w = self.rect.width // n
        return [
            pygame.Rect(self.rect.x + i * w, self.rect.y, w - 6, self.rect.height)
            for i in range(n)
        ]

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._tab_rects()):
                if r.collidepoint(event.pos):
                    changed = i != self.index
                    self.index = i
                    if changed and self.on_change:
                        self.on_change(i)
                    return changed
        return False

    def draw(self, surface: pygame.Surface) -> None:
        for i, r in enumerate(self._tab_rects()):
            active = i == self.index
            theme.draw_panel(surface, r,
                            fill=theme.SURFACE_HI if active else theme.SURFACE,
                            border=self.accent if active else theme.BORDER)
            theme.render_text(surface, self.labels[i], r.center,
                             size=18, color=theme.TEXT if active else theme.TEXT_MUTED,
                             center=True, bold=active, max_width=r.width - 20)


class Marquee:
    """Dòng chữ chạy ngang lặp liên tục."""

    def __init__(self, text: str, speed: float = 120, y_pos: int | None = None) -> None:
        self.text = text
        self.speed = speed
        self.x = float(theme.WIDTH)
        self.y = y_pos if y_pos is not None else theme.HEIGHT - 28
        self.font = theme.get_font(20, family="display", bold=True)
        self.surface = self.font.render(self.text, True, theme.TEXT)
        self.width = self.surface.get_width()

    def update(self, dt: float) -> None:
        """Di chuyển chữ sang trái và reset khi ra khỏi màn hình."""
        self.x -= self.speed * dt
        if self.x < -self.width:
            self.x = float(theme.WIDTH)

    def draw(self, surface: pygame.Surface) -> None:
        """Vẽ dòng chữ chạy."""
        bar_height = 30
        bar_rect = pygame.Rect(0, theme.HEIGHT - bar_height, theme.WIDTH, bar_height)
        
        bar_surf = pygame.Surface((theme.WIDTH, bar_height), pygame.SRCALPHA)
        bar_surf.fill((10, 15, 30, 220))
        surface.blit(bar_surf, bar_rect.topleft)

        surface.blit(self.surface, (int(self.x), self.y))
