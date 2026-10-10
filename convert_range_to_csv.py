import pandas as pd
import os
import re
from datetime import datetime

# ==========================================
# CẤU HÌNH TÊN FILE
# ==========================================
INPUT_EXCEL_FILE = "combined_final_excel.xlsx"
OUTPUT_CSV_FILE = "combined_final_data.csv"
LOG_CSV_FILE = "convert_range_to_csv_log.csv"

def clean_illegal_chars(val):
    """Làm sạch ký tự điều khiển ẩn (Null byte, ASCII control chars) gây hỏng dữ liệu XML/Excel"""
    if not isinstance(val, str):
        return val, False
    
    # Lọc các ký tự ASCII control (0-8, 11-12, 14-31, 127-159)
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', val)
    has_cleaned = len(cleaned) != len(val)
    return cleaned, has_cleaned

def convert_excel_range_to_csv_with_log():
    if not os.path.exists(INPUT_EXCEL_FILE):
        print(f"[Lỗi] Không tìm thấy file Excel đầu vào: {INPUT_EXCEL_FILE}")
        return

    # Khởi tạo danh sách ghi log
    log_entries = []
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"[1/4] Đang đọc dữ liệu từ '{INPUT_EXCEL_FILE}'...")
    df = pd.read_excel(INPUT_EXCEL_FILE, dtype=str)
    
    total_rows_in_file = len(df)
    target_rows = 86997 - 1  # 86,996 dòng dữ liệu (Dòng 2 -> Dòng 86997 trong Excel)
    
    print(f"   => Tìm thấy tổng cộng {total_rows_in_file} dòng dữ liệu gốc.")
    print(f"[2/4] Đang trích xuất {target_rows} dòng dữ liệu đầu tiên (Dòng 2 -> 86997)...")
    
    df_sliced = df.iloc[:target_rows].copy()
    columns_list = df_sliced.columns.tolist()

    # Ghi log tổng quan ban đầu
    log_entries.append({
        "Timestamp": start_time,
        "Log_Type": "INFO",
        "Excel_Row_Index": "HEADER",
        "Status_Or_Reason": f"Khởi tạo chuyển đổi. Tổng dòng Excel: {total_rows_in_file} | Cắt dòng: 2 -> 86997 | Số cột: {len(columns_list)}",
        "Details": f"Danh sách cột: {', '.join(columns_list)}"
    })

    print(f"[3/4] Đang làm sạch dữ liệu & Kiểm tra tính trọn vẹn...")
    cleaned_char_count = 0
    empty_row_count = 0

    for idx, row in df_sliced.iterrows():
        excel_row_num = idx + 2  # Convert index 0-based sang Dòng Excel (index 0 = Dòng 2)
        row_is_empty = True
        
        for col in columns_list:
            val = row[col]
            if pd.notna(val) and str(val).strip() != "":
                row_is_empty = False
                
            cleaned_val, was_cleaned = clean_illegal_chars(val)
            df_sliced.at[idx, col] = cleaned_val
            
            if was_cleaned:
                cleaned_char_count += 1
                log_entries.append({
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Log_Type": "WARNING_CLEANED_CHAR",
                    "Excel_Row_Index": f"Dòng {excel_row_num}",
                    "Status_Or_Reason": f"Phát hiện & Loại bỏ ký tự lạ tại cột '{col}'",
                    "Details": f"Đã khử ký tự điều khiển ẩn để tránh hỏng CSV"
                })

        if row_is_empty:
            empty_row_count += 1
            log_entries.append({
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Log_Type": "WARNING_EMPTY_ROW",
                "Excel_Row_Index": f"Dòng {excel_row_num}",
                "Status_Or_Reason": "Dòng dữ liệu hoàn toàn trống",
                "Details": "Toàn bộ các ô trong dòng này đều rỗng hoặc Null"
            })

    print(f"[4/4] Đang xuất file CSV dữ liệu & File Log...")
    # 1. Lưu dữ liệu chính
    df_sliced.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8-sig')

    # 2. Lưu thông tin tổng kết vào Log
    log_entries.append({
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Log_Type": "SUCCESS",
        "Excel_Row_Index": f"Dòng 2 -> {86997}",
        "Status_Or_Reason": "Chuyển đổi hoàn tất thành công 100%",
        "Details": f"Đã xuất {len(df_sliced)} dòng dữ liệu sang '{OUTPUT_CSV_FILE}'. Tổng dòng trống: {empty_row_count}, Ô đã xử lý ký tự lạ: {cleaned_char_count}"
    })

    # Ghi file Log CSV
    df_log = pd.DataFrame(log_entries)
    df_log.to_csv(LOG_CSV_FILE, index=False, encoding='utf-8-sig')

    print("\n" + "="*60)
    print(f"✅ [HOÀN THÀNH CHUYỂN ĐỔI]")
    print(f" 📄 File dữ liệu CSV: '{OUTPUT_CSV_FILE}' ({len(df_sliced)} dòng)")
    print(f" 📝 File Log kiểm định: '{LOG_CSV_FILE}' ({len(df_log)} bản ghi log)")
    print("="*60)

if __name__ == "__main__":
    convert_excel_range_to_csv_with_log()