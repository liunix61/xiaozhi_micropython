from machine import Pin, SoftI2C
import ssd1306
import time
import math

class EmojiDisplay:
    def __init__(self, scl_pin=6, sda_pin=5, width=128, height=64):
        # 初始化I2C
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        # 初始化SSD1306显示屏
        self.oled = ssd1306.SSD1306_I2C(width, height, self.i2c)
        # 清屏
        self.oled.fill(0)
        self.oled.show()
        # 眼睛参数
        self.eye_radius = 15
        self.eye_left_x = 40
        self.eye_left_y = 32
        self.eye_right_x = 88
        self.eye_right_y = 32

    # 绘制圆形（使用像素点模拟）
    def draw_circle(self, x, y, radius, color=1):
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                if i**2 + j**2 <= radius**2:
                    self.oled.pixel(x + i, y + j, color)

    # 绘制弧形（使用像素点模拟）
    def draw_arc(self, x, y, radius, start_angle, end_angle, color=1):
        for angle in range(start_angle, end_angle + 1):
            rad = math.radians(angle)
            dx = int(radius * math.cos(rad))
            dy = int(radius * math.sin(rad))
            self.oled.pixel(x + dx, y + dy, color)

    # 绘制眼睛
    def draw_eyes(self, blink=False, emotion="normal"):
        # 清屏
        self.oled.fill(0)
        
        # 绘制左眼
        if blink:
            # 眨眼效果：绘制一条线代替眼睛
            self.oled.fill_rect(self.eye_left_x - self.eye_radius, self.eye_left_y - 5, self.eye_radius * 2, 10, 1)
        else:
            # 根据情绪调整眼睛形状
            if emotion == "angry":
                # 生气：倒八字形
                self.oled.line(self.eye_left_x - self.eye_radius, self.eye_left_y + self.eye_radius, self.eye_left_x + self.eye_radius, self.eye_left_y - self.eye_radius, 1)
                self.oled.line(self.eye_left_x - self.eye_radius, self.eye_left_y - self.eye_radius, self.eye_left_x + self.eye_radius, self.eye_left_y + self.eye_radius, 1)
            elif emotion == "sleepy":
                # 犯困：半闭眼
                self.oled.fill_rect(self.eye_left_x - self.eye_radius, self.eye_left_y - 3, self.eye_radius * 2, 6, 1)
            elif emotion == "looking_around":
                # 左右观望：眼睛偏移
                self.oled.fill_rect(self.eye_left_x - self.eye_radius + 5, self.eye_left_y - self.eye_radius, self.eye_radius * 2, self.eye_radius * 2, 1)
            elif emotion == "happy":
                # 开心：弧形眼睛
                self.draw_arc(self.eye_left_x, self.eye_left_y, self.eye_radius, 180, 360)
            elif emotion == "sad":
                # 悲伤：倒弧形眼睛
                self.draw_arc(self.eye_left_x, self.eye_left_y, self.eye_radius, 0, 180)
            elif emotion == "surprised":
                # 惊讶：大圆眼睛
                self.draw_circle(self.eye_left_x, self.eye_left_y, self.eye_radius)
            elif emotion == "love":
                # 爱心眼：绘制爱心
                self.oled.fill_rect(self.eye_left_x - 5, self.eye_left_y - 5, 10, 10, 1)
                self.oled.fill_rect(self.eye_left_x - 10, self.eye_left_y, 20, 10, 1)
            else:
                # 正常眼睛：绘制圆形
                self.draw_circle(self.eye_left_x, self.eye_left_y, self.eye_radius)
        
        # 绘制右眼
        if blink:
            # 眨眼效果：绘制一条线代替眼睛
            self.oled.fill_rect(self.eye_right_x - self.eye_radius, self.eye_right_y - 5, self.eye_radius * 2, 10, 1)
        else:
            # 根据情绪调整眼睛形状
            if emotion == "angry":
                # 生气：倒八字形
                self.oled.line(self.eye_right_x - self.eye_radius, self.eye_right_y + self.eye_radius, self.eye_right_x + self.eye_radius, self.eye_right_y - self.eye_radius, 1)
                self.oled.line(self.eye_right_x - self.eye_radius, self.eye_right_y - self.eye_radius, self.eye_right_x + self.eye_radius, self.eye_right_y + self.eye_radius, 1)
            elif emotion == "sleepy":
                # 犯困：半闭眼
                self.oled.fill_rect(self.eye_right_x - self.eye_radius, self.eye_right_y - 3, self.eye_radius * 2, 6, 1)
            elif emotion == "looking_around":
                # 左右观望：眼睛偏移
                self.oled.fill_rect(self.eye_right_x - self.eye_radius - 5, self.eye_right_y - self.eye_radius, self.eye_radius * 2, self.eye_radius * 2, 1)
            elif emotion == "happy":
                # 开心：弧形眼睛
                self.draw_arc(self.eye_right_x, self.eye_right_y, self.eye_radius, 180, 360)
            elif emotion == "sad":
                # 悲伤：倒弧形眼睛
                self.draw_arc(self.eye_right_x, self.eye_right_y, self.eye_radius, 0, 180)
            elif emotion == "surprised":
                # 惊讶：大圆眼睛
                self.draw_circle(self.eye_right_x, self.eye_right_y, self.eye_radius)
            elif emotion == "love":
                # 爱心眼：绘制爱心
                self.oled.fill_rect(self.eye_right_x - 5, self.eye_right_y - 5, 10, 10, 1)
                self.oled.fill_rect(self.eye_right_x - 10, self.eye_right_y, 20, 10, 1)
            else:
                # 正常眼睛：绘制圆形
                self.draw_circle(self.eye_right_x, self.eye_right_y, self.eye_radius)
        
        # 显示
        self.oled.show()

    # 眨眼动画
    def blink_animation(self, emotion="normal"):
        # 正常眼睛
        self.draw_eyes(blink=False, emotion=emotion)
        time.sleep(1)
        
        # 眨眼
        self.draw_eyes(blink=True, emotion=emotion)
        time.sleep(0.2)
        
        # 恢复正常
        self.draw_eyes(blink=False, emotion=emotion)

    # 显示特定表情
    def show_emotion(self, emotion="normal", blink=False):
        if blink:
            self.blink_animation(emotion)
        else:
            self.draw_eyes(blink=False, emotion=emotion)

# 使用示例
if __name__ == "__main__":
    emoji_display = EmojiDisplay()
    
    # 单独调用每种表情
    emoji_display.show_emotion("normal")  # 正常表情
    time.sleep(2)
    
    emoji_display.show_emotion("happy")  # 开心表情
    time.sleep(2)
    
    emoji_display.show_emotion("angry", blink=True)  # 生气表情，带眨眼
    time.sleep(2)
    
    emoji_display.show_emotion("surprised")  # 惊讶表情
    time.sleep(2)
    
    emoji_display.show_emotion("love")  # 爱心眼表情
    time.sleep(2)
