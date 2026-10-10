from collections import Counter
import pandas as pd

# ==========================================
# 1. ĐỌC FILE DỮ LIỆU ĐÃ TIỀN XỬ LÝ
# ==========================================
INPUT_CSV = "preprocessed_data_for_network.csv"
OUTPUT_WORD_COUNT_CSV = "word_frequency_ranked.csv"

print(f"[1/3] Đang đọc file '{INPUT_CSV}'...")
df = pd.read_csv(INPUT_CSV, dtype=str)

# ==========================================
# 2. ĐẾM TẦN SUẤT XUẤT HIỆN CỦA TỪNG TỪ KHÓA
# ==========================================
print("[2/3] Đang thống kê tần suất xuất hiện của các từ khóa...")

# Lấy tất cả từ khóa từ cột 'Extracted_Keywords' và tách thành danh sách từ
all_words = " ".join(df["Extracted_Keywords"].dropna()).split()

# Đếm tần suất bằng Counter
word_counts = Counter(all_words)

# Chuyển kết quả thành DataFrame
df_word_counts = pd.DataFrame(
    word_counts.items(), columns=["Keyword", "Frequency"]
)

# Sắp xếp giảm dần theo số lần xuất hiện (Frequency)
df_word_counts = df_word_counts.sort_values(
    by="Frequency", ascending=False
).reset_index(drop=True)

# Thêm cột Thứ hạng (Rank) để tiện đưa vào báo cáo/luận văn
df_word_counts.index = df_word_counts.index + 1
df_word_counts.index.name = "Rank"

# ==========================================
# 3. XUẤT FILE CSV & HIỂN THỊ KẾT QUẢ
# ==========================================
print(f"[3/3] Đang xuất kết quả ra file '{OUTPUT_WORD_COUNT_CSV}'...")
df_word_counts.to_csv(OUTPUT_WORD_COUNT_CSV, encoding="utf-8-sig")

print("\n" + "=" * 50)
print(f"✅ Đã xuất thành công {len(df_word_counts):,} từ khóa!")
print(f"📁 File kết quả: {OUTPUT_WORD_COUNT_CSV}")
print("=" * 50)

# Xem trước Top 10 từ khóa xuất hiện nhiều nhất
print("\n📊 Xem trước Top 10 từ khóa hàng đầu:")
print(df_word_counts.head(10))