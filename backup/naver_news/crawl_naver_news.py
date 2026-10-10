import requests
import csv
import time
from datetime import datetime

# ==========================================
# CẤU HÌNH THÔNG TIN API (Thay bằng thông tin của bạn)
# ==========================================
CLIENT_ID = "GpGaMWQLk55JzuOBdZ_p"
CLIENT_SECRET = "6OFccouYR5"

# Danh sách 20 từ khóa tương tự 
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

OUTPUT_FILENAME = "naver_news_openapi.csv"

# Thiết lập khoảng thời gian cần lọc cho luận văn
START_DATE = datetime.strptime("2021-06-01", "%Y-%m-%d")
END_DATE = datetime.strptime("2026-06-01", "%Y-%m-%d")

# Tập hợp (set) lưu trữ các URL đã được lưu để tránh trùng lặp giữa các từ khóa
saved_links = set()

def parse_naver_date(date_str):
    """Chuyển đổi định dạng ngày của Naver API sang datetime object của Python"""
    try:
        clean_date_str = " ".join(date_str.split()[:5])
        return datetime.strptime(clean_date_str, "%a, %d %b %Y %H:%M:%S")
    except Exception:
        return None

def search_news_via_openapi(keyword, start_index=1):
    """Gọi API chính thức của Naver và trả về dữ liệu dạng JSON"""
    url = "https://openapi.naver.com/v1/search/news.json"
    
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    
    params = {
        "query": keyword,
        "display": 100,     # Lấy tối đa 100 bài mỗi lần gọi
        "start": start_index,
        "sort": "date"      # Ưu tiên tin mới nhất
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"\n[Lỗi API] Status Code: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"\n[Lỗi kết nối] {e}")
        return None

# ==========================================
# TIẾN TRÌNH CHẠY CHÍNH (MAIN LOOP)
# ==========================================
print("[Hệ thống] Khởi tạo file và bắt đầu quét danh sách từ khóa...")

# Bước 1: Tạo file và ghi hàng tiêu đề duy nhất 1 lần ở đầu chương trình
with open(OUTPUT_FILENAME, mode='w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Keyword", "Title", "Origin Link", "Publish Date"]) # Thêm cột Keyword để dễ quản lý

total_saved = 0

# Bước 2: Vòng lặp duyệt qua từng từ khóa trong danh sách 20 từ
for idx, keyword in enumerate(KEYWORDS, 1):
    print(f"\n==========================================")
    print(f"[{idx}/{len(KEYWORDS)}] ĐANG QUÉT TỪ KHÓA: {keyword}")
    print(f"==========================================")
    
    start_index = 1
    out_of_range_count = 0  
    keyword_saved_count = 0
    
    while start_index <= 1000:
        print(f"   > [{keyword}] Đang gọi API tại start={start_index}...", end="\r")
        
        data = search_news_via_openapi(keyword, start_index)
        if not data or "items" not in data or len(data["items"]) == 0:
            print(f"\n   [Dừng] Không tìm thấy thêm dữ liệu cho từ khóa này.")
            break
            
        current_items = data["items"]
        saved_in_page = 0
        
        # Mở file bằng chế độ 'a' (append) để ghi thêm dữ liệu, không làm mất dữ liệu cũ
        with open(OUTPUT_FILENAME, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            for item in current_items:
                link = item["originallink"] if item["originallink"] else item["link"]
                
                # KIỂM TRA TRÙNG LẶP: Nếu URL này đã từng được lưu trước đó, bỏ qua bài viết này
                if link in saved_links:
                    continue
                
                pub_date_str = item["pubDate"]
                pub_date = parse_naver_date(pub_date_str)
                
                if pub_date:
                    # Kiểm tra khoảng thời gian luận văn yêu cầu
                    if START_DATE <= pub_date <= END_DATE:
                        title = item["title"].replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                        
                        # Ghi vào file kèm theo tên từ khóa kích hoạt bài viết đó
                        writer.writerow([keyword, title, link, pub_date.strftime("%Y-%m-%d %H:%M:%S")])
                        
                        # Thêm link vào bộ nhớ set để đánh dấu đã xử lý
                        saved_links.add(link)
                        
                        saved_in_page += 1
                        keyword_saved_count += 1
                        total_saved += 1
                        out_of_range_count = 0 
                        
                    elif pub_date < START_DATE:
                        out_of_range_count += 1

        print(f"   > Chỉ mục {start_index}: Lưu mới {saved_in_page} bài (Loại trùng hoặc ngoài dải giờ).")
        
        # Nếu bài viết đã quá cũ so với mốc START_DATE, dừng quét từ khóa này để chuyển từ tiếp theo
        if out_of_range_count > 150:
            print(f"\n   [Hoàn tất] Đã vượt quá mốc thời gian cũ nhất ({START_DATE.strftime('%Y-%m-%d')}).")
            break
            
        start_index += 100
        time.sleep(0.2) # Giữ khoảng trễ nhỏ để an toàn cho API
        
    print(f"-> Hoàn thành từ khóa [{keyword}]. Thu về thêm {keyword_saved_count} bài viết mới không trùng.")

print(f"\n==========================================")
print(f"[Thành công] Toàn bộ tiến trình hoàn tất!")
print(f"-> Tổng số bài viết độc nhất thu được từ 20 từ khóa: {total_saved} bài.")
print(f"-> File kết quả: {OUTPUT_FILENAME}")
print(f"==========================================")