# Gợi ý viết lại báo cáo Smart Elevator

Tài liệu này là khung nội dung để viết lại báo cáo cho dự án **Smart Elevator - AI Dispatch Simulation**. Mục tiêu của báo cáo nên là: người đọc hiểu bài toán thang máy được mô hình hóa thành bài toán tìm kiếm trạng thái như thế nào, các thuật toán AI được cài đặt ra sao, hệ thống mô phỏng/game vận hành thế nào, và kết quả benchmark phản ánh điều gì.

---

## 1. Gợi ý chỉnh lại mục lục

Mục lục hiện tại của bạn đã đúng hướng, nhưng nên chỉnh để nhấn mạnh hơn phần AI và tách rõ giữa **lý thuyết**, **mô hình hóa bài toán**, **cài đặt thuật toán**, **hệ thống game**, và **đánh giá thực nghiệm**.

### Mục lục đề xuất

**CHƯƠNG 1: MỞ ĐẦU**

1.1. Lý do chọn đề tài  
1.2. Mục tiêu đề tài  
1.3. Phạm vi đề tài  
1.4. Đối tượng nghiên cứu  
1.5. Phương pháp thực hiện  
1.6. Cấu trúc báo cáo  

**CHƯƠNG 2: CƠ SỞ LÝ THUYẾT**

2.1. Bài toán tìm kiếm trong không gian trạng thái  
2.2. Thành phần của một bài toán tìm kiếm: state, action, transition, goal, cost  
2.3. Nhóm thuật toán tìm kiếm mù: BFS, DFS, UCS  
2.4. Nhóm thuật toán tìm kiếm có tri thức: Greedy Best-First Search, A*  
2.5. Nhóm thuật toán tìm kiếm cục bộ/giới hạn bộ nhớ: Hill Climbing, Beam Search  
2.6. Heuristic và vai trò của heuristic trong bài toán điều phối thang máy  
2.7. Các tiêu chí đánh giá thuật toán: completeness, optimality, time, memory, expanded/generated nodes  

**CHƯƠNG 3: PHÂN TÍCH VÀ MÔ HÌNH HÓA BÀI TOÁN**

3.1. Phát biểu bài toán Smart Elevator  
3.2. Các thực thể trong hệ thống: Building, Elevator, Passenger, Request, Scenario  
3.3. Biểu diễn trạng thái tìm kiếm  
3.4. Tập hành động của thang máy  
3.5. Quy tắc chuyển trạng thái  
3.6. Hàm chi phí  
3.7. Hàm heuristic  
3.8. Điều kiện kết thúc và ràng buộc mô phỏng  

**CHƯƠNG 4: THIẾT KẾ VÀ CÀI ĐẶT HỆ THỐNG**

4.1. Công nghệ và môi trường phát triển  
4.2. Kiến trúc tổng quan của dự án  
4.3. SimulationEngine - bộ máy mô phỏng  
4.4. Controllers - điều khiển các chế độ chơi  
4.5. Giao diện Pygame và các màn hình chính  
4.6. Cài đặt các thuật toán tìm kiếm  
4.6.1. Lớp cơ sở SearchAlgorithm và SearchResult  
4.6.2. SearchNode và cơ chế khôi phục đường đi  
4.6.3. BFS  
4.6.4. DFS  
4.6.5. UCS  
4.6.6. Greedy Best-First Search  
4.6.7. A* Search  
4.6.8. Hill Climbing  
4.6.9. Beam Search  
4.6.10. AlgorithmFactory  
4.7. Hệ thống thống kê, tính điểm và benchmark  

**CHƯƠNG 5: KẾT QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ**

5.1. Môi trường thử nghiệm  
5.2. Các chế độ chạy thử: Manual, AI, Compare, Benchmark  
5.3. Bộ dữ liệu benchmark Easy/Medium/Hard  
5.4. Bảng kết quả so sánh thuật toán  
5.5. Phân tích kết quả theo từng tiêu chí  
5.6. Nhận xét ưu/nhược điểm của từng thuật toán trong bài toán thang máy  
5.7. Hạn chế của hệ thống  
5.8. Hướng phát triển  

**CHƯƠNG 6: KẾT LUẬN**

6.1. Kết quả đạt được  
6.2. Kiến thức AI đã áp dụng  
6.3. Bài học rút ra  

**TÀI LIỆU THAM KHẢO**

---

## 2. Nội dung nên viết cho từng chương

### Chương 1: Mở đầu

Chương này nên trả lời câu hỏi: vì sao chọn bài toán điều phối thang máy để minh họa thuật toán AI?

Các ý nên có:

- Thang máy là một bài toán điều phối tài nguyên quen thuộc: có vị trí hiện tại, yêu cầu phục vụ, giới hạn sức chứa, thời gian chờ và mục tiêu tối ưu.
- Bài toán phù hợp với môn AI vì có thể mô hình hóa thành không gian trạng thái.
- Có thể áp dụng nhiều thuật toán tìm kiếm khác nhau và so sánh hiệu quả.
- Dự án không chỉ chạy thuật toán trên dữ liệu tĩnh, mà còn có game/mô phỏng trực quan bằng Pygame.

Đoạn gợi ý:

> Đề tài Smart Elevator mô phỏng một hệ thống thang máy thông minh có nhiệm vụ phục vụ hành khách trong tòa nhà. Mỗi hành khách có tầng xuất phát, tầng đích, thời điểm xuất hiện và mức độ ưu tiên. Hệ thống cần quyết định chuỗi hành động của thang máy sao cho phục vụ được nhiều hành khách, giảm thời gian chờ, giảm quãng đường di chuyển và hạn chế hành khách bị bỏ lỡ. Bài toán này phù hợp để áp dụng các thuật toán tìm kiếm trong trí tuệ nhân tạo vì mỗi trạng thái của hệ thống có thể được biểu diễn rõ ràng, từ đó sinh ra các trạng thái kế tiếp thông qua các hành động của thang máy.

### Chương 2: Cơ sở lý thuyết

Không nên chỉ định nghĩa thuật toán rời rạc. Nên nối lý thuyết với bài toán của bạn.

Với mỗi thuật toán, nên trình bày:

- Ý tưởng chính.
- Cấu trúc dữ liệu dùng để lưu frontier.
- Tiêu chí chọn node tiếp theo.
- Có đảm bảo tối ưu không.
- Khi áp dụng vào bài toán thang máy thì mạnh/yếu ở điểm nào.

Bảng tóm tắt nên đưa vào chương 2 hoặc cuối chương 4:

| Thuật toán | Nhóm | Tiêu chí chọn node | Tối ưu? | Điểm mạnh | Hạn chế |
|---|---|---|---|---|---|
| BFS | Uninformed | Node nông nhất | Tối ưu theo số bước nếu chi phí đều | Dễ hiểu, có hệ thống | Mở rộng nhiều node |
| DFS | Uninformed | Node sâu nhất | Không | Ít bộ nhớ hơn BFS | Dễ đi sâu vào nhánh kém |
| UCS | Uninformed | Chi phí g nhỏ nhất | Có, nếu cost không âm | Tối ưu theo cost | Có thể chậm |
| Greedy | Informed | Heuristic h nhỏ nhất | Không | Nhanh, hướng mục tiêu rõ | Dễ chọn đường ngắn hạn |
| A* | Informed | f = g + h | Có nếu heuristic phù hợp | Cân bằng cost và định hướng | Phụ thuộc heuristic |
| Hill Climbing | Local | Láng giềng có h tốt nhất | Không | Nhanh, nhẹ | Dễ kẹt cực trị cục bộ |
| Beam Search | Local/Memory-limited | Giữ k node tốt nhất mỗi tầng | Không | Giảm bộ nhớ | Có thể bỏ mất lời giải tốt |

### Chương 3: Phân tích và mô hình hóa bài toán

Đây là chương quan trọng vì nó chứng minh bạn hiểu cách biến game thành bài toán AI.

#### 3.1. Phát biểu bài toán

Mô tả:

- Có một tòa nhà nhiều tầng.
- Một thang máy di chuyển lên/xuống từng tầng.
- Hành khách xuất hiện theo scenario, có tầng đi, tầng đến, thời điểm xuất hiện và loại hành khách.
- Thang máy có giới hạn sức chứa.
- Mục tiêu là tìm chuỗi hành động để đưa tất cả hành khách đến nơi với chi phí thấp.

#### 3.2. Biểu diễn trạng thái

Trong code, state nằm ở `models/state.py`.

Một `State` gồm:

- `current_time`: thời điểm hiện tại trong mô phỏng.
- `elevator_floor`: tầng hiện tại của thang máy.
- `onboard`: danh sách hành khách đang ở trong thang.
- `waiting_by_floor`: danh sách hành khách đang chờ theo từng tầng.
- `delivered`: số khách đã giao thành công.
- `angry`: số khách bị trễ/hết kiên nhẫn khi đang trong hệ thống.
- `left`: số khách rời đi khi chưa được phục vụ.
- `score`: điểm tạm thời của trạng thái.

Điểm cần nhấn mạnh:

- State được thiết kế bất biến (`frozen=True`) và có thể hash, giúp thuật toán lưu visited/closed set.
- `planning_key()` chỉ lấy các thành phần quan trọng cho planning: tầng thang máy, khách trên thang, khách đang chờ. Điều này giúp loại bỏ trạng thái trùng trong graph search.
- Goal state là trạng thái không còn khách đang chờ và không còn khách trên thang.

#### 3.3. Tập hành động

Các hành động chính:

- `MOVE_UP`: thang máy đi lên một tầng.
- `MOVE_DOWN`: thang máy đi xuống một tầng.
- `STOP`: dừng tại tầng hiện tại để trả khách và đón khách.
- `IDLE`: dùng trong mô phỏng khi không có hành động hữu ích hoặc AI không tìm được plan ngay.

Trong tìm kiếm, successor chủ yếu sinh ra `MOVE_UP`, `MOVE_DOWN`, `STOP` nếu hợp lệ. `IDLE` dùng ở controller/mô phỏng hơn là hành động tối ưu chính.

#### 3.4. Quy tắc chuyển trạng thái

Khi `MOVE_UP` hoặc `MOVE_DOWN`:

- Tầng thang máy thay đổi một đơn vị.
- Thời gian tăng theo `MOVE_COST`.
- Hệ thống cập nhật khách hết hạn chờ.
- Chi phí bước gồm thời gian di chuyển và phạt nếu có khách rời đi/bị trễ.

Khi `STOP`:

- Khách có điểm đến là tầng hiện tại được trả xuống.
- Khách đang chờ tại tầng hiện tại được đón lên nếu thang còn chỗ.
- Thời gian dừng phụ thuộc số lượt lên/xuống.
- Trạng thái cập nhật số khách đã giao, khách bị trễ, khách rời đi và điểm.

#### 3.5. Hàm chi phí

Trong `State.successors()`, chi phí bước được tính theo hướng:

- Di chuyển mất thời gian.
- Khách rời đi bị phạt nặng.
- Khách trở nên tức giận/bị trễ bị phạt.
- `STOP` có chi phí theo thời gian tương tác lên/xuống.

Có thể mô tả công thức khái quát:

```text
step_cost = action_duration + 50 * number_of_left_passengers + 10 * number_of_angry_passengers
```

Với hành động trả khách, hệ thống cũng cộng reward vào `score`, nhưng các thuật toán tìm kiếm chủ yếu so sánh theo cost tích lũy `g`.

#### 3.6. Heuristic

Trong `algorithms/heuristics.py`, có hai heuristic chính:

1. `span`:

- Tìm tập các tầng còn cần ghé: tầng đích của khách trên thang, tầng có khách đang chờ và tầng đích dự kiến.
- Ước lượng khoảng cách tối thiểu cần đi để bao phủ đoạn từ tầng thấp nhất đến tầng cao nhất trong tập mục tiêu.
- Công thức trực quan:

```text
h = (highest_target - lowest_target) + min(|current_floor - lowest_target|, |current_floor - highest_target|)
```

- Dùng mặc định cho A*.

2. `greedy`:

- Kết hợp `span` với số khách còn trong hệ thống và số khách đang chờ.
- Công thức ý tưởng:

```text
h = span + alpha * num_in_system + waiting_weight * num_waiting
```

- Dùng cho Greedy, Beam Search và Hill Climbing để hướng thuật toán ưu tiên giảm số khách chưa phục vụ.

### Chương 4: Thiết kế và cài đặt hệ thống

Chương này nên mô tả kiến trúc dự án trước, rồi mới đi sâu thuật toán.

#### 4.1. Kiến trúc thư mục

Nên trình bày ngắn:

- `algorithms/`: cài đặt thuật toán tìm kiếm.
- `models/`: định nghĩa dữ liệu cốt lõi như State, Elevator, Passenger.
- `simulation/`: chạy mô phỏng theo thời gian.
- `controllers/`: điều phối giữa engine, thuật toán và mode chơi.
- `statistics/`: ghi nhận số liệu, tính điểm, benchmark.
- `views/`: giao diện Pygame.

#### 4.2. Luồng hoạt động của AI Mode

Luồng đúng theo code:

1. `AIScreen` tạo hoặc nạp scenario.
2. `SimulationEngine` chuyển thế giới hiện tại thành `State` bằng `snapshot()`.
3. `AIMode.plan()` gọi thuật toán qua `algorithm.solve(initial_state, stats, node_limit=2000, time_limit=0.15)`.
4. Thuật toán trả về `SearchResult` gồm path, cost, success, nodes expanded/generated, planning time.
5. `AIMode` đưa path vào hàng đợi hành động.
6. Mỗi frame hoặc mỗi nhịp mô phỏng, controller lấy hành động tiếp theo và gọi `SimulationEngine.apply(action)`.
7. Nếu hết plan hoặc số khách đang chờ thay đổi, AI có thể re-plan để phản ứng với khách mới.

Đoạn gợi ý:

> AI Mode không điều khiển thang máy bằng luật cố định, mà liên tục lấy ảnh chụp trạng thái hiện tại của mô phỏng và chạy thuật toán tìm kiếm để sinh ra chuỗi hành động. Chuỗi hành động này sau đó được thực thi từng bước thông qua cùng một SimulationEngine như chế độ thủ công. Nhờ đó, kết quả giữa người chơi và AI có thể so sánh công bằng vì đều tác động lên cùng luật mô phỏng.

#### 4.3. Lớp cơ sở SearchAlgorithm

Nên mô tả:

- `SearchAlgorithm.solve()` là giao diện chung cho mọi thuật toán.
- Hàm này đo thời gian chạy, gắn tên thuật toán và cộng dồn thống kê.
- Mỗi thuật toán chỉ cần cài `_search(initial_state)`.
- Có giới hạn `node_limit` và `time_limit` để tránh treo game.

`SearchResult` gồm:

- `path`: chuỗi hành động tìm được.
- `cost`: tổng chi phí.
- `success`: có tìm được goal không.
- `nodes_expanded`: số node đã mở rộng.
- `nodes_generated`: số node con đã sinh.
- `planning_time_ms`: thời gian lập kế hoạch.
- `algorithm`: tên thuật toán.

#### 4.4. Cài đặt từng thuật toán

Phần này là trọng tâm báo cáo môn AI. Mỗi thuật toán nên có 4 phần nhỏ: ý tưởng, cách cài trong dự án, ưu điểm, hạn chế.

##### BFS

- Dùng queue FIFO (`deque`).
- Mở rộng trạng thái theo từng lớp độ sâu.
- Dùng `visited` để tránh thêm trùng trạng thái vào frontier.
- Khi gặp goal, khôi phục path qua parent node.
- Trong dự án, BFS phù hợp để tìm lời giải có ít hành động, nhưng không tối ưu theo thời gian/chi phí vì mỗi action có chi phí khác nhau.
- Khi vượt giới hạn thời gian/node, code có thể trả về best partial path dựa trên heuristic `span`.

##### DFS

- Dùng stack LIFO.
- Đi sâu theo một nhánh trước khi quay lui.
- Có `visited` để tránh vòng lặp.
- Có thể cấu hình `depth_limit`.
- Không đảm bảo tối ưu và có thể tìm path kém trong bài toán thang máy vì lựa chọn nhánh phụ thuộc thứ tự successor.

##### UCS

- Dùng priority queue theo `g`, tức chi phí tích lũy nhỏ nhất.
- Lưu `best_g` cho mỗi planning key để chỉ giữ đường tốt hơn.
- Vì cost không âm, UCS phù hợp để tìm plan có tổng cost thấp.
- Nhược điểm là có thể mở rộng nhiều node vì không dùng heuristic định hướng.

##### Greedy Best-First Search

- Dùng priority queue theo `h`.
- Chỉ quan tâm trạng thái nhìn có vẻ gần mục tiêu nhất.
- Trong dự án dùng heuristic `greedy`, kết hợp khoảng tầng cần đi và số khách chưa phục vụ.
- Ưu điểm là nhanh, thường sinh plan ngắn hạn tốt.
- Nhược điểm là không xét cost đã đi nên có thể chọn đường gây chi phí tổng cao.

##### A*

- Dùng priority queue theo `f = g + h`.
- `g` là chi phí đã đi, `h` là chi phí ước lượng còn lại.
- Dùng `best_g` và `closed` để loại trạng thái kém.
- Trong dự án, A* dùng heuristic `span` mặc định.
- Đây là thuật toán cân bằng giữa tối ưu chi phí và định hướng tìm kiếm, thường là lựa chọn tốt cho AI Mode.

##### Hill Climbing

- Bắt đầu từ state hiện tại, xét các successor và chọn láng giềng có heuristic tốt nhất.
- Có hỗ trợ sideways move và random restart để giảm nguy cơ kẹt.
- Rất nhẹ về bộ nhớ vì không giữ toàn bộ frontier lớn.
- Không đảm bảo tìm được lời giải toàn cục. Với thang máy, đôi khi cần đi tạm xa mục tiêu để đón/trả khách tốt hơn, nên Hill Climbing dễ kẹt.

##### Beam Search

- Mở rộng theo từng mức.
- Sau mỗi mức chỉ giữ lại tối đa `beam_width` node tốt nhất theo heuristic.
- Giảm bộ nhớ so với BFS/A*, chạy nhanh hơn trong không gian lớn.
- Không hoàn chỉnh và không tối ưu vì có thể loại bỏ sớm nhánh chứa lời giải tốt.

##### AlgorithmFactory

- Dùng registry ánh xạ key như `bfs`, `dfs`, `ucs`, `astar`, `greedy`, `hill`, `beam` sang class thuật toán.
- Giúp UI chỉ cần truyền tên thuật toán, không phụ thuộc trực tiếp vào class cụ thể.
- Là một ứng dụng của Factory Pattern trong thiết kế phần mềm.

#### 4.5. SimulationEngine

Nên mô tả engine như bộ luật chung:

- `new_scenario()` hoặc `load_scenario()` để tạo/nạp màn chơi.
- `reset()` đưa thế giới về trạng thái đầu.
- `_release_due_passengers()` đưa khách đến thời điểm xuất hiện vào hệ thống.
- `_advance_walking()` mô phỏng khách đi vào khu vực chờ thang.
- `apply(action)` là hàm quan trọng nhất: nhận hành động và cập nhật thế giới.
- `_apply_move()` xử lý di chuyển.
- `_apply_stop()` xử lý trả/đón khách.
- `is_finished()` kiểm tra hoàn tất.
- `snapshot()` chuyển trạng thái mô phỏng sang `State` cho thuật toán AI.

#### 4.6. Các mode game

Manual Mode:

- Người chơi điều khiển thang bằng phím.
- Hành động vẫn đi qua `SimulationEngine.apply()`.
- Dùng để so sánh con người với AI hoặc kiểm tra logic mô phỏng.

AI Mode:

- Chọn một thuật toán.
- AI lập kế hoạch và tự chạy.
- Có hiển thị số node expanded/generated, runtime, plan cost.

Compare Mode:

- Chạy hai bên trên cùng scenario.
- Có thể so sánh You vs AI hoặc AI vs AI.
- Kết quả gồm wait time, distance, failures, expanded/generated nodes, planning time, score.

Benchmark:

- Chạy toàn bộ thuật toán trên bộ scenario Easy/Medium/Hard.
- Tính trung bình score, expanded, generated, runtime, wait, satisfaction.
- Dùng để đánh giá thuật toán khách quan hơn so với một màn đơn lẻ.

#### 4.7. Statistics và Score

`StatisticsManager` ghi:

- `nodes_expanded`
- `nodes_generated`
- `planning_time`
- `solution_cost`
- `total_distance`
- `total_wait`
- `delivered_count`
- `urgent_delivered_count`
- `left_count`
- `angry_count`
- `satisfaction_score`

`ScoreManager` tính điểm theo ý tưởng:

```text
score =
  delivered_count * delivery_bonus
+ urgent_delivered_count * urgent_delivery_bonus
+ satisfaction_score * satisfaction_bonus
- total_distance * move_penalty
- total_wait * wait_penalty
- angry_count * angry_penalty
- left_count * lost_penalty
```

Nên giải thích: điểm cao không chỉ do chạy nhanh, mà còn do phục vụ nhiều khách, giảm thời gian chờ, giảm quãng đường và hạn chế thất bại.

### Chương 5: Kết quả và đánh giá

Đây là chương bạn nên chèn ảnh chụp màn hình và bảng benchmark.

Nên có các ảnh:

- Menu chính.
- Manual Mode.
- AI Mode với search visualization.
- Compare AI vs AI.
- Stats Screen.
- Benchmark Screen.

Nên có bảng kết quả benchmark theo Easy/Medium/Hard:

| Difficulty | Algorithm | Success | Avg Score | Avg Expanded | Avg Generated | Runtime | Avg Wait | Satisfaction |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Easy | A* | ... | ... | ... | ... | ... | ... | ... |

Khi phân tích, không chỉ nói thuật toán nào cao nhất. Nên giải thích theo bản chất:

- Nếu UCS/A* có score tốt: vì xét cost nên thường đưa ra lộ trình hợp lý.
- Nếu Greedy nhanh nhưng score không ổn định: vì chỉ nhìn heuristic.
- Nếu BFS mở rộng nhiều node: vì không có định hướng.
- Nếu DFS kết quả kém: vì đi sâu theo nhánh và không tối ưu.
- Nếu Hill Climbing/Beam nhanh nhưng thất bại ở Hard: vì dễ bỏ qua nhánh tốt hoặc kẹt heuristic.
- Nếu Hard không highlight/không thành công nhiều: giải thích do số khách lớn làm không gian trạng thái tăng nhanh.

### Chương 6: Kết luận

Nên kết luận theo 3 lớp:

1. Về sản phẩm:
   - Xây dựng được game mô phỏng thang máy bằng Pygame.
   - Có các mode Manual, AI, Compare, Benchmark.

2. Về AI:
   - Mô hình hóa được bài toán thành state-space search.
   - Cài đặt và so sánh 7 thuật toán.
   - Đo được expanded/generated nodes, runtime, cost và score.

3. Về hướng phát triển:
   - Thêm nhiều thang máy.
   - Cải thiện heuristic có xét deadline/ưu tiên khách urgent.
   - Thêm thuật toán nâng cao như IDA*, Genetic Algorithm, Reinforcement Learning.
   - Xuất benchmark ra CSV/PDF.

---

## 3. Các điểm nên sửa trong mục lục hiện tại

Mục lục hiện tại có vài điểm nên chỉnh:

- Thiếu mục `5.2.2` vì đang có `5.2.1` rồi nhảy sang `5.2.3`.
- Nên thêm riêng mục cho `AI Mode`, vì đây là mode quan trọng nhất với báo cáo AI.
- Không nên để `Cài đặt môi trường phát triển` chiếm quá nhiều trang so với thuật toán. Phần môi trường chỉ cần ngắn, tập trung trang cho thuật toán và mô hình hóa.
- `Logging & Analytics` nên đổi thành `Thống kê, tính điểm và benchmark` để gần với nội dung dự án hơn.
- Chương 4 hiện đang đi sâu code từng thuật toán, tốt, nhưng nên đặt trước đó một mục giải thích `State`, `Action`, `Cost`, `Heuristic`, nếu không người đọc sẽ khó hiểu thuật toán đang tìm trên cái gì.
- Chương 5 nên có phần phân tích kết quả chứ không chỉ chèn bảng/screenshot.

---

## 4. Checklist khi viết báo cáo

- Mỗi thuật toán phải có: ý tưởng, cấu trúc dữ liệu, cách chọn node, ưu/nhược điểm, liên hệ với bài toán thang máy.
- Phải giải thích rõ `State` gồm những gì.
- Phải giải thích rõ `successors()` sinh trạng thái mới như thế nào.
- Phải có công thức hoặc mô tả hàm cost.
- Phải có công thức hoặc mô tả heuristic `span` và `greedy`.
- Phải có sơ đồ luồng AI Mode: snapshot -> solve -> path -> apply action -> re-plan.
- Phải có bảng benchmark Easy/Medium/Hard.
- Khi đánh giá, dùng cả metric AI (`expanded`, `generated`, `runtime`) và metric game (`score`, `wait`, `distance`, `satisfaction`).
- Nên chèn ảnh giao diện để người đọc hiểu đây là mô phỏng tương tác, không chỉ là code thuật toán.

---

## 5. Gợi ý tài liệu tham khảo

Bạn có thể dùng các nguồn cơ bản sau trong phần tài liệu tham khảo:

1. Stuart Russell, Peter Norvig, *Artificial Intelligence: A Modern Approach*, chương về uninformed search và informed search.
2. Tài liệu môn Trí tuệ nhân tạo về BFS, DFS, UCS, Greedy Best-First Search, A*.
3. Pygame documentation cho phần xây dựng giao diện mô phỏng.
4. Python documentation cho `heapq`, `deque`, `dataclasses`.

