import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import csv
import sys
import json

# ==========================================
# CẤU HÌNH TÊN FILE ĐỒNG BỘ
# ==========================================
INPUT_FILENAME = "datagov_search_results.csv"
OUTPUT_FILENAME = "datagov_with_content.csv"
ERROR_FILENAME = "datagov_error_log.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.data.go.kr/"
}

def crawl_datagov_page_content(url):
    """
    Truy cập trang chi tiết data.go.kr và bóc tách nội dung.
    Ưu tiên đọc thẻ JSON-LD để lấy dữ liệu sạch, nếu không có sẽ fallback về BeautifulSoup text.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            raise Exception(f"Lỗi HTTP Status Code: {response.status_code}")
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- ƯU TIÊN 1: BẮT THẺ SCRIPT JSON-LD (DỮ LIỆU SẠCH VÀ CHI TIẾT NHẤT) ---
        json_ld_tag = soup.find("script", type="application/ld+json")
        if json_ld_tag:
            try:
                # Nạp chuỗi HTML thành đối tượng Dictionary trong Python
                data_json = json.loads(json_ld_tag.string)
                
                # Trích xuất các trường dữ liệu lớn để làm phong phú nội dung phân tích từ khóa
                name = data_json.get("name", "")
                description = data_json.get("description", "").replace("<br/>", " ").replace("<br />", " ")
                
                # Xử lý trường keywords (có thể là danh sách hoặc chuỗi)
                keywords_raw = data_json.get("keywords", [])
                if isinstance(keywords_raw, list):
                    keywords = ", ".join(keywords_raw)
                else:
                    keywords = str(keywords_raw)
                
                # Gộp lại thành một chuỗi văn bản hoàn chỉnh phục vụ phân tích luận văn
                full_content = f"데이터셋명: {name} | 상세설명: {description} | 키워드: {keywords}"
                
                # Làm sạch khoảng trắng thừa
                full_content = " ".join(full_content.split())
                if full_content.strip():
                    return full_content
            except Exception:
                pass # Nếu lỗi phân rã JSON thì tự động bỏ qua để xuống cách 2
                
        # --- ƯU TIÊN 2: BÓC TÁCH THEO THẺ HTML TRUYỀN THỐNG (FALLBACK) ---
        content_pieces = []
        
        # Lấy khối mô tả chính trên giao diện web
        desc_box = soup.select_one(".data-search-view .w-desc, .publicDataDesc")
        if desc_box:
            content_pieces.append(desc_box.get_text(strip=True))
            
        # Lấy thông tin bổ sung từ các bảng thuộc tính dữ liệu
        table_info = soup.select(".table-details, .detail-table, table")
        for table in table_info:
            content_pieces.append(table.get_text(" | ", strip=True))
            
        full_content = " ".join("\n".join([p for p in content_pieces if p]).split()).strip()
        
        if not full_content:
            # Biện pháp cuối cùng: lấy toàn bộ text trong view chính của trang
            main_view = soup.select_one(".data-search-view, #contents")
            if main_view:
                full_content = " ".join(main_view.get_text(" ", strip=True).split())
                
        if not full_content:
            raise Exception("Nội dung bóc tách hoàn toàn bị rỗng.")
            
        return full_content
        
    except Exception as e:
        raise Exception(f"Không thể bóc tách trang: {str(e)}")

# ==========================================
# TIẾN TRÌNH KHỞI TẠO & QUÉT CHECKPOINT
# ==========================================
if not os.path.exists(INPUT_FILENAME):
    print(f"[Lỗi] Không tìm thấy file danh sách '{INPUT_FILENAME}'. Hãy chạy file cào tìm kiếm trước.")
    sys.exit()

df_input = pd.read_csv(INPUT_FILENAME, dtype=str)
processed_links = set()

# Nạp checkpoint file thành công cũ để bỏ qua khi chạy lại
if os.path.exists(OUTPUT_FILENAME):
    print(f"[Checkpoint] Phát hiện file kết quả cũ. Đang đồng bộ danh sách đã lấy...")
    try:
        df_old = pd.read_csv(OUTPUT_FILENAME, dtype=str)
        if 'Detail_Link' in df_old.columns:
            processed_links.update(df_old['Detail_Link'].dropna().tolist())
    except Exception:
        pass

# Nạp checkpoint file lỗi cũ để cũng bỏ qua (tránh sa lầy vào link chết)
if os.path.exists(ERROR_FILENAME):
    try:
        df_err = pd.read_csv(ERROR_FILENAME, dtype=str)
        if 'Detail_Link' in df_err.columns:
            processed_links.update(df_err['Detail_Link'].dropna().tolist())
    except Exception:
        pass

# Khởi tạo khung file trống theo đúng định dạng nếu chạy lần đầu tiên
if not os.path.exists(OUTPUT_FILENAME):
    pd.DataFrame(columns=[
        "Keyword", "Data_Type", "Title", "Description", "Provider", "Modify_Date", "Detail_Link", "Keywords_Tag", "Detailed_Content"
    ]).to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig')

if not os.path.exists(ERROR_FILENAME):
    pd.DataFrame(columns=["Keyword", "Title", "Detail_Link", "Error_Message"]).to_csv(ERROR_FILENAME, index=False, encoding='utf-8-sig')

# Tiến hành lọc bỏ toàn bộ các link đã từng xử lý
df_todo = df_input[~df_input['Detail_Link'].isin(processed_links)]
total_items = len(df_input)

print(f"[Hệ thống] Tổng số bản ghi tìm thấy: {total_items}")
print(f"[Hệ thống] Đã hoàn thành/bỏ qua từ trước: {len(processed_links)}")
print(f"[Hệ thống] Số lượng liên kết cần cào nội dung còn lại: {len(df_todo)}")

if len(df_todo) == 0:
    print("[Hoàn tất] Không còn liên kết nào cần xử lý!")
    sys.exit()

# ==========================================
# VÒNG LẶP CÀO CHI TIẾT VÀ GIỮ AN TOÀN KHI DỪNG
# ==========================================
print("\n[Bắt đầu] Đang tiến hành bóc tách nội dung chi tiết từ Chính phủ...")
print("          (Nếu bấm Ctrl + C, hệ thống sẽ chạy NỐT bài hiện tại rồi mới đóng chương trình)")

try:
    for idx, row in df_todo.iterrows():
        keyword = row.get('Keyword', '')
        dtype = row.get('Data_Type', '')
        title = str(row.get('Title', '')).strip() if pd.notna(row.get('Title')) else "[Không tiêu đề]"
        description = row.get('Description', '')
        provider = row.get('Provider', '')
        modify_date = row.get('Modify_Date', '')
        url = row.get('Detail_Link', '')
        keywords_tag = row.get('Keywords_Tag', '')
        
        # Tính toán chỉ số thứ tự thực tế dựa trên index của DataFrame gốc để hiển thị chính xác tiến độ
        actual_index = idx + 1
        print(f"[{actual_index}/{total_items}] Đang xử lý: {title[:25]}...")
        
        try:
            # Gọi hàm cào bóc tách nội dung (Thử JSON-LD trước, HTML sau)
            detailed_content = crawl_datagov_page_content(url)
            
            # GHI NGAY VÀO FILE THÀNH CÔNG (APPEND MODE)
            with open(OUTPUT_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
                csv.writer(f).writerow([keyword, dtype, title, description, provider, modify_date, url, keywords_tag, detailed_content])
                
        except Exception as e:
            # GHI NGAY VÀO FILE LOG LỖI NẾU XẢY RA SỰ CỐ
            error_msg = str(e)
            print(f"   => [LỖI TRANG]: {error_msg}")
            with open(ERROR_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
                csv.writer(f).writerow([keyword, title, url, error_msg])
                
        # Thiết lập độ trễ ngẫu nhiên từ 1.0 đến 2.5 giây để bảo vệ IP khỏi hệ thống chặn của Chính phủ
        time.sleep(random.uniform(0.5, 0.8))

except KeyboardInterrupt:
    print("\n" + "="*60)
    print("[Tín hiệu ngắt] Nhận được phím tắt Ctrl + C từ người dùng!")
    print("[An toàn] Hệ thống đã đợi bài đang chạy lưu xong dữ liệu lên ổ cứng.")
    print("[An toàn] Tiến trình dừng thành công. Bạn có thể bật lại code bất kỳ lúc nào để chạy tiếp.")
    print("="*60)
    sys.exit(0)

print(f"\n==================================================")
print(f"[Hoàn thành] Toàn bộ tiến trình bóc tách dữ liệu chi tiết kết thúc!")
print(f"-> File kết quả nội dung sạch: {OUTPUT_FILENAME}")
print(f"-> File log các liên kết báo lỗi: {ERROR_FILENAME}")
print(f"==================================================")