#backend\app\core\sanitizer.py
import bleach

# 由於我們只允許純文本輸入欄位，我們將使用 bleach 移除所有 HTML 標籤。
# 如果未來需要允許富文本（如加粗、連結），則需要修改 tags 和 attributes 的白名單。

def sanitize_user_input(html_content: str) -> str:
    """
    清理使用者輸入的內容，移除所有 HTML 標籤，防止 XSS 攻擊。
    """
    if html_content is None:
        return ""
        
    allowed_tags = [] # 允許的標籤白名單：空，只允許純文本
    allowed_attrs = {} # 允許的屬性白名單：空
    
    # 執行淨化
    clean_text = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True # 移除不允許的標籤
    )
    return clean_text

# 為了確保資料類型一致性，可以新增一個用於整數/浮點數欄位的簡易淨化
def sanitize_number_input(data: any) -> any:
    """
    處理數字輸入，確保為純淨值。
    """
    return data # 在 FastAPI 中通常由 Pydantic 處理類型轉換，這裡作為一個佔位符。
