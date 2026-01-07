# tencent_ai.py
import base64
import time
import hashlib
import os
import tempfile
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models as ocr_models
from tencentcloud.tmt.v20180321 import tmt_client, models as tmt_models
from tencentcloud.tts.v20190823 import tts_client, models as tts_models
from config import TENCENT_SECRET_ID, TENCENT_SECRET_KEY, REGION


class TencentAIService:
    """
    腾讯云 AI 服务类：封装了 OCR 文字识别、机器翻译 (MT) 和 语音合成 (TTS) 的相关接口。
    """

    def __init__(self):
        """
        初始化方法：使用 config.py 中的密钥和地域信息配置腾讯云认证对象及客户端配置。
        """
        # 初始化身份认证对象
        self.cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        # 配置 HTTP 选项（设置 OCR 服务域名）
        self.httpProfile = HttpProfile()
        self.httpProfile.endpoint = "ocr.tencentcloudapi.com"
        # 配置客户端通用属性
        self.clientProfile = ClientProfile()
        self.clientProfile.httpProfile = self.httpProfile

    def ocr_image(self, image_path):
        """
        图片文字识别 (OCR)。
        :param image_path: 本地图片文件的路径
        :return: 识别出的文字内容（多行文本），若失败则返回错误信息字符串。
        """
        try:
            # 读取图片并转换为 Base64 编码
            with open(image_path, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode("utf-8")

            # 实例化 OCR 客户端对象
            client = ocr_client.OcrClient(self.cred, REGION, self.clientProfile)
            # 构造高精度 OCR 请求
            req = ocr_models.GeneralAccurateOCRRequest()
            req.ImageBase64 = base64_data

            # 调用接口获取响应
            resp = client.GeneralAccurateOCR(req)

            # 提取所有检测到的文本行
            text_results = []
            for detection in resp.TextDetections:
                text_results.append(detection.DetectedText)
            return "\n".join(text_results)
        except TencentCloudSDKException as err:
            # 捕获腾讯云 SDK 异常
            return f"OCR Error: {err}"

    def translate_text(self, text, target_lang, source_lang='auto'):
        """
        文本翻译 (MT)。
        :param text: 待翻译的原文
        :param target_lang: 目标语言代码（如 'en', 'ja' 等）
        :param source_lang: 源语言代码，默认为 'auto' (自动识别)
        :return: 翻译后的目标文本，若失败则返回错误提示。
        """
        try:
            # 实例化翻译客户端
            client = tmt_client.TmtClient(self.cred, REGION)
            # 构造翻译请求
            req = tmt_models.TextTranslateRequest()
            req.SourceText = text
            req.Source = source_lang
            req.Target = target_lang
            req.ProjectId = 0  # 默认项目 ID

            # 执行翻译
            resp = client.TextTranslate(req)
            return resp.TargetText
        except TencentCloudSDKException as err:
            return f"Translate Error: {err}"

    def text_to_speech(self, text, voice_type):
        """
        语音合成 (TTS) - 重构版。
        功能优化：
        1. 使用 MD5 哈希生成文件名，避免重复请求和文件锁冲突。
        2. 使用系统临时目录存储音频，避免污染项目目录。
        3. 去除了上个版本 100 字符的硬性长度限制。

        :param text: 待转语音的文本内容
        :param voice_type: 音色 ID
        :return: 生成的 MP3 文件路径，若失败则返回 None。
        """
        try:
            # 生成唯一的哈希文件名 (基于文本内容和音色)
            # 这样相同的文本和音色组合不会重复调用 API，且不会导致文件写入锁死
            hash_str = f"{text}_{voice_type}"
            file_hash = hashlib.md5(hash_str.encode('utf-8')).hexdigest()

            # 使用系统临时目录
            temp_dir = tempfile.gettempdir()
            file_name = f"tts_{file_hash}.mp3"
            file_path = os.path.join(temp_dir, file_name)

            # 检查缓存：如果文件已存在，直接返回路径（防抖动 + 节省额度 + 避免写入冲突）
            if os.path.exists(file_path):
                print(f"TTS Cache Hit: {file_path}")
                return file_path

            # 实例化 TTS 客户端 (仅在缓存未命中时执行)
            client = tts_client.TtsClient(self.cred, REGION)
            req = tts_models.TextToVoiceRequest()
            req.Text = text
            req.SessionId = str(int(time.time()))
            req.VoiceType = voice_type
            req.ModelType = 1
            req.Codec = "mp3"

            # 获取响应并写入临时文件
            resp = client.TextToVoice(req)
            if resp.Audio:
                audio_data = base64.b64decode(resp.Audio)
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                return file_path
            return None

        except TencentCloudSDKException as err:
            print(f"TTS Error: {err}")
            return None
        except Exception as e:
            print(f"System Error: {e}")
            return None