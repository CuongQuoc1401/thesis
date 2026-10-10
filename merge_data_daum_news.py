import pandas as pd
import os
import sys

# ==========================================
# CẤU HÌNH TÊN FILE (Đồng bộ với các bước trước)
# ==========================================
MASTER_EXCEL_FILE = "combined_final_excel.xlsx" # File Excel tổng đang chứa cả Blog và Naver News
DAUM_CSV_FILE = "daum_news_with_content.csv"     # File Daum News vừa cào xong nội dung chi tiết
ERROR_CSV_FILE = "merge_error_log.csv"          # File log ghi nhận các dòng bị lỗi/trống nội dung

def merge_daum_process():
    # Kiểm tra sự tồn tại của các file đầu vào cốt lõi
    if not os.path.exists(DAUM_CSV_FILE):
        print(f"[Lỗi] Không tìm thấy file dữ liệu Daum chi tiết: {DAUM_CSV_FILE}")
        return
        
    if not os.path.exists(MASTER_EXCEL_FILE):
        print(f"[Lỗi] Không tìm thấy file Excel tổng hợp: {MASTER_EXCEL_FILE}")
        print("      Vui lòng đảm bảo bạn đã chạy bước gộp Naver News trước để tạo ra file này.")
        return

    # 1. ĐỌC FILE EXCEL TỔNG HỢP (MASTER)
    print("[1/4] Đang đọc cấu trúc và dữ liệu từ file Excel tổng hiện tại...")
    df_master = pd.read_excel(MASTER_EXCEL_FILE, dtype=str)
    excel_columns = df_master.columns.tolist()
    
    # Nạp toàn bộ các URL bài viết đã tồn tại trong file tổng vào cấu trúc set để chống trùng
    existing_urls = set(df_master['URL Bài Viết'].dropna().tolist())
    print(f"   => File Excel tổng hiện tại đang có {len(df_master)} dòng dữ liệu (Blog + Naver News).")

    # Khởi tạo file log lỗi nếu chưa tồn tại
    if not os.path.exists(ERROR_CSV_FILE):
        pd.DataFrame(columns=["Title", "Origin Link", "Reason"]).to_csv(ERROR_CSV_FILE, index=False, encoding='utf-8-sig')

    # 2. ĐỌC FILE DAUM NEWS CSV
    print("[2/4] Đang đọc file Daum News CSV chứa nội dung chi tiết...")
    df_daum_csv = pd.read_csv(DAUM_CSV_FILE, dtype=str)
    
    # 3. TIẾN HÀNH DUYỆT TỪNG DÒNG ĐỂ LỌC VÀ GỘP CUỐN CHIẾU
    print("[3/4] Bắt đầu kiểm tra điều kiện nội dung và lọc bài trùng...")
    print("      (Nhấn Ctrl + C nếu muốn dừng an toàn giữa chừng)")
    
    new_rows_to_append = []
    error_rows = []
    
    try:
        for idx, row in df_daum_csv.iterrows():
            title = str(row.get('Title', '')).strip()
            url = row.get('Origin Link', '')
            pub_date = row.get('Publish Date', '')
            content = row.get('Content', '')
            
            # KIỂM TRA CHECKPOINT: Nếu link bài viết này đã tồn tại trong file Excel tổng, bỏ qua lập tức
            if url in existing_urls:
                continue
                
            # KIỂM TRA Ô TRỐNG HOẶC CHỨA CHUỖI BÁO LỖI CÀO MẠNG
            if pd.isna(content) or str(content).strip() == "" or str(content).strip().startswith("[Lỗi]") or str(content).strip().startswith("[Trống]"):
                reason = "Ô nội dung chi tiết của Daum bị trống hoặc lỗi cào"
                error_rows.append({"Title": title, "Origin Link": url, "Reason": reason})
                continue
                
            # ÁNH XẠ DỮ LIỆU HỢP LỆ VÀO KHUNG CỘT EXCEL GỐC
            new_row = {col: None for col in excel_columns} # Tạo hàng trống đồng bộ định dạng cột
            new_row['Tiêu Đề'] = title
            new_row['URL Bài Viết'] = url
            new_row['Tên Blog'] = "Daum news"              # Mặc định nguồn là Daum news
            new_row['Ngày Đăng'] = pub_date
            new_row['Nội Dung Chi Tiết'] = content
            
            new_rows_to_append.append(new_row)
            existing_urls.add(url) # Đánh dấu đã xử lý để tránh trùng lặp trong chính lượt chạy này
            
    except KeyboardInterrupt:
        print("\n" + "="*50)
        print("[Tín hiệu] Bạn đã bấm dừng tiến trình bằng phím Ctrl + C!")
        print("[An toàn] Hệ thống tiến hành đóng gói và lưu giữ phần dữ liệu đã chạy dở...")
        print("="*50)

    # 4. GHI DỮ LIỆU XUỐNG CƠ SỞ DỮ LIỆU EXCEL
    print("[4/4] Đang đóng gói dữ liệu và xuất file cập nhật...")
    
    # Ghi nhận các bài viết lỗi/trống nội dung ra file log CSV nối đuôi
    if error_rows:
        df_new_errors = pd.DataFrame(error_rows)
        df_new_errors.to_csv(ERROR_CSV_FILE, mode='a', index=False, header=False, encoding='utf-8-sig')
        print(f"   => Đã phát hiện và ghi nhận {len(error_rows)} bài Daum lỗi nội dung vào file '{ERROR_CSV_FILE}'.")
        
    # Tiến hành xếp chồng dữ liệu hợp lệ vào đuôi file Excel cũ
    if new_rows_to_append:
        df_new_valid = pd.DataFrame(new_rows_to_append)
        df_final = pd.concat([df_master, df_new_valid], ignore_index=True)
        df_final.to_excel(MASTER_EXCEL_FILE, index=False)
        print(f"   => Đã gộp thêm {len(new_rows_to_append)} bài Daum News hợp lệ vào '{MASTER_EXCEL_FILE}'.")
    else:
        print("   => Không có dữ liệu Daum mới nào đủ điều kiện hợp lệ để chèn thêm.")

    print(f"\n==========================================")
    print(f"[Hoàn tất] File Excel tổng hợp '{MASTER_EXCEL_FILE}' đã được cập nhật an toàn!")
    print(f"==========================================")

if __name__ == "__main__":
    merge_daum_process()