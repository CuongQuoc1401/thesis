import pandas as pd
import os
import sys

# Định nghĩa tên các file
BLOG_EXCEL_FILE = "naver_미래_유망_직업_2021_2026_after_merge.xlsx"
NEWS_CSV_FILE = "naver_news_with_content.csv"
OUTPUT_EXCEL_FILE = "combined_final_excel.xlsx"
ERROR_CSV_FILE = "merge_error_log.csv"

def merge_advanced_process():
    if not os.path.exists(BLOG_EXCEL_FILE) or not os.path.exists(NEWS_CSV_FILE):
        print("[Lỗi] Vui lòng kiểm tra lại đường dẫn 2 file đầu vào.")
        return

    # 1. ĐỌC FILE EXCEL GỐC (BLOg)
    print("[1/4] Đang đọc cấu trúc file Excel gốc...")
    df_excel = pd.read_excel(BLOG_EXCEL_FILE, dtype=str)
    excel_columns = df_excel.columns.tolist()
    
    # Tập hợp các URL đã tồn tại trong file gốc để tránh chèn trùng
    existing_urls = set(df_excel['URL Bài Viết'].dropna().tolist())
    print(f"   => File Excel gốc đang có {len(df_excel)} dòng dữ liệu.")

    # 2. KIỂM TRA CHECKPOINT (NẾU CHẠY LẠI)
    if os.path.exists(OUTPUT_EXCEL_FILE):
        print(f"[Checkpoint] Tìm thấy file kết quả cũ '{OUTPUT_EXCEL_FILE}'. Đang nạp các bài đã gộp để bỏ qua...")
        try:
            df_old_output = pd.read_excel(OUTPUT_EXCEL_FILE, dtype=str)
            if 'URL Bài Viết' in df_old_output.columns:
                # Cập nhật thêm các URL đã được xử lý ở lượt chạy trước
                existing_urls.update(df_old_output['URL Bài Viết'].dropna().tolist())
                # Lấy phần dữ liệu gốc làm nền móng để ghi tiếp
                df_base = df_old_output
                print(f"   => Tổng số bài đã được gộp/xử lý trước đó: {len(existing_urls)}")
        except Exception as e:
            print(f"   => Không thể đọc checkpoint cũ ({e}), tiến hành tạo mới từ file gốc.")
            df_base = df_excel.copy()
    else:
        df_base = df_excel.copy()

    # Khởi tạo file log lỗi nếu chưa tồn tại
    if not os.path.exists(ERROR_CSV_FILE):
        pd.DataFrame(columns=["Title", "Origin Link", "Reason"]).to_csv(ERROR_CSV_FILE, index=False, encoding='utf-8-sig')

    # 3. ĐỌC FILE NEWS CSV CẦN GỘP
    print("[2/4] Đang đọc file News CSV đầu vào...")
    df_news_csv = pd.read_csv(NEWS_CSV_FILE, dtype=str)
    
    # 4. TIẾN HÀNH DUYỆT TỪNG DÒNG VÀ LỌC LỖI CUỐN CHIẾU
    print("[3/4] Bắt đầu tiến trình kiểm tra nội dung và gộp dữ liệu...")
    print("      (Nhấn Ctrl + C nếu muốn dừng an toàn giữa chừng)")
    
    new_rows_to_append = []
    error_rows = []
    
    try:
        for idx, row in df_news_csv.iterrows():
            title = row.get('Title', '')
            url = row.get('Origin Link', '')
            pub_date = row.get('Publish Date', '')
            content = row.get('Content', '')
            
            # KIỂM TRA BỎ QUA: Nếu bài này đã có trong dữ liệu (hoặc đã gộp rồi), bỏ qua lập tức
            if url in existing_urls:
                continue
                
            # KIỂM TRA Ô TRỐNG HOẶC CHỨA THÔNG BÁO LỖI CÀO
            # (Loại bỏ các trường hợp chuỗi trống, NaN, hoặc nội dung bắt đầu bằng chữ '[Lỗi]')
            if pd.isna(content) or str(content).strip() == "" or str(content).strip().startswith("[Lỗi]") or str(content).strip().startswith("[Trống]"):
                reason = "Ô nội dung chi tiết trống hoặc lỗi cào"
                error_rows.append({"Title": title, "Origin Link": url, "Reason": reason})
                continue
                
            # ÁNH XẠ DỮ LIỆU HỢP LỆ VÀO KHUNG EXCEL GỐC
            new_row = {col: None for col in excel_columns} # Tạo dòng trống theo đúng cấu trúc cột Excel
            new_row['Tiêu Đề'] = title
            new_row['URL Bài Viết'] = url
            new_row['Tên Blog'] = "Naver news"
            new_row['Ngày Đăng'] = pub_date
            new_row['Nội Dung Chi Tiết'] = content
            
            new_rows_to_append.append(new_row)
            
    except KeyboardInterrupt:
        print("\n" + "="*50)
        print("[Tín hiệu] Bạn đã bấm dừng gộp file bằng phím Ctrl + C!")
        print("[An toàn] Hệ thống tiến hành đóng gói dữ liệu đã chạy dở...")
        print("="*50)
        # Tiếp tục chạy xuống dưới để lưu phần dữ liệu đã quét được trước khi bấm dừng

    # 5. LƯU DỮ LIỆU
    print("[4/4] Đang đóng gói và cập nhật dữ liệu ra file...")
    
    # Ghi log các bài bị lỗi nội dung trống (nếu có)
    if error_rows:
        df_new_errors = pd.DataFrame(error_rows)
        df_new_errors.to_csv(ERROR_CSV_FILE, mode='a', index=False, header=False, encoding='utf-8-sig')
        print(f"   => Đã phát hiện và xuất {len(error_rows)} dòng bị trống/lỗi nội dung sang file '{ERROR_CSV_FILE}'.")
        
    # Chèn dữ liệu hợp lệ vào sau file base
    if new_rows_to_append:
        df_new_valid = pd.DataFrame(new_rows_to_append)
        df_final = pd.concat([df_base, df_new_valid], ignore_index=True)
        df_final.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print(f"   => Đã gộp thành công thêm {len(new_rows_to_append)} bài báo hợp lệ vào '{OUTPUT_EXCEL_FILE}'.")
    else:
        # Nếu không có dòng mới nào, lưu lại file base để đảm bảo tính liên tục
        df_base.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print("   => Không có bài viết mới nào hợp lệ được thêm vào ở lượt chạy này.")

    print(f"\n==========================================")
    print(f"[Hoàn tất] Tiến trình xử lý dữ liệu kết thúc!")
    print(f"==========================================")

if __name__ == "__main__":
    merge_advanced_process()