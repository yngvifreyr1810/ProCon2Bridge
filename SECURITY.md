# Before you run / Trước khi chạy

Scripts and an open repository are not, by themselves, a guarantee of safety.
This page makes the intended behavior inspectable; it does not promise that
antivirus engines will approve every build or that software can be risk-free.

## What this package does

* ProCon2Bridge-Start.cmd calls the included readable ProCon2Bridge-Start.ps1, then ProCon2Bridge.exe.
  On first use only, it installs the unmodified USB/IP 0.9.8.1 driver from
  drivers/. scripts/ProCon2Bridge-Install-Driver.ps1 checks its pinned SHA-256 and Windows Authenticode
  signature **before** requesting administrator rights and running the installer.
* The bridge reads controller input over Bluetooth and exposes a virtual Switch
  Pro gamepad. It writes a pairing record to the controller; SYNC may be needed
  to pair back to your console. It does not flash controller firmware.
* New bridge services listen only on this PC: 127.0.0.1 TCP 3240 (USB/IP), TCP
  26759 (stop), UDP 26760 (DSU motion) and UDP 26761 (detailed haptics).
  Do not expose these local services through port forwarding.
* These launch/install scripts do not download or execute remote script text,
  create scheduled tasks or services, disable antivirus, or add firewall exceptions. No telemetry
  or remote data upload is implemented in this bridge. Building from source
  separately downloads Python dependencies when you request pip install.
* config.json, status.json and rotating bridge.log stay beside the program.
  They may contain calibration, controller/adapter information and device addresses.
  Do not upload them without reviewing/redacting them. They are excluded from releases.
* ProCon2Bridge-Settings.cmd opens the native GL/GR mapping window in the same executable.
  It edits only the local configuration. config.lock coordinates saves with
  calibration; writes use a temporary file and atomic replacement. The window
  does not install keyboard hooks, inject keyboard/mouse input or create macros.

## Check a download

Use the ZIP from this repository's Releases, compare it with the published
CHECKSUMS-SHA256.txt using `Get-FileHash -Algorithm SHA256 <download.zip>`, and
read the source matching the release tag. Checksums detect changed downloads;
they do not prove the code is harmless or provide an independent security audit.
You may build from source instead. Build instructions and dependency pins are included.

**ProCon2Bridge.exe is currently not digitally signed.** The third-party driver
has its own signature; that does not sign or certify this project's executable.
Windows may show an unknown-publisher/SmartScreen warning. Keep Defender enabled.
If a warning is unexpected or you are unsure, stop and inspect the tagged source,
verify the files or report the exact detection; do not add blanket antivirus exclusions.
The cmd files use process-only ExecutionPolicy Bypass for local scripts; they do
not change the system's saved execution policy. This flag is not a security endorsement.

## Stop and remove

Run ProCon2Bridge-Stop.cmd, close its windows, and delete the extracted package if no longer
needed. If you also want to remove the separately installed USB/IP driver, use
Windows Settings > Apps > Installed apps > USB/IP for Windows. Keep it if another
USB/IP application still needs it. On first launch, the start script adds one
value to the current user's Windows Run key for ProCon2Bridge.exe. It is visible
in Task Manager > Startup apps and can be disabled there; no scheduled task or
service is installed.

## Tiếng Việt

Gói này có source và mã SHA-256 để bạn tự kiểm tra, nhưng đó không phải cam kết
“không có virus”. Script chỉ khởi chạy bridge và cài driver USB/IP có chữ ký số
khi cần; quyền quản trị dùng cho bước cài driver. File exe của project chưa được
ký số. Không cần tắt Defender hay thêm ngoại lệ antivirus. Cấu hình và log nằm
tại máy của bạn, có thể chứa địa chỉ thiết bị; đừng chia sẻ nguyên log công khai.
Chạy ProCon2Bridge-Stop.cmd để dừng, xóa thư mục giải nén để bỏ bridge; driver gỡ riêng trong
Installed apps. Báo vấn đề bảo mật qua mục Security của repository nếu có kênh
riêng; nếu không, chỉ đăng mô tả đã bỏ thông tin nhạy cảm, không đăng keys/log thô.
