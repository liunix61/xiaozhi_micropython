import time
from machine import SPI, Pin
import st7735_buf
from easydisplay import EasyDisplay

# 初始化显示屏
spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(4))
dp = st7735_buf.ST7735(width=160, height=80, spi=spi, cs=6, dc=3, res=2, rotate=3, bl=1, invert=False, rgb=False)
ed = EasyDisplay(dp, "RGB565", font="text_lite_16px_2312.v3.bmf", show=True, color=0xFFFF, clear=False)

def is_chinese_char(char):
    """
    判断字符是否是中文字符
    :param char: 单个字符
    :return: True 是中文字符，False 不是
    """
    unicode_val = ord(char)
    # 判断是否在常用汉字范围内
    if 0x4E00 <= unicode_val <= 0x9FFF:
        return True
    # 判断是否在扩展汉字范围内（可选）
    if 0x3400 <= unicode_val <= 0x4DBF or 0x20000 <= unicode_val <= 0x2A6DF:
        return True
    return False

def is_english_char(char):
    """
    判断字符是否是英文字符
    :param char: 单个字符
    :return: True 是英文字符，False 不是
    """
    unicode_val = ord(char)
    # 判断是否在 ASCII 范围内
    if 0x0000 <= unicode_val <= 0x007F:
        return True
    return False

def get_char_width(char):
    """
    获取字符的宽度（中文字符宽度为 16，英文字符宽度为 8）
    :param char: 单个字符
    :return: 字符宽度
    """
    if is_chinese_char(char):
        return 16  # 中文字符宽度
    elif is_english_char(char):
        return 8   # 英文字符宽度
    else:
        return 8   # 默认宽度

class TextDisplay:
    def __init__(self, display, width=160, height=80, line_height=16):
        self.display = display
        self.width = width
        self.height = height
        self.line_height = line_height
        self.max_lines = height // line_height
        self.current_x = 0
        self.current_y = 0
        self.content = []  # Stores tuples of (text, x, y)
        
    def add_text(self, text):
        for char in text:
            if char == '\n':  # Newline character
                self.current_x = 0
                self.current_y += self.line_height
                self._check_scroll()
                continue
                
            char_width = get_char_width(char)
            
            # Check if we need to wrap to next line
            if self.current_x + char_width > self.width:
                self.current_x = 0
                self.current_y += self.line_height
                self._check_scroll()
            
            # Check if we've gone past the bottom of the screen
            if self.current_y >= self.height:
                self._scroll_up()
                self.current_y = self.height - self.line_height
            
            # Store and display the character
            self.content.append((char, self.current_x, self.current_y))
            self.display.text(char, self.current_x, self.current_y)
            self.current_x += char_width
        
        self.display.show()  # Update the display
    
    def _check_scroll(self):
        """Check if we need to scroll"""
        if self.current_y >= self.height:
            self._scroll_up()
            self.current_y = self.height - self.line_height
    
    def _scroll_up(self):
        """Scroll the display up by one line"""
        # Clear the display
        self.display.fill(0)
        
        # Shift all content up by one line
        new_content = []
        for char, x, y in self.content:
            new_y = y - self.line_height
            if new_y >= 0:  # Only keep content that's still visible
                new_content.append((char, x, new_y))
                self.display.text(char, x, new_y)
        
        self.content = new_content
        self.display.show()
        
# 创建文本显示器
text_display = TextDisplay(ed)

# 示例文本
sample_text = """这是一个示例文本，用于测试显示屏的文本显示和滚动功能。
This is a sample text for testing display scrolling.
混合中英文显示效果 Mixed Chinese and English display.
1234567890!@#$%^&*() 数字和符号显示测试。
"""

# 显示文本
while True:
    for char in sample_text:
        text_display.add_text(char)
        time.sleep(0.05)  # 控制显示速度
    time.sleep(2)  # 显示完成后暂停2秒
