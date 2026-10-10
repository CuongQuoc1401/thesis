import requests
import csv
import time
from datetime import datetime
import os
import sys

# ==========================================
# CẤU HÌNH THÔNG TIN API KAKAO / DAUM
# ==========================================
# Thay bằng REST API Key bạn lấy từ Kakao Developers
REST_API_KEY = "39f47e0372939e21d57086de8cf44946"

KEYWORDS = [
    "미래 유망 직업", "미래 직업", "유망 직종", "미래 일자리", "4차산업 직업",
    "신직업", "미래 유망 기술", "앞으로 뜰 직업", "인기 직업", "직업 트렌드",
    "미래 유망 전공", "인공지능 직업", "미래 산업", "일자리 변화", "직업의 미래",
    "유망 커리어", "미래 고소득 직업", "신성장 산업 직업", "사라지지 않을 직업",
    "미래형 직업", "미래 직업 전망", "미래 직업 추천", "유망 산업", "미래 인재",
    "직업 전망", "취업 전망", "채용 트렌드", "노동시장 변화", "디지털 전환",
    "AI 시대 직업", "AI 일자리", "데이터 직업", "빅데이터 직업", "로봇 산업", 
    "스마트 산업", "친환경 산업", "탄소중립 직업", "메타버스 직업", "반도체 산업",
    "첨단기술 직업"
]

OUTPUT_FILENAME = "daum_news_openapi.csv"

# Thiết lập khoảng thời gian lọc dữ liệu cho luận văn
START_DATE = datetime.strptime("2021-06-01", "%Y-%m-%d")
END_DATE = datetime.strptime("2026-06-01", "%Y-%m-%d")

# Tập hợp lưu trữ URL để tránh trùng lặp giữa các từ khóa
saved_links = set()

def parse_daum_date(date_str):
    """
    Chuyển đổi định dạng ngày của Daum API sang datetime object.
    Định dạng Daum trả về thường là: '2026-05-29T13:50:00.000+09:00'
    """
    try:
        clean_date_str = date_str.split(".")[0] # Loại bỏ phần mili giây và múi giờ
        return datetime.strptime(clean_date_str, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None

def search_daum_news(keyword, page_index=1):
    """Gọi API chính thức của Daum/Kakao để lấy danh sách tin tức"""
    url = "https://dapi.kakao.com/v2/search/web" # Sử dụng bộ tìm kiếm Web/News tổng hợp của Daum
    
    headers = {
        "Authorization": f"KakaoAK {REST_API_KEY}"
    }
    
    params = {
        "query": f"{keyword} 뉴스", # Thêm hậu tố 뉴스 để ép công cụ tìm kiếm lọc các trang báo chí
        "sort": "recency",         # Ưu tiên tin mới nhất để quét ngược thời gian về quá khứ
        "page": page_index,        # Số trang (Tối đa là 50)
        "size": 50                 # Lấy tối đa 50 kết quả mỗi trang để tối ưu hạn mức
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"\n[Lỗi API Daum] Status Code: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"\n[Lỗi kết nối Daum] {e}")
        return None

# ==========================================
# TIẾN TRÌNH CHẠY CHÍNH VỚI CƠ CHẾ AN TOÀN
# ==========================================
print("[Hệ thống] Khởi tạo hệ thống quét dữ liệu học thuật Daum News...")

# Nạp checkpoint nếu file đã tồn tại (để chạy tiếp tục khi bị dừng đột ngột)
if os.path.exists(OUTPUT_FILENAME):
    print(f"[Checkpoint] Tìm thấy file '{OUTPUT_FILENAME}' cũ. Đang nạp danh sách để bỏ qua trùng lặp...")
    try:
        with open(OUTPUT_FILENAME, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader) # Bỏ qua hàng tiêu đề
            for row in reader:
                if len(row) > 2:
                    saved_links.add(row[2]) # Thêm URL vào set phòng ngừa trùng
    except Exception:
        pass
else:
    # Tạo mới file và ghi tiêu đề nếu chưa tồn tại
    with open(OUTPUT_FILENAME, mode='w', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow(["Keyword", "Title", "Origin Link", "Publish Date"])

total_saved = 0

print("\n[Bắt đầu] Nhấn Ctrl + C nếu muốn dừng an toàn giữa chừng.")

try:
    for idx, keyword in enumerate(KEYWORDS, 1):
        print(f"\n==========================================")
        print(f"[{idx}/{len(KEYWORDS)}] ĐANG QUÉT DAUM: {keyword}")
        print(f"==========================================")
        
        page_index = 1
        out_of_range_count = 0
        keyword_saved_count = 0
        
        # Daum API giới hạn tối đa 50 trang cho một truy vấn tìm kiếm
        while page_index <= 50:
            print(f"   > [{keyword}] Đang gọi Daum API tại trang {page_index}...", end="\r")
            
            data = search_daum_news(keyword, page_index)
            if not data or "documents" not in data or len(data["documents"]) == 0:
                print(f"\n   [Dừng] Không tìm thấy thêm dữ liệu trên Daum cho từ khóa này.")
                break
                
            current_items = data["documents"]
            saved_in_page = 0
            
            with open(OUTPUT_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                
                for item in current_items:
                    link = item["url"]
                    
                    # KIỂM TRA TRÙNG LẶP (Chặn trùng giữa các từ khóa hoặc trùng lượt chạy cũ)
                    if link in saved_links:
                        continue
                    
                    # Daum trả về trường datetime cho thời gian xuất bản bài viết
                    pub_date_str = item.get("datetime", "")
                    pub_date = parse_daum_date(pub_date_str)
                    
                    if pub_date:
                        # Kiểm tra khoảng thời gian luận văn yêu cầu
                        if START_DATE <= pub_date <= END_DATE:
                            # Làm sạch các thẻ bẩn HTML (Daum dùng thẻ <b> giống Naver)
                            title = item["title"].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", '&')
                            
                            writer.writerow([keyword, title, link, pub_date.strftime("%Y-%m-%d %H:%M:%S")])
                            saved_links.add(link)
                            
                            saved_in_page += 1
                            keyword_saved_count += 1
                            total_saved += 1
                            out_of_range_count = 0
                            
                        elif pub_date < START_DATE:
                            out_of_range_count += 1
            
            print(f"   > Trang {page_index}: Lưu mới {saved_in_page} bài viết từ Daum.")
            
            # Nếu vượt mốc thời gian quá lâu, ngắt vòng lặp từ khóa này
            if out_of_range_count > 80:
                print(f"\n   [Hoàn tất] Thời gian bài viết trên Daum đã vượt quá mốc cũ nhất ({START_DATE.strftime('%Y-%m-%d')}).")
                break
                
            page_index += 1
            time.sleep(0.3) # Giữ khoảng trễ lịch sự tránh spam API của Kakao
            
        print(f"-> Hoàn thành từ khóa [{keyword}] trên Daum. Thu về {keyword_saved_count} bài mới.")

except KeyboardInterrupt:
    print("\n" + "="*50)
    print("[Tín hiệu] Nhận lệnh dừng từ người dùng (Ctrl + C)!")
    print("[An toàn] Toàn bộ dữ liệu tính tới thời điểm hiện tại đã được bảo toàn trong file CSV.")
    print("="*50)
    sys.exit()

print(f"\n==========================================")
print(f"[Thành công] Tiến trình cào dữ liệu Daum News hoàn tất!")
print(f"-> Tổng số bài viết độc nhất thu được từ Daum: {total_saved} bài.")
print(f"-> File kết quả: {OUTPUT_FILENAME}")
print(f"==========================================")