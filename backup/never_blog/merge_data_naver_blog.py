import os
import re
import signal
import sys
import time
import logging
import pandas as pd

# ==============================================================================
# CẤU HÌNH LOGGING & HỆ THỐNG
# ==============================================================================
RAW_KEYWORD = "미래 유망 직업"
INPUT_EXCEL = f"naver_{RAW_KEYWORD.replace(' ', '_')}_2021_2026.xlsx"
DATA_OUTPUT_CSV = f"data_clean_{RAW_KEYWORD.replace(' ', '_')}.csv"

STAGING_EXCEL = f"staging_{INPUT_EXCEL}"
MERGE_LOG_FILE = f"merge_report_{RAW_KEYWORD.replace(' ', '_')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(MERGE_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

IS_INTERRUPTED = False

def handle_interrupt(sig, frame):
    global IS_INTERRUPTED
    IS_INTERRUPTED = True
    logging.warning("⚠️ [HỆ THỐNG] Phát hiện yêu cầu tắt chương trình (Ctrl+C). Đang hủy bỏ giao tác an toàn...")

signal.signal(signal.SIGINT, handle_interrupt)

# ==============================================================================
# BỘ LỌC ĐỘC QUYỀN ĐỂ SỬA LỖI ILLEGAL CHARACTER
# ==============================================================================
def clean_illegal_chars(val):
    """
    Xóa bỏ toàn bộ ký tự điều khiển ẩn không hợp lệ đối với Excel (Ký tự thuộc dải ASCII từ 0-31 loại trừ tab, xuống dòng).
    """
    if not isinstance(val, str):
        return val
    
    # Loại bỏ các ký tự rác điều khiển hệ thống (Control Characters) ẩn trong chuỗi văn bản
    # Giữ lại các ký tự in được thông thường, tiếng Hàn, tiếng Việt, dấu xuống dòng \n, \r và thụt lề \t
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', val)
    return cleaned

# ==============================================================================
# PIPELINE XỬ LÝ DỮ LIỆU ĐỘC LẬP (ETL ENGINE)
# ==============================================================================
def main():
    start_time = time.time()
    logging.info("🏁 Bắt đầu tiến trình gộp dữ liệu chi tiết vào file Excel gốc...")

    if not os.path.exists(INPUT_EXCEL):
        logging.error(f"❌ Không tìm thấy file Excel gốc: '{INPUT_EXCEL}'. Tiến trình bị hủy.")
        return
    if not os.path.exists(DATA_OUTPUT_CSV):
        logging.error(f"❌ Không tìm thấy file dữ liệu sạch: '{DATA_OUTPUT_CSV}'. Bạn đã cào thành công bài nào chưa?")
        return

    try:
        # --- BƯỚC 1: ĐỌC VÀ CHUẨN HÓA DỮ LIỆU ---
        logging.info("📖 Đang nạp file Excel gốc và dữ liệu sạch CSV vào RAM...")
        df_excel = pd.read_excel(INPUT_EXCEL, engine="openpyxl")
        df_csv = pd.read_csv(DATA_OUTPUT_CSV, dtype={"Post ID (LogNo)": str})

        if IS_INTERRUPTED: raise KeyboardInterrupt

        # --- BƯỚC 2: BIẾN ĐỔI VÀ KHỬ TRÙNG ---
        logging.info("🧹 Đang tiền xử lý, đồng bộ khóa định danh và xử lý trùng lặp...")
        df_excel["Post ID (LogNo)"] = df_excel["Post ID (LogNo)"].astype(str).str.strip()
        df_csv["Post ID (LogNo)"] = df_csv["Post ID (LogNo)"].astype(str).str.strip()

        initial_csv_count = len(df_csv)
        df_csv = df_csv.drop_duplicates(subset=["Post ID (LogNo)"], keep="last")
        dedup_count = initial_csv_count - len(df_csv)
        if dedup_count > 0:
            logging.info(f"   🔹 Đã loại bỏ {dedup_count} dòng trùng lặp trong file CSV dữ liệu cào.")

        if "Nội Dung Chi Tiết" in df_excel.columns:
            df_excel = df_excel.drop(columns=["Nội Dung Chi Tiết"])

        if IS_INTERRUPTED: raise KeyboardInterrupt

        # --- BƯỚC 3: GỘP DỮ LIỆU ---
        logging.info("🔀 Đang thực hiện ánh xạ (Mapping) dữ liệu dựa trên Post ID...")
        df_final = pd.merge(df_excel, df_csv, on="Post ID (LogNo)", how="left")

        # --- BƯỚC VÁ LỖI TỐI ƯU CỦA SENIOR ---
        logging.info("🧼 Đang kích hoạt bộ lọc ký tự độc hại ẩn (Sanitize Illegal Characters)...")
        # Áp dụng hàm làm sạch dữ liệu cho cột văn bản chi tiết trước khi chuyển giao cho openpyxl
        df_final["Nội Dung Chi Tiết"] = df_final["Nội Dung Chi Tiết"].apply(clean_illegal_chars)

        total_rows = len(df_final)
        matched_rows = df_final["Nội Dung Chi Tiết"].notna().sum()
        mismatched_rows = total_rows - matched_rows

        if IS_INTERRUPTED: raise KeyboardInterrupt

        # --- BƯỚC 4: GHI DỮ LIỆU AN TOÀN ---
        logging.info(f"💾 Đang xuất bảng dữ liệu hoàn chỉnh ra file trung gian: '{STAGING_EXCEL}'...")
        df_final.to_excel(STAGING_EXCEL, index=False, engine="openpyxl")
        
        if IS_INTERRUPTED:
            if os.path.exists(STAGING_EXCEL): os.remove(STAGING_EXCEL)
            raise KeyboardInterrupt

        # --- BƯỚC 5: CHỐT GIAO TÁC NGUYÊN TỬ ---
        logging.info("🔒 Ghi file thành công. Đang cập nhật và khóa tệp dữ liệu gốc...")
        
        BACKUP_EXCEL = f"backup_{INPUT_EXCEL}"
        if os.path.exists(INPUT_EXCEL):
            if os.path.exists(BACKUP_EXCEL): os.remove(BACKUP_EXCEL)
            os.rename(INPUT_EXCEL, BACKUP_EXCEL)
            
        os.rename(STAGING_EXCEL, INPUT_EXCEL)
        if os.path.exists(BACKUP_EXCEL): os.remove(BACKUP_EXCEL)

        duration = time.time() - start_time
        logging.info("=" * 80)
        logging.info("🎉 TIẾN TRÌNH GỘP DỮ LIỆU THÀNH CÔNG RỰC RỠ!")
        logging.info(f"⏱️  Thời gian thực hiện: {duration:.2f} giây")
        logging.info(f"📊 Tổng số bản ghi trong danh sách gốc: {total_rows:,} dòng")
        logging.info(f"✅ Số dòng khớp và đã nạp nội dung:  {matched_rows:,} dòng ({matched_rows/total_rows*100:.2f}%)")
        logging.info(f"⚠️  Số dòng trống (Bị lỗi hoặc chưa cào): {mismatched_rows:,} dòng")
        logging.info(f"📝 Nhật ký báo cáo chi tiết được lưu tại: '{MERGE_LOG_FILE}'")
        logging.info("=" * 80)

    except KeyboardInterrupt:
        logging.warning("❌ Tiến trình bị hủy bỏ chủ động bởi người dùng. Trạng thái file Excel gốc được giữ vẹn nguyên như ban đầu.")
    except Exception as e:
        logging.error(f"💥 LỖI HỆ THỐNG XẢY RA: {str(e)}", exc_info=True)
        if os.path.exists(STAGING_EXCEL): os.remove(STAGING_EXCEL)


if __name__ == "__main__":
    main()