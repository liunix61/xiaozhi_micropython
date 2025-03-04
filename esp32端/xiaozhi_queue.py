import subprocess
import socket, os, time, re, wave, struct
import base64
import requests
import json
from pydub import AudioSegment
from zhipuai import ZhipuAI
import time
import uuid
import io
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

# 全局变量用于控制线程终止
running = True

# 创建全局队列用于在线程间传递数据
audio_data_queue = queue.Queue()
text_queue = queue.Queue()
response_queue = queue.Queue()
audio_output_queue = queue.Queue()

class ByteDanceTTS:
    def __init__(self, appid="xxx", access_token="xxx", cluster="xxx", voice_type="BV064_streaming", rate="16000"):
        self.appid = appid
        self.access_token = access_token
        self.cluster = cluster
        self.voice_type = voice_type
        self.rate = rate
        self.host = "openspeech.bytedance.com"
        self.api_url = f"https://{self.host}/api/v1/tts"
        self.header = {"Authorization": f"Bearer;{self.access_token}"}

    def generate_tts(self, client_socket, text):
        request_json = {
            "app": {
                "appid": self.appid,
                "token": "access_token",
                "cluster": self.cluster
            },
            "user": {
                "uid": "xxx"
            },
            "audio": {
                "voice_type": self.voice_type,
                "rate": self.rate,
                "encoding": "wav",
                "speed_ratio": 0.9,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }

        try:
            resp = requests.post(self.api_url, json.dumps(request_json), headers=self.header)
            if "data" in resp.json():
                data = resp.json()["data"]
                audio_data = base64.b64decode(data)
                audio_output_queue.put(audio_data)
                print("ByteDance TTS音频已生成并加入队列")
                return True
            else:
                print("Failed to generate TTS audio.")
                return False
        except Exception as e:
            print(f"⚠️ ByteDance TTS生成失败: {str(e)}")
            return False

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
        self._get_access_token()  # 初始化时就获取token

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
                print("无效的访问令牌")
                return False
            print("成功获取百度语音识别Token")
            return True
        except requests.exceptions.RequestException as e:
            print(f"获取Access Token失败: {str(e)}")
            return False

    def recognize(self, audio_data):
        """
        语音识别主方法
        :param audio_data: 音频数据
        :return: 识别结果文本
        """
        try:
            # 确保有访问令牌
            if not self.access_token:
                if not self._get_access_token():
                    return None
            
            # 编码音频数据
            if isinstance(audio_data, bytes) and audio_data[:4] == b'RIFF':
                # 这是WAV文件，需要跳过文件头
                audio_data_body = audio_data[44:]
            else:
                audio_data_body = audio_data
                
            speech_base64 = base64.b64encode(audio_data_body).decode('utf-8')
            
            # 构造请求参数
            payload = json.dumps({
                "format": "wav",
                "rate": 8000,
                "channel": 1,
                "cuid": "xxx",
                "speech": speech_base64,
                "len": len(audio_data_body),
                "token": self.access_token
            }, ensure_ascii=False)
            
            # 发送请求并处理响应
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.recognize_url, 
                headers=headers, 
                data=payload, 
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            if 'result' in result:
                recognized_text = result['result'][0]
                print(f"百度语音识别结果: {recognized_text}")
                return recognized_text
            if 'err_msg' in result and result['err_msg'] != 'success.':
                print(f"识别错误: {result['err_msg']}")
                return None
            print("未知的API响应格式")
            return None
            
        except Exception as e:
            print(f"⚠️ 百度语音识别API错误：{str(e)}")
            return None

class ZhipuAIClient:
    def __init__(self, api_key="xxx"):
        self.client = ZhipuAI(api_key=api_key)
        print("ChatGLM客户端初始化成功")

    def generate_slogan(self, product_info):
        try:
            print(f"向ChatGLM发送请求: {product_info}")
            history.append({"role": "user", "content": product_info})
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=history,
                stream=True,
            )
            content_list = []
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    content_list.append(content)
            
            processed_sentence = ''.join(content_list)
            cleaned_text = re.sub(r'### |^- \*\*|\*\*', '', processed_sentence, flags=re.MULTILINE)
            history.append({"role": "assistant", "content": cleaned_text})
            print(f"ChatGLM响应: {cleaned_text}")
            return cleaned_text
        except Exception as e:
            print(f"⚠️ ChatGLM API错误：{str(e)}")
            return None

class AudioDataCollector:
    def __init__(self):
        self.SAMPLE_RATE = 16000
        self.BITS = 16
        self.CHANNELS = 1
        self.BUFFER_SIZE = 4096

    def receive_audio_data(self, conn):
        """接收音频数据并返回完整的WAV数据"""
        audio_data = b''
        try:
            # 读取包头
            header = conn.recv(4)
            if not header or len(header) < 4:
                return None
                
            data_len = struct.unpack('<I', header)[0]
            if data_len == 0:  # 结束标记
                return None
                
            # 读取数据体
            data = b''
            remaining = data_len
            while remaining > 0:
                packet = conn.recv(min(remaining, self.BUFFER_SIZE))
                if not packet:
                    break
                data += packet
                remaining -= len(packet)
                
            if len(data) == data_len:
                audio_data = data
                
                # 创建WAV文件头
                wav_header = self.create_wav_header(len(audio_data))
                complete_wav = wav_header + audio_data
                return complete_wav
            return None
                
        except Exception as e:
            print(f"接收音频数据错误: {e}")
            return None

    def create_wav_header(self, data_length):
        """创建WAV文件头"""
        header = bytearray()
        # RIFF header
        header.extend(b'RIFF')
        header.extend(struct.pack('<I', data_length + 36))  # 文件长度
        header.extend(b'WAVE')
        # fmt chunk
        header.extend(b'fmt ')
        header.extend(struct.pack('<I', 16))  # chunk size
        header.extend(struct.pack('<H', 1))  # PCM format
        header.extend(struct.pack('<H', self.CHANNELS))  # channels
        header.extend(struct.pack('<I', self.SAMPLE_RATE))  # sample rate
        bytes_per_second = self.SAMPLE_RATE * self.CHANNELS * (self.BITS // 8)
        header.extend(struct.pack('<I', bytes_per_second))  # bytes per second
        block_align = self.CHANNELS * (self.BITS // 8)
        header.extend(struct.pack('<H', block_align))  # block align
        header.extend(struct.pack('<H', self.BITS))  # bits per sample
        # data chunk
        header.extend(b'data')
        header.extend(struct.pack('<I', data_length))  # data size
        return header

class MAX98357AudioPlay:
    def __init__(self):
        self.chunk = 1024

    def send_audio_data(self, client_socket, audio_data):
        """将音频数据分块发送到客户端"""
        try:
            # 对于WAV文件，跳过前44字节的文件头
            if audio_data[:4] == b'RIFF':
                audio_data = audio_data[44:]
            
            # 分块发送音频数据
            for i in range(0, len(audio_data), self.chunk):
                chunk = audio_data[i:i+self.chunk]
                if not chunk:
                    break
                client_socket.sendall(chunk)
            
            time.sleep(0.1)
            client_socket.sendall("END_OF_STREAM\n".encode())
            print("回复音频已完成发送")
            return True
        except Exception as e:
            print(f"发送音频数据错误: {e}")
            try:
                client_socket.sendall("END_OF_STREAM\n".encode())
            except:
                pass
            return False

class XiaoZhi_Ai_TCPServer:
    def __init__(self, host="0.0.0.0", port=8888):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # 初始化组件
        self.speech_recognizer = SpeechRecognizer()
        self.ai_client = ZhipuAIClient()
        self.tts_engine = ByteDanceTTS()
        self.audio_player = MAX98357AudioPlay()
        self.audio_collector = AudioDataCollector()
        
        # 活跃连接列表
        self.active_connections = {}
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)

    def start(self):
        """启动服务器"""
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        local_ip = socket.gethostbyname(socket.gethostname())
        print("\n=== 小智AI对话机器人服务器_V2.0 已启动 ===")
        print(f"IP端口为：{local_ip}:{self.port}")
        print("等待客户端的连接...")
        
        try:
            while True:
                conn, addr = self.socket.accept()
                print(f"接收到来自 {addr} 的新连接")
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("服务器正在关闭...")
        finally:
            global running
            running = False
            self.socket.close()
            self.executor.shutdown(wait=False)

    def handle_client(self, conn, addr):
        """处理单个客户端连接"""
        client_id = f"{addr[0]}:{addr[1]}"
        self.active_connections[client_id] = conn
        
        try:
            while running:
                # 接收音频数据
                audio_data = self.audio_collector.receive_audio_data(conn)
                if not audio_data:
                    # 检查连接是否仍然有效
                    try:
                        conn.sendall(b"ping")
                        time.sleep(0.5)
                        continue
                    except:
                        print(f"客户端 {addr} 已断开连接")
                        break
                
                # 识别语音
                text = self.speech_recognizer.recognize(audio_data)
                if not text:
                    print("语音识别失败，继续等待下一段录音")
                    conn.sendall("END_OF_STREAM\n".encode())  # 告诉客户端此次对话结束
                    continue
                
                print(f"从客户端 {addr} 识别到文本: {text}")
                
                # 获取AI回复
                response = self.ai_client.generate_slogan(text)
                if not response:
                    print("生成AI回复失败")
                    conn.sendall("END_OF_STREAM\n".encode())
                    continue
                
                print(f"AI回复给客户端 {addr}: {response}")
                
                # 生成语音
                self.tts_engine.generate_tts(conn, response)
                
                # 从队列获取生成的音频
                try:
                    audio_data = audio_output_queue.get(timeout=10)
                    # 发送音频数据
                    self.audio_player.send_audio_data(conn, audio_data)
                    audio_output_queue.task_done()
                except queue.Empty:
                    print("TTS生成超时")
                    conn.sendall("END_OF_STREAM\n".encode())
        except Exception as e:
            print(f"处理客户端 {addr} 时出错: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            print(f"连接 {addr} 已关闭")

if __name__ == "__main__":
    # 初始化历史对话
    history = [
        {"role": "system", "content": "回答问题控制在120字以内；你是一个叫小智的台湾机车女孩，声音超好听。"}
    ]
    # 启动服务器
    server = XiaoZhi_Ai_TCPServer()
    server.start()
