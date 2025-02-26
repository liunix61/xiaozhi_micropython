# 客户端与服务器可在单次TCP连接，实现无限轮次对话，直至主动断开。
import subprocess
import socket, os, time,re,wave,struct
import soundfile as sf  # 添加音频读取库
import edge_tts
from openai import OpenAI
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

import base64
import requests
import json

#百度ASR 替换为自己的百度api—key，secret-key
class SpeechRecognizer:
    """百度语音识别API封装类"""

    def __init__(self, api_key="xxx", secret_key="xxx"):
        """
        初始化语音识别器
        :param api_key: 百度API Key
        :param secret_key: 百度Secret Key
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.token_url = "https://aip.baidubce.com/oauth/2.0/token"
        self.recognize_url = "https://vop.baidubce.com/server_api"
        self.access_token = None

    def _get_access_token(self):
        """获取百度语音API的访问令牌"""
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        try:
            response = requests.post(self.token_url, params=params, timeout=5)
            response.raise_for_status()
            self.access_token = response.json().get("access_token")
            if not self.access_token:
                raise ValueError("无效的访问令牌")
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取Access Token失败: {str(e)}")

    def _validate_audio_file(self, file_path):
        """验证音频文件有效性"""
        if not os.path.exists(file_path):
            raise FileNotFoundError("音频文件不存在")
        if not file_path.lower().endswith('.wav'):
            raise ValueError("仅支持WAV格式音频文件")
        if os.path.getsize(file_path) > 1024 * 1024 * 10:  # 10MB限制
            raise ValueError("音频文件大小超过10MB限制")

    def _encode_audio_to_base64(self, file_path):
        """将WAV文件编码为Base64"""
        try:
            with open(file_path, "rb") as audio_file:
                audio_data = audio_file.read()
                return base64.b64encode(audio_data).decode('utf-8')
        except IOError as e:
            raise Exception(f"文件读取失败: {str(e)}")

    def _send_recognition_request(self, payload):
        """发送语音识别API请求"""
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(
                self.recognize_url, 
                headers=headers, 
                data=payload, 
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")

    def recognize(self, client_socket, audio_path):
        """
        语音识别主方法
        :param audio_path: 音频文件路径
        :return: 识别结果文本
        """
        try:
            # 文件验证
            self._validate_audio_file(audio_path)
            
            # 获取访问令牌
            if not self.access_token:
                self._get_access_token()
            
            # 编码音频文件
            speech_base64 = self._encode_audio_to_base64(audio_path)
            
            # 构造请求参数
            payload = json.dumps({
                "format": "wav",
                "rate": 8000,
                "channel": 1,
                "cuid": "5NNHy4FsIbdFu1qOU8T6c559oHh4bbp3",
                "speech": speech_base64,
                "len": os.path.getsize(audio_path),
                "token": self.access_token
            }, ensure_ascii=False)
            
            # 发送请求并处理响应
            result = self._send_recognition_request(payload)
            
            if 'result' in result:
                return result['result'][0]
            if 'err_msg' in result:
                raise Exception(f"识别错误: {result['err_msg']}")
            raise Exception("未知的API响应格式")
            
        except Exception as e:
            print(f"⚠️ API错误：{str(e)}")
            time.sleep(0.03)# 结束客户端等待服务器返回播放数据
            client_socket.sendall("END_OF_STREAM\n".encode())


# FunASR语音识别，语音转文字
class INMP441ToWAV:
    def __init__(self):
        self.SAMPLE_RATE = 16000
        self.BITS = 16
        self.CHANNELS = 1
        self.BUFFER_SIZE = 4096


    def receive_inmp441_data(self, conn):
        audio_data = b''  # 用于累积音频数据的缓冲区
        while True:
            # 读取包头
            header = conn.recv(4)
            if not header:
                break
            data_len = struct.unpack('<I', header)[0]
            # 读取数据体
            data = b''
            while len(data) < data_len:
                packet = conn.recv(data_len - len(data))
                if not packet:
                    break
                data += packet
            if data_len == 0:  # 结束标记
                if audio_data:
                    self.save_inmp441_wav(audio_data)
                    audio_data = b''  # 清空缓冲区
                    return "recording_1.wav"
            else:
                audio_data += data  # 累积音频数据

    def save_inmp441_wav(self, data):
        filename = "recording_1.wav"
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(self.BITS // 8)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(data)
        print(f"已保存录音文件：{filename}")


# FunASR语音识别，语音转文字
class FunasrSpeechToText:
    def __init__(self):
        # 正确加载模型
        self.model = AutoModel(
            model="iic/SenseVoiceSmall",  # 使用标准模型ID而非本地路径
            # model="iic/paraformer-zh-streaming",  # 使用标准模型ID而非本地路径
        )

    def recognize_speech(self, client_socket,audio_path):
        try:
            # 正确读取音频数据
            audio_path = audio_path  # 确保文件存在
            speech, sample_rate = sf.read(audio_path)  # 读取为numpy数组
            cache = {}
            # 使用音频数组作为输入
            res = self.model.generate(
                input=speech,  # 传入音频数据而非路径
                input_fs=sample_rate,  # 添加采样率参数
                cache=cache,
                language="zn",  # "zn", "en", "yue", "ja", "ko", "nospeech"
                is_final=False,
                chunk_size=[0, 10, 5],
                encoder_chunk_look_back=4,
                decoder_chunk_look_back=1
            )
            # print("实时结果:", res[0]['text'])
            text = rich_transcription_postprocess(res[0]["text"])
            # print('识别结果:', text)
            return str(text)

        except Exception as e:
            print(f"⚠️ API错误：{str(e)}")
            time.sleep(0.03)# 结束客户端等待服务器返回播放数据
            client_socket.sendall("END_OF_STREAM\n".encode())

# deepseek 的回复 替换为自己的deepseek-api-key  和api的base-url
class DeepSeekReply:
    def __init__(self):
        self.api_key = "sk-xxxx"
        self.base_url = "https://api.siliconflow.cn/v1"
        # self.role_setting = "（习惯简短表达，不要多行，不要回车，你是一个叫小智的温柔女朋友，声音好听，只要中文，爱用网络梗，最后抛出一个提问。）"
        # self.role_setting = "（习惯简短表达，最后抛出一个提问。）"
        # self.role_setting = "（不要多行）"
        # self.role_setting = "（你是DeepSeek-R1，由深度求索公司开发的智能助手，主要帮助您回答问题和提供信息。）"
        # self.role_setting = '（最后抛出一个提问）'
        self.role_setting = '（习惯简短表达）'
        self.deepseek_model = 'deepseek-ai/DeepSeek-V2.5'
        # self.deepseek_model = 'deepseek-ai/DeepSeek-V3'
        # self.deepseek_model = 'Qwen/Qwen2.5-7B-Instruct'
        # self.deepseek_model = 'Pro/deepseek-ai/DeepSeek-R1'

    def get_deepseek_response(self, client_socket,text):
        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            response = client.chat.completions.create(
                model=self.deepseek_model,
                messages=[{
                    'role': 'user',
                    'content': f"{text}{self.role_setting}"
                }],
                stream=True
            )
            content_list = []
            for chunk in response:
                content = chunk.choices[0].delta.content
                content_list.append(content)
            # 1. 去掉'练习', '跑步', '需要',==练习跑步需要
            processed_sentence = ''.join([element for element in content_list if element])
            # 2.去掉  ###，- **， **
            cleaned_text = re.sub(r'### |^- \*\*|\*\*', '', processed_sentence, flags=re.MULTILINE)
            return cleaned_text
        except Exception as e:
            print(f"⚠️ API错误：{str(e)}")
            # TTS生成失败，结束客户端等待服务器返回播放数据
            time.sleep(0.03)
            client_socket.sendall("END_OF_STREAM\n".encode())

# EdgeTTS文字生成语音
class EdgeTTSTextToSpeech:
    def __init__(self):
        self.voice = "zh-CN-XiaoxiaoNeural"# zh-TW-HsiaoYuNeural
        self.rate = '+16%'
        self.volume = '+0%'
        self.pitch = '+0Hz'

        self.communicate_path = "response.mp3"

    def generate_audio(self, client_socket, text):# EdgeTTS文字生成语音
        try:
            communicate = edge_tts.Communicate(
                text = text,
                voice = self.voice,
                rate = self.rate,
                volume = self.volume,
                pitch = self.pitch)
            communicate.save_sync(self.communicate_path)


            return self.communicate_path# print("语音文件已生成...")
        except Exception as e:
            print(f"⚠️ TTS生成失败: {str(e)}")
            time.sleep(0.03)# 结束客户端等待服务器返回播放数据
            client_socket.sendall("END_OF_STREAM\n".encode())

# FFmpeg 音频转换器
class FFmpegToWav:
    def __init__(self, sample_rate, channels, bit_depth):
        self.sample_rate = sample_rate
        self.channels = channels
        if bit_depth in [16, 24]:
            self.bit_depth = bit_depth
        else:
            raise ValueError("bit_depth 必须是 16 或 24")

    def convert_to_wav(self, client_socket, input_file, output_file):
        codec = 'pcm_s16le' if self.bit_depth == 16 else 'pcm_s24le'
        try:
            subprocess.run([
                    'ffmpeg',
                    '-i', input_file,  # 输入文件
                    '-vn',  # 禁用视频流
                    '-acodec', codec,  # 动态设置编码器（根据位深）
                    '-ar', str(self.sample_rate),  # 采样率
                    '-ac', str(self.channels),  # 声道数
                    '-y',  # 覆盖输出文件
                    output_file],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            print(f"转换成功: {output_file}")

        except subprocess.CalledProcessError as e:
            print(f"转换失败: {e.stderr.decode('utf-8')}")
        except FileNotFoundError:
            print("错误: 未找到 FFmpeg，请确保已正确安装并添加到系统 PATH")
            time.sleep(0.03)# 结束客户端等待服务器返回播放数据
            client_socket.sendall("END_OF_STREAM\n".encode())

# MAX98357播放声音
class MAX98357AudioPlay:
    def __init__(self):
        self.chunk = 1024 # 音频帧数（缓冲区大小）

    def send_wav_file(self, client_socket, wav_file_path):
        with open(wav_file_path, "rb") as audio_file:
            audio_file.seek(44)# 跳过前44字节的WAV文件头信息
            while True:
                chunk = audio_file.read(1024)
                if not chunk:
                    break
                client_socket.sendall(chunk)
        time.sleep(0.1)
        client_socket.sendall("END_OF_STREAM\n".encode())
        print("回复音频已发送")

# 小智AI服务器 主循环
class XiaoZhi_Ai_TCPServer:
    def __init__(self, host="0.0.0.0", port=8888, save_path="audio/received_audio.wav"):
        self.host = host
        self.port = port
        self.received_audio_filename = save_path
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.fstt = FunasrSpeechToText()# FunASR 语音识别，语音转文字
        self.fstt = SpeechRecognizer()# BaiduASR 语音识别，语音转文字
        self.dsr = DeepSeekReply()# deepseek 的回复
        self.etts = EdgeTTSTextToSpeech()# EdgeTTS 文字生成语音
        self.mapl = MAX98357AudioPlay()# MAX98357 播放音频
        self.fftw = FFmpegToWav(sample_rate=8000, channels=1, bit_depth=16)# # FFmpeg 音频转换器24100, 44100,32000
        self.inmp441tw = INMP441ToWAV()
    def start(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        local_ip = socket.gethostbyname(socket.gethostname())
        print("\n=== 小智AI对话机器人服务器_V1.1 已启动 ===")
        print(f"IP端口为：{local_ip}:{self.port}")
        print("等待客户端的连接...")
        try:
            while True:  # 外层循环接受新连接
                conn, addr = self.socket.accept()
                print(f"接收到来自 {addr} 的持久连接")
                try:
                    while True:
                        try:
                            # 接收INMP441 麦克风数据
                            inmp441wav_path = self.inmp441tw.receive_inmp441_data(conn)

                            # FunASR语音识别，语音转文字
                            fstt_text = self.fstt.recognize(conn, inmp441wav_path)
                            print("FunASR 语音识别---：", fstt_text)

                            # DeepSeek 生成回复
                            if fstt_text.strip():
                                gdr_text = self.dsr.get_deepseek_response(conn, fstt_text)
                                print("DeepSeek 的回复---：", gdr_text)

                                # EdgeTTS 文字生成语音
                                tts_path = self.etts.generate_audio(conn, gdr_text)
                                print("EdgeTTS 音频地址---：", tts_path)
                                # tts_path_file_size = os.path.getsize(tts_path)

                                # FFmpeg 音频转换器
                                self.fftw.convert_to_wav(conn, tts_path, 'output.wav')

                                # MAX98357 播放音频'audio/textlen44-43380.wav'
                                self.mapl.send_wav_file(conn, 'output.wav')  # gada
                            else:
                                print('FunASR语音识别为空，继续讲话....')
                                time.sleep(0.03)
                                conn.sendall("END_OF_STREAM\n".encode())



                        except ConnectionError as e:
                            print(f"连接异常: {e}")
                            break  # 退出内层循环，关闭连接
                        except Exception as e:
                            print(f"处理错误: {e}")
                            continue  # 继续等待下一个请求
                finally:
                    conn.close()  # 🔴 关键修改 3: 手动关闭连接
                    print(f"连接 {addr} 已关闭")
        except KeyboardInterrupt:
            print("服务器正在关闭...")
        finally:
            self.socket.close()

if __name__ == "__main__":
    server = XiaoZhi_Ai_TCPServer()
    server.start()
