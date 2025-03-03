from OLEDScroller import OLEDScroller
scroller = OLEDScroller()

long_text = """这是一个长文本，将逐字符显示。如果一行超出屏幕宽度，它将自动换行。当屏幕满时，它将逐行向上滚动。这是文本显示功能的优化版本。你可以根据需要调整字符延迟、行延迟和滚动延迟。"""

# 显示长文本
scroller.display_text_with_scroll(long_text, char_delay=0.05, line_delay=0.03, scroll_delay=0.01)

# 清屏
#scroller.clear()
