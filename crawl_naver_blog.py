import json
import math
import os
import re
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
import utils

# Cấu hình ban đầu
raw_keyword = "미래 유망 직업"
keyword = utils.get_encoded_keyword(raw_keyword)
count_per_page = 30
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://section.blog.naver.com/Search/Post.naver",
}

# Tên file cố định xuyên suốt quá trình chạy
excel_file = f"naver_{raw_keyword.replace(' ', '_')}_2021_2026.xlsx"

# CẤU HÌNH KHOẢNG THỜI GIAN TỔNG
current_end_date = datetime.strptime("2026-06-01", "%Y-%m-%d")
final_start_date = datetime.strptime("2021-06-01", "%Y-%m-%d")
days_interval = 11  # Cào theo từng block ~10 ngày

# Hàm dọn dẹp thẻ HTML
def clean_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", str(text))


print("🚀 Khởi động hệ thống cào dữ liệu lưu trữ thời gian thực (Real-time Saving)...")
print(f"💾 Dữ liệu sẽ được bảo toàn liên tục vào file: '{excel_file}'")

# VÒNG LẶP CHÍNH: Dịch chuyển khoảng thời gian lùi dần về quá khứ
while current_end_date > final_start_date:
    # 🌟 KHỞI TẠO LẠI MẢNG RỖNG CHO MỖI BLOCK: Giúp RAM luôn nhẹ, không bị phình to
    block_posts = []

    current_start_date = current_end_date - timedelta(days=days_interval)
    if current_start_date < final_start_date:
        current_start_date = final_start_date

    start_date_str = current_start_date.strftime("%Y-%m-%d")
    end_date_str = current_end_date.strftime("%Y-%m-%d")

    print("\n" + "=" * 60)
    print(
        f"📅 GIAI ĐOẠN: {start_date_str} ---> {end_date_str}"
    )
    print("=" * 60)

    current_page = 1

    # VÒNG LẶP CON: Cào sạch các trang của block hiện tại
    while True:
        print(
            f"   -> Đang cào Trang {current_page} ({start_date_str} ~ {end_date_str})..."
        )
        url = f"https://section.blog.naver.com/ajax/SearchList.naver?countPerPage={count_per_page}&currentPage={current_page}&endDate={end_date_str}&keyword={keyword}&orderBy=sim&startDate=start_date_str&type=post"
        # Sửa lỗi logic chuỗi trong url ở prompt trước: gán biến động chuẩn xác
        url = f"https://section.blog.naver.com/ajax/SearchList.naver?countPerPage={count_per_page}&currentPage={current_page}&endDate={end_date_str}&keyword={keyword}&orderBy=sim&startDate={start_date_str}&type=post"

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                raw_text = response.text
                clean_json_text = raw_text.split("}',")[-1].strip()
                data = json.loads(clean_json_text)

                if current_page == 1:
                    total_count = data.get("result", {}).get("totalCount", 0)
                    print(
                        f"   📊 Tìm thấy {total_count} bài viết trong giai đoạn này."
                    )

                search_list = data.get("result", {}).get("searchList", [])

                if not search_list:
                    print(f"   ⏹️ Hết dữ liệu ở trang {current_page}.")
                    break

                for post in search_list:
                    timestamp = post.get("addDate")
                    formatted_date = (
                        pd.to_datetime(timestamp, unit="ms").strftime(
                            "%Y-%m-%d"
                        )
                        if timestamp
                        else ""
                    )

                    post_data = {
                        "Blog ID": post.get("domainIdOrBlogId"),
                        "Post ID (LogNo)": post.get("logNo"),
                        "GDID": post.get("gdid"),
                        "URL Bài Viết": post.get("postUrl"),
                        "Tiêu Đề": clean_html(post.get("title")),
                        "Tóm Tắt Nội Dung": clean_html(post.get("contents")),
                        "Biệt Danh Tác Giả": post.get("nickName"),
                        "Tên Blog": post.get("blogName"),
                        "Ngày Đăng": formatted_date,
                    }
                    block_posts.append(post_data)

                current_page += 1
                time.sleep(1.5)  # Nghỉ để qua mắt hệ thống anti-bot của Naver

            else:
                print(
                    f"   ❌ Lỗi kết nối trang {current_page}. Mã lỗi: {response.status_code}"
                )
                break

        except Exception as e:
            print(f"   ❌ Lỗi hệ thống trang {current_page}: {e}")
            break

    # 🌟 THỰC HIỆN LƯU NGAY KHI CÀO XONG 1 BLOCK THỜI GIAN
    if block_posts:
        new_df = pd.DataFrame(block_posts)

        # Nếu file đã tồn tại trên ổ cứng -> Đọc lên, gộp vào, lọc trùng rồi đè lại
        if os.path.exists(excel_file):
            try:
                old_df = pd.read_excel(excel_file, engine="openpyxl")
                combined_df = pd.concat([old_df, new_df], ignore_index=True)

                # Thanh lọc trùng lặp ngay lập tức để giữ file gọn gàng
                combined_df.drop_duplicates(
                    subset=["URL Bài Viết"], keep="first", inplace=True
                )
                combined_df.to_excel(excel_file, index=False, engine="openpyxl")
                print(
                    f"💾 ĐÃ CHỐT: Nối thành công {len(new_df)} hàng mới vào file cứng."
                )
            except Exception as e:
                print(f"⚠️ Gặp lỗi khi ghi đè file: {e}. Đang thử ghi lại...")
                time.sleep(2)
                new_df.to_excel(
                    f"backup_{int(time.time())}.xlsx",
                    index=False,
                    engine="openpyxl",
                )
        else:
            # Nếu chạy đợt đầu tiên và file chưa có -> Tạo file mới hoàn toàn
            new_df.to_excel(excel_file, index=False, engine="openpyxl")
            print(f"🆕 ĐÃ CHỐT: Tạo file mới và lưu {len(new_df)} hàng đầu tiên.")

        # In ra tổng số dòng tích lũy thực tế trong file Excel tính đến hiện tại
        total_rows_now = len(pd.read_excel(excel_file, engine="openpyxl"))
        print(f"📈 Tổng số hàng an toàn trên ổ cứng hiện tại: {total_rows_now}")

    else:
        print("   ℹ️ Giai đoạn này trống, không có dữ liệu để lưu.")

    # 🌟 DỊCH CHUYỂN THỜI GIAN LÙI VỀ QUÁ KHỨ CHO ĐỢT TIẾP THEO
    current_end_date = current_start_date - timedelta(days=1)

print("\n" + "=" * 60)
print(f"🎉 HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH 5 NĂM (2021 - 2026)!")
print(
    f"🔒 TẤT CẢ DỮ LIỆU ĐÃ NẰM AN TOÀN TRONG FILE: '{excel_file}'"
)
print("=" * 60)