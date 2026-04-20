# app/core/logger.py
import logging
import sys
import json

# 自訂 JSON formatter（讓 log 可被 ELK / GCP parsing）
class JsonFormatter(logging.Formatter):
    def format(self, record):
        """
        將 log record 轉為 JSON 格式（structured logging）
        好處：
        - 可被 logging 系統解析（ELK / Cloud Logging）
        - 可以用 key 查詢（例如 request_id）
        """

        log_record = {
            "time": self.formatTime(record),     # 時間
            "level": record.levelname,           # INFO / ERROR
            "logger": record.name,               # logger 名稱（app.system / app.biz）
            "message": record.msg,               # 原始訊息
        }

        # 如果 message 本身是 dict（推薦用法），就 merge 進去
        if isinstance(record.msg, dict):
            log_record.update(record.msg)

        return json.dumps(log_record, ensure_ascii=False)


def setup_app_logging():
    """
    初始化整個應用程式的 logging 設定

    設計重點：
    - 所有 logger 統一輸出格式（JSON）
    - 避免使用 uvicorn 預設 logger
    - 支援分層 logger（system / business / audit）
    """

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # 建立多個 logger（分層）
    for name in ["app", "app.system", "app.biz", "app.audit"]:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # 清空舊 handler（避免重複輸出）
        logger.handlers = []

        logger.addHandler(handler)

        # 關閉向上傳遞（避免重複 log 到 root logger）
        logger.propagate = False


# 提供給其他模組直接 import 使用
system_logger = logging.getLogger("app.system")   # 系統流程（middleware）
business_logger = logging.getLogger("app.biz")    # 業務行為（訂單/商品）
audit_logger = logging.getLogger("app.audit")     # 審計紀錄（準備寫 DB）