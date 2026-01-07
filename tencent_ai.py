# tencent_ai.py
import base64
import time
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
        语音合成 (TTS)。
        :param text: 待转语音的文本内容
        :param voice_type: 音色 ID（参考 VOICE_MAP）
        :return: 生成的 MP3 文件路径，若失败则返回 None。
        """
        try:
            # 为了演示，对输入文本长度进行限制
            if len(text) > 100: text = text[:100]

            # 实例化 TTS 客户端
            client = tts_client.TtsClient(self.cred, REGION)
            # 构造语音合成请求
            req = tts_models.TextToVoiceRequest()
            req.Text = text
            req.SessionId = str(int(time.time())) # 使用时间戳作为会话 ID
            req.VoiceType = voice_type
            req.ModelType = 1
            req.Codec = "mp3"

            # 获取响应
            resp = client.TextToVoice(req)
            if resp.Audio:
                # 将返回的 Base64 语音数据解码并保存为本地文件
                audio_data = base64.b64decode(resp.Audio)
                file_path = "output_audio.mp3"
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                return file_path
            return None
        except TencentCloudSDKException as err:
            print(f"TTS Error: {err}")
            return None