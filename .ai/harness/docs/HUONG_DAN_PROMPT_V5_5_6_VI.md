# Hướng dẫn giao việc cho AI - Harness v5.5.6

## Dùng bằng câu nói bình thường

Bạn không cần học một bộ công thức prompt mới. Khi dự án đã cài
Harness, gửi một trong các câu sau cho agent đang làm việc.
Đây là câu nhắc tự nhiên, không phải slash command hay bằng chứng kích hoạt Skill.

### Làm rõ rồi thực hiện

> Làm rõ yêu cầu này theo brief-task của Harness rồi triển khai.
> Giữ các quyết định đã chốt, chỉ hỏi khi thiếu thông tin làm thay đổi kết quả.
> Yêu cầu: [mục tiêu và kết quả bạn muốn].

Agent đọc trạng thái dự án, làm rõ phạm vi và điều kiện hoàn thành,
sau đó thực hiện trong quyền hiện có. Không dừng ở việc viết một prompt khác.

### Chỉ soạn prompt để gửi cho agent khác

> Soạn một prompt cho Codex thực hiện yêu cầu sau theo Harness.
> Ở lượt này chỉ trả prompt, không sửa dự án: [yêu cầu].

Phân biệt người soạn và người nhận: bạn chỉ yêu cầu soạn ở đây,
nhưng Codex nhận prompt có thể được yêu cầu thực hiện.
Nếu chưa có task gốc, kết quả là bản nháp DRAFT, không giả vờ đã xác minh.

### Đổi từ Codex sang Antigravity / Claude

> Chuẩn bị bàn giao task hiện tại sang Antigravity bằng brief-task.
> Giữ mục tiêu, phạm vi, quyết định và lịch sử thất bại;
> chỉ mang theo tiến độ có checkpoint và bằng chứng còn hợp lệ.

Bản giao không mang lời hứa "đã xong" thay cho bằng chứng. Agent nhận vẫn cần
truy cập đúng dự án/task. Profile native phải được lập kế hoạch
portable/audited trước khi lấy bằng chứng bàn giao; công cụ không tự đổi profile.

### Thoát vòng lặp sửa lỗi

> Đọc bằng chứng lần thất bại vừa rồi, nêu giả thuyết nguyên nhân mới,
> lập brief sửa lỗi với thí nghiệm nhỏ nhất. Không chạy lại mù cùng cách.

Giả thuyết chỉ là điều cần kiểm chứng, không phải kết luận đúng.

## Lệnh cho người dùng kỹ thuật

```powershell
python .ai/scripts/prompt_brief.py lint --task TASK-EXAMPLE
python .ai/scripts/prompt_brief.py compile --task TASK-EXAMPLE --host codex
python .ai/scripts/prompt_brief.py compile --task TASK-EXAMPLE --host claude --language en
python .ai/scripts/prompt_brief.py handoff --task TASK-EXAMPLE --host antigravity --save
```

Thay TASK-EXAMPLE bằng task thật. Mặc định chỉ in kết quả; --save mới ghi capsule
vào .ai/checkpoints/briefs. Không cần cài prompt-master riêng, không thêm Skill thứ 14.
Bản tiếng Anh: --language en. Host gồm codex, claude, gemini, antigravity;
chọn host không đồng nghĩa tự đổi model hay cấp thêm quyền.

## Giới hạn cần biết

Script chuyển task có cấu trúc thành brief, không tự hiểu mọi câu nói tự nhiên.
Phần hiểu ý do agent thực hiện, cần đối chiếu với yêu cầu gốc.
Không tuyên bố tiết kiệm token hay nhớ đủ ngữ cảnh nếu chưa đo bằng live eval.
Không dán khóa API, mật khẩu vào task/prompt. Kiểm tra heuristic không bảo đảm bắt hết bí mật.
Nếu brief cũ bị từ chối, xác minh lại dữ liệu gốc rồi tạo bản mới; không sửa hash để qua gate.
