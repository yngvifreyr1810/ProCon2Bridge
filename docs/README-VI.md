# ProCon2Bridge — hướng dẫn nhanh

Tải ZIP Windows trong Releases, giải nén vào thư mục có quyền ghi và bấm
**ProCon2Bridge-Start.cmd**. Lần đầu Windows có thể yêu cầu quyền quản trị để cài driver USB/IP
đã ký số; khởi động lại nếu được yêu cầu. Không cần cài Python.

Giữ **SYNC** để ghép nối lần đầu, sau đó chỉ cần bấm một nút để kết nối lại.
Game nhận tay cầm dưới tên Nintendo Switch Pro Controller. Giữ cửa sổ bridge mở;
**ProCon2Bridge-Stop.cmd** dùng để dừng. Nếu gyro trôi, bấm **ProCon2Bridge-Calibrate.cmd**, đặt tay cầm nằm
phẳng và giữ yên vài giây. config.json tự tạo, không cần nhập địa chỉ Bluetooth.

Bản **0.3.3** có **ProCon2Bridge-Settings.cmd** để gán hai nút sau **GL / GR**. Chọn nút hoặc
nhập tổ hợp như `ZL + ZR`, bấm **Save mappings** để áp dụng trong vòng một giây,
không cần kết nối lại. Ví dụ GL = B, GR = A. `NONE` là tắt gán nút. Tên nút theo
bố cục Nintendo; đây là gán vào nút Switch Pro 1 có sẵn, không phải thêm nút độc
lập cho game. Không có macro thời gian, turbo hoặc giả lập bàn phím. Cấu hình
gyro và các cài đặt cũ được giữ nguyên.

Với PowerMoon-Switch2Pro: cài bridge trước, rồi dùng PowerMoon-Switch2Pro-Install.cmd của gói cập nhật
Power Moon để chọn bản 0.1.6 hiện có. Sau đó dùng PowerMoon-Switch2Pro-Play.cmd. F1 > Controls có bật/tắt
motion, rung, đường truyền rung chi tiết thử nghiệm và nút test rung 2 giây.

Đã kiểm thử motion và rung trên tay cầm thật. Cấu hình tần số rung chi tiết vẫn
là thử nghiệm, chưa đảm bảo giống tuyệt đối HD Rumble/HD Rumble 2 của console.
Ngoài TOTK Recomp và SMO Recomp đã thử trong quá trình phát triển, chủ project
đã xác nhận rung/motion hoạt động với giả lập qua giao thức Switch Pro 1 và GL/GR
hoạt động đúng trong bản 0.3.2. Chưa ghi lại tên/phiên bản giả lập cho báo cáo đó;
không khẳng định mọi giả lập hoặc mọi game đều tương thích.
Lần đầu chạy, launcher thêm ProCon2Bridge vào danh sách tự khởi động của tài khoản
Windows hiện tại. Mục **ProCon2Bridge** xuất hiện trong **Task Manager > Startup apps**;
người dùng có thể tắt mục này để chuyển sang mở thủ công.

Đọc [README](../README.md), [HD-RUMBLE](HD-RUMBLE.md) và [THIRD_PARTY](THIRD_PARTY.md) để biết phạm vi và nguồn tham khảo.
Gói không chứa game, keys, firmware, dữ liệu trích xuất hay log cá nhân.
