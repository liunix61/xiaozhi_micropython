from machine import I2S, Pin, I2C
import time, array
import math, network, socket
import ustruct as struct

# 这是一个使用示例 This is an example of usage
import time
from machine import SPI, Pin
import st7735_buf
from easydisplay import EasyDisplay

'''
引脚连接图
    st7789       esp32s3
1    LEDA			bl
2    GND			GND
3    RESET			res
4    RS				dc
5    SDA			mosi
6    SCL			sck
7    VDD			VCC
8    CS				CS
'''

# ESP32S3 & ST7735
spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(4))
dp = st7735_buf.ST7735(width=160, height=80, spi=spi, cs=6, dc=3, res=2, rotate=1, bl=1, invert=False, rgb=False)
ed = EasyDisplay(dp, "RGB565", font="text_lite_16px_2312.v3.bmf", show=True, color=0xFFFF, clear=True)

class VoiceRecorder:
    def __init__(self):
        # INMP441 硬件参数配置
        self.INMP441_sck_pin = Pin(7)    # BCK
        self.INMP441_ws_pin = Pin(8)     # WS/LRC
        self.INMP441_sd_pin = Pin(9)     # DIN
        self.buf_size = 2048    # 减小缓冲区大小以避免内存溢出
        self.sample_rate = 8000  # 8kHz采样率
        self.bits = 16           # 每音频采样比特数
        self.format = I2S.MONO   # 改为单声道模式以减少内存使用
        self.channels = 1        # 单声道
        
        # 优化VAD参数
        self.energy_threshold = 40   # 初始阈值
        self.silence_duration = 1.5  # 减少静音持续时间(s)
        self.min_voice_duration = 0.5  # 减少最短有效语音时长(s)
        
        # 标志位
        self.is_recording = False 
        self.silence_counter = 0
        self.INMP441_is_send_wav = False
          
        # MAX98357 初始化引脚定义
        self.MAX98357_sck_pin = Pin(13)
        self.MAX98357_ws_pin = Pin(12)
        self.MAX98357_sd_pin = Pin(11)

        # 调节MAX98357 喇叭声音
        self.volume_factor = 0.53

        # 配置Wi-Fi连接信息 替换为自己的wifi信息
        self.WIFI_SSID = "zhou"
        self.WIFI_PASSWORD = "18961210318"

        # 服务器配置
        self.SERVER_IP = "192.168.1.9" #根据实际的服务器端地址
        self.SERVER_PORT = 8888

        # 初始化I2S
        self.init_i2s()    
        # 初始化连接 WiFi
        self.connect_wifi()
        # 连接到 TCP服务器
        self.sock = self.connect_socket()
 
    # 初始化I2S录音设备
    def init_i2s(self):  
        # INMP441 录音   
        self.audio_in = I2S(
            0,
            sck=self.INMP441_sck_pin,
            ws=self.INMP441_ws_pin,
            sd=self.INMP441_sd_pin,
            mode=I2S.RX,
            bits=self.bits,
            format=self.format,
            rate=self.sample_rate,
            ibuf=self.buf_size
            )
        
        # MAX98357初始化喇叭
        self.audio_out = I2S(
            1,
            sck=self.MAX98357_sck_pin,
            ws=self.MAX98357_ws_pin,
            sd=self.MAX98357_sd_pin,
            mode=I2S.TX,
            bits=16,
            format=I2S.MONO,
            rate=8000,
            ibuf=2048  # 减小缓冲区
            )
        print(f"[INIT] INMP441采样率: {self.sample_rate} INMP441缓冲区: {self.buf_size}字节")
        print("[INIT] I2S录音设备就绪")
        ed.text("[INIT] I2S录音设备就绪", 0, 0)
        time.sleep(2)
       
    # 连接 WiFi
    def connect_wifi(self):     
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected(): 
            print("正在连接WiFi ...")
            ed.text("正在连接WiFi ...", 0, 0)
            sta_if.active(True) 
            sta_if.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
            
            # 添加连接超时
            timeout = 20  # 20秒超时
            start_time = time.time()
            while not sta_if.isconnected():
                if time.time() - start_time > timeout:
                    print("WiFi连接超时，重试...")
                    ed.text("WiFi连接超时，重试...", 0, 0)
                    sta_if.disconnect()
                    time.sleep(1)
                    sta_if.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
                    start_time = time.time()
                time.sleep(0.5)
                
        print("[INIT] WiFi 连接成功!")
        print("IP地址:", sta_if.ifconfig()[0])
        ed.text(f"[INIT] WiFi 连接成功!\nIP地址:{sta_if.ifconfig()[0]}", 0, 0)
        time.sleep(2)

    # 带重试的socket连接
    def connect_socket(self):  
        print("[INIT] 正在连接服务器...")
        ed.text("[INIT] 正在连接服务器...", 0, 0)
        retry_delay = 5  # 重试间隔秒数
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.SERVER_IP, self.SERVER_PORT))
                print(f"成功连接到 {self.SERVER_IP}:{self.SERVER_PORT}")
                ed.text(f"成功连接到:\n {self.SERVER_IP}:{self.SERVER_PORT}", 0, 0)
                return sock
            except OSError as e:
                print(f"连接失败: {e}, {retry_delay}秒后重试...")
                ed.text(f"连接失败: \n{e}, \n{retry_delay}秒后重试...", 0, 0)
                time.sleep(retry_delay)

    # 优化的RMS计算
    def rms(self, data):    
        if len(data) < 2:
            return 0
            
        samples = len(data) // 2
        sum_squares = 0
        
        # 处理较大的数据块时分批计算以避免内存问题
        chunk_size = 64  # 每次处理的样本数
        for i in range(0, samples, chunk_size):
            end = min(i + chunk_size, samples)
            for j in range(i, end):
                idx = j * 2
                sample = (data[idx+1] << 8) | data[idx]
                if sample >= 0x8000:
                    sample -= 0x10000
                sum_squares += sample * sample
                
        if samples == 0:
            return 0
            
        return int(math.sqrt(sum_squares / samples))

    # 流式发送音频
    def stream_audio(self, data):
        try:
            self.sock.sendall(data)
        except OSError as e:
            print(f"传输中断: {e}, 尝试重连...")
            ed.text(f"传输中断: {e}, 尝试重连...", 0, 0)
            self.sock = self.connect_socket()
            # 重连后尝试重发
            try:
                self.sock.sendall(data)
            except:
                print("重连后发送仍失败")
                ed.text("重连后发送仍失败", 0, 0)

    # 流式处理音频
    def process_audio(self):
        read_buf = bytearray(self.buf_size)
        self.INMP441_is_send_wav = False
        
        # 计算静音检测参数
        max_silence = int(self.silence_duration * self.sample_rate / (self.buf_size // 2))
        
        while not self.INMP441_is_send_wav:
            # 读取音频数据
            try:
                bytes_read = self.audio_in.readinto(read_buf)
                if bytes_read == 0:
                    time.sleep(0.01)  # 防止CPU过载
                    continue
                    
                current_frame = read_buf[:bytes_read]
                energy = self.rms(current_frame)
                
                print(f"[DEBUG] 瞬时能量: {energy:.1f}")
                #ed.text(f"[DEBUG] \n瞬时能量: {energy:.1f}", 0, 0)
                
                if energy > self.energy_threshold:
                    if not self.is_recording:
                        print("检测到语音开始")
                        ed.text("检测到语音开始", 0, 0)
                        self.is_recording = True
                        self.silence_counter = 0
                        
                    # 直接发送音频帧和长度
                    header = struct.pack('<I', len(current_frame))
                    self.stream_audio(header + current_frame)
                else:
                    if self.is_recording:
                        self.silence_counter += 1
                        
                        # 静音帧也发送，让服务器处理
                        header = struct.pack('<I', len(current_frame))
                        self.stream_audio(header + current_frame)
                        
                        if self.silence_counter > max_silence:
                            # 发送结束标记
                            end_header = struct.pack('<I', 0)
                            self.sock.sendall(end_header)
                            self.is_recording = False
                            self.INMP441_is_send_wav = True
                            print("语音结束")
                            ed.text("语音发送完毕", 0, 0)
                            time.sleep(3)
                            #ed.text("开始回答......", 0, 0)
                            ed.pbm("star-struck.pbm", 0, 0)
                            
            except Exception as e:
                print(f"处理音频错误: {e}")
                ed.text(f"处理音频错误: {e}", 0, 0)
                # 释放资源
                del read_buf
                # 创建新缓冲区
                read_buf = bytearray(self.buf_size)
                time.sleep(0.5)

    # 接收并播放音频
    def receive_wavfile(self):
        try:
            # 优化接收缓冲区大小
            recv_buffer_size = 512  # 较小的缓冲区
            
            print("等待服务器返回播放数据...")
            #ed.text("等待服务器返回播放数据...", 0, 0)
            while True:
                content_byte = self.sock.recv(recv_buffer_size)
                if not content_byte or b"END_OF_STREAM" in content_byte:
                    break
                    
                print("接收到音频数据:", len(content_byte), "bytes")
                
                # 使用小缓冲区处理音频
                try:
                    # 创建整数数组
                    audio_samples = array.array('h')
                    
                    # 处理单个样本以调整音量
                    for i in range(0, len(content_byte), 2):
                        if i + 1 < len(content_byte):
                            value = content_byte[i] | (content_byte[i+1] << 8)
                            if value >= 0x8000:
                                value -= 0x10000
                            value = int(value * self.volume_factor)
                            audio_samples.append(value)
                    
                    # 播放处理后的音频
                    if len(audio_samples) > 0:
                        self.audio_out.write(audio_samples)
                        
                except Exception as e:
                    print(f"处理播放数据时出错: {e}")
                    ed.text(f"处理播放数据时出错: {e}", 0, 0)
                    
                # 释放资源
                del audio_samples
                
        except Exception as e:
            print("连接错误，尝试重新连接:", e)
            ed.text("连接错误，尝试重新连接:", 0, 0)
            self.sock = self.connect_socket()

    def start(self):
        while True:
            try:
                self.process_audio()
                
                if self.INMP441_is_send_wav:
                    self.receive_wavfile()
                    # 重置状态准备下次录音
                    self.INMP441_is_send_wav = False
                    self.is_recording = False
                    # 执行垃圾回收
                    import gc
                    gc.collect()
                #ed.text("倾听中......", 0, 0)
                ed.pbm("neutral_face.pbm", 0, 0)
                #time.sleep(3)
                    
            except Exception as e:
                print(f"主循环错误: {e}")
                ed.text(f"主循环错误: {e}", 0, 0)
                time.sleep(1)
                # 执行垃圾回收
                import gc
                gc.collect()
                

if __name__ == "__main__":
    # 执行垃圾回收以确保干净开始
    import gc
    gc.collect()
    
    # 启动录音系统
    print("\n=== INMP441语音检测系统 ===")
    ed.text("\n=== INMP441语音检测系统 ===", 0, 0)
    try:
        recorder = VoiceRecorder()
        print("提示：首次使用建议进行阈值校准")
        ed.text("提示：首次使用建议进行阈值校准", 0, 0)
        print("--------------------------------")
        ed.text("--------------------------------", 0, 0)
        recorder.start()
    except MemoryError:
        print("内存不足，系统重启...")
        ed.text("内存不足，系统重启...", 0, 0)
        import machine
        machine.reset()
    except Exception as e:
        print(f"系统错误: {e}")
        ed.text(f"系统错误: {e}", 0, 0)
        import machine
        machine.reset()
