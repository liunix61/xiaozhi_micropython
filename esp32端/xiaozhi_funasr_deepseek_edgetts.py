from machine import I2S, Pin, I2C
import time, array, os
import math, network, socket
import sh1106
import framebuf
import ustruct as struct  # MicroPython使用ustruct

class VoiceRecorder:
    def __init__(self):
        # sh1106 I2C初始化
        self.i2c = I2C(0, scl=Pin(42), sda=Pin(41), freq=400000)
        # 显示屏初始化
        self.display = sh1106.SH1106_I2C(128, 64, self.i2c, None, 0x3c)
        self.display.rotate(True)  # 根据实际显示方向调整
        # 图片数据
        self.LOGO = bytearray([
        0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X04,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X06,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X86,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0XC6,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X10,0XC7,0X03,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X30,0XC7,0X03,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X38,0XC3,0X03,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X38,0XC3,0X01,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X38,0XC3,0X01,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X30,0XC3,0X81,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X30,0XC3,0X81,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X30,0XC1,0X80,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X30,0XC1,0X80,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X30,0XC1,0X80,0XE0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X30,0XC1,0XC0,0XE0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X10,0X30,0XC1,0XC0,0X60,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X10,0X70,0XC0,0XC0,0X60,0X00,0X50,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X10,0X70,0XC0,0XC0,0X60,0XF8,0X50,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X38,0X60,0XC0,0XC0,0X70,0X88,0X50,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X38,0X60,0XC0,0XC0,0X70,0X8A,0X52,0X00,0X00,0X00,0X00,0X00,0X20,0X00,0X00,0X00,0X38,0X60,0XC0,0XC2,0X30,0X89,0X56,0X00,0X00,0X00,0X00,0X00,0X20,0X02,0X02,0X00,0X28,0XE0,0XC0,0X07,0X30,0X89,0X5C,0X00,0X00,0X00,0X01,0XF8,0X60,0X1F,0XFF,0XC0,0X28,0XE0,0XC0,0X07,0X30,0XD9,0XD8,0X00,0X00,0X00,0X00,0X43,0XFE,0X02,0X02,0X00,0X68,0XC0,0XC0,0X07,0X30,0X70,0XD0,0X00,0X00,0X00,0X00,0X40,0X20,0X02,0X02,0X00,0X68,0XC0,0XC0,0X07,0X30,0X20,0X50,0X00,0X00,0X00,0X00,0XC0,0X20,0X03,0XFE,0X00,0X69,0XC0,0XC0,0X07,0X30,0XA0,0X58,0X00,0X00,0X00,0X00,0XF0,0X20,0X02,0X02,0X00,0X49,0XC0,0XC0,0X06,0X00,0XB0,0X5C,0X00,0X00,0X00,0X01,0X97,0XFF,0X03,0XFE,0X00,0XC8,0X00,0XFF,0XFE,0X00,0XB9,0XD6,0X00,0X00,0X00,0X01,0X93,0XFF,0X02,0X02,0X00,0XCC,0X00,0X7F,0XFC,0X00,0XA2,0X52,0X00,0X00,0X00,0X02,0X90,0X20,0X06,0X03,0X00,0XCC,0X00,0X1F,0XF8,0X00,0XA0,0X51,0X00,0X00,0X00,0X04,0X90,0X20,0X3F,0XFF,0XE0,0XCC,0X00,0X00,0X00,0X00,0XA0,0X91,0X00,0X00,0X00,0X00,0X93,0XFE,0X02,0X23,0X00,0X8C,0X00,0X00,0X00,0X00,0XB9,0X90,0X00,0X00,0X00,0X00,0X93,0XFE,0X0C,0X20,0X81,0X8C,0X00,0X00,0X00,0X01,0XF3,0X18,0X80,0X00,0X00,0X00,0X90,0X20,0X39,0XFE,0X61,0X8C,0X00,0X00,0X00,0X03,0X06,0X0F,0X00,0X00,0X00,0X00,0X90,0X20,0X20,0X20,0X21,0X8C,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X90,0X20,0X00,0X20,0X01,0X0C,0X00,0X00,0X00,0X00,0X03,0X00,0X00,0X00,0X00,0X00,0X90,0X20,0X00,0X20,0X03,0X04,0X00,0X00,0X00,0X00,0X03,0X80,0X00,0X00,0X00,0X00,0XF7,0XFF,0X1F,0XFF,0XC3,0X04,0X00,0X00,0X00,0X00,0X03,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X03,0X04,0X00,0X00,0X00,0X00,0X07,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X03,0X06,0X00,0X18,0X00,0X00,0X06,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X02,0X06,0X00,0X18,0X00,0X00,0X06,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X06,0X06,0X00,0X3C,0X00,0X01,0X04,0XC0,0X00,0X00,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XFE,0X06,0X00,0X66,0X00,0X03,0X8C,0X60,0X00,0X00,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XFC,0X06,0X3F,0XE7,0XFF,0XFE,0XCC,0X7F,0XFF,0XFF,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X06,0X3F,0XC3,0XFF,0XFC,0X78,0X3F,0XFF,0XFF,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X06,0X60,0X00,0X00,0X00,0X30,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X06,0X60,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X06,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X02,0XC0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X02,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X02,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X03,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X03,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X03,0X80,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X01,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X01,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X01,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
        ])
        # 创建帧缓冲对象
        self.logo = framebuf.FrameBuffer(self.LOGO, 128, 64, framebuf.MONO_HLSB)
        # 显示图片
        self.display.fill(0)
        self.display.blit(self.logo, 0, 0)
        self.display.show()


        # INMP441 硬件参数配置
        self.INMP441_sck_pin = Pin(5)    # BCK
        self.INMP441_ws_pin = Pin(4)     # WS/LRC
        self.INMP441_sd_pin = Pin(6)     # DIN
        self.buf_size = 32768    # 优化缓冲区大小（需为1024的倍数）
        self.sample_rate = 8000  # 8kHz采样率
        self.bits = 16           #每音频采样比特数
        self.format = I2S.STEREO # 立体声模式
        self.channels = 1        # 单声道
        
        # 优化后的VAD参数（需要根据实际环境校准）
        self.energy_threshold = 40   # 初始阈值（安静环境建议800-1200）
        self.silence_duration = 3    # 静音持续时间(s)
        self.min_voice_duration = 1  # 最短有效语音时长(s)
        self.pre_roll = 1            # 预录音时长(s)
        
        # 音频缓冲区
        self.pre_buffer = bytearray()
        self.rec_buffer = bytearray()
        self.is_recording = False # 是不是正在录音
        self.silence_counter = 0
      
        # WAV文件路径
        self.send_wav_file = "/send_wav_file.wav"   # 确保文件存在
        self.INMP441_is_send_wav = False # INMP441 录音文件保存成功
          
        # MAX98357 初始化引脚定义
        self.MAX98357_sck_pin = Pin(15)  # 串行时钟输出
        self.MAX98357_ws_pin = Pin(16)   # 字时钟
        self.MAX98357_sd_pin = Pin(7)    # 串行数据输出

        # 调节MAX98357 8欧3瓦 喇叭 声音
        # 音量因子，范围为0.0到1.0，1.0为原音量，0.5为半音量，0.0为静音
        self.volume_factor = 0.13

        # 配置Wi-Fi连接信息
        self.WIFI_SSID = "HONOR 50"
        self.WIFI_PASSWORD = "12345678"

        # 服务器配置
        self.SERVER_IP = "192.168.188.104"  # 替换为服务器IP
        self.SERVER_PORT = 8888          # 替换为服务器端口

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
            format=self.format,  # 应用单声道配置
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
            format=I2S.MONO,# STEREO,MONO
            rate=8000,# 24100, 44100,32000
            ibuf=4096 #1024,2048,4096,8192,16384,32768
            )
        print(f"[INIT] INMP441采样率: {self.sample_rate} INMP441缓冲区: {self.buf_size}字节")
        print("[INIT] I2S录音设备就绪") 
       
    # 连接 WiFi
    def connect_wifi(self):     
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected(): 
            print("正在连接WiFi ...")
            sta_if.active(True) 
            sta_if.connect(self.WIFI_SSID,  self.WIFI_PASSWORD)
            while not sta_if.isconnected(): 
                time.sleep(0.5) 
        print("[INIT] WiFi 连接成功!")
        print("IP地址:", sta_if.ifconfig()[0]) 

    # 带重试的socket连接
    def connect_socket(self):  
        print("[INIT] 正在连接服务器...")
        retry_delay = 5  # 重试间隔秒数
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.SERVER_IP, self.SERVER_PORT))
                print(f"成功连接到 {self.SERVER_IP}:{self.SERVER_PORT}")
                return sock
            except OSError as e:
                print(f"连接失败: {e}, {retry_delay}秒后重试...")
                time.sleep(retry_delay)

    # 兼容旧版MicroPython的RMS计算
    def rms(self, data):    
        sum_squares = 0
        sample_count = len(data) // 2  # 每个样本2字节(int16)          
        for i in range(0, len(data), 2):# 将字节数据转换为16位有符号整数 
            sample = (data[i+1] << 8) | data[i]# 小端字节序转换（根据硬件实际情况调整）
            # 转换为有符号整数
            if sample >= 0x8000:
                sample -= 0x10000
            sum_squares += sample * sample     
        if sample_count == 0:
            return 0       
        return int(math.sqrt(sum_squares / sample_count))# 使用浮点运算替代isqrt
  

    # 添加淡出效果防止爆音
    def add_fadeout(self, fade_time=0.1):     
        print("[AUDIO] 添加淡出效果...")
        fade_samples = int(self.sample_rate * fade_time)
        fade_step = 1.0 / fade_samples      
        data = self.rec_buffer
        start_idx = max(0, len(data) - fade_samples*2)   
        for i in range(start_idx, len(data), 2):
            progress = (i - start_idx) // 2
            factor = max(0.0, 1.0 - progress * fade_step)
            sample = int.from_bytes(data[i:i+2], 'little', True)
            attenuated = int(sample * factor)
            data[i:i+2] = attenuated.to_bytes(2, 'little', True)



    # 开始音频处理循环（已适配单声道）
    def process_audio(self):
        read_buf = bytearray(self.buf_size)

        self.INMP441_is_send_wav = False
        while not self.INMP441_is_send_wav:
            # 持续读取音频数据
            bytes_read = self.audio_in.readinto(read_buf)
            current_frame = read_buf[:bytes_read]

            energy = self.rms(current_frame)
            print(f"[DEBUG] 瞬时能量: {energy:.1f}") 
            if energy > self.energy_threshold * 1.2:  # 增加触发阈值
                if not self.is_recording:
                    print("检测到语音开始")
                    self.is_recording = True
                    self.silence_counter = 0
                    # 清空预缓冲防止重复
                    self.pre_buffer = bytearray()

                # 仅保留数据长度包头
                header = struct.pack('<I', len(current_frame))
                self.stream_audio(header + current_frame)
                
                self.rec_buffer += current_frame
            else:
                if self.is_recording:
                    self.silence_counter += 1
                    max_silence = int(self.silence_duration * self.sample_rate / (self.buf_size // 2))
                    
                    if self.silence_counter > max_silence:
                        # 发送空包时应保持包头+空数据的结构
                        end_header = struct.pack('<I', 0)
                        self.sock.sendall(end_header)  # ✅ 仅发送长度为0的包头
                        self.is_recording = False
                        self.INMP441_is_send_wav = True
                        print("语音结束")
    
    
    def stream_audio(self, data):
        try:
            # 统一使用struct打包包头
            header = struct.pack('<I', len(data)) # ✅ 4字节小端序
            self.sock.sendall(header + data)      # ✅ 使用sendall确保完整发送
        except OSError as e:
            print(f"传输中断: {e}, 尝试重连...")
            self.sock = self.connect_socket()





    #  接收 wav文件
    def receive_wavfile(self):
        try:      
            # 接收服务器响应
            print("等待服务器返回播放数据...")  
            while True:
                content_byte = self.sock.recv(128) 
                if not content_byte or b"END_OF_STREAM" in content_byte:
                    break
                print("接收到音频数据:", len(content_byte), "bytes")
                # 添加音频播放逻辑       
                audio_samples = array.array('h', content_byte)# 将字节数据转换为16位整数数组       
                for i in range(len(audio_samples)):# 调整音量
                    audio_samples[i] = int(audio_samples[i] * self.volume_factor)
                self.audio_out.write(audio_samples) # 调用I2S对象播放音频
       
        except Exception as e:
            print("连接错误，尝试重新连接:", e)
            self.sock = self.connect_socket()  # 重新连接
        finally:
            pass

    def start(self):
        while True:  # 主循环保持持续运行
            self.process_audio()

            if self.INMP441_is_send_wav:
                self.receive_wavfile()
                
                # 重置状态准备下次录音
                self.INMP441_is_send_wav = False
                self.is_recording = False
                self.rec_buffer = bytearray()
                self.pre_buffer = bytearray()


if __name__ == "__main__":
    # 启动录音系统
    print("\n=== INMP441语音检测系统 ===")
    recorder = VoiceRecorder()
    print("提示：首次使用建议进行阈值校准")
    print("--------------------------------")
    recorder.start()
