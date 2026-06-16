# Smart Elevator 🏢🤖

Smart Elevator là một dự án mô phỏng và trò chơi (game) kết hợp với Trí tuệ nhân tạo (AI) tập trung vào bài toán lập lịch và điều khiển thang máy. Dự án cho phép người chơi tự tay điều khiển thang máy (Manual Mode), hoặc để các thuật toán AI tìm kiếm đường đi (AI Mode), và thậm chí so sánh hiệu năng giữa các thuật toán với nhau (Compare Mode).

## 🌟 Tính Năng Nổi Bật (Current Features)
- **Đa dạng Chế độ chơi (Game Modes)**:
  - **Manual Mode**: Tự tay bạn điều khiển thang máy (Lên, Xuống, Dừng/Đón khách) để phục vụ hành khách.
  - **AI Mode**: Hệ thống tự động sử dụng các thuật toán Tìm kiếm AI để lên kế hoạch và vận hành thang máy một cách tối ưu. AI có khả năng phản ứng lại với các thay đổi (ví dụ: hành khách mới xuất hiện).
  - **Compare Mode**: Chạy song song và so sánh trực quan hiệu quả của 2 thuật toán khác nhau trên cùng một kịch bản.
  - **Benchmark**: Chế độ đánh giá hiệu năng tự động hàng loạt.
- **Thuật toán AI phong phú**: Hỗ trợ hàng loạt các thuật toán tìm kiếm kinh điển trong AI:
  - Tìm kiếm mù (Uninformed): BFS, DFS, Uniform Cost Search (UCS).
  - Tìm kiếm theo kinh nghiệm (Informed): A* (A-Star), Greedy Search.
  - Tìm kiếm cục bộ (Local): Hill Climbing, Beam Search.
- **Cơ chế mô phỏng thực tế**:
  - Tải trọng tối đa của thang máy (Capacity).
  - Hành khách xuất hiện ngẫu nhiên theo thời gian thực với các độ ưu tiên (Normal/Urgent).
  - Điểm số (Score) dựa trên thời gian chờ đợi và thời gian di chuyển của hành khách.
- **Giao diện trực quan**: Được xây dựng bằng `Pygame` với các sprite nhân vật, hình ảnh tầng và thang máy sinh động.

---

## 🎮 Cách Vận Hành (How to Run)
1. **Yêu cầu hệ thống**: Python 3.8+ và thư viện `pygame`.
2. **Cài đặt**: 
   ```bash
   pip install pygame
   ```
3. **Khởi chạy**: 
   Mở terminal tại thư mục gốc của dự án và chạy lệnh:
   ```bash
   python main.py
   ```
4. **Thao tác**:
   - Sử dụng chuột để tương tác với các nút trên giao diện Menu.
   - Trong Manual Mode: Bạn có thể sử dụng các phím mũi tên hoặc click trên màn hình để ra lệnh cho thang máy (Move Up, Move Down, Stop/Idle).

---

## 🧠 Logic Game (Game Logic)
- **Bản chất trò chơi**: Nhiệm vụ của thang máy là vận chuyển tất cả hành khách từ điểm đón đến điểm trả mong muốn của họ trong thời gian ngắn nhất.
- **Trạng thái (State)**: Mỗi bước đi, môi trường sẽ lưu lại một `State` bao gồm: Tầng hiện tại, Danh sách khách trên thang (giới hạn sức chứa), và Danh sách khách đang chờ ở các tầng.
- **Hành động (Action)**: Thang máy có 3 hành động chính tại mỗi State: 
  - `MOVE_UP`: Di chuyển lên 1 tầng.
  - `MOVE_DOWN`: Di chuyển xuống 1 tầng.
  - `STOP` (hay `IDLE`): Dừng lại để đón/trả khách hoặc đứng chờ.
- **Đánh giá (Score/Stats)**: Mỗi hành động tiêu tốn thời gian. Khách chờ quá lâu sẽ bị trừ điểm. Các thuật toán AI cố gắng mô phỏng trước các `Action` để tìm ra con đường (path) ít tốn kém cost nhất (hành trình ngắn nhất). Nếu AI không tìm ra do giới hạn tài nguyên (thời gian/số node mở rộng), cơ chế `Greedy Fallback` sẽ tự động kích hoạt để điều khiển thang máy đi tới mục tiêu gần nhất.

---

## 📂 Cấu Trúc Thư Mục (Directory Structure)

Dưới đây là sơ đồ và chức năng chi tiết của từng thư mục, file trong hệ thống:

```text
SmartElevator/
│
├── main.py                     # Entry point (Điểm bắt đầu). Chạy file này để khởi động game.
├── .gitignore                  # Bỏ qua các file không cần thiết khi push lên Git (như __pycache__).
│
├── algorithms/                 # Chứa toàn bộ các thuật toán AI và Logic Tìm kiếm.
│   ├── base_search.py          # Class trừu tượng định nghĩa cấu trúc cơ bản cho mọi thuật toán.
│   ├── algorithm_factory.py    # Design Pattern Factory để khởi tạo thuật toán theo tên.
│   ├── astar.py                # Thuật toán A* Search.
│   ├── bfs.py, dfs.py, ucs.py  # Các thuật toán tìm kiếm mù (Breadth-First, Depth-First, Uniform-Cost).
│   ├── greedy.py               # Thuật toán Greedy Best-First Search.
│   ├── beam_search.py          # Thuật toán Beam Search.
│   ├── hill_climbing.py        # Thuật toán Hill Climbing.
│   ├── heuristics.py           # Các hàm đánh giá Heuristic dùng cho A* và Greedy.
│   └── search_node.py          # Cấu trúc Node trên cây tìm kiếm.
│
├── assets/                     # Tài nguyên tĩnh của game.
│   └── images/                 # Chứa các file ảnh (.png): giao diện, nhân vật, thang máy, background.
│
├── controllers/                # Điều khiển logic giữa Data (Models) và UI (Views).
│   ├── mode_controller.py      # Base Controller cho các chế độ chơi.
│   ├── manual_mode.py          # Logic xử lý khi người chơi tự điều khiển.
│   ├── ai_mode.py              # Logic gọi AI tính toán và điều khiển tự động (có chứa Fallback).
│   ├── compare_mode.py         # Logic chạy song song 2 AI để so sánh.
│   ├── input_handler.py        # Xử lý sự kiện (bàn phím, chuột) từ Pygame.
│   └── scenario_*.py           # Các file quản lý, validate và load kịch bản màn chơi.
│
├── models/                     # Chứa các cấu trúc dữ liệu cốt lõi (Domain Models).
│   ├── building.py             # Đại diện cho toà nhà (chứa các tầng, thang máy).
│   ├── elevator.py             # Thực thể thang máy (vị trí, hành khách trên xe).
│   ├── passenger.py            # Thực thể hành khách.
│   ├── request.py              # Lời gọi thang máy của khách.
│   ├── state.py                # Trạng thái hiện tại của game (dành cho thuật toán AI phân tích).
│   └── enums.py                # Định nghĩa các hằng số liệt kê (Action, PassengerType, GameMode).
│
├── simulation/                 # Engine cốt lõi chạy vòng lặp mô phỏng.
│   ├── simulation_engine.py    # Engine chính, cập nhật trạng thái game sau mỗi frame/step.
│   ├── scenario.py             # Sinh ra và cấu hình các Scenario (kịch bản hành khách xuất hiện).
│   └── dataset.py              # Cung cấp bộ dữ liệu test.
│
├── statistics/                 # Ghi nhận và tính toán thông số/điểm số.
│   ├── score_manager.py        # Tính điểm dựa vào thời gian hoàn thành và mức độ hài lòng.
│   ├── statistics_manager.py   # Theo dõi thông số AI (thời gian chạy, số node đã mở, etc).
│   └── benchmark_manager.py    # Quản lý chạy Benchmark tự động đánh giá các thuật toán.
│
├── utils/                      # Chứa các hàm/biến phụ trợ.
│   └── settings.py             # File quan trọng chứa các Hằng số (Màu sắc, FPS, Số tầng, Kích thước màn hình).
│
└── views/                      # UI Layer (Giao diện hiển thị với Pygame).
    ├── app.py                  # Quản lý cửa sổ Pygame và Scene hiện tại.
    ├── theme.py                # Định nghĩa các style (font, color cho UI).
    ├── widgets.py              # Các UI Component tự tạo (Button, Text).
    ├── building_view.py        # Vẽ toà nhà, thang máy và người lên màn hình.
    └── screens/                # Chứa các Scene/Màn hình khác nhau của Game.
        ├── menu_screens.py     # Màn hình Menu chính.
        ├── play_screens.py     # Màn hình chơi (Manual/AI).
        ├── compare_screen.py   # Màn hình so sánh Compare.
        └── stats_screen.py     # Màn hình hiển thị kết quả, bảng thống kê.
```
