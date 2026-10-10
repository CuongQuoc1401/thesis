from collections import Counter
import re
import pandas as pd
from kiwipiepy import Kiwi

# ==============================================================================
# GIAI ĐOẠN 1: KHỞI TẠO KIWI & ĐĂNG KÝ TỪ ĐIỂN CHUYÊN NGÀNH
# ==============================================================================
print(
    "[1/4] Đang khởi tạo bộ phân tích hình thái học Kiwi và nạp từ điển chuyên"
    " ngành..."
)
kiwi = Kiwi()

# Danh sách danh từ ghép chuyên ngành về Công nghệ, Nghề nghiệp và Kỹ năng tương lai.
# Việc thêm danh sách này giúp Kiwi KHÔNG bị cắt rời các từ ghép (ví dụ: '인공지능' không bị tách thành '인공' + '지능').
DOMAIN_KEYWORDS = [
    # 1. Công nghệ mũi nhọn & Lĩnh vực chuyển đổi số
    "인공지능",
    "빅데이터",
    "공공데이터",
    "자율주행",
    "블록체인",
    "메타버스",
    "사물인터넷",
    "클라우드",
    "로보틱스",
    "생성형AI",
    "양자컴퓨팅",
    "드론",
    "스마트시티",
    "스마트팜",
    "스마트팩토리",
    "신재생에너지",
    "바이오헬스",
    "핀테크",
    "에듀테크",
    "사이버보안",
    "디지털트윈",
    "ESG경영",
    "가상현실",
    "증강현실",
    "딥러닝",
    "머신러닝",
    # 2. Vị trí việc làm & Danh xưng nghề nghiệp tương lai
    "데이터분석가",
    "데이터엔지니어",
    "데이터사이언티스트",
    "AI전문가",
    "프롬프트엔지니어",
    "소프트웨어개발자",
    "보안전문가",
    "로봇공학자",
    "3D프린팅전문가",
    "신재생에너지전문가",
    "기후변화전문가",
    "스마트팜운영자",
    "컨텐츠크리에이터",
    "메타버스크리에이터",
    "사회복지사",
    "정보보안전문가",
    # 3. Kỹ năng số & Các khái niệm xu hướng
    "디지털전환",
    "디지털리터러시",
    "창의적사고",
    "문제해결력",
    "융합인재",
    "평생교육",
    "원격근무",
    "유연근무제",
    "직무역량",
    "신산업",
    "유망직업",
    "미래직업",
    "자격증취득",
]

# Đăng ký từng từ vào Kiwi với thẻ 'NNG' (Danh từ chung) và gán điểm ưu tiên (score=10.0)
for word in DOMAIN_KEYWORDS:
  kiwi.add_user_word(word, "NNG", score=10.0)

# ==============================================================================
# GIAI ĐOẠN 2: THIẾT LẬP BỘ QUY TẮC ĐỒNG NHẤT TỪ (SYNONYM) & TỪ DỪNG (STOPWORDS)
# ==============================================================================

# Bảng quy đổi từ đồng nghĩa / từ phái sinh (Áp dụng SAU KHI Kiwi đã tách từ)
# Giúp gộp các biến thể từ vựng về một từ khóa chuẩn duy nhất để tăng độ tập trung liên kết mạng lưới
POST_TOKEN_SYNONYMS = {
    # Nhóm chuyên môn, bằng cấp, việc làm
    "전문": "전문가",
    "자격": "자격증",
    "자격증취득": "자격증",
    "취득": "자격증",
    "개발자": "개발",
    "일자리": "고용",
    "취업": "고용",
    "채용": "고용",
    "복지사": "사회복지사",
    "복지": "사회복지사",  # [BỔ SUNG MỚI] Gộp '복지' về '사회복지사'
    "사회복지": "사회복지사",  # [BỔ SUNG MỚI] Gộp '사회복지' về '사회복지사'
    # Nhóm công nghệ & dữ liệu (Gộp các mảnh từ bị bẻ rời hoặc từ viết tắt)
    "지능": "인공지능",
    "인공": "인공지능",
    "공공": "공공데이터",
    "데이터": "빅데이터",
    "콘텐츠": "컨텐츠크리에이터",
    "컨텐츠": "컨텐츠크리에이터",
    "영상": "컨텐츠크리에이터",  # [BỔ SUNG MỚI] Gộp '영상' về '컨텐츠크리에이터'
    "로봇공학": "로봇",
    "인공지능전문가": "AI전문가",
    "코딩": "소프트웨어",
    "프로그램": "소프트웨어",
    "컴퓨터": "소프트웨어",
    "보안": "사이버보안",  # [BỔ SUNG MỚI] Gộp '보안' về '사이버보안'
    # Nhóm đào tạo & nhân lực
    "학습": "교육",
    "훈련": "교육",
    "이수": "교육",
    "교사": "교육",  # [BỔ SUNG MỚI] Gộp '교사' về '교육'
    "교수": "교육",  # [BỔ SUNG MỚI] Gộp '교수' về '교육'
    "지도사": "전문가",  # [BỔ SUNG MỚI] Gộp '지도사' về '전문가'
    "인력": "인재",
    "양성": "인재",
    # Nhóm y tế & chăm sóc sức khỏe
    "병원": "의료",
    "치료": "의료",
    "보건": "의료",
    "의사": "의료",
    "심리": "심리상담",
    "상담사": "심리상담",  # [BỔ SUNG MỚI] Gộp '상담사' về '심리상담'
    # Nhóm giao thông & phương tiện
    "자동차": "자율주행",
    "교통": "자율주행",
}

# Danh sách từ dừng (Stopwords) triệt để: Loại bỏ những từ không mang giá trị cho mạng ngữ nghĩa
JOB_STOPWORDS = set([
    # 1. Từ khóa tìm kiếm gốc (Cào bài nào cũng có, nếu để lại sẽ tạo thành Hub ảo nuốt hết liên kết)
    "직업",
    "미래",
    "유망",
    "기술",
    "산업",
    # 2. Từ ngữ quảng cáo tuyển sinh, trung tâm luyện thi, mẫu văn bản hành chính
    "학원",
    "무료",
    "수강",
    "강의",
    "합격",
    "국비",
    "강사",
    "출처",
    "번호",
    "허락",
    "키워드",
    "코드",
    "다음",
    "질문",
    "소개",
    "참고",
    "모집",
    "신청",
    "등록",
    "작성",
    "파일",
    "안내",
    "첨부",
    "추천",
    "정리",
    "홈페이지",
    "다운로드",
    "주소",
    "사진",
    "뉴스",
    # [BỔ SUNG MỚI] Lọc các từ hành chính/mẫu đơn phát hiện từ lần chạy trước:
    "전화번호",
    "올해",
    "계약",
    "워드",
    "식품",
    "여부",
    "구체",
    "연도",
    "일부",
    "제시",
    "조직",
    "주목",
    "예정",
    "학력",
    "인식",
    "유무",
    "과거",
    "우수",
    "근거",
    "민간",
    "면접",
    "아래",
    "행사",
    "소통",
    "인생",
    "예방",
    "자유",
    "종류",
    "공고",
    "상승",
    "한계",
    "이미지",
    "모습",
    "방문",
    "상품",
    "확장",
    "사랑",
    "표현",
    "도구",
    "장점",
    "판단",
    "조성",
    "포털",
    "근무",
    "걱정",
    "특별",
    "위기",
    "희망",
    "대학교",
    "인기",
    "지방",
    "역사",
    "학점은행제",
    "공급",
    "장비",
    "학점",
    "페이지",
    "카드",
    "강조",
    "영업",
    "커리큘럼",
    "부모",
    "주제",
    "활성",
    "현재",
    "대한민국",
    "이동",
    "진학",
    "실시간",
    "탐색",
    "업종",
    "서울특별시",
    "형식",
    "단체",
    "데이터셋명",
    "거래",
    "아동",
    "컨설팅",
    "하루",
    "진출",
    "공동",
    "직장",
    "조회",
    "전반",
    "보장",
    "개념",
    "신뢰",
    "정확",
    "주변",
    "브랜드",
    "여행",
    "진단",
    "정비",
    "관리사",
    "선수",
    "금액",
    "커리어",
    "발급",
    "실적",
    # 3. Danh từ trừu tượng / Thuật ngữ chung chung không mang tính công nghệ/nghề nghiệp cụ thể
    "가능",
    "활용",
    "필요",
    "다양",
    "중요",
    "시간",
    "운영",
    "준비",
    "자료",
    "방법",
    "문제",
    "시작",
    "진행",
    "체계",
    "이상",
    "변화",
    "경우",
    "이용",
    "범위",
    "선택",
    "시설",
    "시대",
    "연구",
    "센터",
    "상담",
    "확인",
    "기회",
    "계획",
    "결과",
    "상황",
    "강화",
    "주요",
    "확대",
    "제도",
    "부분",
    "정도",
    "구축",
    "부서",
    "개선",
    "조사",
    "연계",
    "생산",
    "현실",
    "수익",
    "자동",
    "대비",
    "영향",
    "부과",
    "협력",
    "최근",
    "제작",
    "추진",
    "자산",
    "추가",
    "최대",
    "향상",
    "예상",
    "소득",
    "기능",
    "확보",
    "수집",
    "기대",
    "마련",
    "처음",
    "접근",
    "업데이트",
    "기록",
    "기존",
    "성과",
    "세상",
    "고려",
    "목적",
    "수정",
    "종합",
    "사실",
    "검사",
    "가격",
    "특정",
    "특성",
    "예측",
    "해외",
    "자체",
    "최고",
    "자리",
    "전국",
    "자연",
    "자원",
    "대체",
    "기여",
    "장기",
    "경기",
    "부족",
    "기획",
    "평균",
    "경쟁",
    "동시",
    "경험",
    "성공",
    "가치",
    "이야기",
    "마음",
    "단순",
    "지금",
    "오늘",
    "동안",
    "사례",
    "노력",
    "고민",
    "실제",
    "도전",
    "발생",
    "이후",
    "의미",
    "유지",
    "수준",
    "맞춤",
    "형태",
    "관계",
    "단위",
    "집중",
    "조건",
    "보유",
    "적용",
    "상태",
    "이론",
    "방향",
    "주기",
    "요구",
    "부담",
    "일정",
    "사고",
    "연결",
    "위험",
    "전체",
    "기본",
    "결정",
    "해결",
    "효율",
    "효과",
    "수립",
    "수행",
    "통합",
    "제한",
    "처리",
    "대응",
    "작업",
    "비용",
    "평가",
    "업무",
    "핵심",
    "현장",
    "참여",
    "공간",
    "생활",
    "안정",
    "목표",
    "지속",
    "실무",
    "구조",
    "구성",
    "관심",
    "기간",
    "방식",
    "규모",
    "분야",
    "역량",
    "과정",
    "단계",
    "기반",
    "내용",
    "현황",
    "관련",
    "제공",
    "사업",
    "개요",
    "분석",
    "상세",
    "설명",
    "기준",
    "대상",
    "위치",
    "정보",
    "관리",
    "지원",
    "구분",
    "생각",
    "사람",
    "개인",
    "자신",
    "가족",
    "항목",
    "사용",
    "해당",
    "이해",
    "분류",
    "도움",
    "유형",
    "중심",
    "필수",
    "기초",
    "파악",
    "이번",
    "이유",
    "사항",
    "일반",
    "대표",
    "필요성",
    "역할",
    "포함",
    "기사",
    # [BỔ SUNG MỚI] Lọc các từ trừu tượng/chung chung lọt vào Top 70:
    "활동",
    "발전",
    "증가",
    "수요",
    "전망",
    "지식",
    "회사",
    "업체",
    "모델",
    "제품",
    "프로젝트",
    "보호",
    "주택",
    "전환",
    "세대",
    "노동",
    "응시",
    "스마트",
    "비교",
    "중국",
    "안녕",
    "기타",
    "영역",
    "요즘",
    "행동",
    "흐름",
    "존재",
    "선정",
    "발표",
    "트렌드",
    "시민",
    "인정",
    "공개",
    "설치",
    "지도",
    "시기",
    "바탕",
    "도입",
    "혁명",
    "반영",
    "공유",
    "문의",
    "기자",
    "친구",
    "판매",
    "생성",
    "감정",
    "환자",
    "재정",
    "창출",
    "적극",
    "일자",
    "과제",
    "혜택",
    "최신",
    "학위",
    "인증",
    "본인",
    "요소",
    # 4. Địa danh / Quốc gia / Đối tượng nhân khẩu học chung
    "한국",
    "서울",
    "경기도",
    "부산",
    "인천",
    "미국",
    "국내",
    "국가",
    "세계",
    "글로벌",
    "도시",
    "지역",
    "국제",
    "아이",
    "인간",
    "청년",
    "여성",
    "노인",
    "청소년",
    "국민",
    "고객",
    "인구",
    # 5. Trường học truyền thống & thủ tục học vụ
    "대학",
    "학생",
    "학교",
    "수업",
    "학과",
    "공부",
    "과목",
    "전공",
    "체험",
    "실습",
    "졸업",
    "시험",
])


def preprocess_korean_text(text):
  """Hàm tiền xử lý từng đoạn văn bản tiếng Hàn:

  1. Chuẩn hóa Regex các từ viết tắt tiếng Anh sang tiếng Hàn
  2. Xóa bỏ ký tự đặc biệt
  3. Phân tích hình thái học Kiwi (chỉ lấy NNG, NNP)
  4. Gộp từ đồng nghĩa (POST_TOKEN_SYNONYMS)
  5. Lọc từ đơn (<2 ký tự) và loại bỏ từ dừng (JOB_STOPWORDS)
  """
  # Kiểm tra nếu chuỗi rỗng hoặc không hợp lệ thì trả về chuỗi rỗng
  if not isinstance(text, str) or not text.strip():
    return ""

  # 1. Chuẩn hóa các từ viết tắt tiếng Anh thông dụng sang tiếng Hàn tương ứng
  text = re.sub(
      r"\b(AI|ARTIFICIAL INTELLIGENCE)\b", "인공지능", text, flags=re.IGNORECASE
  )
  text = re.sub(r"\b(BIG\s*DATA)\b", "빅데이터", text, flags=re.IGNORECASE)
  text = re.sub(r"\b(METAVERSE)\b", "메타버스", text, flags=re.IGNORECASE)
  text = re.sub(r"\b(BLOCKCHAIN|NFT)\b", "블록체인", text, flags=re.IGNORECASE)
  text = re.sub(r"\b(IOT)\b", "사물인터넷", text, flags=re.IGNORECASE)
  text = re.sub(r"\b(CLOUD)\b", "클라우드", text, flags=re.IGNORECASE)

  # 2. Xóa toàn bộ ký tự đặc biệt, chỉ giữ lại chữ tiếng Hàn, chữ tiếng Anh và số
  text = re.sub(r"[^가-힣A-Z0-9\s]", " ", text)

  # 3. Phân tích hình thái học bằng Kiwi
  tokens = kiwi.tokenize(text)

  extracted_keywords = []
  for token in tokens:
    # Chỉ trích xuất Danh từ chung (NNG) và Danh từ riêng (NNP)
    if token.tag in ["NNG", "NNP"]:
      word = token.form.strip()

      # Bước 4: Áp dụng bảng gộp từ đồng nghĩa
      word = POST_TOKEN_SYNONYMS.get(word, word)

      # Bước 5: Bỏ qua nếu từ ngắn hơn 2 ký tự hoặc nằm trong danh sách từ dừng
      if len(word) < 2 or word in JOB_STOPWORDS:
        continue

      extracted_keywords.append(word)

  # Nối các từ khóa đã làm sạch thành một chuỗi cách nhau bởi khoảng trắng
  return " ".join(extracted_keywords)


# ==============================================================================
# GIAI ĐOẠN 3: NẠP DỮ LIỆU THÔ & TIẾN HÀNH TIỀN XỬ LÝ HÀNG LOẠT
# ==============================================================================
INPUT_CSV = "combined_final_data.csv"  # Tên file dữ liệu thô ban đầu
CLEANED_DATA_CSV = (
    "preprocessed_data_for_network.csv"  # File lưu dữ liệu sau khi làm sạch
)
OUTPUT_ALL_RANKED_CSV = (
    "word_frequency_ranked_all.csv"  # File lưu bảng xếp hạng TẤT CẢ từ khóa
)

print(f"[2/4] Đang đọc file dữ liệu thô '{INPUT_CSV}'...")
df = pd.read_csv(INPUT_CSV, dtype=str)

# Tự động nhận diện cột nội dung (hỗ trợ cả 'Nội Dung Chi Tiết' hoặc 'Nội Dung')
content_col = (
    "Nội Dung Chi Tiết" if "Nội Dung Chi Tiết" in df.columns else "Nội Dung"
)

# Gộp cột Tiêu Đề và Nội Dung thành một cột chuỗi hoàn chỉnh để phân tích
df["Full_Text"] = (
    df["Tiêu Đề"].fillna("").astype(str)
    + " "
    + df[content_col].fillna("").astype(str)
)

print(
    f"[3/4] Đang thực hiện phân tích hình thái học và làm sạch trên {len(df):,}"
    " dòng dữ liệu..."
)
# Áp dụng hàm tiền xử lý lên toàn bộ dữ liệu
df["Extracted_Keywords"] = df["Full_Text"].apply(preprocess_korean_text)

# Xóa cột văn bản thô để giảm dung lượng file lưu trữ
df.drop(columns=["Full_Text"], inplace=True)

# Lưu kết quả làm sạch ra file CSV trung gian
df.to_csv(CLEANED_DATA_CSV, index=False, encoding="utf-8-sig")

# ==============================================================================
# GIAI ĐOẠN 4: THỐNG KÊ TẦN SUẤT & XUẤT TOÀN BỘ DANH SÁCH TỪ KHÓA
# ==============================================================================
print(
    "[4/4] Đang đếm tần suất toàn bộ từ vựng và xuất ra file"
    f" '{OUTPUT_ALL_RANKED_CSV}'..."
)

# Tách toàn bộ từ khóa trong cột 'Extracted_Keywords' thành danh sách từ đơn
all_words = " ".join(df["Extracted_Keywords"].dropna()).split()

# Đếm số lần xuất hiện của từng từ bằng Counter
word_counts = Counter(all_words)

# Chuyển kết quả sang DataFrame để sắp xếp và đánh số thứ tự Rank
df_ranked_all = pd.DataFrame(
    word_counts.items(), columns=["Keyword", "Frequency"]
)
df_ranked_all = df_ranked_all.sort_values(
    by="Frequency", ascending=False
).reset_index(drop=True)

# Đặt chỉ số Rank bắt đầu từ 1
df_ranked_all.index = df_ranked_all.index + 1
df_ranked_all.index.name = "Rank"

# Lưu 100% danh sách từ khóa kèm tần suất ra file CSV để người dùng mở Excel kiểm tra
df_ranked_all.to_csv(OUTPUT_ALL_RANKED_CSV, encoding="utf-8-sig")

print("\n" + "=" * 70)
print("✅ HOÀN THÀNH TINH CHỈNH VÀ LỌC SẠCH TỪ VỰNG!")
print(
    f"📁 Tổng số từ khóa phân biệt trích xuất được: {len(df_ranked_all):,} từ"
)
print(f"📁 File dữ liệu sau tiền xử lý:              {CLEANED_DATA_CSV}")
print(f"📁 File bảng xếp hạng toàn bộ từ khóa:       {OUTPUT_ALL_RANKED_CSV}")
print("=" * 70)

# Hiển thị nhanh Top 30 từ khóa có tần suất cao nhất để xem trước
print("\n📊 Xem trước Top 30 từ khóa trọng tâm sau tinh chỉnh:")
print(df_ranked_all.head(30).to_string())