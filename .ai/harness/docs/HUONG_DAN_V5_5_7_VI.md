# Hướng dẫn v5.5.7 - nâng cấp an toàn

Bản này kế thừa v5.5.6; baseline chất lượng vẫn là v5.3.0.
Không có cài đặt tự động vào dự án thật.

## 1. Xem kế hoạch trước khi cài

Giải nén gói bên ngoài project root. Giữ bản sao riêng trước khi nâng cấp.
Chạy từ thư mục source vừa giải nén:

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN"
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN" --apply --confirm PLAN_DIGEST
```

Thay PLAN_DIGEST bằng giá trị từ kế hoạch. Đọc phần preflight:
CI gọi lệnh cũ, state chưa track/bị ignore, văn bản legacy,
hoặc scan chưa đầy đủ. Kế hoạch không tự sửa CI hay xóa nội dung project.

## 2. Khi Git đổi LF thành CRLF

Mặc định hash vẫn so đúng từng byte. Chỉ dùng tuỳ chọn sau
khi kế hoạch chứng minh đây là thay đổi CRLF khớp baseline cũ:

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN" --repair-eol
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN" --repair-eol --apply --confirm REPAIR_PLAN_DIGEST
```

Không tự sửa hash, không normalize toàn repo. BOM hoặc nội dung khác
vẫn là conflict. Block trong .gitattributes chỉ ghi đúng các path Harness quản lý;
phải review nếu project có filter riêng. Thuộc tính Git ở thư mục con
hoặc .git/info/attributes có thể ưu tiên cao hơn; kiểm tra installed vẫn bắt buộc.

## 3. CI phải có state cài đặt

Review rồi commit .ai/HARNESS_INSTALL_STATE.json, .gitattributes và các path
đã cài thuộc phạm vi nâng cấp. Không stage nhầm task/evidence cũ.
Không ignore cả thư mục runtime nếu làm mất README được quản lý.
Ví dụ cần review với quy tắc Git thực tế của dự án:

```gitignore
.ai/checkpoints/*
!.ai/checkpoints/README.md
.ai/evidence/*
!.ai/evidence/README.md
```

Trong project đã cài:

```powershell
python .ai/scripts/verify_installation.py --root .
python .ai/scripts/self_test.py --context installed
python .ai/scripts/surface_drift.py
```

validate_harness.py và full regression chạy ở source, không ở project installed.
Để scratch ngoài source; không nới sandbox chỉ để test qua.

## 4. Phát hành đúng thứ tự

Chuẩn bị task/runtime URL/marker/rollback -> commit candidate -> thu bằng chứng
-> close_task -> commit closure -> deploy đúng closure SHA -> thu production-smoke
và production-critical-flow -> accept_release.

--ephemeral chỉ dùng cho probe bổ sung; không thay thế bằng chứng production
bắt buộc. Không cần deploy lại chỉ vì vừa ghi evidence. COMPLETE không mở lại:
tạo task kế tiếp cho candidate mới, giữ nguyên lịch sử.
Thay URL/revision/artifact thật vẫn là thay môi trường, cần bằng chứng mới.

## 5. Task, Skill và UI/UX

Có mẫu FEATURE/RELEASE đã điền trong .ai/harness/templates/.
Thay dữ liệu giả định trước khi dùng. task_guidance.py chỉ nhắc Skill phù hợp;
không chứng minh agent đã nạp Skill. .ai/UX_TOKENS.json là tùy chọn do
project khai báo, có schema và mẫu; hợp lệ về cấu trúc không có nghĩa
UI đẹp hay đạt accessibility. 13 Skills canonical không bị thay đổi.

Native Windows, live Skill và production acceptance phải có kết quả riêng;
không suy ra từ test Linux/fixture. Xem acceptance report của bản phát hành.
