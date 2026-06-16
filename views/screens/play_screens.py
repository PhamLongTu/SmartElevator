"""Màn hình chơi game: Chế độ Thủ công và Chế độ AI."""

from __future__ import annotations

import pygame
import os

from algorithms.algorithm_factory import AlgorithmFactory
from controllers.ai_mode import AIMode
from controllers.manual_mode import ManualMode
from models.enums import ElevatorAction, PassengerType
from simulation import RandomScenarioGenerator, SimulationEngine
from statistics import ScoreManager, StatisticsManager
from views import theme
from views.app import Screen
from views.building_view import BuildingView, draw_hud, draw_onboard_strip
from views.widgets import Button, Dropdown
from controllers.scenario_table import ScenarioTable
from controllers.scenario_validator import ScenarioValidator
from controllers.scenario_summary import ScenarioSummary
from controllers.scenario_serializer import ScenarioSerializer
from controllers.spawn_controller import SpawnController
from views.scenario_table_ui import ScenarioTableUI


def _new_engine(session) -> SimulationEngine:
    """Xây dựng engine từ các thiết lập kịch bản trong phiên (session) chung."""
    engine = SimulationEngine(
        stats=StatisticsManager(),
        generator=RandomScenarioGenerator(
            num_passengers=session.passengers, seed=session.seed
        ),
    )
    engine.new_scenario()
    return engine


class ManualScreen(Screen):
    """Thang máy do người chơi điều khiển bằng các phím W/S/Space (hoặc Mũi tên)."""

    def on_enter(self) -> None:
        self.engine = _new_engine(self.session)
        self.controller = ManualMode(self.engine, score=ScoreManager())
        self.view = BuildingView(pygame.Rect(30, 90, 720, 560), accent=theme.HUMAN)
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.reset_btn = Button((1150, 30, 100, 40), "Reset", self._reset, accent=theme.WARN)
        self.start_btn = Button((935, 558, 160, 44), "START", self._start, accent=theme.WIN)
        self.started = False
        self.countdown = 0.0
        self._move_cooldown = 0.0
        self.time_left = 30.0

    def _start(self) -> None:
        self.started = True
        self.countdown = 3.0

    def _reset(self) -> None:
        self.engine.reset()
        self.controller.score.reset()

    def _finish(self) -> None:
        self.session.last_engine = self.engine
        self.session.last_score = self.controller.score.value
        self.session.last_label = "Manual (You)"
        self.session.last_mode = "manual"
        # Xóa dữ liệu cũ của Chế độ Đối đầu để màn hình Thống kê không hiển thị các tab cũ
        self.session.compare_engine = None
        self.app.go_to("stats")

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        if not self.started:
            self.start_btn.handle(event)
            return

        self.reset_btn.handle(event)
        if event.type == pygame.KEYDOWN:
            action = self.controller.input.from_pygame_key(event.key)
            if action is not None:
                # Chống spam: chỉ đưa vào hàng đợi nếu không có hành động nào đang chờ xử lý
                if not self.controller._queue:
                    self.controller.queue_action(action)
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
            self._finish()
            return

        # Áp dụng các hành động đã xếp hàng với nhịp độ ổn định, dễ quan sát.
        self._move_cooldown -= dt
        if self._move_cooldown <= 0 and not self.controller.finished:
            result = self.controller.update()
            if result is not None:
                # Đồng bộ với tốc độ của AI
                self._move_cooldown = 0.54
        if self.controller.finished:
            self._finish()

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "MANUAL MODE", (theme.WIDTH // 2, 50),
                         size=30, color=theme.HUMAN, family="display", bold=True, center=True)
        self.back.draw(surface)
        self.reset_btn.draw(surface)
        self.view.draw(surface, self.engine, title="BUILDING")
        
        timer_color = theme.TEXT if self.time_left > 10 else theme.WARN
        extra = [("Session Time", f"{self.time_left:.1f}s", timer_color)]
        draw_hud(surface, pygame.Rect(780, 90, 470, 360), self.engine,
                 self.controller.score.value, accent=theme.HUMAN, extra=extra)
        if not self.started:
            # Nút BẮT ĐẦU nằm ở bảng bên phải, tách biệt khỏi phần tòa nhà.
            panel = pygame.Rect(780, 470, 470, 180)
            theme.draw_panel(surface, panel)
            theme.render_text(surface, "Press START to begin driving",
                             (panel.centerx, panel.y + 50),
                             size=16, color=theme.TEXT_MUTED, center=True)
            self.start_btn.draw(surface)
            return

        if self.countdown > 0:
            theme.draw_countdown(surface, self.countdown)

        # Thanh điều khiển.
        bar = pygame.Rect(780, 470, 470, 180)
        theme.draw_panel(surface, bar)
        theme.render_text(surface, "CONTROLS", (bar.x + 18, bar.y + 14),
                         size=14, color=theme.HUMAN, bold=True)
        keys = [(1, "Move Up"), (-1, "Move Down"), ("Space", "Open Door (serve)")]
        for i, (k, desc) in enumerate(keys):
            y = bar.y + 50 + i * 38
            key_rect = pygame.Rect(bar.x + 20, y, 90, 30)
            theme.draw_panel(surface, key_rect, fill=theme.SURFACE_HI, border=theme.HUMAN)
            if isinstance(k, int):
                theme.draw_arrow(surface, key_rect.center, k, size=14, color=theme.HUMAN)
            else:
                theme.render_text(surface, k, key_rect.center, size=16, color=theme.HUMAN,
                                 center=True, bold=True)
            theme.render_text(surface, desc, (bar.x + 130, y + 4), size=17, color=theme.TEXT)


class AIScreen(Screen):
    """Thang máy do AI điều khiển với khả năng chọn thuật toán và hình ảnh hóa quá trình tìm kiếm."""

    def on_enter(self) -> None:
        self.engine = _new_engine(self.session)
        self.algo_keys = AlgorithmFactory.available()
        self.algo_labels = [AlgorithmFactory.info(k).display_name for k in self.algo_keys]
        self.algo_index = self.algo_keys.index(self.session.algorithm) \
            if self.session.algorithm in self.algo_keys else self.algo_keys.index("astar")
        
        self.view = BuildingView(pygame.Rect(30, 90, 720, 560), accent=theme.AI)
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.dropdown = Dropdown((980, 40, 270, 40), self.algo_labels,
                                 index=self.algo_index, on_change=self._select_algo,
                                 accent=theme.AI)
        
        self.state = "PREVIEW"
        self.table = ScenarioTable()
        self.table_ui = ScenarioTableUI(pygame.Rect(30, 90, 700, 560), self.table)
        self.spawn_ctrl = SpawnController(self.engine)
        self.engine.extra_finished_check = self.spawn_ctrl.is_finished
        # Các nút cho chế độ Thiết lập (Căn chỉnh cân đối)
        btn_center_x = 950 + 150 - 110 # Tâm của bảng 300px là 950+150, chiều rộng nút là 220
        self.random_btn = Button((btn_center_x, 520, 220, 40), "RANDOM", lambda: self.table.randomize("Medium"), accent=theme.AI)
        self.reset_btn = Button((btn_center_x, 580, 220, 40), "RESET", self.table.reset, accent=theme.WARN)
        self.save_btn = Button((btn_center_x, 640, 220, 46), "SAVE & BACK", self._save_setup, accent=theme.WIN)
        
        # Các nút cho chế độ Xem trước (hàng dưới cùng)
        self.goto_setup_btn = Button((830, 640, 200, 40), "SET UP", self._go_to_setup, accent=theme.AI)
        self.play_start_btn = Button((1050, 640, 200, 40), "PLAY", self._start_play, accent=theme.WIN)
        
        # Tải kịch bản ban đầu
        if self.session.ai_scenario_rows:
            self.table.import_data(self.session.ai_scenario_rows)
            
        self.spawn_ctrl.load_scenario(self.table.get_requests())
        self.planned = []
        self._build_controller() # Xây dựng kế hoạch ban đầu cho chế độ xem trước
        
        self.playing = False
        self.validation_error = ""
        self.validation_timer = 0.0
        self.speeds = [0.5, 1.0, 2.0, 4.0]
        self.speed_i = 1
        self.play_btn = Button((830, 640, 120, 40), "Pause", self._toggle_play, accent=theme.AI)
        self.step_btn = Button((960, 640, 110, 40), "Step", self._single_step, accent=theme.AI)
        self.speed_btn = Button((1080, 640, 130, 40), "Speed 1x", self._cycle_speed, accent=theme.AI)
        self._cooldown = 0.0
        self.time_limit = 45.0 # Độ dài phiên cố định
        self.time_left = self.time_limit

    def _go_to_setup(self) -> None:
        self.state = "SETUP"

    def _save_setup(self) -> None:
        if ScenarioValidator.validate_all(self.table.rows):
            self.state = "PREVIEW"
            # Xóa kịch bản ngẫu nhiên cũ để việc reset() không nạp lại những hành khách cũ
            self.engine.scenario = None
            self.engine.reset()
            self.spawn_ctrl.load_scenario(self.table.get_requests())
            # Xây dựng lại bộ điều khiển AI để chế độ XEM TRƯỚC phản ánh thiết lập mới
            self._build_controller()
            # Lưu lại vào phiên (session)
            self.session.ai_scenario_rows = self.table.export_data()
            self.validation_error = ""
        else:
            self.validation_error = "Bảng dữ liệu không hợp lệ! Vui lòng kiểm tra các ô màu đỏ."
            self.validation_timer = 3.0
            print("Validation failed!")

    def _start_play(self) -> None:
        self.state = "RUNNING"
        self.playing = True
        self.countdown = 3.0
        self.time_left = self.time_limit
        
        # Đảm bảo bắt đầu mới hoàn toàn
        self.engine.scenario = None
        self.engine.reset()
        self._build_controller()

    def _validate_and_start(self) -> None:
        # Sử dụng nội bộ / Kế thừa
        self._start_play()

    def _retry(self):
        self._start_play()

    def _new_setup(self):
        self.state = "SETUP"


    def _build_controller(self) -> None:
        self.session.algorithm = self.algo_keys[self.algo_index]
        kwargs = {"beam_width": 10} if self.session.algorithm == "beam" else {}
        self.controller = AIMode(self.engine, algorithm=self.session.algorithm,
                                 score=ScoreManager(), **kwargs)
        self.result = self.controller.plan()
        self.planned = self.controller.planned_floor_sequence()

    def _select_algo(self, index: int) -> None:
        self.algo_index = index
        if self.state == "RUNNING":
            self._build_controller()

    def _toggle_play(self) -> None:
        self.playing = not self.playing
        self.play_btn.label = "Play" if not self.playing else "Pause"

    def _single_step(self) -> None:
        self.playing = False
        self.play_btn.label = "Play"
        if not self.controller.finished:
            self.controller.update()
            # Ép buộc các NPC đang đi bộ phải đến nơi ngay lập tức để AI có thể đón
            self.spawn_ctrl.update(self.spawn_ctrl.walk_duration)

    def _cycle_speed(self) -> None:
        self.speed_i = (self.speed_i + 1) % len(self.speeds)
        self.speed_btn.label = f"Speed {self.speeds[self.speed_i]:g}x"

    def _finish(self) -> None:
        self.session.last_engine = self.engine
        self.session.last_score = self.controller.score.value
        self.session.last_label = f"AI ({self.algo_labels[self.algo_index]})"
        self.session.last_mode = "ai"
        self.app.go_to("stats")

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        
        if self.state == "PREVIEW":
            self.goto_setup_btn.handle(event)
            self.play_start_btn.handle(event)
            self.dropdown.handle(event)

        elif self.state == "SETUP":
            # Xử lý các nút TRƯỚC để chúng không bị bảng dữ liệu chặn mất sự kiện
            if self.random_btn.handle(event): return
            if self.reset_btn.handle(event): return
            if self.save_btn.handle(event): return
            if self.dropdown.handle(event): return
            self.table_ui.handle_event(event)
            
        elif self.state == "RUNNING":
            # Chặn các tương tác trong thời gian 3 giây đếm ngược
            if self.countdown <= 0:
                self.play_btn.handle(event)
                self.step_btn.handle(event)
                self.speed_btn.handle(event)
                self.dropdown.handle(event)
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go_to("main")

    def update(self, dt: float) -> None:
        if self.state == "SETUP":
            # Kiểm tra dữ liệu thời gian thực để phản hồi trên giao diện
            ScenarioValidator.validate_all(self.table.rows)
            if self.validation_timer > 0:
                self.validation_timer -= dt
            return

        if self.state == "PREVIEW":
            return

        if self.state == "RUNNING":
            # Cập nhật việc sinh và đi bộ của NPC bất kể trạng thái chơi (playing)
            self.spawn_ctrl.update(dt if self.playing else 0)

            if self.countdown > 0:
                if self.playing:
                    self.countdown -= dt
                return
            
            # Sử dụng thời gian mô phỏng để đảm bảo tính nhất quán của bộ đếm giờ
            self.time_left = max(0, self.time_limit - self.engine.time) 
            if self.time_left <= 0:
                self.playing = False
                self._finish()
                return
                
            if self.playing and not self.controller.finished:
                self._cooldown -= dt * self.speeds[self.speed_i]
                if self._cooldown <= 0:
                    self.controller.update()
                    self.result = self.controller.result
                    self.planned = self.controller.planned_floor_sequence()
                    self._cooldown = 0.54
            if self.controller.finished and self.playing and self.spawn_ctrl.is_finished():
                self.playing = False
                self._finish()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BG_TOP)
        self.back.draw(surface)
        
        if self.state == "SETUP":
            title = "AI SCENARIO SETUP"
        else:
            title = "AI SIMULATION"
        theme.render_text(surface, title, (600, 45),
                         size=28, color=theme.AI, family="display", bold=True, center=True)
        
        if self.state == "SETUP":
            self.table_ui.draw(surface)
            
            # Bảng Tổng quan (Căn biên phải)
            panel_rect = pygame.Rect(950, 90, 300, 420)
            theme.draw_panel(surface, panel_rect)
            theme.render_text(surface, "SCENARIO SUMMARY", (panel_rect.x + 20, panel_rect.y + 15), 
                             size=14, color=theme.AI, bold=True)
            
            summary = ScenarioSummary.calculate(self.table.rows)
            rows = [
                ("Total Passengers", str(summary["total"])),
                ("Normal", str(summary["normal"])),
                ("Urgent", str(summary["urgent"])),
                ("Avg Spawn Time", f"{summary['avg_spawn_time']:.1f}s"),
                ("Avg Distance", f"{summary['avg_dist']:.1f}f"),
                ("Density", f"{summary['density']:.2f}")
            ]
            for i, (l, v) in enumerate(rows):
                y = panel_rect.y + 50 + i * 28
                theme.render_text(surface, l, (panel_rect.x + 20, y), size=15, color=theme.TEXT_MUTED)
                theme.render_text(surface, v, (panel_rect.right - 20, y), size=15, color=theme.TEXT, right=True, bold=True)
                
            # Huy hiệu Độ khó
            diff_y = panel_rect.y + 240
            pygame.draw.rect(surface, theme.SURFACE_HI, (panel_rect.x + 20, diff_y, panel_rect.width - 40, 60), border_radius=8)
            theme.render_text(surface, "DIFFICULTY", (panel_rect.centerx, diff_y + 12), size=12, color=theme.TEXT_MUTED, center=True)
            
            colors = {"Easy": theme.WIN, "Medium": theme.GOLD, "Hard": theme.WARN, "Extreme": (255, 0, 0)}
            theme.render_text(surface, summary["difficulty"].upper(), (panel_rect.centerx, diff_y + 35), 
                             size=22, color=colors.get(summary["difficulty"], theme.TEXT), center=True, bold=True)

            if self.validation_error and self.validation_timer > 0:
                # Nằm ở giữa trên cùng, dưới tiêu đề
                theme.render_text(surface, self.validation_error, (600, 85),
                                 size=16, color=theme.WARN, center=True, bold=True)

            self.random_btn.draw(surface)
            self.reset_btn.draw(surface)
            self.save_btn.draw(surface)
            self.dropdown.draw(surface)
            self.dropdown.draw_overlay(surface)
            return

        if self.state == "PREVIEW":
            # Chế độ xem tòa nhà chung
            self.view.draw(surface, self.engine, title="AI SIMULATION PREVIEW")
        else:
            self.view.draw(surface, self.engine, walking_npcs=self.spawn_ctrl.walking_npcs,
                           planned_floors=self.planned, title="AI SIMULATION")

        # --- Các bảng bên phải dùng chung (Hình ảnh hóa tìm kiếm, Khách trên tàu, HUD) ---
        # Search visualization panel
        panel = pygame.Rect(780, 84, 480, 266)
        theme.draw_panel(surface, panel)
        theme.render_text(surface, "SEARCH VISUALIZATION", (panel.x + 18, panel.y + 14),
                         size=14, color=theme.AI, bold=True)
        
        # Ở chế độ Xem trước tại t=0, chúng ta vẫn muốn hiển thị kết quả kế hoạch hiện tại (mặc định)
        res = self.result or self.controller.result
        metrics = [
            ("Nodes expanded", str(res.nodes_expanded)),
            ("Nodes generated", str(res.nodes_generated)),
            ("Runtime", f"{res.planning_time_ms:.2f} ms"),
            ("Solution cost", f"{res.cost:.1f}"),
        ]
        for i, (label, value) in enumerate(metrics):
            y = panel.y + 54 + i * 28
            theme.render_text(surface, label, (panel.x + 18, y), size=16, color=theme.TEXT_MUTED)
            theme.render_text(surface, value, (panel.right - 18, y), size=16,
                             color=theme.AI, family="mono", bold=True, right=True)

        # Dải hiển thị hành khách đang trên thang máy
        onboard_rect = pygame.Rect(panel.x + 12, panel.y + 176, panel.width - 24, 78)
        draw_onboard_strip(surface, onboard_rect, self.engine, accent=theme.AI, spr_h=54)

        # Thanh tiến trình
        done, total_act = self.controller.progress if hasattr(self, "controller") else (0, 0)
        bar_bg = pygame.Rect(780, 360, 470, 26)
        theme.draw_panel(surface, bar_bg, fill=theme.SURFACE_HI)
        if total_act:
            fill_w = int(bar_bg.width * done / total_act)
            if fill_w > 0:
                pygame.draw.rect(surface, theme.AI,
                                 pygame.Rect(bar_bg.x, bar_bg.y, fill_w, bar_bg.height),
                                 border_radius=14)
        theme.render_text(surface, f"{done} / {total_act} actions", bar_bg.center,
                         size=14, color=theme.TEXT, center=True, bold=True)

        # Thiết bị hiển thị (Chỉ số)
        timer_color = theme.TEXT if self.time_left > 10 else theme.WARN
        extra = [("Session Time", f"{self.time_left:.1f}s", timer_color)]
        score_val = self.controller.score.value if hasattr(self, "controller") else 0
        draw_hud(surface, pygame.Rect(780, 394, 470, 276), self.engine,
                 score_val, accent=theme.AI, extra=extra)

        # --- Các nút điều khiển phía dưới (Theo ngữ cảnh) ---
        if self.state == "PREVIEW":
            self.goto_setup_btn.draw(surface)
            self.play_start_btn.draw(surface)
        else:
            self.play_btn.draw(surface)
            self.step_btn.draw(surface)
            self.speed_btn.draw(surface)
            
        self.dropdown.draw(surface)
        self.dropdown.draw_overlay(surface)
        
        if self.state == "RUNNING" and self.countdown > 0:
            theme.draw_countdown(surface, self.countdown)
        if self.state == "RUNNING" and self.countdown > 0:
            theme.draw_countdown(surface, self.countdown)
