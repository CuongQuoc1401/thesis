import pandas as pd
import time
import random
from newspaper import Article
import os
import csv
import sys

# Cấu hình tên file đồng bộ với dữ liệu Daum
INPUT_FILENAME = "daum_news_openapi.csv"
OUTPUT_FILENAME = "daum_news_with_content.csv"
ERROR_FILENAME = "daum_error_log.csv"

def crawl_article_content(url):
    """Truy cập URL bài báo và tự động trích xuất nội dung văn bản chi tiết"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
    ]
    
    # Khởi tạo đối tượng Article bóc tách tiếng Hàn
    article = Article(url, language='ko', user_agent=random.choice(user_agents))
    article.download()
    article.parse()
    
    content = article.text.strip()
    if not content:
        raise Exception("Nội dung bóc tách bị rỗng (Chuỗi văn bản rỗng)")
    return content

# ==========================================
# TIẾN TRÌNH KHỞI TẠO & KIỂM TRA CHECKPOINT
# ==========================================
if not os.path.exists(INPUT_FILENAME):
    print(f"[Lỗi] Không tìm thấy file đầu vào {INPUT_FILENAME}! Vui lòng chạy file lấy API Daum trước.")
    sys.exit()

# Đọc danh sách gốc thu được từ Daum
df_input = pd.read_csv(INPUT_FILENAME)

# Set lưu trữ toàn bộ các link đã xử lý (Thành công + Lỗi) để bỏ qua khi chạy lại
processed_links = set()

# Kiểm tra file thành công cũ để nạp checkpoint
if os.path.exists(OUTPUT_FILENAME):
    print(f"[Checkpoint] Tìm thấy file kết quả Daum cũ. Đang quét các bài đã chạy...")
    try:
        df_old = pd.read_csv(OUTPUT_FILENAME)
        if 'Origin Link' in df_old.columns:
            processed_links.update(df_old['Origin Link'].dropna().tolist())
    except Exception:
        pass

# Kiểm tra file lỗi cũ để cũng bỏ qua luôn (tránh sa lầy vào link chết)
if os.path.exists(ERROR_FILENAME):
    try:
        df_err = pd.read_csv(ERROR_FILENAME)
        if 'Origin Link' in df_err.columns:
            processed_links.update(df_err['Origin Link'].dropna().tolist())
    except Exception:
        pass

# Tạo cấu hình file ban đầu nếu chạy lần đầu tiên
if not os.path.exists(OUTPUT_FILENAME):
    with open(OUTPUT_FILENAME, mode='w', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow(["Keyword", "Title", "Origin Link", "Publish Date", "Content"])

if not os.path.exists(ERROR_FILENAME):
    with open(ERROR_FILENAME, mode='w', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow(["Keyword", "Title", "Origin Link", "Publish Date", "Error Message"])

# Lọc loại bỏ toàn bộ các link đã xử lý xong
df_todo = df_input[~df_input['Origin Link'].isin(processed_links)]

print(f"[Hệ thống] Tổng số bài viết gốc từ Daum: {len(df_input)}")
print(f"[Hệ thống] Đã hoàn thành/bỏ qua từ trước: {len(processed_links)}")
print(f"[Hệ thống] Số lượng bài còn lại cần cào nội dung: {len(df_todo)}")

if len(df_todo) == 0:
    print("[Hoàn tất] Toàn bộ danh sách bài viết từ Daum đã được cào nội dung đầy đủ!")
    sys.exit()

# ==========================================
# TIẾN TRÌNH CÀO CUỐN CHIẾU & BẢO VỆ DỮ LIỆU
# ==========================================
print("\n[Bắt đầu] Đang tiến hành cào nội dung chi tiết...")
print("          (Bấm Ctrl + C nếu muốn dừng an toàn giữa chừng)")
total_items = len(df_input)

try:
    for idx, row in df_todo.iterrows():
        keyword = str(row['Keyword']) if pd.notna(row['Keyword']) else ""
        title = str(row['Title']) if pd.notna(row['Title']) else "[Không có tiêu đề]" # <--- Ép kiểu str an toàn
        url = row['Origin Link']
        pub_date = row['Publish Date']
        
        # Bây giờ in ra sẽ mượt mà không lo bị sập code nữa
        print(f"[{idx + 1}/{total_items}] Đang lấy nội dung: {title[:25]}...")
        
        try:
            # Thực hiện tải và bóc tách nội dung
            content = crawl_article_content(url)
            
            # GHI VÀO FILE THÀNH CÔNG NGAY LẬP TỨC (MODE APPEND)
            with open(OUTPUT_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
                csv.writer(f).writerow([keyword, title, url, pub_date, content])
                
        except Exception as e:
            # GHI VÀO FILE LỖI NGAY LẬP TỨC NẾU CÓ SỰ CỐ TRANG WEB
            error_msg = str(e)
            print(f"   => [Lỗi bài viết] {error_msg}")
            with open(ERROR_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
                csv.writer(f).writerow([keyword, title, url, pub_date, error_msg])
        
        # Thiết lập độ trễ ngẫu nhiên từ 1.5 đến 3 giây để an toàn cho IP của bạn
        time.sleep(random.uniform(0.5, 0.8))

except KeyboardInterrupt:
    # Bắt tín hiệu ngắt lệnh Ctrl + C
    print("\n" + "="*50)
    print("[Tín hiệu ngắt] Phát hiện bạn đã bấm Ctrl + C để dừng chương trình!")
    print("[An toàn] Hệ thống đã đợi bài viết đang chạy lưu xong dữ liệu lên đĩa.")
    print("[An toàn] Dữ liệu đã gộp được bảo toàn. Bạn có thể bật lại code bất kỳ lúc nào để chạy tiếp.")
    print("="*50)
    sys.exit()

print(f"\n==========================================")
print(f"[Thành công] Toàn bộ tiến trình hoàn tất!")
print(f"-> File chứa nội dung chi tiết sạch: {OUTPUT_FILENAME}")
print(f"-> File log chứa các bài báo lỗi: {ERROR_FILENAME}")
print(f"==========================================")