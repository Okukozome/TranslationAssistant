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
    def __init__(self):
        self.cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        self.httpProfile = HttpProfile()
        self.httpProfile.endpoint = "ocr.tencentcloudapi.com"
        self.clientProfile = ClientProfile()
        self.clientProfile.httpProfile = self.httpProfile

    def ocr_image(self, image_path):
        try:
            with open(image_path, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode("utf-8")

            client = ocr_client.OcrClient(self.cred, REGION, self.clientProfile)
            req = ocr_models.GeneralAccurateOCRRequest()
            req.ImageBase64 = base64_data

            resp = client.GeneralAccurateOCR(req)

            text_results = []
            for detection in resp.TextDetections:
                text_results.append(detection.DetectedText)
            return "\n".join(text_results)
        except TencentCloudSDKException as err:
            return f"OCR Error: {err}"

    def translate_text(self, text, target_lang, source_lang='auto'):
        try:
            client = tmt_client.TmtClient(self.cred, REGION)
            req = tmt_models.TextTranslateRequest()
            req.SourceText = text
            req.Source = source_lang
            req.Target = target_lang
            req.ProjectId = 0

            resp = client.TextTranslate(req)
            return resp.TargetText
        except TencentCloudSDKException as err:
            return f"Translate Error: {err}"

    def text_to_speech(self, text, voice_type):
        try:
            if len(text) > 100: text = text[:100]  # Demo limit

            client = tts_client.TtsClient(self.cred, REGION)
            req = tts_models.TextToVoiceRequest()
            req.Text = text
            req.SessionId = str(int(time.time()))
            req.VoiceType = voice_type
            req.ModelType = 1
            req.Codec = "mp3"

            resp = client.TextToVoice(req)
            if resp.Audio:
                audio_data = base64.b64decode(resp.Audio)
                file_path = "output_audio.mp3"
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                return file_path
            return None
        except TencentCloudSDKException as err:
            print(f"TTS Error: {err}")
            return None