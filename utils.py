import urllib.parse


def get_encoded_keyword(keyword_text: str) -> str:
    """Hàm nhận vào một chuỗi tiếng Hàn (hoặc bất kỳ ngôn ngữ nào)

    và trả về chuỗi đã được mã hóa URL mã UTF-8 để gắn vào API.
    """
    if not keyword_text:
        return ""
    # Tiến hành mã hóa chuỗi văn bản
    return urllib.parse.quote(keyword_text.strip())