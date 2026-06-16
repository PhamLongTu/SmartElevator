"""Màn hình chế độ Đối đầu: người chơi vs AI trên cùng một kịch bản, hiển thị song song."""

from __future__ import annotations

import pygame

from algorithms.algorithm_factory import AlgorithmFactory
from controllers.compare_mode import CompareMode
from simulation import RandomScenarioGenerator
from views import theme
from views.app import Screen
from views.building_view import BuildingView, draw_onboard_strip
from views.widgets import Button, Dropdown, Tabs


class CompareScreen(Screen):
    """Chạy một người chơi thủ công và một AI trên cùng một kịch bản chung; tuyên bố người thắng cuộc."""

    def on_enter(self) -> None:
        self.generator = RandomScenarioGenerator(
            num_passengers=self.session.passengers, seed=self.session.seed
        )
        # Lựa chọn thuật toán cho bên AI.
        self.algo_keys = AlgorithmFactory.available()
        self.algo_labels = [AlgorithmFactory.info(k).display_name for k in self.algo_keys]
        self.algo_index = self.algo_keys.index(self.session.algorithm) \
            if self.session.algorithm in self.algo_keys else self.algo_keys.index("astar")

        self.player_view = BuildingView(pygame.Rect(20, 90, 480, 560), accent=theme.HUMAN)
        self.ai_view = BuildingView(pygame.Rect(780, 90, 480, 560), accent=theme.AI)
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)

        # Thiết lập các điều khiển (hiển thị trước khi bắt đầu chạy).
        self.is_ai_vs_ai = False
        
        self.type_tabs = Tabs((520, 135, 240, 36), ["You vs AI", "AI vs AI"],
                               index=0, on_change=self._select_compare_type,
                               accent=theme.WIN)

        self.algo1_index = self.algo_index
        self.algo2_index = self.algo_index

        self.dropdown1 = Dropdown((520, 200, 240, 40), self.algo_labels,
                                  index=self.algo1_index, on_change=self._select_algo1,
                                  accent=theme.HUMAN)
        
        self.dropdown2 = Dropdown((520, 250, 240, 40), self.algo_labels,
                                  index=self.algo2_index, on_change=self._select_algo2,
                                  accent=theme.AI)
                                  
        self.start_btn = Button((545, 320, 190, 44), "START", self._start, accent=theme.WIN)

        self.started = False
        self.countdown = 0.0
        self._cooldown = 0.0       # nhịp độ bước đi của người chơi
        self._ai_cooldown = 0.0    # nhịp độ bước đi của AI (chậm hơn)
        self.time_left = 30.0
        self._done = False
        self._build_compare()

    def _build_compare(self) -> None:
        """(Xây dựng lại) kịch bản đối đầu với (các) thuật toán AI hiện đang được chọn."""
        ai2_alg = self.algo_keys[self.algo2_index]
        self.session.algorithm = ai2_alg
        self.algo2_name = self.algo_labels[self.algo2_index]
        
        ai1_alg = self.algo_keys[self.algo1_index] if self.is_ai_vs_ai else None
        self.algo1_name = self.algo_labels[self.algo1_index]

        self.compare = CompareMode(generator=self.generator,
                                   ai_algorithm=ai2_alg,
                                   player_algorithm=ai1_alg)
        self._cooldown = 0.0
        self._ai_cooldown = 0.0

    def _select_compare_type(self, index: int) -> None:
        self.is_ai_vs_ai = (index == 1)
        self._build_compare()

    def _select_algo1(self, index: int) -> None:
        self.algo1_index = index
        self._build_compare()

    def _select_algo2(self, index: int) -> None:
        self.algo2_index = index
        self._build_compare()

    def _start(self) -> None:
        """Bắt đầu lượt chạy đối đầu với thuật toán đã chọn."""
        self.started = True
        self.countdown = 3.0

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        if not self.started:
            if not self.type_tabs.handle(event):
                if self.is_ai_vs_ai and self.dropdown1.open:
                    if self.dropdown1.handle(event): return
                elif self.dropdown2.open:
                    if self.dropdown2.handle(event): return
                else:
                    if self.is_ai_vs_ai: self.dropdown1.handle(event)
                    self.dropdown2.handle(event)
            self.start_btn.handle(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.app.go_to("main")
            return
        # Khi kết thúc, nút "Xem Thống kê" trên biểu ngữ người thắng cuộc sẽ được kích hoạt.
        if self._done and hasattr(self, "stats_btn"):
            self.stats_btn.handle(event)
        if event.type == pygame.KEYDOWN:
            if hasattr(self.compare.player, "input") and self.compare.player.input:
                action = self.compare.player.input.from_pygame_key(event.key)
                if action is not None:
                    # Chống spam: chỉ đưa vào hàng đợi nếu không có hành động nào đang chờ xử lý
                    if not self.compare.player._queue:
                        self.compare.player.queue_action(action)
            elif event.key == pygame.K_ESCAPE:
                self.app.go_to("main")

    def update(self, dt: float) -> None:
        if not self.started:
            return
            
        if self.countdown > 0:
            self.countdown -= dt
            return
            
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            if not self._done:
                self._done = True
                self._finish_compare()
            return
        self._cooldown -= dt
        if self._cooldown <= 0:
            # Người chơi và AI giờ đây có tốc độ bằng nhau (0.54 giây mỗi quyết định)
            self._cooldown = 0.54
            if not self.compare.player.finished:
                self.compare.update_player()
        # AI bước đi chậm hơn người chơi.
        self._ai_cooldown -= dt
        if self._ai_cooldown <= 0:
            self._ai_cooldown = 0.54
            if not self.compare.ai.finished:
                self.compare.update_ai()
        if self.compare.finished and not self._done:
            self._done = True
            self._finish_compare()

    def _finish_compare(self) -> None:
        report = self.compare.report()
        # AI 2 (Bên phải)
        self.session.last_engine = self.compare.ai_engine
        self.session.last_score = report.ai_score
        self.session.last_label = f"AI 2 ({self.algo2_name})" if self.is_ai_vs_ai else f"AI ({self.algo2_name})"
        
        # Người chơi hoặc AI 1 (Bên trái)
        self.session.compare_engine = self.compare.player_engine
        self.session.compare_score = report.player_score
        self.session.compare_label = f"AI 1 ({self.algo1_name})" if self.is_ai_vs_ai else "YOU (Manual)"
        
        self.session.last_mode = "compare"

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "COMPARE MODE", (theme.WIDTH // 2, 50),
                         size=30, color=theme.WIN, family="display", bold=True, center=True)
        self.back.draw(surface)
        player_title = f"AI 1 ({self.algo1_name})" if self.is_ai_vs_ai else "YOU (Manual)"
        self.player_view.draw(surface, self.compare.player_engine, title=player_title)
        self.ai_view.draw(surface, self.compare.ai_engine, title=f"AI 2 ({self.algo2_name})")

        # Các dải hiển thị hành khách trên tàu bên dưới mỗi thang máy (được di chuyển lên để không bị che bởi thanh chữ chạy).
        draw_onboard_strip(surface, pygame.Rect(18, 630, 484, 52),
                           self.compare.player_engine, accent=theme.HUMAN, spr_h=36)
        draw_onboard_strip(surface, pygame.Rect(778, 630, 484, 52),
                           self.compare.ai_engine, accent=theme.AI, spr_h=36)

        panel = pygame.Rect(510, 90, 260, 560)
        theme.draw_panel(surface, panel)

        if not self.started:
            self._draw_setup(surface, panel)
        else:
            self._draw_scoreboard(surface, panel)

        if self._done:
            self._draw_winner(surface, self.compare.report())
            
        if self.countdown > 0:
            theme.draw_countdown(surface, self.countdown)

    def _draw_setup(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        """Bảng thiết lập trước khi chạy: chọn thuật toán của AI, sau đó BẮT ĐẦU."""
        theme.render_text(surface, "COMPARE SETUP", (panel.centerx, panel.y + 15),
                         size=18, color=theme.WIN, center=True, bold=True)
        
        self.type_tabs.draw(surface)
        
        if self.is_ai_vs_ai:
            theme.render_text(surface, "Watch two AIs compete:",
                             (panel.centerx, panel.y + 175), size=14,
                             color=theme.TEXT_MUTED, center=True)
        else:
            theme.render_text(surface, "AI ALGORITHM", (panel.centerx, panel.y + 175),
                             size=14, color=theme.AI, center=True, bold=True)
        
        self.start_btn.draw(surface)
        
        if self.is_ai_vs_ai:
            theme.render_text(surface, "Starts automatically",
                             (panel.centerx, panel.bottom - 40), size=14,
                             color=theme.TEXT_MUTED, center=True)
            self.dropdown2.draw(surface)
            self.dropdown1.draw(surface)
            # Vẽ các lớp phủ ngược lại để lớp 1 hiển thị trên cùng nếu cả hai đều đang mở.
            self.dropdown2.draw_overlay(surface)
            self.dropdown1.draw_overlay(surface)
        else:
            theme.render_text(surface, "You drive with arrow keys + Space",
                             (panel.centerx, panel.bottom - 40), size=14,
                             color=theme.HUMAN, center=True)
            self.dropdown2.draw(surface)
            self.dropdown2.draw_overlay(surface)

    def _draw_scoreboard(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        """Bảng điểm trực tiếp trong quá trình chạy."""
        timer_color = theme.TEXT if self.time_left > 10 else theme.WARN
        theme.render_text(surface, f"TIME: {self.time_left:.1f}s", (panel.centerx, panel.y + 12),
                         size=18, color=timer_color, center=True, bold=True)
        
        report = self.compare.report()
        theme.render_text(surface, "HEAD-TO-HEAD", (panel.centerx, panel.y + 40),
                         size=14, color=theme.TEXT_MUTED, center=True, bold=True)
        p1_label = "AI 1" if self.is_ai_vs_ai else "YOU"
        p2_label = "AI 2" if self.is_ai_vs_ai else "AI"
        headers = [("", p1_label, p2_label)]
        rows = [
            ("Wait", f"{report.player_wait:.1f}", f"{report.ai_wait:.1f}"),
            ("Dist", str(report.player_distance), str(report.ai_distance)),
            ("Urgent", str(report.player_urgent), str(report.ai_urgent)),
            ("Fail", report.player_failures, report.ai_failures),
            ("Score", str(report.player_score), str(report.ai_score)),
        ]
        cols = [panel.x + 16, panel.x + 130, panel.x + 195]
        y = panel.y + 53
        for label, pv, av in headers + rows:
            theme.render_text(surface, label, (cols[0], y + 5), size=15, color=theme.TEXT_MUTED)
            theme.render_text(surface, pv, (cols[1], y + 5), size=15, color=theme.HUMAN,
                             family="mono", bold=True)
            theme.render_text(surface, av, (cols[2], y + 5), size=15, color=theme.AI,
                             family="mono", bold=True)
            y += 32

        if self.is_ai_vs_ai:
            theme.render_text(surface, "Watching AIs run...",
                             (panel.centerx, panel.bottom - 60), size=13,
                             color=theme.TEXT_MUTED, center=True)
        else:
            theme.render_text(surface, "Drive with keys",
                             (panel.centerx, panel.bottom - 60), size=13,
                             color=theme.HUMAN, center=True)
        status = f"{p2_label}: running..." if not self.compare.ai.finished else f"{p2_label}: done"
        theme.render_text(surface, status, (panel.centerx, panel.bottom - 36),
                         size=13, color=theme.TEXT_MUTED, center=True)

    def _draw_winner(self, surface: pygame.Surface, report) -> None:
        overlay = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 9, 20, 220)) # Slightly darker
        surface.blit(overlay, (0, 0))
        
        # Biểu ngữ lớn hơn để phù hợp với bảng kết quả
        banner = pygame.Rect(theme.WIDTH // 2 - 280, theme.HEIGHT // 2 - 180, 560, 360)
        winner = report.winner
        accent = {"Player": theme.HUMAN, "AI": theme.AI}.get(winner, theme.TEXT_MUTED)
        theme.draw_panel(surface, banner, fill=theme.SURFACE_HI, border=accent, border_w=2)
        
        if self.is_ai_vs_ai:
            title_map = {"AI 1": "AI 1 WINS!", "AI 2": "AI 2 WINS!", "Tie": "TIE"}
            title = title_map.get(winner, "TIE")
            p1_label, p2_label = "AI 1", "AI 2"
        else:
            title_map = {"Player": "YOU WIN!", "AI": "AI WINS!", "Tie": "TIE"}
            title = title_map.get(winner, "TIE")
            p1_label, p2_label = "YOU", "AI"
            
        theme.render_text(surface, title, (banner.centerx, banner.y + 40),
                         size=42, color=accent, family="display", bold=True, center=True)
        
        # Bảng kết quả bên trong biểu ngữ
        y = banner.y + 100
        cols = [banner.x + 40, banner.x + 240, banner.x + 400]
        
        # Tiêu đề cột
        theme.render_text(surface, "METRIC", (cols[0], y), size=16, color=theme.TEXT_MUTED, bold=True)
        theme.render_text(surface, p1_label, (cols[1], y), size=16, color=theme.HUMAN, bold=True)
        theme.render_text(surface, p2_label, (cols[2], y), size=16, color=theme.AI, bold=True)
        
        pygame.draw.line(surface, (theme.BORDER[0], theme.BORDER[1], theme.BORDER[2], 100), 
                         (banner.x + 30, y + 25), (banner.right - 30, y + 25), 1)
        
        rows = [
            ("Avg Wait", f"{report.player_wait:.1f}s", f"{report.ai_wait:.1f}s"),
            ("Distance", str(report.player_distance), str(report.ai_distance)),
            ("Fail (L/A)", report.player_failures, report.ai_failures),
            ("FINAL SCORE", str(report.player_score), str(report.ai_score)),
        ]
        
        y += 40
        for i, (label, p1v, p2v) in enumerate(rows):
            is_score = (label == "FINAL SCORE")
            color = theme.GOLD if is_score else theme.TEXT
            theme.render_text(surface, label, (cols[0], y), size=16 if not is_score else 20, 
                             color=theme.TEXT_MUTED if not is_score else theme.GOLD, bold=is_score)
            theme.render_text(surface, p1v, (cols[1], y), size=16 if not is_score else 22, 
                             color=theme.HUMAN if not is_score else theme.GOLD, family="mono", bold=is_score)
            theme.render_text(surface, p2v, (cols[2], y), size=16 if not is_score else 22, 
                             color=theme.AI if not is_score else theme.GOLD, family="mono", bold=is_score)
            y += 35
            
        # Chú thích cuối bảng tổng kết
        sub = f"Winner leads by {report.margin} points" if report.margin else "It's a dead heat!"
        theme.render_text(surface, sub, (banner.centerx, banner.bottom - 82),
                         size=16, color=theme.TEXT_MUTED, center=True)
                         
        if not hasattr(self, "stats_btn"):
            self.stats_btn = Button((banner.centerx - 80, banner.bottom - 70, 160, 44),
                                    "View Stats", lambda: self.app.go_to("stats"),
                                    accent=theme.WIN)
        self.stats_btn.draw(surface)
        
        theme.render_text(surface, "Press Esc to return to Main Menu",
                         (banner.centerx, banner.bottom - 15), size=12,
                         color=theme.TEXT_MUTED, center=True)

    def handle_event_late(self, event: pygame.event.Event) -> None:  # pragma: no cover
        if self._done and hasattr(self, "stats_btn"):
            self.stats_btn.handle(event)
