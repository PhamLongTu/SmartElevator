import pygame
from models.enums import PassengerType
from views import theme
from utils.settings import NUM_FLOORS

class ScenarioTableUI:
    """Hiển thị bảng cấu hình kịch bản AI tương tác."""
    def __init__(self, rect: pygame.Rect, table):
        self.rect = rect
        self.table = table
        self.selected_row = 0
        self.selected_col = 1 # Bắt đầu tại cột Tầng đón (Spawn Floor)
        
        # Chiều rộng các cột (Cân đối để dễ đọc và chừa không gian hiển thị lỗi)
        self.cols = [80, 120, 100, 120, 140, 140]
        self.headers = ["ID", "Spawn Floor", "Side", "Destination", "Time (s)", "Character"]
        
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_row = (self.selected_row - 1) % 15
            elif event.key == pygame.K_DOWN:
                self.selected_row = (self.selected_row + 1) % 15
            elif event.key == pygame.K_LEFT:
                self.selected_col = max(1, self.selected_col - 1)
            elif event.key == pygame.K_RIGHT:
                self.selected_col = min(len(self.cols) - 1, self.selected_col + 1)
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self._toggle_current_cell()
            
            # Nhập số cho Thời gian xuất hiện (Spawn Time)
            if self.selected_col == 4:
                if event.key >= pygame.K_0 and event.key <= pygame.K_9:
                    row = self.table.rows[self.selected_row]
                    val = int(event.unicode)
                    # Nếu vừa mới bắt đầu nhập (0), thay thế. Nếu không, viết tiếp vào sau.
                    if row.spawn_time == 0:
                        row.spawn_time = val
                    else:
                        new_val = row.spawn_time * 10 + val
                        if new_val <= 300: # Giới hạn ở mức 300 giây
                            row.spawn_time = new_val
                elif event.key == pygame.K_BACKSPACE:
                    row = self.table.rows[self.selected_row]
                    row.spawn_time //= 10

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                rel_x = event.pos[0] - self.rect.x
                rel_y = event.pos[1] - self.rect.y
                
                # Chiều cao tiêu đề là 40
                if rel_y > 40:
                    clicked_row = (rel_y - 40) // 34
                    if 0 <= clicked_row < 15:
                        self.selected_row = clicked_row
                        
                        # Xác định cột
                        curr_x = 0
                        for i, w in enumerate(self.cols):
                            if curr_x <= rel_x < curr_x + w:
                                if i > 0: # Không thể chọn cột ID hành khách (Passenger #)
                                    self.selected_col = i
                                    self._toggle_current_cell() # Tự động chuyển đổi khi nhấp chuột
                                break
                            curr_x += w

    def _toggle_current_cell(self):
        row = self.table.rows[self.selected_row]
        if self.selected_col == 1: # Tầng đón (Spawn Floor)
            row.spawn_floor = (row.spawn_floor + 1) % NUM_FLOORS
        elif self.selected_col == 2: # Bên (Side)
            row.spawn_side = "RIGHT" if row.spawn_side == "LEFT" else "LEFT"
        elif self.selected_col == 3: # Tầng đến (Destination)
            row.destination = (row.destination + 1) % NUM_FLOORS
        elif self.selected_col == 5: # Nhân vật (Loại hành khách)
            types = list(PassengerType)
            curr_idx = types.index(row.passenger_type)
            row.passenger_type = types[(curr_idx + 1) % len(types)]

    def draw(self, surface: pygame.Surface):
        # Background
        theme.draw_panel(surface, self.rect, fill=theme.BG_BOTTOM)
        
        # Tiêu đề cột
        header_y = self.rect.y
        curr_x = self.rect.x
        for i, header in enumerate(self.headers):
            h_rect = pygame.Rect(curr_x, header_y, self.cols[i], 40)
            pygame.draw.rect(surface, theme.SURFACE_HI, h_rect)
            pygame.draw.rect(surface, theme.BORDER, h_rect, 1)
            theme.render_text(surface, header, h_rect.center, size=14, color=theme.AI, bold=True, center=True)
            curr_x += self.cols[i]
            
        # Các hàng dữ liệu
        for i, row in enumerate(self.table.rows):
            row_y = self.rect.y + 40 + i * 34
            curr_x = self.rect.x
            
            # Tô sáng hàng đang chọn
            if i == self.selected_row:
                pygame.draw.rect(surface, (40, 40, 60), (self.rect.x, row_y, sum(self.cols), 34))
            
            # Nền / viền báo lỗi nếu dữ liệu không hợp lệ
            if not row.is_valid:
                # Subtly tint the row background red
                pygame.draw.rect(surface, (60, 20, 20), (self.rect.x, row_y, sum(self.cols), 34))
                # Thicker red border
                pygame.draw.rect(surface, theme.WARN, (self.rect.x, row_y, sum(self.cols), 34), 2)
                
                # Hiển thị thông báo lỗi - hiện tại đã được tích hợp hoặc căn lề tốt hơn
                # Chúng tôi sẽ đặt nó ở cuối hàng, kèm theo nền để làm nổi bật
                theme.render_text(surface, f"! {row.error_message}", (self.rect.x + sum(self.cols) + 10, row_y + 10), 
                                 size=12, color=theme.WARN, bold=True)

            # Columns
            data = [
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
                
                # Tô sáng ô đang hoạt động
                if i == self.selected_row and j == self.selected_col:
                    pygame.draw.rect(surface, theme.AI, cell_rect, 2)
                
                color = theme.TEXT
                if j == 0: color = theme.TEXT_MUTED
                if j == 5 and row.passenger_type == PassengerType.URGENT: color = theme.WARN
                
                theme.render_text(surface, val, cell_rect.center, size=14, color=color, center=True)
                curr_x += self.cols[j]
