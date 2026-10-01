# Hướng dẫn nâng cấp Harness v5.5.5

Giải nén bộ nguồn NGOÀI thư mục dự án. Không copy đè root.
Từ thư mục vừa giải nén, chạy plan trước:

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN"
python INSTALL_HARNESS.py --target "D:\Projects\TEN_DU_AN" --apply --confirm PLAN_DIGEST
```

Trong dự án đã cài, kiểm tra đúng ngữ cảnh installed:

```powershell
python .ai/scripts/self_test.py --context installed
```

Bộ regression đầy đủ chỉ chạy từ gói SOURCE đã kiểm chứng.
Thư mục tạm phải ghi được và nằm ngoài toàn bộ cây nguồn:

```powershell
python .ai/scripts/deterministic_regression_gate.py --temp-root "D:\HarnessScratch" --out "D:\HarnessScratch\v555-regression.json"
```

Không đổi Git global, không nới sandbox, không xóa bản cũ bằng wildcard.
Các đường dẫn ví dụ cần thuộc vùng bạn cho phép ghi.
Giữ snapshot dự án trước khi nâng cấp.

Linux/WSL PASS không thay thế native Windows PASS. CRLF/BOM fixture PASS
cũng không chứng minh toàn bộ Windows runtime. Bản này chưa
có vòng kiểm thử native Windows thực tế trong môi trường phát hành.
CI accepted, deployment success và production UX acceptance là ba mức khác nhau.
