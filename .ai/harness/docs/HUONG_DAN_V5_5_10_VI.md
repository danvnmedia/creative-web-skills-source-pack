# Hướng dẫn v5.5.10

Bản này vá một khe hở quan trọng khi dùng chiến lược **free trước, paid fallback sau**: ngân sách phải được kiểm tra trên **đích thực sự sắp tính tiền**, không chỉ trên model được yêu cầu ban đầu.

Ví dụ đúng:

```text
free A còn dùng được -> chạy free A
free A lỗi/quota -> xét paid B
                  -> kiểm tra quyền + toàn bộ budget áp dụng cho paid B
                  -> đủ budget: reserve nguyên tử rồi chạy
                  -> hết budget: bỏ paid B, thử đích hợp lệ khác hoặc degrade
```

Một request tới model free vẫn có thể chạy free khi người dùng đã hết paid budget. Chỉ đích paid mới bị chặn. Nếu chi phí hoặc budget scope của đích paid không xác định, policy v3 fail closed thay vì âm thầm tính tiền.

`provider_route_budget.py` là bộ đánh giá tham chiếu thuần local, không gọi API và không trừ tiền. Router thật phải tự bảo đảm reservation nguyên tử, chống race/concurrency và giải phóng reservation khi đích không chạy.

Nâng cấp vẫn theo installer plan -> review -> apply đúng digest. Không tự sửa policy trong dự án đang hoạt động chỉ để qua lint.
