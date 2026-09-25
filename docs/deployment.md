# Khởi tạo Admin và kết nối frontend/backend

Các biến `INITIAL_ADMIN_*` chỉ đặt trên **FastAPI backend**. Không đặt chúng trong `NEXT_PUBLIC_*`, frontend build, Terraform, hoặc Docker image. Dùng secret manager/biến môi trường của nơi chạy backend. `.env.example` chỉ chứa placeholder không dùng được làm mật khẩu.

```dotenv
APP_ENV=production
INITIAL_ADMIN_ENABLED=true
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=<mật khẩu mạnh duy nhất, ít nhất 12 ký tự, chữ và số>
INITIAL_ADMIN_NAME=Administrator
```

Sau migration, khi backend khởi động, bootstrap tìm email cấu hình. Nếu chưa có, tạo tài khoản `ADMIN`, `ACTIVE`, `is_test_account=false` và hash mật khẩu bằng cùng Argon2 của luồng đăng nhập. Nếu đã có, chỉ nâng `role=ADMIN` nếu cần, thu hồi các phiên cũ khi nâng quyền, và **giữ nguyên mật khẩu hiện có**. Chạy lại nhiều lần không tạo bản sao. Email thiếu, hoặc mật khẩu thiếu khi tài khoản chưa tồn tại, sẽ được ghi log rõ ràng và không tạo tài khoản; mật khẩu ngắn hoặc placeholder như `change-me` gây lỗi cấu hình khi bootstrap bật. `INITIAL_ADMIN_ENABLED=false` tắt hoàn toàn bootstrap.

Đăng nhập qua `/login` thông thường và kiểm tra `/admin`. Sau khi tạo thành công: thay mật khẩu nếu muốn, xóa `INITIAL_ADMIN_PASSWORD` khỏi môi trường và đặt `INITIAL_ADMIN_ENABLED=false`, rồi khởi động lại. Tài khoản Admin vẫn tồn tại. Có thể dùng CLI: `python -m app.cli.create_admin --email admin@example.com --name Administrator --new-account`; CLI hỏi mật khẩu tương tác. Với tài khoản có sẵn, bỏ `--new-account` để nâng quyền mà không đổi mật khẩu.

Frontend static export dùng `NEXT_PUBLIC_API_BASE_URL=https://api.example.com` **lúc build**. Backend cần `FRONTEND_URL=https://<frontend-hostname>` trùng chính xác origin trình duyệt (không có path). CORS bật credentials cho origin này. Khi frontend CloudFront và API thuộc hai site khác nhau, đặt `COOKIE_SAMESITE=none` và chạy backend qua HTTPS; cookie sẽ là `HttpOnly; Secure; SameSite=None`. Backend kiểm tra Origin cho mọi yêu cầu ghi, kể cả `Sec-Fetch-Site: cross-site`. Nếu dùng subdomain cùng site, `lax` có thể phù hợp nhưng vẫn cần kiểm tra login trên trình duyệt thực. Cookie bên thứ ba có thể bị trình duyệt chặn; cấu hình frontend và API cùng site qua custom domain là phương án ổn định hơn.

Không triển khai backend/database bằng Terraform trong `devops/`. Xem [hướng dẫn CDN](../devops/README.md).
