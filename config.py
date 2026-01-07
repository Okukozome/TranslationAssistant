# config.py

# 腾讯云配置
TENCENT_SECRET_ID = "YOUR_SECRET_ID"
TENCENT_SECRET_KEY = "YOUR_SECRET_KEY"
REGION = "ap-guangzhou"

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'trans_assistant'
}

# 语言映射
LANG_MAP = {
    '中文': 'zh', '英语': 'en', '日语': 'ja', '韩语': 'ko',
    '法语': 'fr', '德语': 'de', '西班牙语': 'es'
}

# 音色映射
VOICE_MAP = {
    '智瑜 (情感女声)': 101001,
    '智聆 (通用女声)': 101002,
    '智美 (客服女声)': 101003,
    '智云 (通用男声)': 101004,
    'WeJack (英文男声)': 101050
}