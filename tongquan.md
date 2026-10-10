# Tổng Quan Dự Án Nghiên Cứu Phân Tích Mạng Lưới Từ Khóa "Nghề Nghiệp Tương Lai Triển Vọng" (미래 유망 직업)

Dự án này phục vụ luận văn cao học / nghiên cứu khoa học với mục tiêu thu thập dữ liệu lớn (Big Data) từ nhiều nguồn tại Hàn Quốc (Chính phủ, Tin tức, Blog), tiến hành tiền xử lý văn bản tiếng Hàn (NLP), thống kê tần suất từ khóa, xây dựng ma trận đồng xuất hiện (Co-occurrence Matrix) và phân tích mạng lưới xã hội (Social Network Analysis - SNA).

---

## I. Công Nghệ Sử Dụng (Technology Stack)

### 1. Ngôn ngữ lập trình chính
- **Python (3.x)**: Ngôn ngữ nền tảng xử lý toàn bộ luồng công việc từ cào dữ liệu, xử lý chuỗi, phân tích NLP đến tính toán ma trận.

### 2. Thu thập dữ liệu (Web Scraping & API Integration)
- **`requests`**: Gửi các yêu cầu HTTP/HTTPS lấy dữ liệu từ Open API (data.go.kr, Naver Open API) và HTML trang web.
- **`BeautifulSoup4` (`bs4`)**: Phân tích cú pháp HTML/XML để trích xuất tiêu đề, nội dung, thẻ từ khóa và ngày xuất bản.
- **`newspaper3k` & `lxml_html_clean`**: Trích xuất bài viết tự động từ các trang tin tức (Naver News, Daum News).
- **`time`, `random`, `datetime`**: Kiểm soát tần suất gửi request (chống khóa IP/rate limit) và xử lý khoảng thời gian thu thập (01/06/2021 ~ 01/06/2026).

### 3. Xử lý & Quản lý dữ liệu lớn (Data Processing & Storage)
- **`pandas`**: Quản lý DataFrame, lọc dữ liệu trùng lặp (deduplication), xử lý mốc thời gian, đọc/ghi file CSV và Excel.
- **`numpy`**: Tính toán đại số tuyến tính và khởi tạo ma trận vuông 1-mode ($N \times N$) cho mạng lưới.
- **`openpyxl`**: Trích xuất dữ liệu ma trận ra định dạng Excel (`.xlsx`) bảo toàn mã hóa tiếng Hàn UTF-8/CP949.
- **`re` (Regular Expressions)**: Xử lý chuỗi, loại bỏ ký tự đặc biệt, làm sạch văn bản và chuẩn hóa các thuật ngữ viết tắt.

### 4. Xử lý Ngôn ngữ Tự nhiên Tiếng Hàn (Korean NLP & Morphological Analysis)
- **`kiwipiepy` (`Kiwi`)** *(Thư viện chính đang được sử dụng trực tiếp trong code)*:
  - Được import và chạy trực tiếp trong [`step2_text_preprocessing.py`](file:///d:/Visual/thesis/step2_text_preprocessing.py) và [`step4_again_step2_and_step3.py`](file:///d:/Visual/thesis/step4_again_step2_and_step3.py).
  - Tách từ, trích xuất danh từ (`NNG`, `NNP`).
  - Khởi tạo và đăng ký từ điển chuyên ngành (`Kiwi.add_user_word`) cho hơn 60+ thuật ngữ công nghệ mới (AI, 생성형AI, 프롬프트엔지니어, 데이터분석가, v.v.) để tránh bị cắt rời từ ghép.
  - Tốc độ phân tích cực nhanh và độ chính xác cao đối với văn bản dữ liệu lớn.
- **`konlpy`**: Có trong gói phụ thuộc `requirements.txt` (dùng làm dự phòng), nhưng **không được gọi trực tiếp trong bất kỳ file code nào của dự án**.

### 5. Phân tích & Trực quan hóa Mạng lưới (Network Analysis & Visualization)
- **`networkx`**: Thư viện Python dùng cho xử lý và dựng đồ thị mạng lưới từ khóa.
- **UCINET & NetDraw**: Thư viện/phần mềm chuyên dụng phân tích mạng lưới xã hội (SNA) đọc ma trận dạng `.xlsx` / `.dl` để tính toán các chỉ số trung tâm (Centrality) và phân tích cụm (CONCOR).

---

## II. Các Bước Thực Hiện Dự Án (Implementation Steps)

### Bước 1: Thu thập dữ liệu đa nguồn (Multi-Source Data Crawling)
1. **Thiết lập tập từ khóa tìm kiếm**: 41 từ khóa chính liên quan đến nghề nghiệp tương lai (ví dụ: `미래 유망 직업`, `인공지능 직업`, `4차산업 직업`, `빅데이터 직업`, v.v.).
2. **Khởi chạy các bộ cào dữ liệu**:
   - [`crawl_datagov.py`](file:///d:/Visual/thesis/crawl_datagov.py) & [`crawl_datagov_details.py`](file:///d:/Visual/thesis/crawl_datagov_details.py): Quét 4 loại định dạng dữ liệu (`FILE`, `API`, `STD`, `LINKED`) trên cổng `data.go.kr`. Tích hợp cơ chế Checkpoint lưu vết chống cào trùng bản ghi.
   - [`crawl_naver_news.py`](file:///d:/Visual/thesis/crawl_naver_news.py) & [`crawl_naver_news_details.py`](file:///d:/Visual/thesis/crawl_naver_news_details.py): Thu thập bài viết tin tức từ Naver.
   - [`crawl_naver_blog.py`](file:///d:/Visual/thesis/crawl_naver_blog.py) & [`crawl_naver_blog_details.py`](file:///d:/Visual/thesis/crawl_naver_blog_details.py): Thu thập bài viết blog từ Naver.
   - [`crawl_daum_news.py`](file:///d:/Visual/thesis/crawl_daum_news.py) & [`crawl_daum_news_details.py`](file:///d:/Visual/thesis/crawl_daum_news_details.py): Thu thập tin tức từ Daum News.

### Bước 2: Hợp nhất & Làm sạch dữ liệu thô (Data Merging & Cleaning)
1. Chạy các script hợp nhất: [`merge_datagov.py`](file:///d:/Visual/thesis/merge_datagov.py), [`merge_data_naver_news.py`](file:///d:/Visual/thesis/merge_data_naver_news.py), [`merge_data_naver_blog.py`](file:///d:/Visual/thesis/merge_data_naver_blog.py), [`merge_data_daum_news.py`](file:///d:/Visual/thesis/merge_data_daum_news.py), [`convert_range_to_csv.py`](file:///d:/Visual/thesis/convert_range_to_csv.py).
2. Lọc bỏ các bản ghi trùng lặp theo liên kết (URL / Detail Link), xử lý các bản ghi rỗng/lỗi mã hóa.
3. Tạo tập dữ liệu hợp nhất hoàn chỉnh: `combined_final_data.csv` và `data_clean_미래_유망_직업.csv`.

### Bước 3: Tiền xử lý văn bản & Phân tích hình thái học (Text Preprocessing & NLP)
Chạy script [`step2_text_preprocessing.py`](file:///d:/Visual/thesis/step2_text_preprocessing.py) (và [`step4_again_step2_and_step3.py`](file:///d:/Visual/thesis/step4_again_step2_and_step3.py)):
1. **Đăng ký từ điển người dùng (`Kiwi.add_user_word`)**: Bổ sung các danh từ riêng và từ ghép công nghệ (ví dụ: `생성형AI`, `프롬프트엔지니어`, `데이터분석가`, `디지털전환`).
2. **Đồng nhất từ đồng nghĩa (Synonym Mapping)**: Quy đổi các cụm từ về chuẩn tiếng Hàn (ví dụ: `AI` $\rightarrow$ `인공지능`, `BIG DATA` $\rightarrow$ `빅데이터`, `머신 러닝` $\rightarrow$ `머신러닝`).
3. **Loại bỏ từ dừng (Stopwords)**: Loại bỏ các từ vô nghĩa, từ chung chung, con số, và ký tự đặc biệt.
4. Trích xuất danh sách các từ khóa danh từ có ý nghĩa cho từng bài viết và lưu vào file `preprocessed_data_for_network.csv`.

### Bước 4: Thống kê tần suất & Xếp hạng từ khóa (Word Frequency Ranking)
Chạy script [`step3_export_word_counts.py`](file:///d:/Visual/thesis/step3_export_word_counts.py):
1. Sử dụng `collections.Counter` để tính tổng số lần xuất hiện của từng từ khóa trên toàn bộ tập dữ liệu.
2. Sắp xếp thứ hạng tần suất giảm dần và lưu ra file `word_frequency_ranked.csv` & `word_frequency_ranked_all.csv`.
3. Xác định danh sách **Top N từ khóa cốt lõi** (ví dụ: Top 70 từ khóa xuất hiện nhiều nhất) để làm danh sách các Node trong đồ thị mạng lưới.

### Bước 5: Tính toán Ma trận đồng xuất hiện (Co-occurrence Matrix Generation)
Chạy script [`step5_matrix.py`](file:///d:/Visual/thesis/step5_matrix.py):
1. Khởi tạo ma trận vuông 1-mode $70 \times 70$ chứa giá trị ban đầu bằng 0.
2. Với mỗi bài viết, lấy tập hợp các từ xuất hiện thuộc Top 70, dùng `itertools.combinations` để tính trọng số liên kết (cộng 1 vào ma trận cho mỗi cặp từ xuất hiện cùng nhau trong cùng một bài viết).
3. Xuất file kết quả đa định dạng:
   - File Excel: `co_occurrence_matrix_top70.xlsx` (dùng nạp trực tiếp vào UCINET không lo lỗi font tiếng Hàn).
   - File CSV: `co_occurrence_matrix_top70.csv` (dùng kiểm tra nhanh dữ liệu).
   - File DL: `network_data_top70.dl` (định dạng UCINET DL).

### Bước 6: Phân tích Mạng lưới Xã hội & Trực quan hóa (Network Analysis & SNA Visualization)
1. **Nạp dữ liệu vào UCINET / NetDraw**: Import file `.xlsx` hoặc `.dl` vào phần mềm UCINET.
2. **Tính toán các chỉ số mạng lưới (SNA Metrics)**:
   - **Degree Centrality** (Bậc trung tâm): Độ kết nối trực tiếp của từ khóa.
   - **Betweenness Centrality** (Trung gian trung tâm): Vai trò cầu nối của từ khóa giữa các cụm chủ đề.
   - **Closeness Centrality** (Gần gũi trung tâm): Mức độ tiếp cận nhanh chóng đến các từ khóa khác.
   - **Eigenvector Centrality**: Mức độ ảnh hưởng dựa trên kết nối với các từ khóa quan trọng khác.
3. **Phân tích Cụm (CONCOR / Community Detection)**: Gom nhóm các từ khóa thành các cụm chủ đề xu hướng (ví dụ: cụm Trí tuệ nhân tạo, cụm Dữ liệu lớn & Chuyển đổi số, cụm Năng lượng xanh & Đô thị thông minh).
4. **Vẽ sơ đồ mạng lưới & Báo cáo kết quả**: Vẽ biểu đồ đồ thị mạng lưới bằng NetDraw/NetworkX để đưa vào nội dung luận văn.
