# Admin login và khôi phục mật khẩu

Admin đăng nhập bằng `/login` và cùng `POST /api/v1/auth/login` như người dùng thường. Backend trả thông tin người dùng và đặt cookie `HttpOnly` cho access/refresh token. Frontend dùng `credentials: include`; `/admin` kiểm tra `role === "ADMIN"`, còn API kiểm tra người dùng từ DB theo JWT `sub` và phiên. Không có mật khẩu hoặc token Admin trong frontend.

## Chẩn đoán an toàn

Trong môi trường chạy backend, sau khi migrate DB:

```sh
python -m app.cli.check_admin --email admin@example.com --verify-env-password
# Docker local:
docker compose exec backend python -m app.cli.check_admin --email admin@example.com --verify-env-password
```

Lệnh chỉ cho biết bootstrap có bật, email/mật khẩu có được cấu hình, tài khoản có tồn tại, `role`, `status`, có hash và mật khẩu cấu hình có khớp hay không. Lệnh không in mật khẩu hoặc hash. `--verify-env-password` chỉ so sánh, không thay đổi DB. Kiểm tra đúng tên DB và môi trường của backend đang chạy; `.env` của shell và container có thể khác nhau. Để kiểm tra biến đã vào Docker mà không in giá trị: `docker compose exec backend python -c 'import os; print({k: bool(os.getenv(k)) for k in ("INITIAL_ADMIN_ENABLED", "INITIAL_ADMIN_EMAIL", "INITIAL_ADMIN_PASSWORD")})'`.

Nếu tài khoản thiếu, đặt `INITIAL_ADMIN_ENABLED=true` cùng email và mật khẩu mới đủ mạnh trong secret environment backend, chạy migrate rồi khởi động backend; hoặc dùng `python -m app.cli.create_admin --email admin@example.com --name Administrator --new-account` và nhập mật khẩu hai lần. Sau khi tạo, tắt bootstrap và xóa mật khẩu ban đầu khỏi môi trường. Nếu tài khoản đã tồn tại, bootstrap chỉ nâng quyền, **không thay mật khẩu**. Vì vậy giá trị `INITIAL_ADMIN_PASSWORD` mới không tự biến thành mật khẩu đăng nhập của tài khoản cũ.

Nếu tài khoản tồn tại nhưng mật khẩu không khớp, chạy lệnh đặt lại tường minh:

```sh
python -m app.cli.reset_admin_password --email admin@example.com
# Docker local sau khi image backend được build lại:
docker compose exec backend python -m app.cli.reset_admin_password --email admin@example.com
```

Lệnh hỏi mật khẩu mới và xác nhận qua terminal ẩn; yêu cầu ít nhất 12 ký tự, chữ và số, loại bỏ placeholder phổ biến. Nó chỉ áp dụng cho tài khoản đang có `role=ADMIN`, hash bằng cùng Argon2 của đăng ký/đăng nhập, ghi audit và thu hồi phiên cũ. Không thay `status`; nếu `status=DISABLED`, cần kích hoạt bằng quy trình quản trị hợp lệ. Sau khi reset, đăng nhập lại bình thường và dùng mật khẩu mới. Không đặt mật khẩu vào argv, shell history, frontend hoặc Terraform. Tùy chọn `--password-file` chỉ dành cho môi trường tự động có file thường chmod `600`, không phải symlink; xóa file ngay khi hoàn tất.

## Các lỗi thường gặp

| Triệu chứng | Kiểm tra |
| --- | --- |
| Login `401` | Email chuẩn hóa, tài khoản đúng DB, `--verify-env-password`; thử reset tường minh nếu mật khẩu cũ không còn. Public login giữ thông báo chung để không tiết lộ sự tồn tại của tài khoản. |
| Login `403` tài khoản bị vô hiệu hóa | `check_admin` phải báo `status=ACTIVE`; không bỏ qua kiểm tra status. |
| Login `200` nhưng `/admin` chặn | `check_admin` phải báo `role=ADMIN`; gọi `/api/v1/auth/me` và `/api/v1/admin/dashboard` cùng cookie. User thường phải nhận `403` từ admin API. |
| Login thành công rồi về `/login` | Xem Network: `Set-Cookie`, `/auth/me`, `/auth/refresh`; kiểm tra `FRONTEND_URL`, `NEXT_PUBLIC_API_BASE_URL`, `credentials: include`, `COOKIE_SAMESITE` và HTTPS. |
| Bootstrap không tạo tài khoản | Xem `INITIAL_ADMIN_ENABLED`, email/mật khẩu hiện diện, validation mật khẩu, migrate DB trước startup; log `initial_admin_bootstrap` không chứa secret. |
| Trang Admin gọi nhầm API | Build lại frontend sau khi đổi `NEXT_PUBLIC_API_BASE_URL`; giá trị này được đóng vào static bundle. Docker local mặc định dùng `http://localhost:8000`. |

Docker Compose nội suy ký tự `$` trong `.env`/Compose; dùng `$$` khi cần truyền một `$` qua Compose, hoặc cấu hình secret bằng cơ chế của nơi deploy. Ký tự `#`, dấu nháy và khoảng trắng cũng cần kiểm tra theo cú pháp `.env`; lệnh `check_admin --verify-env-password` giúp nhận biết giá trị thực tế đã vào backend có khớp hash hay không mà không in bí mật. Khi frontend và API ở hai site khác nhau, backend HTTPS cần `COOKIE_SAMESITE=none`; với local `localhost:3000`/`localhost:8000`, mặc định `lax` phù hợp. `FRONTEND_URL` phải khớp origin frontend, không dùng wildcard cùng credentialed CORS.
