from collections import Counter
import re
import pandas as pd
from kiwipiepy import Kiwi

# ==========================================
# 1. KHỞI TẠO KIWI & ĐĂNG KÝ TỪ ĐIỂN CHUYÊN NGÀNH
# ==========================================
print(
    "[1/5] Khởi tạo Kiwi & Đăng ký Từ điển Chuyên ngành Nghề nghiệp Tương"
    " lai..."
)
kiwi = Kiwi()

FUTURE_JOB_CUSTOM_WORDS = [
    # 1. Công nghệ mũi nhọn & Lĩnh vực mới
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
    # 2. Tên các Ngành nghề Tương lai (Job Titles)
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
    # 3. Kỹ năng, Chứng chỉ & Khái niệm Xu hướng (Skills & Trends)
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

for word in FUTURE_JOB_CUSTOM_WORDS:
  kiwi.add_user_word(word, "NNG")


# ==========================================
# 2. THIẾT LẬP TỪ DỪNG (STOPWORDS) & ĐỒNG NHẤT TỪ
# ==========================================
STRING_REPLACE_MAP = {
    r"\bAI\b": "인공지능",
    r"\bARTIFICIAL INTELLIGENCE\b": "인공지능",
    r"\bBIG DATA\b": "빅데이터",
    r"\bBIGDATA\b": "빅데이터",
    r"\bMETAVERSE\b": "메타버스",
    r"\bBLOCKCHAIN\b": "블록체인",
    r"\bIOT\b": "사물인터넷",
    r"\bNFT\b": "블록체인",
    r"인공\s+지능": "인공지능",
    r"빅\s+데이터": "빅데이터",
    r"공공\s+데이터": "공공데이터",
    r"자율\s+주행": "자율주행",
    r"스마트\s+시티": "스마트시티",
    r"스마트\s+팜": "스마트팜",
    r"머신\s+러닝": "머신러닝",
    r"딥\s+러닝": "딥러닝",
    r"자율주행차": "자율주행",
    r"자율주행자동차": "자율주행",
    r"디지털\s+트랜스포메이션": "디지털전환",
    r"디지털\s+혁신": "디지털전환",
    r"일자리": "고용",
    r"취업": "고용",
    r"자격증\s+취득": "자격증취득",
    r"\b자격\b": "자격증",  # Đồng nhất '자격' về '자격증'
    r"\b지능\b": "인공지능",  # Gộp từ đơn '지능' về '인공지능'
    r"\b공공\b": "공공데이터",  # Gộp '공공' về '공공데이터'
    r"\b복지사\b": "사회복지사",  # Ghép '복지사' thành '사회복지사'
}

JOB_STOPWORDS = set([
    # Từ ngữ hành chính / Dữ liệu go.kr
    "데이터",
    "명",
    "건",
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
    "지역",
    "한국",
    "서울",
    "경기도",
    "부산",
    "인천",
    "올해",
    "작년",
    "안내",
    "목적",
    "첨부",
    # Từ ngữ chung chung về Xu hướng / Nghiên cứu
    "직업",
    "미래",
    "유망",
    "트렌드",
    "연구",
    "조사",
    "전망",
    "변화",
    "필요",
    "증가",
    "중요",
    "사회",
    "시대",
    "분야",
    "역량",
    "인재",
    "육성",
    "교육",
    "학습",
    "과정",
    "발전",
    "추진",
    "비전",
    "향후",
    "가능",
    "모습",
    "영향",
    "상황",
    "단계",
    "기반",
    # Stopwords chung chung từ các đợt kiểm định trước
    "사람",
    "생각",
    "시간",
    "다양",
    "자료",
    "활용",
    "준비",
    "운영",
    "서비스",
    "기관",
    "기업",
    "산업",
    "기술",
    "경우",
    "정도",
    "위해",
    "통해",
    "대해",
    "부분",
    "가지",
    "이용",
    "확인",
    "진행",
    "실시",
    "작성",
    "등록",
    "신청",
    "방법",
    "문제",
    "시작",
    "이상",
    "체계",
    "결과",
    "내용",
    "주요",
    "개선",
    "확대",
    "강화",
    "구축",
    "마련",
    "필요성",
    "역할",
    "포함",
    # [CẬP NHẬT MỚI NHẤT] Lọc triệt để các từ rác phát hiện từ word_frequency_ranked.csv
    "자신",
    "활동",
    "범위",
    "선택",
    "시설",
    "센터",
    "상담",
    "기회",
    "개인",
    "계획",
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
    # [CẬP NHẬT RANK 41-100] Lọc các từ rác & từ quá chung chung
    "이번",
    "파일",
    "이유",
    "사항",
    "일반",
    "대표",
]
)


# ==========================================
# 3. HÀM XỬ LÝ LÀM SẠCH VÀ TRÍCH XUẤT DANH TỪ
# ==========================================
def preprocess_korean_text(text):
  if not isinstance(text, str) or not text.strip():
    return ""

  text = text.upper()

  for pattern, replacement in STRING_REPLACE_MAP.items():
    text = re.sub(pattern, replacement, text)

  text = re.sub(r"[^가-힣A-Z0-9\s]", " ", text)
  tokens = kiwi.tokenize(text)

  extracted_keywords = []
  for token in tokens:
    if token.tag in ["NNG", "NNP"]:
      word = token.form.strip()

      if len(word) < 2:
        continue

      if word not in JOB_STOPWORDS:
        extracted_keywords.append(word)

  return " ".join(extracted_keywords)


# ==========================================
# 4. TIẾN HÀNH THỰC THI TRÊN FILE CSV MASTER
# ==========================================
INPUT_CSV = "combined_final_data.csv"
OUTPUT_PREPROCESSED_CSV = "preprocessed_data_for_network.csv"

print(f"[2/5] Đang đọc file CSV Master ('{INPUT_CSV}')...")
df = pd.read_csv(INPUT_CSV, dtype=str)

print("[3/5] Đang tổng hợp văn bản Tiêu đề + Nội dung...")
content_col = None
if "Nội Dung Chi Tiết" in df.columns:
  content_col = "Nội Dung Chi Tiết"
elif "Nội Dung" in df.columns:
  content_col = "Nội Dung"

title_text = df["Tiêu Đề"].fillna("") if "Tiêu Đề" in df.columns else ""
content_text = df[content_col].fillna("") if content_col else ""

df["Full_Text"] = title_text.astype(str) + " " + content_text.astype(str)

print(
    f"[4/5] Đang thực hiện phân tích hình thái học trên {len(df)} dòng dữ"
    " liệu..."
)

df["Extracted_Keywords"] = df["Full_Text"].apply(preprocess_korean_text)
df.drop(columns=["Full_Text"], inplace=True)


# ==========================================
# 5. XUẤT FILE KẾT QUẢ & THỐNG KÊ TOP 40 KEYWORDS
# ==========================================
print(f"[5/5] Đang lưu kết quả ra file '{OUTPUT_PREPROCESSED_CSV}'...")
df.to_csv(OUTPUT_PREPROCESSED_CSV, index=False, encoding="utf-8-sig")

all_words = " ".join(df["Extracted_Keywords"].dropna()).split()
word_counts = Counter(all_words)

print("\n" + "=" * 65)
print("📊 BÁO CÁO KIỂM ĐỊNH KẾT QUẢ TIỀN XỬ LÝ MỚI (TOP 40 KEYWORDS)")
print("=" * 65)

top_40 = word_counts.most_common(40)
for rank, (word, count) in enumerate(top_40, start=1):
  print(f"{rank:>2}. {word:<18}: {count:,} lần")

print("=" * 65)