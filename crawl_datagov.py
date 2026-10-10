import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import os
import sys

# ==========================================
# 1. CẤU HÌNH VÀ KHỞI TẠO HỆ THỐNG
# ==========================================
OUTPUT_FILENAME = "datagov_search_results.csv"

# Khoảng thời gian thu thập cho luận văn (2021/06/01 ~ 2026/06/01)
START_DATE = datetime.strptime("2021-06-01", "%Y-%m-%d")
END_DATE = datetime.strptime("2026-06-01", "%Y-%m-%d")

# Danh sách 4 loại hình dữ liệu cần quét theo yêu cầu của bạn
D_TYPES = ["FILE", "API", "STD", "LINKED"]

# Tập hợp lưu trữ link chi tiết để chống trùng bản ghi tuyệt đối
saved_links = set()

# Cơ chế Checkpoint: Nạp lại dữ liệu cũ để chạy tiếp nếu chương trình bị ngắt quãng
if os.path.exists(OUTPUT_FILENAME):
    print(f"[Checkpoint] Tìm thấy file '{OUTPUT_FILENAME}' cũ. Đang nạp danh sách để bỏ qua trùng lặp...")
    try:
        df_old = pd.read_csv(OUTPUT_FILENAME, dtype=str)
        if 'Detail_Link' in df_old.columns:
            saved_links.update(df_old['Detail_Link'].dropna().tolist())
        print(f"   => Đã nạp thành công {len(saved_links)} liên kết cũ để bảo vệ chống trùng lặp.")
    except Exception as e:
        print(f"   => Lỗi nạp checkpoint cũ (tiến hành cào mới): {e}")
else:
    # Khởi tạo file mới với cấu trúc cột chuẩn (Thêm cột Data_Type)
    pd.DataFrame(columns=["Keyword", "Data_Type", "Title", "Description", "Provider", "Modify_Date", "Detail_Link", "Keywords_Tag"]).to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig')

# Danh sách 41 từ khóa luận văn của bạn
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.data.go.kr/"
}

def parse_date(date_str):
    """Đọc chuỗi ngày tháng dạng YYYY-MM-DD an toàn"""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except Exception:
        return None

# ==========================================
# 2. VÒNG LẶP TIẾN TRÌNH CÀO TOÀN DIỆN
# ==========================================
print("\n[Hệ thống] Bắt đầu khởi chạy bộ cào đa nguồn dữ liệu trên data.go.kr...")
print("           Nhấn Ctrl + C để dừng an toàn bất kỳ lúc nào.\n")

total_new_saved = 0

try:
    for kw_idx, keyword in enumerate(KEYWORDS, 1):
        print(f"\n======================================================================")
        print(f"[{kw_idx}/{len(KEYWORDS)}] TỪ KHÓA CHÍNH: {keyword}")
        print(f"======================================================================")
        
        # Lặp qua từng loại hình dữ liệu cho mỗi từ khóa
        for dtype in D_TYPES:
            print(f" 🟩 Đang quét định dạng dType = {dtype}...")
            
            current_page = 1
            has_next_page = True
            dtype_saved_count = 0
            
            while has_next_page:
                url = "https://www.data.go.kr/tcs/dss/selectDataSetList.do"
                params = {
                    "dType": dtype,        # Chạy động qua FILE, API, STD, LINKED
                    "keyword": keyword,
                    "currentPage": current_page,
                    "perPage": "40",
                    "sort": "_score",
                    "operator": "OR",
                    "pblonsipScopeCode": "PBDE07"
                }
                
                print(f"   > [Page {current_page}] Gửi yêu cầu lên hệ thống...", end="\r")
                
                try:
                    response = requests.get(url, headers=HEADERS, params=params, timeout=15)
                    if response.status_code != 200:
                        print(f"\n   [Cảnh báo] Hệ thống phản hồi lỗi ({response.status_code}). Chuyển loại hình khác.")
                        break
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    list_items = soup.select("div.result-list > ul > li")
                    
                    # Nếu trang này không chứa thẻ li nào, tức là đã hết trang dữ liệu của loại hình này
                    if not list_items:
                        break
                    
                    valid_items_in_page = 0
                    page_data = []
                    
                    for item in list_items:
                        try:
                            # 1. Trích xuất link chi tiết
                            a_tag = item.select_one("dl > dt > a")
                            if not a_tag or 'href' not in a_tag.attrs:
                                continue
                            detail_link = "https://www.data.go.kr" + a_tag['href']
                            
                            # Kiểm tra trùng lặp (Chặn trùng giữa các trang, các từ khóa hoặc lượt cào trước)
                            if detail_link in saved_links:
                                continue
                            
                            # 2. Tiêu đề
                            title_tag = item.select_one("dl > dt > a .title")
                            title = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)
                            
                            # 3. Tóm tắt mô tả dữ liệu
                            desc_tag = item.select_one("dd.publicDataDesc")
                            description = desc_tag.get_text(strip=True) if desc_tag else ""
                            
                            # 4. Phân tích các trường thông tin đi kèm
                            info_ps = item.select("div.info-data > p")
                            provider = ""
                            modify_date_str = ""
                            keywords_tag = ""
                            
                            for p in info_ps:
                                p_text = p.get_text(strip=True)
                                data_span = p.select_one(".data")
                                
                                if "제공기관" in p_text and data_span:
                                    provider = data_span.get_text(strip=True)
                                elif "수정일" in p_text:
                                    modify_date_str = p_text.replace("수정일", "").strip()
                                elif "키워드" in p_text:
                                    keywords_tag = p_text.replace("키워드", "").strip()
                            
                            # 5. Bộ lọc thời gian chuẩn học thuật (2021-06-01 đến 2026-06-01)
                            mod_date = parse_date(modify_date_str)
                            if mod_date and (START_DATE <= mod_date <= END_DATE):
                                # Đưa vào mảng dữ liệu kèm loại dtype
                                page_data.append([
                                    keyword, dtype, title, description, provider, modify_date_str, detail_link, keywords_tag
                                ])
                                saved_links.add(detail_link)
                                valid_items_in_page += 1
                                dtype_saved_count += 1
                                total_new_saved += 1
                                
                        except Exception:
                            continue
                    
                    # Lưu cuốn chiếu ngay sau khi kết thúc trang dữ liệu sạch
                    if page_data:
                        df_page = pd.DataFrame(page_data)
                        df_page.to_csv(OUTPUT_FILENAME, mode='a', index=False, header=False, encoding='utf-8-sig')
                    
                    print(f"   > [Xong] Page {current_page}: Thu về {valid_items_in_page} tài nguyên hợp lệ.")
                    
                    # Nếu số lượng phần tử trả về nhỏ hơn kích thước trang mặc định (40), nghĩa là đây là trang cuối
                    if len(list_items) < 40:
                        has_next_page = False
                    else:
                        current_page += 1
                        time.sleep(random.uniform(0.5, 0.8)) # Giãn cách an toàn cho hệ thống server
                        
                except requests.exceptions.RequestException as e:
                    print(f"\n   [Lỗi mạng] {e}. Tự động bỏ qua trang này.")
                    break
            
            print(f"   => Hoàn thành loại [{dtype}] của từ khóa [{keyword}]. Thu mới: {dtype_saved_count} dòng.")

except KeyboardInterrupt:
    print("\n" + "="*60)
    print("[Hệ thống] Nhận được lệnh dừng đột ngột (Ctrl + C) từ bạn!")
    print("[An toàn] Toàn bộ dữ liệu của các từ khóa và các dType đã chạy xong trước đó đã được lưu hoàn chỉnh!")
    print(f"[An toàn] File lưu trữ hiện tại: {OUTPUT_FILENAME}")
    print("="*60)
    sys.exit(0)

print(f"\n======================================================================")
print(f"[Thành công] Toàn bộ chiến dịch quét đa loại hình dữ liệu hoàn tất!")
print(f"-> Tổng số lượng tài nguyên mới cập nhật: {total_new_saved} dòng.")
print(f"-> Đường dẫn file dữ liệu tổng: {os.path.abspath(OUTPUT_FILENAME)}")
print(f"======================================================================")