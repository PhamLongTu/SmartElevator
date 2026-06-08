"""Play screens: Manual Mode and AI Mode."""

from __future__ import annotations

import pygame

from algorithms.algorithm_factory import AlgorithmFactory
from controllers.ai_mode import AIMode
from controllers.manual_mode import ManualMode
from models.enums import ElevatorAction
from simulation import RandomScenarioGenerator, SimulationEngine
from statistics import ScoreManager, StatisticsManager
from views import theme
from views.app import Screen
from views.building_view import BuildingView, draw_hud
from views.widgets import Button, Dropdown


def _new_engine(session) -> SimulationEngine:
    """Build an engine from the shared session's scenario setup."""
    engine = SimulationEngine(
        stats=StatisticsManager(),
        generator=RandomScenarioGenerator(
            num_passengers=session.passengers, seed=session.seed
        ),
    )
    engine.new_scenario()
    return engine


class ManualScreen(Screen):
    """Player-driven elevator with W/S/Space controls."""

    def on_enter(self) -> None:
        self.engine = _new_engine(self.session)
        self.controller = ManualMode(self.engine, score=ScoreManager())
        self.view = BuildingView(pygame.Rect(30, 90, 720, 560), accent=theme.HUMAN)
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.reset_btn = Button((1150, 30, 100, 40), "Reset", self._reset, accent=theme.WARN)
        self.start_btn = Button((theme.WIDTH // 2 - 80, theme.HEIGHT // 2 - 22, 160, 44), "START", self._start, accent=theme.WIN)
        self.started = False
        self.countdown = 0.0
        self._move_cooldown = 0.0

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
                self.controller.queue_action(action)
            elif event.key == pygame.K_ESCAPE:
                self.app.go_to("main")

    def update(self, dt: float) -> None:
        if not self.started:
            return
        if self.countdown > 0:
            self.countdown -= dt
            return

        # Apply queued actions at a steady, readable cadence.
        self._move_cooldown -= dt
        if self._move_cooldown <= 0 and not self.controller.finished:
            result = self.controller.update()
            if result is not None:
                self._move_cooldown = 0.18
        if self.controller.finished:
            self._finish()

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "MANUAL MODE", (theme.WIDTH // 2, 50),
                         size=30, color=theme.HUMAN, family="display", bold=True, center=True)
        self.back.draw(surface)
        self.reset_btn.draw(surface)
        self.view.draw(surface, self.engine, title="BUILDING")
        draw_hud(surface, pygame.Rect(780, 90, 470, 360), self.engine,
                 self.controller.score.value, accent=theme.HUMAN)
        
        if not self.started:
            self.start_btn.draw(surface)
            theme.render_text(surface, "Press START to begin driving", (theme.WIDTH // 2, theme.HEIGHT // 2 + 40),
                             size=16, color=theme.TEXT_MUTED, center=True)
        elif self.countdown > 0:
            theme.draw_countdown(surface, self.countdown)

        # Controls bar.
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
    """AI-driven elevator with algorithm selection and search visualization."""

    def on_enter(self) -> None:
        self.engine = _new_engine(self.session)
        self.algo_keys = AlgorithmFactory.available()
        self.algo_labels = [AlgorithmFactory.info(k).display_name for k in self.algo_keys]
        self.algo_index = self.algo_keys.index(self.session.algorithm) \
            if self.session.algorithm in self.algo_keys else self.algo_keys.index("astar")
        self.view = BuildingView(pygame.Rect(30, 90, 720, 560), accent=theme.AI)
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.dropdown = Dropdown((980, 34, 270, 40), self.algo_labels,
                                 index=self.algo_index, on_change=self._select_algo,
                                 accent=theme.AI)
        self.started = False   # wait for the user to pick an algorithm and press START
        self.playing = False
        self.speeds = [0.5, 1.0, 2.0, 4.0]
        self.speed_i = 1
        self.start_btn = Button((630, 624, 160, 44), "START", self._start, accent=theme.WIN)
        self.play_btn = Button((630, 624, 120, 40), "Pause", self._toggle_play, accent=theme.AI)
        self.step_btn = Button((760, 624, 110, 40), "Step", self._single_step, accent=theme.AI)
        self.speed_btn = Button((880, 624, 130, 40), "Speed 1x", self._cycle_speed, accent=theme.AI)
        self._cooldown = 0.0
        self.countdown = 0.0
        self._build_controller()

    def _start(self) -> None:
        """Begin the simulation with the currently selected algorithm."""
        self.started = True
        self.countdown = 3.0  # Start countdown
        self.playing = True   # Ready to play after countdown

    def _build_controller(self) -> None:
        self.engine.reset()
        self.session.algorithm = self.algo_keys[self.algo_index]
        kwargs = {"beam_width": 10} if self.session.algorithm == "beam" else {}
        self.controller = AIMode(self.engine, algorithm=self.session.algorithm,
                                 score=ScoreManager(), **kwargs)
        self.result = self.controller.plan()
        self.planned = self.controller.planned_floor_sequence()

    def _select_algo(self, index: int) -> None:
        self.algo_index = index
        self._build_controller()
        # Resume only if the run has already begun; otherwise stay on the
        # setup screen so the user can keep choosing before pressing START.
        self.playing = self.started

    def _toggle_play(self) -> None:
        self.playing = not self.playing
        self.play_btn.label = "Play" if not self.playing else "Pause"

    def _single_step(self) -> None:
        self.playing = False
        self.play_btn.label = "Play"
        if not self.controller.finished:
            self.controller.update()

    def _cycle_speed(self) -> None:
        self.speed_i = (self.speed_i + 1) % len(self.speeds)
        self.speed_btn.label = f"Speed {self.speeds[self.speed_i]:g}x"

    def _finish(self) -> None:
        self.session.last_engine = self.engine
        self.session.last_score = self.controller.score.value
        self.session.last_label = f"AI ({self.algo_labels[self.algo_index]})"
        self.app.go_to("stats")

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        if not self.started:
            self.start_btn.handle(event)
        else:
            self.play_btn.handle(event)
            self.step_btn.handle(event)
            self.speed_btn.handle(event)
        self.dropdown.handle(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go_to("main")

    def update(self, dt: float) -> None:
        if self.countdown > 0:
            self.countdown -= dt
            return

        if self.playing and not self.controller.finished:
            self._cooldown -= dt * self.speeds[self.speed_i]
            if self._cooldown <= 0:
                self.controller.update()
                self._cooldown = 0.54
        if self.controller.finished and self.playing:
            self.playing = False
            self._finish()

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "AI MODE", (300, 50),
                         size=30, color=theme.AI, family="display", bold=True, center=True)
        self.back.draw(surface)
        self.view.draw(surface, self.engine, planned_floors=self.planned, title="BUILDING")

        # Search visualization panel.
        panel = pygame.Rect(780, 90, 470, 230)
        theme.draw_panel(surface, panel)
        theme.render_text(surface, "SEARCH VISUALIZATION", (panel.x + 18, panel.y + 14),
                         size=14, color=theme.AI, bold=True)
        if self.result.success:
            seq = "->".join(str(f) for f in self.planned[:10])
            if len(self.planned) > 10:
                seq += "->..."
            theme.render_text(surface, f"Plan: {seq}", (panel.x + 18, panel.y + 44),
                             size=15, color=theme.TEXT_MUTED, family="mono")
        else:
            theme.render_text(surface, "No complete plan found (local optimum)",
                             (panel.x + 18, panel.y + 44), size=15, color=theme.WARN)
        metrics = [
            ("Nodes expanded", str(self.result.nodes_expanded)),
            ("Nodes generated", str(self.result.nodes_generated)),
            ("Runtime", f"{self.result.planning_time_ms:.2f} ms"),
            ("Solution cost", f"{self.result.cost:.1f}"),
        ]
        for i, (label, value) in enumerate(metrics):
            y = panel.y + 80 + i * 30
            theme.render_text(surface, label, (panel.x + 18, y), size=16, color=theme.TEXT_MUTED)
            theme.render_text(surface, value, (panel.right - 18, y), size=16,
                             color=theme.AI, family="mono", bold=True, right=True)

        # Progress bar.
        done, total = self.controller.progress
        bar_bg = pygame.Rect(780, 340, 470, 26)
        theme.draw_panel(surface, bar_bg, fill=theme.SURFACE_HI)
        if total:
            fill_w = int(bar_bg.width * done / total)
            if fill_w > 0:
                pygame.draw.rect(surface, theme.AI,
                                 pygame.Rect(bar_bg.x, bar_bg.y, fill_w, bar_bg.height),
                                 border_radius=14)
        theme.render_text(surface, f"{done} / {total} actions", bar_bg.center,
                         size=14, color=theme.TEXT, center=True, bold=True)

        # HUD + controls.
        draw_hud(surface, pygame.Rect(780, 380, 470, 234), self.engine,
                 self.controller.score.value, accent=theme.AI)
        if not self.started:
            self.start_btn.draw(surface)
            theme.render_text(surface, "Pick an algorithm above, then press START",
                             (panel.right, 646), size=14, color=theme.TEXT_MUTED, right=True)
        else:
            self.play_btn.draw(surface)
            self.step_btn.draw(surface)
            self.speed_btn.draw(surface)
        self.dropdown.draw(surface)
        self.dropdown.draw_overlay(surface)
        
        if self.countdown > 0:
            theme.draw_countdown(surface, self.countdown)
