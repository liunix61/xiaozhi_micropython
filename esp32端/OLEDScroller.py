import time
from machine import SoftI2C, Pin
import ssd1306
import ufont

class OLEDScroller:
    def __init__(self, scl_pin=6, sda_pin=5, width=128, height=64, font_file="unifont-14-12917-16.v3.bmf"):
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.oled_width = width
        self.oled_height = height
        self.display = ssd1306.SSD1306_I2C(width, height, self.i2c)
        self.font = ufont.BMFont(font_file)
        self.font_size = 16  # 字体大小
        self.line_height = 16  # 行高
        self.max_lines = self.oled_height // self.line_height  # 每屏最大行数

    def clear(self):
        """清屏"""
        self.display.fill(0)
        self.display.show()

    def is_chinese_char(self, char):
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

    def is_english_char(self, char):
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

    def get_char_width(self, char):
        """
        获取字符的宽度（假设中文字符宽度为 16，英文字符宽度为 8）
        :param char: 单个字符
        :return: 字符宽度
        """
        if self.is_chinese_char(char):
            return 16  # 中文字符宽度
        elif self.is_english_char(char):
            return 8   # 英文字符宽度
        else:
            return 8   # 默认宽度

    def display_text_with_scroll(self, text, char_delay=0.1, line_delay=0.5, scroll_delay=0.02, fast_scroll_delay=0.01):
        """
        逐个打印字符，自动换行，满屏后逐行向上滚动
        :param text: 要显示的文本
        :param char_delay: 每个字符的显示延迟
        :param line_delay: 每行显示后的延迟
        :param scroll_delay: 向上滚动时的延迟
        :param fast_scroll_delay: 快速滚动时的延迟
        """
        lines = []  # 当前屏的行
        current_line = ""  # 当前行内容
        x, y = 0, 0  # 当前字符的坐标

        words = text.split(' ')  # 按空格分割文本为单词
        for word in words:
            # 计算单词宽度
            word_width = sum(self.get_char_width(char) for char in word)
            if x + word_width > self.oled_width:  # 换行
                lines.append(current_line)
                current_line = ""
                x = 0
                y += self.line_height

                if y >= self.oled_height:  # 满屏后向上滚动
                    self._scroll_up(lines, scroll_delay)
                    y -= self.line_height
                    lines.pop(0)  # 移除最上面一行

            # 绘制当前单词
            for char in word:
                char_width = self.get_char_width(char)
                if x + char_width > self.oled_width:  # 换行
                    lines.append(current_line)
                    current_line = ""
                    x = 0
                    y += self.line_height

                    if y >= self.oled_height:  # 满屏后向上滚动
                        self._scroll_up(lines, scroll_delay)
                        y -= self.line_height
                        lines.pop(0)  # 移除最上面一行

                self.font.text(self.display, char, x, y, show=False)
                self.display.show()
                current_line += char
                x += char_width
                time.sleep(char_delay)

            # 添加空格（单词间）
            if x + self.get_char_width(' ') <= self.oled_width:
                current_line += ' '
                x += self.get_char_width(' ')

        # 显示剩余内容
        if current_line:
            lines.append(current_line)
            self._scroll_up(lines, scroll_delay)

        # 完成打印后快速从头到尾滚动
        self._fast_scroll(fast_scroll_delay)

    def _scroll_up(self, lines, scroll_delay):
        """
        向上滚动一屏内容
        :param lines: 当前屏的行
        :param scroll_delay: 滚动延迟
        """
        for _ in range(self.line_height):  # 每次滚动一个像素
            self.display.scroll(0, -1)  # 向上滚动
            self.display.show()
            time.sleep(scroll_delay)

        # 清空最下面一行
        self.display.fill_rect(0, self.oled_height - self.line_height, self.oled_width, self.line_height, 0)
        self.display.show()

    def _fast_scroll(self, fast_scroll_delay):
        """
        快速从头到尾滚动
        :param fast_scroll_delay: 快速滚动延迟
        """
        for _ in range(self.oled_height):  # 每次滚动一个像素，直到所有内容移出屏幕
            self.display.scroll(0, -1)  # 向上滚动
            self.display.show()
            time.sleep(fast_scroll_delay)

        # 清屏
        self.clear()
        
'''
# 使用示例
if __name__ == "__main__":
    scroller = OLEDScroller()

    long_text = """这是一个长文本，将逐字符显示。
如果一行超出屏幕宽度，它将自动换行。
当屏幕满时，它将逐行向上滚动。
这是文本显示功能的优化版本。
你可以根据需要调整字符延迟、行延迟和滚动延迟。"""

    # 显示长文本
    scroller.display_text_with_scroll(long_text, char_delay=0.05, line_delay=0.3, scroll_delay=0.01, fast_scroll_delay=0.005)

    # 清屏
    scroller.clear()
'''
