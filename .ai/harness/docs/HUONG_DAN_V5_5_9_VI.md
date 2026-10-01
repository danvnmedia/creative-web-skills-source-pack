# Hướng dẫn v5.5.9

Bản này giảm ma sát ở release mà không hạ gate: có `release_doctor.py` đọc-only, cảnh báo revision marker sớm, và `record_evidence.py --summary` cho output một dòng. JSON mặc định và evidence lưu trữ vẫn giữ nguyên.

Policy AI v2 làm rõ: được phép chuyển giữa các nguồn/quota scope độc lập đã được cấu hình hợp lệ, kể cả free -> paid khi dự án đã cho phép ngân sách. Nhiều key cùng một quota scope không được tính là dung lượng mới. Không tự bật billing, không vượt spend cap, không dùng 403/policy denial như lý do để đổi nguồn né quyền.

Ví dụ:

```bash
python .ai/scripts/release_doctor.py --task TASK-123
python .ai/scripts/release_doctor.py --task TASK-123 --json
python .ai/scripts/record_evidence.py --task TASK-123 --check unit --summary -- python -m pytest -q
```

Kết quả doctor không thay cho CI/provider/deployment verification và không tự fetch/push/deploy.
