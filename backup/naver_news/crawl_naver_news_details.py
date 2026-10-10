import pandas as pd
import time
import random
from newspaper import Article
import os
import csv
import sys

INPUT_FILENAME = "naver_news_openapi.csv"
OUTPUT_FILENAME = "naver_news_with_content.csv"
ERROR_FILENAME = "error_log.csv"

def crawl_article_content(url):
    """Truy cập URL bài báo và tự động trích xuất nội dung văn bản chi tiết"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
    ]
    
    # Khởi tạo Article
    article = Article(url, language='ko', user_agent=random.choice(user_agents))
    article.download()
    article.parse()
    
    content = article.text.strip()
    if not content:
        raise Exception("Nội dung bóc tách bị rỗng (Chuỗi rỗng)")
    return content

# ==========================================
# TIẾN TRÌNH KHỞI TẠO & KIỂM TRA CHECKPOINT
# ==========================================
if not os.path.exists(INPUT_FILENAME):
    print(f"[Lỗi] Không tìm thấy file đầu vào {INPUT_FILENAME}!")
    sys.exit()

# Đọc file danh sách gốc
df_input = pd.read_csv(INPUT_FILENAME)

# Tập hợp (set) chứa các link đã được cào thành công hoặc ghi nhận lỗi trước đó
processed_links = set()

# Kiểm tra xem file OUTPUT đã tồn tại chưa để nạp checkpoint (chạy tiếp tục)
if os.path.exists(OUTPUT_FILENAME):
    print(f"[Checkpoint] Tìm thấy file kết quả cũ. Đang quét các bài đã chạy...")
    try:
        df_old = pd.read_csv(OUTPUT_FILENAME)
        if 'Origin Link' in df_old.columns:
            processed_links.update(df_old['Origin Link'].dropna().tolist())
    except Exception:
        pass

# Kiểm tra xem file ERROR đã tồn tại chưa để cũng bỏ qua các link lỗi (tránh thử lại vô ích)
if os.path.exists(ERROR_FILENAME):
    try:
        df_err = pd.read_csv(ERROR_FILENAME)
        if 'Origin Link' in df_err.columns:
            processed_links.update(df_err['Origin Link'].dropna().tolist())
    except Exception:
        pass

# Khởi tạo các file CSV nếu chưa tồn tại (Ghi hàng tiêu đề)
if not os.path.exists(OUTPUT_FILENAME):
    with open(OUTPUT_FILENAME, mode='w', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow(["Keyword", "Title", "Origin Link", "Publish Date", "Content"])

if not os.path.exists(ERROR_FILENAME):
    with open(ERROR_FILENAME, mode='w', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow(["Keyword", "Title", "Origin Link", "Publish Date", "Error Message"])

# Lọc bỏ các bài viết đã được xử lý ra khỏi danh sách chạy hiện tại
df_todo = df_input[~df_input['Origin Link'].isin(processed_links)]

print(f"[Hệ thống] Tổng số bài viết gốc: {len(df_input)}")
print(f"[Hệ thống] Đã hoàn thành/bỏ qua trước đó: {len(processed_links)}")
print(f"[Hệ thống] Số bài còn lại cần cào: {len(df_todo)}")

if len(df_todo) == 0:
    print("[Hoàn tất] Toàn bộ danh sách đã được cào xong!")
    sys.exit()

# ==========================================
# TIẾN TRÌNH CHẠY CHÍNH VỚI GRACEFUL SHUTDOWN
# ==========================================
print("\n[Bắt đầu] Nhấn Ctrl + C nếu muốn dừng an toàn giữa chừng.")
total_items = len(df_input)

try:
    for idx, row in df_todo.iterrows():
        keyword = row['Keyword']
        title = row['Title']
        url = row['Origin Link']
        pub_date = row['Publish Date']
        
        # In tiến độ thực tế dựa trên vị trí của bài viết trong file gốc
        print(f"[{idx + 1}/{total_items}] Đang xử lý: {title[:25]}...")
        
        try:
            # Tiến hành cào nội dung bài viết
            content = crawl_article_content(url)
            
            # GHI VÀO FILE THÀNH CÔNG NGAY LẬP TỨC
            with open(OUTPUT_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
                csv.writer(f).writerow([keyword, title, url, pub_date, content])
                
        except Exception as e:
            # GHI VÀO FILE LỖI NGAY LẬP TỨC NẾU CÓ SỰ CỐ
            error_msg = str(e)
            print(f"   => [Lỗi] {error_msg}")
            with open(ERROR_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
                csv.writer(f).writerow([keyword, title, url, pub_date, error_msg])
        
        # Giãn cách thời gian ngẫu nhiên để an toàn
        time.sleep(random.uniform(0.5, 0.8))

except KeyboardInterrupt:
    # Kích hoạt khi người dùng bấm Ctrl + C trong Terminal
    print("\n" + "="*50)
    print("[Tín hiệu] Phát hiện bạn đã bấm dừng chương trình (Ctrl + C)!")
    print("[An toàn] Hệ thống đã đợi bài viết hiện tại hoàn tất và lưu dữ liệu xong.")
    print("[An toàn] Bạn có thể an tâm bật lại code bất cứ lúc nào để chạy tiếp mốc này.")
    print("="*50)
    sys.exit()

print(f"\n==========================================")
print(f"[Thành công] Tiến trình hoàn tất 100% danh sách!")
print(f"-> File thành công: {OUTPUT_FILENAME}")
print(f"-> File chứa các link lỗi: {ERROR_FILENAME}")
print(f"==========================================")