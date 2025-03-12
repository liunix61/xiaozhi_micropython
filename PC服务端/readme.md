# 小智AI对话机器人服务器

## 项目简介

小智AI对话机器人服务器是一个基于TCP协议的语音交互系统，支持实时语音识别、自然语言处理和语音合成功能。该系统能够通过麦克风接收用户的语音输入，将其转换为文本后生成智能回复，并通过语音合成技术将回复内容转换为语音输出。系统支持多轮对话，适用于智能音箱、语音助手等场景。

## 功能特性

- **语音识别**：支持通过百度语音识别API或FunASR进行语音转文字。
- **自然语言处理**：集成DeepSeek、ChatGLM等AI模型，生成智能回复。
- **语音合成**：支持通过EdgeTTS、百度TTS或火山引擎TTS将文本转换为语音。
- **音频播放**：通过MAX98357模块播放生成的语音。
- **持久连接**：支持单次TCP连接下的多轮对话，直至主动断开。
- **模块化设计**：各功能模块独立封装，易于扩展和维护。

## 依赖库

- **语音识别**：
  - `funasr`：用于FunASR语音识别。
  - `requests`：用于百度语音识别API调用。
- **自然语言处理**：
  - `openai`：用于DeepSeek API调用。
  - `zhipuai`：用于ChatGLM API调用。
- **语音合成**：
  - `edge_tts`：用于EdgeTTS语音合成。
  - `requests`：用于百度TTS和火山引擎TTS API调用。
- **音频处理**：
  - `pydub`：用于音频格式转换。
  - `soundfile`：用于音频文件读取。
  - `wave`：用于WAV文件处理。
- **网络通信**：
  - `socket`：用于TCP通信。
- **其他工具**：
  - `subprocess`：用于调用FFmpeg进行音频格式转换。
  - `uuid`：用于生成唯一标识符。

## 快速开始

### 1. 环境准备

确保已安装Python 3.7及以上版本，并安装以下依赖库：

```bash
pip install requests soundfile pydub edge_tts openai zhipuai funasr
```

### 2. 配置API密钥

在代码中替换以下API密钥和配置信息：

- **百度语音识别**：替换 `BaiduTextToSpeech` 类中的 `api_key` 和 `secret_key`。
- **百度TTS**：替换 `BaiduTextToSpeech` 类中的 `api_key` 和 `secret_key`。
- **火山引擎TTS**：替换 `ByteDanceTTS` 类中的 `appid`、`access_token` 和 `cluster`。
- **DeepSeek**：替换 `DeepSeekReply` 类中的 `api_key`。
- **ChatGLM**：替换 `ZhipuAIClient` 类中的 `api_key`。

### 3. 启动服务器

启动服务器：

```bash
python xiaozhi_server_baiduasr_chatglm_bytedancetts.py
```
or
```bash
python xiaozhi_server_funasr_deepseek_edgetts.py
```

服务器启动后，会监听指定的IP和端口（默认 `0.0.0.0:8888`），等待客户端连接。

### 4. 客户端连接

客户端可以通过TCP连接到服务器，发送语音数据并接收生成的语音回复。服务器支持多轮对话，直至客户端主动断开连接。

## 代码结构

- **`BaiduTextToSpeech`**：百度TTS语音合成模块。
- **`ByteDanceTTS`**：火山引擎TTS语音合成模块。
- **`ZhipuAIClient`**：ChatGLM自然语言处理模块。
- **`SpeechRecognizer`**：百度语音识别模块。
- **`FunasrSpeechToText`**：FunASR语音识别模块。
- **`INMP441ToWAV`**：INMP441麦克风数据处理模块。
- **`DeepSeekReply`**：DeepSeek自然语言处理模块。
- **`EdgeTTSTextToSpeech`**：EdgeTTS语音合成模块。
- **`FFmpegToWav`**：FFmpeg音频格式转换模块。
- **`MAX98357AudioPlay`**：MAX98357音频播放模块。
- **`XiaoZhi_Ai_TCPServer`**：主服务器类，负责处理客户端连接和请求。

## 配置参数

- **服务器配置**：
  - `host`：服务器监听地址，默认为 `0.0.0.0`。
  - `port`：服务器监听端口，默认为 `8888`。
- **语音识别配置**：
  - `sample_rate`：音频采样率，默认为 `16000`。
  - `bits`：音频位深，默认为 `16`。
  - `channels`：音频声道数，默认为 `1`。
- **语音合成配置**：
  - `voice`：EdgeTTS语音类型，默认为 `zh-CN-XiaoxiaoNeural`。
  - `rate`：语音语速，默认为 `+16%`。
  - `volume`：语音音量，默认为 `+0%`。
  - `pitch`：语音音调，默认为 `+0Hz`。

## 注意事项

- **API调用限制**：部分API（如百度语音识别、DeepSeek等）可能有调用频率限制，请合理使用。
- **音频格式**：系统默认使用WAV格式处理音频，确保输入音频格式正确。
- **网络稳定性**：系统依赖网络通信，建议在稳定的网络环境下使用。

## 示例

### 1. 启动服务器

```bash
#基于百度语音识别、智谱清言对话大模型、字节语音合成
python xiaozhi_server_baiduasr_chatglm_bytedancetts.py
```
```bash
#基于funasr语音识别、deekseek对话大模型、edge语音合成
python xiaozhi_server_funasr_deepseek_edgetts.py
```


## 贡献

欢迎提交Issue和Pull Request来改进本项目。

## 许可证

本项目基于MIT许可证开源，详情请参见 [LICENSE](LICENSE) 文件。

---

希望本项目能为你提供帮助！如果有任何问题或建议，欢迎在Issue中提出。
