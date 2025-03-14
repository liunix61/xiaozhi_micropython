import subprocess
import socket
import os
import time
import re
import wave
import struct
import logging
import soundfile as sf
import edge_tts
from openai import OpenAI
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class INMP441ToWAV:
    def __init__(self):
        self.SAMPLE_RATE = 16000
        self.BITS = 16
        self.CHANNELS = 1
        self.BUFFER_SIZE = 4096

    def receive_inmp441_data(self, conn):
        audio_data = b''
        while True:
            header = conn.recv(4)
            if not header:
                break
            data_len = struct.unpack('<I', header)[0]
            data = b''
            while len(data) < data_len:
                packet = conn.recv(data_len - len(data))
                if not packet:
                    break
                data += packet
            if data_len == 0:
                if audio_data:
                    self.save_inmp441_wav(audio_data)
                    audio_data = b''
                    return "recording_1.wav"
            else:
                audio_data += data

    def save_inmp441_wav(self, data):
        filename = "recording_1.wav"
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(self.BITS // 8)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(data)
        logging.info(f"已保存录音文件：{filename}")


class FunasrSpeechToText:
    def __init__(self):
        self.model = AutoModel(model="iic/SenseVoiceSmall")

    def recognize_speech(self, audio_path):
        try:
            speech, sample_rate = sf.read(audio_path)
            res = self.model.generate(input=speech, input_fs=sample_rate, language="zn", is_final=False,
                                      chunk_size=[0, 10, 5], encoder_chunk_look_back=4, decoder_chunk_look_back=1)
            text = rich_transcription_postprocess(res[0]["text"])
            return text
        except Exception as e:
            logging.error(f"API错误：{str(e)}")
            return None


class DeepSeekReply:
    def __init__(self):
        self.api_key = "sk-qibubtyemfiuqefhpzhfvhdiyddmapedvxeltcooasezpvha"
        self.base_url = "https://api.siliconflow.cn/v1"
        self.role_setting = '（习惯简短表达）'
        self.deepseek_model = 'deepseek-ai/DeepSeek-V2.5'

    def get_deepseek_response(self, text):
        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(model=self.deepseek_model,
                                                      messages=[{'role': 'user', 'content': f"{text}{self.role_setting}"}],
                                                      stream=True)
            content_list = [chunk.choices[0].delta.content for chunk in response]
            processed_sentence = ''.join([element for element in content_list if element])
            cleaned_text = re.sub(r'### |^- \*\*|\*\*', '', processed_sentence, flags=re.MULTILINE)
            return cleaned_text
        except Exception as e:
            logging.error(f"API错误：{str(e)}")
            return None


class EdgeTTSTextToSpeech:
    def __init__(self):
        self.voice = "zh-CN-XiaoxiaoNeural"
        self.rate = '+16%'
        self.volume = '+0%'
        self.pitch = '+0Hz'
        self.communicate_path = "response.mp3"

    def generate_audio(self, text):
        try:
            communicate = edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate,
                                               volume=self.volume, pitch=self.pitch)
            communicate.save_sync(self.communicate_path)
            return self.communicate_path
        except Exception as e:
            logging.error(f"TTS生成失败: {str(e)}")
            return None


class FFmpegToWav:
    def __init__(self, sample_rate, channels, bit_depth):
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth

    def convert_to_wav(self, input_file, output_file):
        codec = 'pcm_s16le' if self.bit_depth == 16 else 'pcm_s24le'
        try:
            subprocess.run(['ffmpeg', '-i', input_file, '-vn', '-acodec', codec, '-ar', str(self.sample_rate),
                            '-ac', str(self.channels), '-y', output_file], check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            logging.info(f"转换成功: {output_file}")
        except subprocess.CalledProcessError as e:
            logging.error(f"转换失败: {e.stderr.decode('utf-8')}")
        except FileNotFoundError:
            logging.error("错误: 未找到 FFmpeg，请确保已正确安装并添加到系统 PATH")


class MAX98357AudioPlay:
    def __init__(self):
        self.chunk = 1024

    def send_wav_file(self, conn, wav_file_path):
        with open(wav_file_path, "rb") as audio_file:
            audio_file.seek(44)
            while chunk := audio_file.read(self.chunk):
                conn.sendall(chunk)
        time.sleep(0.1)
        conn.sendall("END_OF_STREAM\n".encode())
        logging.info("回复音频已发送")


class XiaoZhi_Ai_TCPServer:
    def __init__(self, host="0.0.0.0", port=8888, save_path="audio/received_audio.wav"):
        self.host = host
        self.port = port
        self.received_audio_filename = save_path
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.fstt = FunasrSpeechToText()
        self.dsr = DeepSeekReply()
        self.etts = EdgeTTSTextToSpeech()
        self.mapl = MAX98357AudioPlay()
        self.fftw = FFmpegToWav(sample_rate=8000, channels=1, bit_depth=16)
        self.inmp441tw = INMP441ToWAV()

    def start(self):
        with self.socket:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            local_ip = socket.gethostbyname(socket.gethostname())
            logging.info(f"\n=== 小智AI对话机器人服务器_V1.1 已启动 ===\nIP端口为：{local_ip}:{self.port}\n等待客户端的连接...")
            with ThreadPoolExecutor() as executor:
                while True:
                    conn, addr = self.socket.accept()
                    logging.info(f"接收到来自 {addr} 的持久连接")
                    executor.submit(self.handle_client, conn, addr)

    def handle_client(self, conn, addr):
        with conn:
            while True:
                try:
                    inmp441wav_path = self.inmp441tw.receive_inmp441_data(conn)
                    fstt_text = self.fstt.recognize_speech(inmp441wav_path)
                    logging.info(f"FunASR 语音识别---：{fstt_text}")
                    if fstt_text.strip():
                        gdr_text = self.dsr.get_deepseek_response(fstt_text)
                        logging.info(f"DeepSeek 的回复---：{gdr_text}")
                        tts_path = self.etts.generate_audio(gdr_text)
                        logging.info(f"EdgeTTS 音频地址---：{tts_path}")
                        self.fftw.convert_to_wav(tts_path, 'output.wav')
                        self.mapl.send_wav_file(conn, 'output.wav')
                    else:
                        logging.info('FunASR语音识别为空，继续讲话....')
                        time.sleep(0.03)
                        conn.sendall("END_OF_STREAM\n".encode())
                except ConnectionError as e:
                    logging.error(f"连接异常: {e}")
                    break
                except Exception as e:
                    logging.error(f"处理错误: {e}")
                    continue


if __name__ == "__main__":
    server = XiaoZhi_Ai_TCPServer()
    server.start()