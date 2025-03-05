from machine import Pin, PWM, I2C
import time
import math
from ssd1306 import SSD1306_I2C

# 自定义 SSD1306_I2C 类，添加 fill_round_rect 和 fill_triangle 方法
class CustomSSD1306_I2C(SSD1306_I2C):
    def fill_round_rect(self, x, y, w, h, r, color):
        """
        绘制一个填充的圆角矩形
        :param x: 左上角 x 坐标
        :param y: 左上角 y 坐标
        :param w: 宽度
        :param h: 高度
        :param r: 圆角半径
        :param color: 颜色 (0 或 1)
        """
        # 绘制中间的矩形
        self.fill_rect(x + r, y, w - 2 * r, h, color)
        self.fill_rect(x, y + r, w, h - 2 * r, color)
        
        # 绘制四个角的圆角
        def draw_circle_part(cx, cy):
            for i in range(cx - r, cx + r + 1):
                for j in range(cy - r, cy + r + 1):
                    if (i - cx) ** 2 + (j - cy) ** 2 <= r ** 2:
                        self.pixel(i, j, color)
        
        # 左上角
        draw_circle_part(x + r, y + r)
        # 右上角
        draw_circle_part(x + w - r - 1, y + r)
        # 左下角
        draw_circle_part(x + r, y + h - r - 1)
        # 右下角
        draw_circle_part(x + w - r - 1, y + h - r - 1)

    def fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """
        绘制一个填充的三角形
        :param x0, y0: 第一个顶点坐标
        :param x1, y1: 第二个顶点坐标
        :param x2, y2: 第三个顶点坐标
        :param color: 颜色 (0 或 1)
        """
        def sort_by_y(a, b):
            if a[1] > b[1]:
                return b, a
            return a, b

        # 按 y 坐标排序顶点
        (x0, y0), (x1, y1) = sort_by_y((x0, y0), (x1, y1))
        (x0, y0), (x2, y2) = sort_by_y((x0, y0), (x2, y2))
        (x1, y1), (x2, y2) = sort_by_y((x1, y1), (x2, y2))

        if y1 == y2:
            self.fill_bottom_flat_triangle(x0, y0, x1, y1, x2, y2, color)
        elif y0 == y1:
            self.fill_top_flat_triangle(x0, y0, x1, y1, x2, y2, color)
        else:
            # 分割三角形为上下两部分
            x3 = int(x0 + ((y1 - y0) / (y2 - y0)) * (x2 - x0))
            y3 = y1
            self.fill_bottom_flat_triangle(x0, y0, x1, y1, x3, y3, color)
            self.fill_top_flat_triangle(x1, y1, x3, y3, x2, y2, color)

    def fill_bottom_flat_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """绘制底部平坦的三角形"""
        invslope1 = (x1 - x0) / (y1 - y0)
        invslope2 = (x2 - x0) / (y2 - y0)

        curx1 = x0
        curx2 = x0

        for scanline in range(y0, y1 + 1):
            self.line(int(curx1), scanline, int(curx2), scanline, color)
            curx1 += invslope1
            curx2 += invslope2

    def fill_top_flat_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """绘制顶部平坦的三角形"""
        invslope1 = (x2 - x0) / (y2 - y0)
        invslope2 = (x2 - x1) / (y2 - y1)

        curx1 = x2
        curx2 = x2

        for scanline in range(y2, y0 - 1, -1):
            self.line(int(curx1), scanline, int(curx2), scanline, color)
            curx1 -= invslope1
            curx2 -= invslope2


class EyeExpression:
    def __init__(self):
        # 屏幕配置
        self.SCREEN_WIDTH = 128
        self.SCREEN_HEIGHT = 64
        self.i2c = I2C(0, scl=Pin(6), sda=Pin(5), freq=400000)
        self.display = CustomSSD1306_I2C(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.i2c)

        # 舵机配置
        self.X_PIN = 12
        self.Y_PIN = 13
        self.STEP = 1
        self.SERVO_DELAY = 10
        self.X_CENTER = 130
        self.X_OFFSET = 25
        self.Y_CENTER = 70
        self.Y_OFFSET = 50
        self.x_min = self.X_CENTER - self.X_OFFSET
        self.x_max = self.X_CENTER + self.X_OFFSET
        self.y_min = self.Y_CENTER - self.Y_OFFSET
        self.y_max = self.Y_CENTER + self.Y_OFFSET

        # 舵机 PWM 配置
        self.servo_x = self.setup_servo(self.X_PIN)
        self.servo_y = self.setup_servo(self.Y_PIN)

        # 眼睛参数
        self.ref_eye_height = 40
        self.ref_eye_width = 40
        self.ref_space_between_eye = 10
        self.ref_corner_radius = 10

        # 眼睛状态
        self.current_state = {
            'left_eye_height': self.ref_eye_height,
            'left_eye_width': self.ref_eye_width,
            'right_eye_x': 32 + self.ref_eye_width + self.ref_space_between_eye,
            'left_eye_x': 32,
            'left_eye_y': 32,
            'right_eye_y': 32,
            'right_eye_height': self.ref_eye_height,
            'right_eye_width': self.ref_eye_width
        }

        # 初始化舵机位置
        self.write_servo(self.servo_x, self.X_CENTER)
        self.write_servo(self.servo_y, self.Y_CENTER)

        # 初始化屏幕
        self.eye_center()
        self.display.show()
        print("Initialization complete")

    def setup_servo(self, pin):
        pwm = PWM(Pin(pin))
        pwm.freq(50)  # 50Hz 标准舵机频率
        return pwm

    def angle_to_duty(self, angle):
        return int((angle / 180) * 1023)  # ESP32 PWM 分辨率为10位

    def write_servo(self, pwm, angle):
        duty = self.angle_to_duty(angle)
        pwm.duty(duty)

    def draw_eyes(self, update=True):
        self.display.fill(0)
        
        # 绘制左眼
        x = int(self.current_state['left_eye_x'] - self.current_state['left_eye_width']/2)
        y = int(self.current_state['left_eye_y'] - self.current_state['left_eye_height']/2)
        self.display.fill_round_rect(x, y, 
                                   self.current_state['left_eye_width'], 
                                   self.current_state['left_eye_height'],
                                   self.ref_corner_radius, 1)
        
        # 绘制右眼
        x = int(self.current_state['right_eye_x'] - self.current_state['right_eye_width']/2)
        y = int(self.current_state['right_eye_y'] - self.current_state['right_eye_height']/2)
        self.display.fill_round_rect(x, y, 
                                   self.current_state['right_eye_width'], 
                                   self.current_state['right_eye_height'],
                                   self.ref_corner_radius, 1)
        
        if update:
            self.display.show()

    def eye_center(self, update=True):
        self.current_state.update({
            'left_eye_height': self.ref_eye_height,
            'left_eye_width': self.ref_eye_width,
            'right_eye_height': self.ref_eye_height,
            'right_eye_width': self.ref_eye_width,
            'left_eye_x': self.SCREEN_WIDTH//2 - self.ref_eye_width//2 - self.ref_space_between_eye//2,
            'left_eye_y': self.SCREEN_HEIGHT//2,
            'right_eye_x': self.SCREEN_WIDTH//2 + self.ref_eye_width//2 + self.ref_space_between_eye//2,
            'right_eye_y': self.SCREEN_HEIGHT//2
        })
        self.draw_eyes(update)

    def eye_blink(self, speed=6):
        self.draw_eyes()
        for _ in range(3):
            self.current_state['left_eye_height'] -= speed
            self.current_state['right_eye_height'] -= speed
            self.draw_eyes()
            time.sleep_ms(10)
        for _ in range(3):
            self.current_state['left_eye_height'] += speed
            self.current_state['right_eye_height'] += speed
            self.draw_eyes()
            time.sleep_ms(10)

    def eye_happy(self):
        self.eye_center(update=False)
        offset = self.ref_eye_height // 2
        for _ in range(10):
            # 绘制左眼的倒三角形
            self.display.fill_triangle(
                self.current_state['left_eye_x'] - self.current_state['left_eye_width']//2 - 1,
                self.current_state['left_eye_y'] + offset,
                self.current_state['left_eye_x'] + self.current_state['left_eye_width']//2 + 1,
                self.current_state['left_eye_y'] + 5 + offset,
                self.current_state['left_eye_x'] - self.current_state['left_eye_width']//2 - 1,
                self.current_state['left_eye_y'] + self.current_state['left_eye_height'] + offset,
                0
            )
            # 绘制右眼的倒三角形
            self.display.fill_triangle(
                self.current_state['right_eye_x'] + self.current_state['right_eye_width']//2 + 1,
                self.current_state['right_eye_y'] + offset,
                self.current_state['right_eye_x'] - self.current_state['right_eye_width']//2 - 1,
                self.current_state['right_eye_y'] + 5 + offset,
                self.current_state['right_eye_x'] + self.current_state['right_eye_width']//2 + 1,
                self.current_state['right_eye_y'] + self.current_state['right_eye_height'] + offset,
                0
            )
            offset -= 2
            self.display.show()
            time.sleep_ms(10)
        time.sleep_ms(1000)

    def eye_sad(self):
        self.eye_center(update=False)
        offset = self.ref_eye_height // 2
        for _ in range(10):
            # 绘制左眼的倒三角形
            self.display.fill_triangle(
                self.current_state['right_eye_x'] - self.current_state['left_eye_width']//2 - 1,
                self.current_state['right_eye_y'] + offset,
                self.current_state['right_eye_x'] + self.current_state['left_eye_width']//2 + 1,
                self.current_state['right_eye_y'] + 5 + offset,
                self.current_state['right_eye_x'] - self.current_state['left_eye_width']//2 - 1,
                self.current_state['right_eye_y'] + self.current_state['left_eye_height'] + offset,
                0
            )
            # 绘制右眼的倒三角形
            self.display.fill_triangle(
                self.current_state['left_eye_x'] + self.current_state['right_eye_width']//2 + 1,
                self.current_state['left_eye_y'] + offset,
                self.current_state['left_eye_x'] - self.current_state['right_eye_width']//2 - 1,
                self.current_state['left_eye_y'] + 5 + offset,
                self.current_state['left_eye_x'] + self.current_state['right_eye_width']//2 + 1,
                self.current_state['left_eye_y'] + self.current_state['right_eye_height'] + offset,
                0
            )
            offset -= 2
            self.display.show()
            time.sleep_ms(10)
        time.sleep_ms(1000)

    def main(self):
        while True:
            # 测试各种功能
            self.eye_blink()
            time.sleep(1)
            self.eye_happy()
            time.sleep(1)
            self.eye_sad()
            time.sleep(1)

if __name__ == "__main__":
    eye_expression = EyeExpression()
    eye_expression.main()
