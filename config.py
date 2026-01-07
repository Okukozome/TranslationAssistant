# config.py
from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv()

# 腾讯云配置
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY")
REGION = os.getenv("REGION", "ap-guangzhou")

# 数据库配置
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD", ""),
    'database': os.getenv("DB_NAME", "trans_assistant")
}

# 语言和音色映射
LANG_MAP = {
    '中文': 'zh', '英语': 'en', '日语': 'ja', '韩语': 'ko',
    '法语': 'fr', '德语': 'de', '西班牙语': 'es'
}
VOICE_MAP = {
    '智瑜 (情感女声)': 101001,
    '智聆 (通用女声)': 101002,
    '智美 (客服女声)': 101003,
    '智云 (通用男声)': 101004,
    'WeJack (英文男声)': 101050
}