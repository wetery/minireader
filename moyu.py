import tkinter as tk
import random
from tkinter import filedialog, messagebox, ttk, scrolledtext


class ReadingWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg="white", padx=20, pady=10)

        # 绑定鼠标事件
        self.bind("<Enter>", self.on_mouse_enter)
        self.bind("<Leave>", self.on_mouse_leave)
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.on_move)

        # 新增双击关闭绑定
        self.bind("<Double-1>", self.on_double_click)

        self.label = tk.Label(self, text="", font=("微软雅黑", 12), bg="white")
        self.label.pack()

        # 记录鼠标进入前的播放状态
        self.previous_play_state = False

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def on_move(self, event):
        deltax = event.x - self._x
        deltay = event.y - self._y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def on_mouse_enter(self, event):
        # 保存当前播放状态并暂停
        self.previous_play_state = self.master.is_playing
        if self.master.is_playing:
            self.master.toggle_play()

    def on_mouse_leave(self, event):
        # 恢复之前的播放状态
        if self.previous_play_state and not self.master.is_playing:
            self.master.toggle_play()

    # 新增双击事件处理方法
    def on_double_click(self, event):
        self.destroy()


class FileContentViewer(tk.Toplevel):
    def __init__(self, master, content, current_line):
        super().__init__(master)
        self.title("快速跳转 - 点击选择行号")
        self.geometry("600x400")

        # 创建带滚动条的文本框
        self.text = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("宋体", 12))
        self.text.pack(expand=True, fill=tk.BOTH)

        # 插入带行号的内容
        for idx, line in enumerate(content, 1):
            self.text.insert(tk.END, f"{idx:4d} | {line}\n")

        # 禁用编辑功能
        self.text.config(state=tk.DISABLED)

        # 绑定点击事件
        self.text.tag_configure("current", background="#E0E0E0")
        self.text.bind("<Button-1>", self.on_click)

        # 高亮当前行
        self.highlight_current_line(current_line)

    def highlight_current_line(self, line_num):
        self.text.config(state=tk.NORMAL)
        start = f"{line_num + 1}.0"
        end = f"{line_num + 1}.end"
        self.text.tag_add("current", start, end)
        self.text.see(f"{line_num + 1}.0")  # 滚动到当前行
        self.text.config(state=tk.DISABLED)

    def on_click(self, event):
        # 获取点击位置对应的行号
        index = self.text.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0]) - 1  # 转换为0-based索引

        if 0 <= line_num < len(self.master.file_content):
            self.master.jump_to_line(line_num)
            self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("迷你阅读器")
        self.geometry("400x300")

        # 初始化变量
        self.file_content = []
        self.current_line = 0
        self.is_playing = False
        self.bg_colors = ["white", "#F0F0F0", "#E0FFE0", "#E0F0FF"]
        self.current_bg = 0
        self.reading_window = None
        self.after_id = None
        self.play_speed = 2000
        self.play_modes = ["顺序", "倒序", "随机"]
        self.current_mode = 0  # 0:顺序 1:倒序 2:随机
        self.speed预设列表 = [1000, 2000, 3000, 4000, 5000]  # 对应1-5秒/行
        self.current_speed预设 = 2  # 默认2秒/行（索引从0开始）

        # 创建界面控件
        self.create_widgets()

    def create_widgets(self):
        # 文件控制区
        file_frame = tk.Frame(self)
        file_frame.pack(pady=5)
        tk.Button(file_frame, text="打开文件", command=self.open_file).pack(side=tk.LEFT, padx=5)

        # 播放控制区
        control_frame = tk.Frame(self)
        control_frame.pack(pady=5)

        tk.Button(control_frame, text="暂停/播放", command=self.toggle_play).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="上一行", command=self.prev_line).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="下一行", command=self.next_line).pack(side=tk.LEFT, padx=5)

        # 模式控制区
        mode_frame = tk.Frame(self)
        mode_frame.pack(pady=5)

        self.mode_btn = tk.Button(mode_frame, text="模式：顺序",
                                  command=self.toggle_play_mode)
        self.mode_btn.pack(side=tk.LEFT, padx=5)

        # 设置区
        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=5)

        tk.Button(setting_frame, text="切换背景", command=self.change_bg).pack(side=tk.LEFT, padx=5)
        tk.Button(setting_frame, text="行数跳转", command=self.show_content_viewer).pack(side=tk.LEFT, padx=5)

        # 速度控制区修改为预设按钮
        speed_frame = tk.Frame(self)
        speed_frame.pack(pady=5)

        # 创建预设速度按钮
        self.speed_buttons = []
        for i, speed in enumerate([1000, 2000, 3000, 4000, 5000]):
            btn = tk.Button(speed_frame, text=f"{i + 1}s",
                            command=lambda s=speed: self.set_preset_speed(s))
            btn.pack(side=tk.LEFT, padx=5)
            self.speed_buttons.append(btn)

        # 更新速度显示标签
        self.speed_label = tk.Label(speed_frame, text="2.0秒/行")
        self.speed_label.pack(side=tk.LEFT)

    def toggle_play_mode(self):
        self.current_mode = (self.current_mode + 1) % 3
        mode_name = self.play_modes[self.current_mode]
        self.mode_btn.config(text=f"模式：{mode_name}")
        if self.is_playing:
            self.after_cancel(self.after_id)
            self.play_next_line()

    def get_next_line(self):
        total = len(self.file_content)
        if total == 0:
            return -1

        if self.play_modes[self.current_mode] == "顺序":
            return self.current_line + 1 if self.current_line < total - 1 else -1
        elif self.play_modes[self.current_mode] == "倒序":
            return self.current_line - 1 if self.current_line > 0 else -1
        else:  # 随机模式
            return random.randint(0, total - 1)

    def play_next_line(self):
        if not self.is_playing:
            return

        next_line = self.get_next_line()
        if next_line == -1:
            self.is_playing = False
            return

        self.current_line = next_line
        self.update_display()
        self.after_id = self.after(self.play_speed, self.play_next_line)

    def set_preset_speed(self, speed):
        """设置预设速度"""
        self.play_speed = speed
        self.last_speed = speed
        self.speed_label.config(text=f"{speed / 1000:.1f}秒/行")

        # 如果正在播放，需要调整定时器
        if self.is_playing and self.after_id:
            remaining = self.after_info(self.after_id)["remaining"]
            self.after_cancel(self.after_id)
            self.after_id = self.after(remaining, self.play_next_line)

    @property
    def total_lines(self):
        return len(self.file_content)

    def open_file(self):
        """打开文件"""
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filepath:
            return

        with open(filepath, "r", encoding="utf-8") as f:
            self.file_content = [line.strip() for line in f.readlines()]

        self.current_line = 0
        # 销毁旧的阅读窗口实例
        if self.reading_window:
            self.reading_window.destroy()
        # 创建新的阅读窗口
        self.reading_window = ReadingWindow(self)
        self.update_display()
        self.start_play()

    def update_display(self):
        """更新显示内容"""
        if not self.reading_window or not self.file_content:
            return
        if 0 <= self.current_line < len(self.file_content):
            self.reading_window.label.config(text=self.file_content[self.current_line])

    def start_play(self):
        """开始播放"""
        if not self.reading_window or not self.file_content:
            return
        self.is_playing = True
        self.play_next_line()

    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_next_line()
        else:
            if self.after_id:
                self.after_cancel(self.after_id)

    def next_line(self):
        next_line = self.get_next_line()
        if next_line != -1:
            self.current_line = next_line
            self.update_display()
        if self.is_playing:
            self.toggle_play()

    def prev_line(self):
        total = len(self.file_content)
        if total == 0:
            return

        # 独立实现上一行逻辑以保持直观操作
        if self.play_modes[self.current_mode] == "顺序":
            target = max(0, self.current_line - 1)
        elif self.play_modes[self.current_mode] == "倒序":
            target = min(total - 1, self.current_line + 1)
        else:
            target = random.randint(0, total - 1)

        self.current_line = target
        self.update_display()
        if self.is_playing:
            self.toggle_play()

    def change_bg(self):
        self.current_bg = (self.current_bg + 1) % len(self.bg_colors)
        if self.reading_window:
            color = self.bg_colors[self.current_bg]
            self.reading_window.config(bg=color)
            self.reading_window.label.config(bg=color)

    def show_content_viewer(self):
        if self.file_content:
            FileContentViewer(self, self.file_content, self.current_line)
        else:
            messagebox.showwarning("提示", "请先打开文件")

    def jump_to_line(self, line_num):
        if 0 <= line_num < self.total_lines:
            self.current_line = line_num
            self.update_display()
            if self.is_playing:
                self.after_cancel(self.after_id)
                self.play_next_line()


if __name__ == "__main__":
    app = App()
    app.mainloop()
