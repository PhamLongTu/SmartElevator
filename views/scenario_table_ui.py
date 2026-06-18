import pygame
from models.enums import PassengerType
from views import theme
from utils.settings import NUM_FLOORS


class ScenarioTableUI:
    """Hiển thị bảng cấu hình scenario AI tương tác."""

    def __init__(self, rect: pygame.Rect, table):
        self.rect = rect
        self.table = table
        self.selected_row = 0
        self.selected_col = 1

        self.cols = [44, 70, 120, 100, 120, 110, 140]
        self.headers = ["✓", "ID", "Spawn Floor", "Side", "Destination", "Time (s)", "Character"]

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_row = (self.selected_row - 1) % 15
            elif event.key == pygame.K_DOWN:
                self.selected_row = (self.selected_row + 1) % 15
            elif event.key == pygame.K_LEFT:
                self.selected_col = max(0, self.selected_col - 1)
            elif event.key == pygame.K_RIGHT:
                self.selected_col = min(len(self.cols) - 1, self.selected_col + 1)
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self._toggle_current_cell()

            if self.selected_col == 5:
                row = self.table.rows[self.selected_row]
                if event.key >= pygame.K_0 and event.key <= pygame.K_9:
                    val = int(event.unicode)
                    if row.spawn_time == 0:
                        row.spawn_time = val
                    else:
                        new_val = row.spawn_time * 10 + val
                        if new_val <= 300:
                            row.spawn_time = new_val
                elif event.key == pygame.K_BACKSPACE:
                    row.spawn_time //= 10

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                rel_x = event.pos[0] - self.rect.x
                rel_y = event.pos[1] - self.rect.y

                if rel_y > 40:
                    clicked_row = (rel_y - 40) // 34
                    if 0 <= clicked_row < 15:
                        self.selected_row = clicked_row

                        curr_x = 0
                        for i, w in enumerate(self.cols):
                            if curr_x <= rel_x < curr_x + w:
                                self.selected_col = i
                                self._toggle_current_cell()
                                break
                            curr_x += w

    def _toggle_current_cell(self):
        row = self.table.rows[self.selected_row]
        if self.selected_col == 0:
            row.enabled = not row.enabled
        elif self.selected_col == 2:
            row.spawn_floor = (row.spawn_floor + 1) % NUM_FLOORS
        elif self.selected_col == 3:
            row.spawn_side = "RIGHT" if row.spawn_side == "LEFT" else "LEFT"
        elif self.selected_col == 4:
            row.destination = (row.destination + 1) % NUM_FLOORS
        elif self.selected_col == 6:
            types = list(PassengerType)
            curr_idx = types.index(row.passenger_type)
            row.passenger_type = types[(curr_idx + 1) % len(types)]

    def draw(self, surface: pygame.Surface):
        theme.draw_panel(surface, self.rect, fill=theme.BG_BOTTOM)

        header_y = self.rect.y
        curr_x = self.rect.x
        for i, header in enumerate(self.headers):
            h_rect = pygame.Rect(curr_x, header_y, self.cols[i], 40)
            pygame.draw.rect(surface, theme.SURFACE_HI, h_rect)
            pygame.draw.rect(surface, theme.BORDER, h_rect, 1)
            hdr_color = (80, 200, 120) if i == 0 else theme.AI
            theme.render_text(surface, header, h_rect.center, size=14,
                              color=hdr_color, bold=True, center=True)
            curr_x += self.cols[i]

        for i, row in enumerate(self.table.rows):
            row_y = self.rect.y + 40 + i * 34
            curr_x = self.rect.x
            total_w = sum(self.cols)

            if i == self.selected_row:
                pygame.draw.rect(surface, (40, 40, 60),
                                 (self.rect.x, row_y, total_w, 34))

            if not row.is_valid:
                pygame.draw.rect(surface, (60, 20, 20),
                                 (self.rect.x, row_y, total_w, 34))
                pygame.draw.rect(surface, theme.WARN,
                                 (self.rect.x, row_y, total_w, 34), 2)
                theme.render_text(surface, f"! {row.error_message}",
                                  (self.rect.x + total_w + 10, row_y + 10),
                                  size=12, color=theme.WARN, bold=True)

            disabled_overlay = not row.enabled
            data = [
                None,
                f"P{row.id}",
                "G" if row.spawn_floor == 0 else f"F{row.spawn_floor}",
                row.spawn_side,
                "G" if row.destination == 0 else f"F{row.destination}",
                f"{row.spawn_time}s",
                row.passenger_type.name
            ]

            for j, val in enumerate(data):
                cell_rect = pygame.Rect(curr_x, row_y, self.cols[j], 34)
                pygame.draw.rect(surface, theme.BORDER, cell_rect, 1)

                if i == self.selected_row and j == self.selected_col:
                    pygame.draw.rect(surface, theme.AI, cell_rect, 2)

                if j == 0:
                    self._draw_checkbox(surface, cell_rect, row.enabled,
                                        is_selected=(i == self.selected_row and j == self.selected_col))
                else:
                    if disabled_overlay:
                        color = (80, 80, 90)
                    else:
                        color = theme.TEXT
                        if j == 1:
                            color = theme.TEXT_MUTED
                        if j == 6 and row.passenger_type == PassengerType.URGENT:
                            color = theme.WARN

                    theme.render_text(surface, val, cell_rect.center,
                                      size=14, color=color, center=True)

                curr_x += self.cols[j]

            if disabled_overlay:
                data_start_x = self.rect.x + self.cols[0]
                data_width = total_w - self.cols[0]
                dim_surf = pygame.Surface((data_width, 34), pygame.SRCALPHA)
                dim_surf.fill((0, 0, 0, 90))
                surface.blit(dim_surf, (data_start_x, row_y))

    def _draw_checkbox(self, surface: pygame.Surface, cell_rect: pygame.Rect,
                        checked: bool, is_selected: bool):
        """Vẽ checkbox ở giữa cell."""
        cx = cell_rect.centerx
        cy = cell_rect.centery
        box_size = 18

        box_rect = pygame.Rect(cx - box_size // 2, cy - box_size // 2,
                               box_size, box_size)

        bg_color = (60, 180, 100) if checked else (30, 30, 45)
        pygame.draw.rect(surface, bg_color, box_rect, border_radius=4)

        border_color = (80, 220, 120) if checked else (80, 80, 100)
        if is_selected:
            border_color = theme.AI
        pygame.draw.rect(surface, border_color, box_rect, 2, border_radius=4)

        if checked:
            pts = [
                (cx - 5, cy),
                (cx - 1, cy + 4),
                (cx + 6, cy - 5),
            ]
            pygame.draw.lines(surface, (255, 255, 255), False, pts, 2)
