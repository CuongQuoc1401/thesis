import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import WordCloud

# 1. Đọc file CSV và lấy 70 từ đầu tiên
# Lưu ý kiểm tra encoding (utf-8, utf-8-sig hoặc cp949 nếu mở file tiếng Hàn bị lỗi ký tự)
df = pd.read_csv("word_frequency_ranked_all.csv", encoding="utf-8-sig")

# Lấy top 70 từ khóa có thứ hạng cao nhất
top70_df = df.head(70)

# Chuyển 2 cột 'Keyword' và 'Frequency' thành dictionary {từ: tần suất}
word_counts = dict(zip(top70_df["Keyword"], top70_df["Frequency"]))

# 2. Cấu hình Word Cloud
# font_path cần chỉ đúng đường dẫn font hỗ trợ tiếng Hàn
font_path = "C:/Windows/Fonts/malgun.ttf"  # Hoặc "NanumGothic.ttf"

wc = WordCloud(
    font_path=font_path,
    width=1200,  # Tăng độ phân giải cho hình vẽ sắc nét hơn
    height=800,
    background_color="white",  # Nền trắng phù hợp chèn vào luận văn
    colormap="viridis",  # Bảng màu (có thể đổi sang 'plasma', 'tab10', 'Blues',...)
    max_words=70,  # Giới hạn đúng 70 từ
    random_state=42,  # Cố định vị trí các từ để kết quả không bị thay đổi mỗi lần chạy
)

# 3. Tạo Word Cloud từ tần suất
wc.generate_from_frequencies(word_counts)

# 4. Hiển thị và lưu file ảnh chất lượng cao (300 DPI)
plt.figure(figsize=(12, 8))
plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.tight_layout(pad=0)

# Lưu ảnh để chèn vào báo cáo/luận văn
plt.savefig("wordcloud_top70.png", dpi=300, bbox_inches="tight")
plt.show()