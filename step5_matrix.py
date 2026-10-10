from collections import Counter
from itertools import combinations
import numpy as np
import pandas as pd

# ==============================================================================
# GIAI ĐOẠN 1: THIẾT LẬP KÍCH THƯỚC MẠNG VÀ TRÍCH XUẤT TOP 70 TỪ KHÓA
# ==============================================================================
# Thiết lập số lượng Node cần phân tích trong mạng lưới (Top 70 từ khóa phổ biến nhất)
TOP_N = 70  

# Đường dẫn file danh sách từ khóa đã xếp hạng tần suất
ALL_RANKED_CSV = "word_frequency_ranked_all.csv"
# Đường dẫn file dữ liệu văn bản đã qua bước tiền xử lý và lọc từ khóa
CLEANED_DATA_CSV = "preprocessed_data_for_network.csv"

# Tên file ma trận xuất ra dạng CSV (dùng cho báo cáo/xem nhanh)
output_matrix_file = f"co_occurrence_matrix_top{TOP_N}.csv"
# Tên file ma trận Excel chuẩn (dùng để import thẳng vào UCINET không lo lỗi font)
output_matrix_excel = f"co_occurrence_matrix_top{TOP_N}.xlsx"
# Tên file xuất ra định dạng DL (dùng cho phương án import DL truyền thống)
OUTPUT_UCINET_DL = f"network_data_top{TOP_N}.dl"

print(f"[1/3] Đang nạp danh sách Top {TOP_N} từ khóa từ '{ALL_RANKED_CSV}'...")
# Đọc file xếp hạng từ khóa vào DataFrame
df_ranked = pd.read_csv(ALL_RANKED_CSV)

# Lấy chính xác 70 từ khóa đầu bảng, ép kiểu chuỗi và xóa bỏ khoảng trắng thừa ở 2 đầu
top_keywords = [str(word).strip() for word in df_ranked["Keyword"].head(TOP_N)]

# Tạo từ điển ánh xạ: từ_khóa -> vị trí index (0 đến 69) để tra cứu vị trí hàng/cột với độ phức tạp O(1)
keyword_to_idx = {word: i for i, word in enumerate(top_keywords)}

# ==============================================================================
# GIAI ĐOẠN 2: TÍNH TOÁN MA TRẬN ĐỒNG XUẤT HIỆN 1-MODE (70 x 70)
# ==============================================================================
print(f"[2/3] Đang quét dữ liệu văn bản để tính tần suất đồng xuất hiện...")
# Đọc file dữ liệu văn bản đã tiền xử lý
df_data = pd.read_csv(CLEANED_DATA_CSV, dtype=str)

# Khởi tạo ma trận vuông kích thước 70x70 với toàn bộ giá trị ban đầu là 0
matrix = np.zeros((TOP_N, TOP_N), dtype=int)

# Duyệt qua từng bài viết/dòng dữ liệu đã trích xuất từ khóa (bỏ qua các dòng trống)
for text in df_data["Extracted_Keywords"].dropna():
    # Sử dụng set() để loại bỏ từ trùng lặp trong CÙNG MỘT bài viết
    # Đảm bảo nguyên tắc học thuật: Một cặp từ chỉ tính đồng xuất hiện tối đa 1 lần / 1 bài viết
    unique_doc_words = set(str(text).split())
    
    # Lọc và chỉ giữ lại những từ nằm trong danh sách Top 70 đang xét
    valid_words = [w for w in unique_doc_words if w in keyword_to_idx]

    # Tạo tất cả các cặp kết hợp không trùng nhau (w1, w2) từ danh sách từ hợp lệ
    for w1, w2 in combinations(valid_words, 2):
        # Lấy chỉ số hàng/cột tương ứng của từng từ
        i, j = keyword_to_idx[w1], keyword_to_idx[w2]
        
        # Tăng trọng số liên kết (cộng 1 vào cả ô (i, j) và ô đối xứng (j, i))
        matrix[i, j] += 1
        matrix[j, i] += 1

# ==============================================================================
# GIAI ĐOẠN 3: XUẤT FILE CHUẨN ĐA ĐỊNH DẠNG (CSV, EXCEL .XLSX VÀ UCINET DL)
# ==============================================================================
print(f"[3/3] Đang xuất file ma trận theo chuẩn bảng mã tiếng Hàn...")

# 1. Chuyển mảng NumPy thành DataFrame Pandas với nhãn hàng và cột là danh sách 70 từ khóa
matrix_df = pd.DataFrame(matrix, index=top_keywords, columns=top_keywords)

# 2. Xuất ra file CSV (UTF-8 có BOM)
matrix_df.to_csv(output_matrix_file, encoding="utf-8-sig")

# 3. [BỔ SUNG MỚI] Xuất trực tiếp ra file Excel .xlsx để import trực tiếp vào UCINET
# File Excel dạng binary tự bảo toàn 100% font tiếng Hàn, không phụ thuộc locale của Windows
matrix_df.to_excel(output_matrix_excel, engine="openpyxl")

# 4. Định dạng nhãn cho file DL: Bọc nhãn trong dấu nháy kép nếu nhãn có chứa khoảng trắng
formatted_labels = [f'"{kw}"' if " " in kw else kw for kw in top_keywords]

# Ghi file DL dự phòng
with open(OUTPUT_UCINET_DL, "w", encoding="cp949", errors="replace") as f:
    f.write(f"DL N={TOP_N}\n")
    f.write("FORMAT=FULLMATRIX\n")
    f.write("LABELS:\n")
    f.write(" ".join(formatted_labels) + "\n")
    f.write("DATA:\n")
    for row in matrix:
        f.write(" ".join(map(str, row)) + "\n")

print("\n" + "=" * 70)
print(f"✅ ĐÃ XUẤT THÀNH CÔNG MA TRẬN TOP {TOP_N}!")
print(f"📁 1. File Excel nạp thẳng UCINET (.xlsx): {output_matrix_excel}")
print(f"📁 2. File CSV xem dữ liệu (.csv):         {output_matrix_file}")
print(f"📁 3. File DL truyền thống (.dl):           {OUTPUT_UCINET_DL}")
print("=" * 70)