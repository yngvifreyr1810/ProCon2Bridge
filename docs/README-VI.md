# ProCon2Bridge 0.4.0

Giải nén đầy đủ gói rồi mở **ProCon2Bridge.exe** một lần. Ứng dụng tự cài vào
`%LOCALAPPDATA%/Programs/ProCon2Bridge`, đăng ký Startup và chạy nền với biểu tượng
tay cầm màu xanh cạnh đồng hồ. Nếu chưa có driver, Windows hỏi quyền cài USB/IP.
Không cần giữ cửa sổ CMD. Sau đó chỉ cần bật tay cầm; lần đầu ghép nối thì giữ SYNC.

Bấm chuột phải biểu tượng để mở Settings (gán GL/GR), Calibrate motion (đặt tay cầm
nằm yên), xem thư mục/log, mở cài đặt Startup hoặc Exit ProCon2Bridge. Mở EXE lần nữa
sẽ mở Settings. Tắt trong Task Manager > Startup apps > ProCon2Bridge nếu không muốn
tự chạy; ứng dụng tôn trọng lựa chọn của bạn. Không tự khởi chạy Power Moon/game.

Ứng dụng và cấu hình được chép sang thư mục cố định nên có thể dọn thư mục giải nén
sau khi cài. Khi nâng cấp, config.json đang dùng được giữ lại. Để gỡ: thoát từ tray,
xóa shortcut ProCon2Bridge trong shell:startup và xóa thư mục cài trên.
Driver USB/IP gỡ riêng trong Windows Installed apps nếu không ứng dụng nào cần.

Đã thử rung/motion trong TOTK Recomp, SMO Recomp và giả lập qua giao thức
Switch Pro 1; chưa có danh sách đầy đủ tên/phiên bản giả lập. Không khẳng định
mọi game đều tương thích hoặc HD Rumble giống tuyệt đối console.

Xem [README](../README.md), [HD-RUMBLE](HD-RUMBLE.md), [THIRD_PARTY](THIRD_PARTY.md)
và [SECURITY](../SECURITY.md). Gói không chứa game, keys, firmware hay tài nguyên game.
