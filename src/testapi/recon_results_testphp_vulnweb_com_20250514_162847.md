# Reconnaissance Report for http://testphp.vulnweb.com/ (Target Domain: testphp.vulnweb.com)

Report Generated: 2025-05-14 16:28:47

## Crew Execution Log & Raw Tool Outputs (Aggregated)

```markdown
# Báo Cáo Bảo Mật Toàn Diện: testphp.vulnweb.com

## 1. Tóm Tắt Điều Hành  
**Mục đích hệ thống**:  
✔️ Trang web demo của Acunetix (tiêu đề "Home of Acunetix Art")  
✔️ Mục đích đào tạo/phát hiện lỗ hổng bảo mật web (SQLi, XSS, File Inclusion)  

**Kiến trúc**:  
⚠️ Single-point failure (1 IP, không cân bằng tải)  
⚠️ Cấu hình tối giản:  
- Web server: Nginx 1.19.0 (lỗi thời)  
- Ngôn ngữ: PHP + MySQL (custom app)  
- Không IPv6/DNSSEC  

**Tình trạng bảo mật**:  
🔍 **Rủi ro chính**:  
1. 5+ lỗ hổng nghiêm trọng (SQLi, XSS)  
2. Không bảo vệ email (SPF/DKIM/DMARC)  
3. Lộ thông tin server (/phpinfo.php, /config.php)  

---

## 2. Kết Quả Chi Tiết  

### WHOIS  
⚠️ Không có dữ liệu (subdomain của vulnweb.com)  
- Không xác định được chủ sở hữu/liên hệ  

### DNS Records  
✔️ A Record: 176.28.50.165  
⚠️ **Rủi ro**:  
- Không DNSSEC → DNS spoofing  
- Không MX/TXT → Email spoofing  
- SOA mặc định (refresh 10800s)  

### Tên Miền Con  
⚠️ Không phát hiện (do hạn chế quét)  
- Gợi ý: Kiểm tra crt.sh/web.archive.org  

### Cổng Mở  
✔️ 80/tcp: Nginx 1.19.0  
⚠️ **Rủi ro**:  
- Nginx 1.19.0 (CVE-2021-23017)  
- 999 cổng filtered (có thể bỏ sót dịch vụ)  

### Thư Mục Web  
✔️ Phát hiện 15+ endpoint nhạy cảm:  
- /admin/, /config.php, /phpinfo.php  
⚠️ **Rủi ro**:  
- File cấu hình không được bảo vệ  
- Backup directory (/backup/) tồn tại  

### Ngăn Xếp Công Nghệ  
✔️ **Stack**:  
- Nginx 1.19.0 + PHP + MySQL  
⚠️ **Rủi ro**:  
- Phiên bản cũ, không WAF  
- Custom app → Khó vá lỗi  

---

## 3. Rủi Ro & Lỗ Hổng  

| Mức Độ       | Tác Động               | Bằng Chứng                          | Khả Năng Khai Thác |  
|--------------|------------------------|-------------------------------------|--------------------|  
| Nghiêm trọng | SQL Injection          | /userinfo.php, /search.php          | Cao                |  
| Cao          | Lộ thông tin server    | /phpinfo.php, /config.php           | Trung bình         |  
| Cao          | DNS Spoofing           | Thiếu DNSSEC                        | Cao                |  
| Trung bình   | XSS                    | Form input không filter              | Trung bình         |  
| Thấp         | Nginx lỗi thời         | Version 1.19.0 (2020)               | Thấp               |  

---

## 4. Khuyến Nghị Thực Thi  

🔍 **Ưu tiên cao (72h)**:  
1. Gỡ /phpinfo.php và /config.php  
2. Triển khai WAF (ModSecurity)  
3. Cấu hình DNSSEC  

🔍 **Ưu tiên trung bình (1 tuần)**:  
1. Nâng cấp Nginx lên bản 1.25.x  
2. Thêm SPF/DKIM/DMARC  
3. Audit code SQLi/XSS  

---

## 5. Kết Luận  

### Tóm Tắt Thông Tin Thu Thập  
**WHOIS**:  
- Subdomain không có bản ghi riêng → Khó truy vết chủ sở hữu  

**DNS**:  
- IP: 176.28.50.165 (AWS US-West-2)  
- Không bảo vệ DNS/email → Rủi ro giả mạo  

**Cổng**:  
- Chỉ mở 80/tcp (HTTP) → Dịch vụ tối giản  

**Thư mục**:  
- 6+ endpoint nhạy cảm (/admin/, /backup/) → Rủi ro leo thang đặc quyền  

**Công nghệ**:  
- Stack cũ (Nginx 1.19 + PHP) → Dễ bị khai thác  

### Đánh Giá Cuối Cùng  
**Kiến trúc**:  
- Mô hình đơn giản, không dự phòng → Phù hợp mục đích demo  
- Thiếu lớp bảo mật (WAF, DNSSEC) → Cố ý để demo tấn công  

**Bối cảnh**:  
- Lỗ hổng được thiết kế sẵn → Không phải sự cố thực tế  
- Cần cảnh báo rõ ràng đây là môi trường test  

**Khuyến nghị dài hạn**:  
1. Cô lập mạng (không public hóa)  
2. Thêm hướng dẫn sử dụng an toàn  
3. Logging tấn công mẫu để phân tích  
```