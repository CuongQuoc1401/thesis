import pandas as pd
import os
import re

# ==========================================
# CẤU HÌNH TÊN FILE (Sử dụng chuẩn CSV)
# ==========================================
MASTER_CSV_FILE = "combined_final_data.csv"   # File CSV tổng chứa toàn bộ dữ liệu
DATA_GOV_CSV_FILE = "datagov_with_content.csv" # File dữ liệu chính phủ đã cào nội dung chi tiết
ERROR_CSV_FILE = "merge_error_log.csv"        # File log lỗi chung

def clean_illegal_chars(val):
    """Làm sạch ký tự điều khiển ẩn (Null byte, control characters) gây hỏng cấu trúc văn bản"""
    if not isinstance(val, str):
        return val
    # Loại bỏ các ký tự ASCII control (0-8, 11-12, 14-31, 127-159)
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', val)
    return cleaned

def merge_datagov_to_csv_process():
    # Kiểm tra sự tồn tại của file dữ liệu đầu vào
    if not os.path.exists(DATA_GOV_CSV_FILE):
        print(f"[Lỗi] Không tìm thấy file dữ liệu Data.go.kr chi tiết: {DATA_GOV_CSV_FILE}")
        return
        
    if not os.path.exists(MASTER_CSV_FILE):
        print(f"[Cảnh báo] Chưa tìm thấy file Master CSV '{MASTER_CSV_FILE}'. Hệ thống sẽ tự động khởi tạo mới.")
        df_master = pd.DataFrame()
    else:
        # 1. ĐỌC FILE CSV TỔNG HỢP (MASTER)
        print("[1/4] Đang đọc cấu trúc và dữ liệu từ file Master CSV hiện tại...")
        df_master = pd.read_csv(MASTER_CSV_FILE, dtype=str, encoding='utf-8-sig')

    excel_columns = df_master.columns.tolist() if not df_master.empty else []
    
    # Làm sạch khoảng trắng của toàn bộ URL cũ trong Master CSV để so sánh lọc trùng
    if 'URL Bài Viết' in df_master.columns:
        existing_urls = set(df_master['URL Bài Viết'].dropna().astype(str).str.strip().tolist())
    else:
        existing_urls = set()
        
    print(f"   => File Master CSV hiện tại đang có {len(df_master)} dòng dữ liệu gốc.")

    # Khởi tạo file log lỗi nếu chưa tồn tại
    if not os.path.exists(ERROR_CSV_FILE):
        pd.DataFrame(columns=["Title", "Origin Link", "Reason"]).to_csv(ERROR_CSV_FILE, index=False, encoding='utf-8-sig')

    # 2. ĐỌC FILE DATA.GO.KR CSV
    print("[2/4] Đang đọc file Data.go.kr CSV chứa nội dung chi tiết...")
    df_gov_csv = pd.read_csv(DATA_GOV_CSV_FILE, dtype=str, encoding='utf-8-sig')
    print(f"   => Tìm thấy tổng cộng {len(df_gov_csv)} dòng trong file CSV cào chi tiết.")
    
    # Định nghĩa cấu trúc cột chuẩn nếu file Master trước đó chưa có dữ liệu
    if not excel_columns:
        excel_columns = ['Blog ID', 'Post ID', 'GDID', 'URL Bài Viết', 'Tiêu Đề', 'Tóm Tắt', 'Biệt Danh', 'Tên Blog', 'Ngày Đăng', 'Nội Dung']

    # 3. TIẾN HÀNH DUYỆT TỪNG DÒNG ĐỂ LỌC VÀ GỘP CUỐN CHIẾU
    print("[3/4] Bắt đầu kiểm tra điều kiện nội dung và lọc trùng bài viết...")
    print("      (Nhấn Ctrl + C nếu muốn dừng an toàn giữa chừng)")
    
    new_rows_to_append = []
    error_rows = []
    
    skip_by_duplicate = 0
    skip_by_empty = 0
    
    try:
        for idx, row in df_gov_csv.iterrows():
            dtype = row.get('Data_Type', 'FILE')
            title = str(row.get('Title', '')).strip() if pd.notna(row.get('Title')) else "[Không tiêu đề]"
            url = str(row.get('Detail_Link', '')).strip() # Cắt khoảng trắng URL
            pub_date = row.get('Modify_Date', '')
            content = row.get('Detailed_Content', '')
            
            # KIỂM TRA TRÙNG: Nếu thực sự đã trùng liên kết trong Master CSV
            if url in existing_urls:
                skip_by_duplicate += 1
                continue
                
            # KIỂM TRA Ô NỘI DUNG RỖNG HOẶC LỖI CÀO
            if pd.isna(content) or str(content).strip() == "" or str(content).strip().startswith("[Lỗi]") or str(content).strip().startswith("[Trống]"):
                reason = f"Ô nội dung chi tiết của Data.go.kr ({dtype}) bị trống hoặc lỗi cào"
                error_rows.append({"Title": title, "Origin Link": url, "Reason": reason})
                skip_by_empty += 1
                continue
                
            # ÁNH XẠ DỮ LIỆU HỢP LỆ VÀO KHUNG CỘT CSV
            new_row = {col: "" for col in excel_columns}
            
            # Khử sạch ký tự lạ gây hỏng cấu trúc
            clean_content_text = clean_illegal_chars(str(content))
            
            new_row['Tiêu Đề'] = title
            new_row['URL Bài Viết'] = url
            new_row['Tên Blog'] = f"Data.go.kr ({dtype})"   
            new_row['Ngày Đăng'] = pub_date
            
            # Tự động ánh xạ vào cột Nội Dung (dù tên cột là 'Nội Dung' hay 'Nội Dung Chi Tiết')
            if 'Nội Dung Chi Tiết' in excel_columns:
                new_row['Nội Dung Chi Tiết'] = clean_content_text
            elif 'Nội Dung' in excel_columns:
                new_row['Nội Dung'] = clean_content_text

            new_rows_to_append.append(new_row)
            existing_urls.add(url)
            
    except KeyboardInterrupt:
        print("\n" + "="*50)
        print("[Tín hiệu] Bạn đã bấm dừng tiến trình bằng phím Ctrl + C!")
        print("[An toàn] Hệ thống tiến hành đóng gói phần dữ liệu đã duyệt...")
        print("="*50)

    # 4. GHI DỮ LIỆU XUỐNG FILE CSV TỔNG
    print("[4/4] Đang đóng gói dữ liệu và xuất file cập nhật...")
    print(f"   => Thống kê lượt duyệt: Bỏ qua do trùng lặp: {skip_by_duplicate} bài | Bỏ qua do nội dung trống/lỗi: {skip_by_empty} bài.")
    
    # Ghi log lỗi
    if error_rows:
        df_new_errors = pd.DataFrame(error_rows)
        df_new_errors.to_csv(ERROR_CSV_FILE, mode='a', index=False, header=False, encoding='utf-8-sig')
        print(f"   => Đã phát hiện và ghi thêm {len(error_rows)} bản ghi lỗi vào file '{ERROR_CSV_FILE}'.")
        
    # Nối đuôi dữ liệu và ghi đè lưu file
    if new_rows_to_append:
        df_new_valid = pd.DataFrame(new_rows_to_append)
        df_final = pd.concat([df_master, df_new_valid], ignore_index=True)
        
        print(f"   => Đang tiến hành ghi {len(new_rows_to_append)} dòng mới vào file Master CSV...")
        df_final.to_csv(MASTER_CSV_FILE, index=False, encoding='utf-8-sig')
        print(f"   => [Thành công] Đã gộp thêm {len(new_rows_to_append)} bài viết từ Data.go.kr vào '{MASTER_CSV_FILE}'.")
    else:
        print("   => Không có dữ liệu Data.go.kr mới nào đủ điều kiện để chèn thêm (Toàn bộ đã bị trùng hoặc trống).")

if __name__ == "__main__":
    merge_datagov_to_csv_process()