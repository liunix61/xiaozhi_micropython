# 小智AI esp32端

本项目基于 INMP441 麦克风模块和 MAX98357 音频放大器模块，实现了一个简单的语音检测与传输系统。系统能够实时检测语音活动，并通过 Wi-Fi 将音频数据流式传输到远程服务器，同时支持从服务器接收音频数据并通过喇叭播放。

## 功能特性

- **语音活动检测 (VAD)**: 通过能量阈值检测语音活动，支持动态调整静音检测时长和最短语音时长。
- **音频流式传输**: 将检测到的语音数据通过 TCP 协议实时传输到远程服务器。
- **音频播放**: 支持从服务器接收音频数据并通过 MAX98357 模块播放。
- **Wi-Fi 连接**: 支持自动连接 Wi-Fi，并在连接失败时自动重试。
- **内存优化**: 通过调整缓冲区大小和分块处理数据，减少内存占用，避免内存溢出。

## 硬件要求

- **INMP441 麦克风模块**: 用于音频输入。
- **MAX98357 音频放大器模块**: 用于音频输出。
- **ESP32 或其他支持 MicroPython 的开发板**: 用于运行本项目的代码。
- **Wi-Fi 网络**: 用于连接远程服务器。

## 软件依赖

- **MicroPython**: 本项目基于 MicroPython 开发，确保你的设备已刷入 MicroPython 固件。
- **socket 模块**: 用于网络通信。
- **I2S 模块**: 用于音频输入输出的硬件接口。

## 快速开始

1. **硬件连接**:
   - 将 INMP441 的 SCK、WS、SD 引脚分别连接到 ESP32 的 GPIO2、GPIO3、GPIO4。
   - 将 MAX98357 的 SCK、WS、SD 引脚分别连接到 ESP32 的 GPIO9、GPIO8、GPIO7。

2. **配置 Wi-Fi**:
   - 在代码中修改 `WIFI_SSID` 和 `WIFI_PASSWORD` 为你的 Wi-Fi 名称和密码。

3. **配置服务器**:
   - 修改 `SERVER_IP` 和 `SERVER_PORT` 为你的服务器地址和端口。

4. **上传代码**:
   - 将代码文件xiaozhi.py上传到 ESP32 并运行。

5. **启动系统**:
   - 系统启动后会自动连接 Wi-Fi 并开始语音检测。检测到语音后，音频数据将通过 TCP 传输到服务器，并等待服务器返回的音频数据进行播放。

## 参数调整

- **能量阈值 (`energy_threshold`)**: 用于检测语音活动的能量阈值，可根据环境噪音调整。
- **静音时长 (`silence_duration`)**: 用于判断语音结束的静音时长，单位为秒。
- **最短语音时长 (`min_voice_duration`)**: 最短的有效语音时长，小于该时长的语音将被忽略。
- **音量因子 (`volume_factor`)**: 控制喇叭播放音量的因子，范围为 0 到 1。

## 注意事项

- **内存管理**: 由于 MicroPython 的内存限制，建议在使用过程中定期执行垃圾回收 (`gc.collect()`) 以避免内存溢出。
- **网络稳定性**: 在网络不稳定的环境下，系统会自动重连服务器，但可能会影响实时性。

## 示例代码

```python
if __name__ == "__main__":
    import gc
    gc.collect()
    
    print("\n=== INMP441语音检测系统 ===")
    try:
        recorder = VoiceRecorder()
        print("提示：首次使用建议进行阈值校准")
        print("--------------------------------")
        recorder.start()
    except MemoryError:
        print("内存不足，系统重启...")
        import machine
        machine.reset()
    except Exception as e:
        print(f"系统错误: {e}")
        import machine
        machine.reset()
```

## Todo
-[  ] ssd1306显示表情和文字  
-[  ] 摄像头用于人脸识别和图像解读  
-[  ] 舵机控制用于人脸追踪  

## 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 许可证

本项目基于 MIT 许可证开源，详情请参见 [LICENSE](LICENSE) 文件。

---

希望本项目能为你提供帮助！如果有任何问题或建议，欢迎在 Issue 中提出。
