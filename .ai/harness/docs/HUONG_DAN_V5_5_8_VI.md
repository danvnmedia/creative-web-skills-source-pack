# Hướng dẫn v5.5.8 - Recorder

Bản vá nối tiếp 5.5.7, giữ baseline 5.3.0 và 13 Skills.
Sửa lỗi lệnh exit 0 bị ghi BLOCKED chỉ vì output có từ DNS.
Timeout, mutation, evidence thiếu/cũ và skill-eval-live vẫn được kiểm tra.

## Cập nhật an toàn

Giải nén ngoài project root; không copy đè thủ công.
Chạy plan, đọc conflict/preflight, rồi apply đúng digest:

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN"
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN" --apply --confirm PLAN_DIGEST
```

Không sửa hash hoặc đổi nhãn evidence cũ. Task COMPLETE vẫn bất biến; candidate mới dùng task kế tiếp.
Chỉ dùng regression thay thế khi catalog xác nhận đúng check, revision, context và môi trường.

## Kiểm tra

Từ project đã cài:

```powershell
python .ai/scripts/self_test.py --context installed
python .ai/scripts/v558_regression_test.py
```

Bộ regression đầy đủ chỉ chạy từ source, với temp ở ngoài cây source.
Kết quả Linux không thay thế native Windows, live Skill hoặc production acceptance.
INITIAL-LOAD-BUDGET không thuộc phạm vi bản vá Harness này.
Chi tiết: `RECORDER_STATUS_V5_5_8.md` trong cùng thư mục.
