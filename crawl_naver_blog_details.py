import os
import random
import re
import signal
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ==============================================================================
# CẤU HÌNH HỆ THỐNG
# ==============================================================================
RAW_KEYWORD = "미래 유망 직업"
INPUT_EXCEL = f"naver_{RAW_KEYWORD.replace(' ', '_')}_2021_2026.xlsx"

# BẬT KIẾN TRÚC PHÂN TÁCH FILE
PROGRESS_CSV = f"progress_{RAW_KEYWORD.replace(' ', '_')}.csv"  # File cũ của bạn
DATA_OUTPUT_CSV = f"data_clean_{RAW_KEYWORD.replace(' ', '_')}.csv"
ERROR_LOG_CSV = f"error_log_{RAW_KEYWORD.replace(' ', '_')}.csv"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

IS_EXITING = False


def signal_handler(sig, frame):
    global IS_EXITING
    if not IS_EXITING:
        IS_EXITING = True
        print(
            "\n⚠️  [HỆ THỐNG] Nhận tín hiệu ngắt (Ctrl+C). Đang xử lý nốt bài hiện tại để đóng file an toàn..."
        )


signal.signal(signal.SIGINT, signal_handler)


# ==============================================================================
# MÔ-ĐUN HỖ TRỢ CHUYÊN BIỆT
# ==============================================================================
def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://blog.naver.com/",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }


def convert_to_real_url(url, blog_id=None, log_no=None):
    if not url or pd.isna(url):
        if blog_id and log_no:
            return f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}&redirect=Dlog&widgetTypeCall=true"
        return None
    if "PostView.naver" not in url:
        match = re.search(r"blog\.naver\.com/([^/]+)/(\d+)", url)
        if match:
            return f"https://blog.naver.com/PostView.naver?blogId={match.group(1)}&logNo={match.group(2)}&redirect=Dlog&widgetTypeCall=true"
    return url


def extract_pure_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    content_area = (
        soup.select_one(".se-main-container")
        or soup.select_one("#postViewArea")
        or soup.select_one(".se_component_wrap")
    )
    if content_area:
        text = content_area.get_text(separator=" ", strip=True)
        return " ".join(text.split())
    return None


def fetch_with_retry(url, retries=3, backoff_factor=2):
    """Cào dữ liệu có cơ chế tự động thử lại (Retry) tại chỗ 3 lần với thời gian tăng dần."""
    for i in range(retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=12)
            if response.status_code == 200:
                return response.text, None
            elif response.status_code in [404, 403]:  # Lỗi cố định không cần retry
                return None, f"HTTP_{response.status_code}"
        except requests.RequestException as e:
            if i == retries - 1:
                return None, type(e).__name__

        # Gặp lỗi mạng tạm thời -> Ngủ tăng dần (2s -> 4s -> 8s) rồi thử lại
        print(f"   ⚠️ Lỗi mạng tạm thời, đang thử lại lần {i+1}/{retries}...")
        time.sleep(backoff_factor ** (i + 1))
    return None, "TIMEOUT_EXCEEDED"


# ==============================================================================
# TIẾN TRÌNH ENGINE CHÍNH
# ==============================================================================
def main():
    global IS_EXITING
    if not os.path.exists(INPUT_EXCEL):
        print(f"❌ Không tìm thấy file danh sách gốc: '{INPUT_EXCEL}'")
        return

    print("📊 1. Đang đồng bộ danh sách và thiết lập Checkpoint...")
    df_src = pd.read_excel(INPUT_EXCEL, engine="openpyxl")
    df_src["Post ID (LogNo)"] = df_src["Post ID (LogNo)"].astype(str).str.strip()

    # --- BƯỚC DI TRÚ DỮ LIỆU CŨ (MỘT LẦN DUY NHẤT) ---
    if os.path.exists(PROGRESS_CSV) and not os.path.exists(DATA_OUTPUT_CSV):
        print("🔄 Phát hiện dữ liệu cũ dở dang. Đang phân tách sang cấu hình mới...")
        try:
            df_old = pd.read_csv(PROGRESS_CSV, dtype=str)
            df_old_clean = df_old[~df_old["Nội Dung Chi Tiết"].str.contains(r"\[LỖI", na=False)]
            df_old_error = df_old[df_old["Nội Dung Chi Tiết"].str.contains(r"\[LỖI", na=False)].copy()
            
            df_old_clean.to_csv(DATA_OUTPUT_CSV, index=False, encoding="utf-8-sig")
            
            df_old_error["Thời Gian"] = time.strftime('%Y-%m-%d %H:%M:%S')
            df_old_error.columns = ["Post ID (LogNo)", "Mã Lỗi", "Thời Gian"]
            df_old_error.to_csv(ERROR_LOG_CSV, index=False, encoding="utf-8-sig")
            print("   ✅ Phân tách dữ liệu cũ hoàn tất thành công!")
        except Exception as e:
            print(f"   ⚠️ Không thể di trú tự động file cũ: {e}. Hệ thống sẽ chạy độc lập.")

    # Khởi tạo các file xuất dữ liệu nếu chưa tồn tại
    if not os.path.exists(DATA_OUTPUT_CSV):
        pd.DataFrame(columns=["Post ID (LogNo)", "Nội Dung Chi Tiết"]).to_csv(DATA_OUTPUT_CSV, index=False, encoding="utf-8-sig")
    if not os.path.exists(ERROR_LOG_CSV):
        pd.DataFrame(columns=["Post ID (LogNo)", "Mã Lỗi", "Thời Gian"]).to_csv(ERROR_LOG_CSV, index=False, encoding="utf-8-sig")

    # Xác định các bài viết đã xử lý thành công hoặc thất bại cố định để bỏ qua
    processed_ids = set()
    try:
        processed_ids.update(pd.read_csv(DATA_OUTPUT_CSV, usecols=["Post ID (LogNo)"], dtype=str)["Post ID (LogNo)"].dropna().tolist())
    except Exception: pass
    
    try:
        processed_ids.update(pd.read_csv(ERROR_LOG_CSV, usecols=["Post ID (LogNo)"], dtype=str)["Post ID (LogNo)"].dropna().tolist())
    except Exception: pass

    # Lọc danh sách hàng cần chạy thực tế (Tự động loại trừ hoặc nạp lại bài lỗi nếu bạn xóa file log)
    todo_df = df_src[~df_src["Post ID (LogNo)"].isin(processed_ids)]
    total_todo = len(todo_df)

    print(f"📊 Tổng số: {len(df_src)} | Đã xử lý: {len(processed_ids)} | 📈 Còn lại cần cào: {total_todo}")

    if total_todo == 0:
        print("🎉 Tất cả bài viết đã được xử lý hoàn chỉnh!")
        return

    print("\n🚀 Kích hoạt Senior Engine (Graceful & Resilient)...")
    print("=" * 80)

    for idx, (original_index, row) in enumerate(todo_df.iterrows()):
        if IS_EXITING:
            break

        raw_url = row.get("URL Bài Viết")
        blog_id = row.get("Blog ID")
        log_no = row.get("Post ID (LogNo)")
        target_url = convert_to_real_url(raw_url, blog_id, log_no)

        if not target_url:
            continue

        print(f"🌐 [{idx + 1}/{total_todo}] (Dòng Excel: {original_index + 2}) -> {target_url}")

        # Thực hiện cào có kèm cấu hình chịu lỗi
        html_content, error_code = fetch_with_retry(target_url)

        if html_content:
            text_content = extract_pure_text(html_content)
            if text_content and len(text_content.strip()) > 0:
                # 🌟 GHI VÀO FILE DATA SẠCH
                pd.DataFrame([[log_no, text_content]], columns=["Post ID (LogNo)", "Nội Dung Chi Tiết"]).to_csv(
                    DATA_OUTPUT_CSV, mode="a", header=False, index=False, encoding="utf-8-sig"
                )
                print(f"   ✅ Thành công: Lấy xong text ({len(text_content)} ký tự).")
            else:
                error_code = "EMPTY_OR_DOM_CHANGED"

        if error_code:
            # 🌟 GHI VÀO FILE LOG LỖI BIỆT LẬP
            pd.DataFrame([[log_no, error_code, time.strftime('%Y-%m-%d %H:%M:%S')]], columns=["Post ID (LogNo)", "Mã Lỗi", "Thời Gian"]).to_csv(
                ERROR_LOG_CSV, mode="a", header=False, index=False, encoding="utf-8-sig"
            )
            print(f"   ❌ Thất bại: Đã đẩy vào danh sách lỗi [{error_code}]. Tiếp tục sang bài kế tiếp.")

        time.sleep(random.uniform(0.5, 0.8))

    print("\n" + "=" * 80)
    print("🔒 [HỆ THỐNG ĐÃ ĐÓNG AN TOÀN]")
    print(f"💾 File dữ liệu sạch (Data Clean): '{DATA_OUTPUT_CSV}'")
    print(f"⚠️  File nhật ký lỗi (Error Log): '{ERROR_LOG_CSV}'")
    print("=" * 80)


if __name__ == "__main__":
    main()