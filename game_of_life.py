"""
康威生命游戏 (Conway's Game of Life) — 元胞自动机演示
运行: python game_of_life.py
操作:
  - 鼠标左键点击 / 拖拽: 点亮/擦除细胞
  - 空格: 开始/暂停 | S: 单步 | C: 清空 | R: 随机 | Q: 滑翔机枪
"""
import tkinter as tk
from tkinter import ttk
import random

# 经典 B3/S23 规则，也可以在界面上改
DEFAULT_BIRTH = {3}
DEFAULT_SURVIVE = {2, 3}

CELL = 12          # 每个格子像素大小
COLS, ROWS = 70, 45


class LifeGame:
    def __init__(self, root):
        self.root = root
        root.title("元胞自动机 — 康威生命游戏")
        root.resizable(False, False)

        self.birth = set(DEFAULT_BIRTH)
        self.survive = set(DEFAULT_SURVIVE)
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.running = False
        self.generation = 0
        self.speed_ms = 80
        self.draw_mode = 1  # 按下时画1还是画0，视首个格子而定

        # ---------- 画布 ----------
        self.canvas = tk.Canvas(root, width=COLS * CELL, height=ROWS * CELL,
                                bg="#111318", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.rect_ids = [[None] * COLS for _ in range(ROWS)]

        # ---------- 控制栏 ----------
        bar = ttk.Frame(root)
        bar.pack(fill="x", padx=10, pady=(0, 6))

        self.btn_run = ttk.Button(bar, text="▶ 开始", command=self.toggle, width=10)
        self.btn_run.pack(side="left", padx=2)
        ttk.Button(bar, text="单步", command=self.step_once, width=8).pack(side="left", padx=2)
        ttk.Button(bar, text="随机", command=self.random_fill, width=8).pack(side="left", padx=2)
        ttk.Button(bar, text="清空", command=self.clear, width=8).pack(side="left", padx=2)

        ttk.Label(bar, text="速度:").pack(side="left", padx=(10, 0))
        self.speed = ttk.Scale(bar, from_=10, to=300, value=self.speed_ms,
                               orient="horizontal", length=110,
                               command=self.on_speed)
        self.speed.pack(side="left")

        ttk.Label(bar, text="密度:").pack(side="left", padx=(10, 0))
        self.density = ttk.Scale(bar, from_=5, to=60, value=18,
                                 orient="horizontal", length=90)
        self.density.pack(side="left")

        # ---------- 预设 ----------
        bar2 = ttk.Frame(root)
        bar2.pack(fill="x", padx=10, pady=(0, 6))
        for name, fn in [("滑翔机", self.put_glider), ("滑翔机枪", self.put_gun),
                         ("脉冲星", self.put_pulsar), ("随机汤", self.random_fill),
                         ("昼与夜", self.put_day_night)]:
            ttk.Button(bar2, text=name, command=fn, width=10).pack(side="left", padx=2)

        self.info = ttk.Label(bar2, text="第 0 代 · 存活 0")
        self.info.pack(side="right", padx=4)

        # ---------- 规则 ----------
        bar3 = ttk.Frame(root)
        bar3.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(bar3, text="Birth (B):").pack(side="left")
        self.e_birth = ttk.Entry(bar3, width=8)
        self.e_birth.insert(0, "3")
        self.e_birth.pack(side="left", padx=4)
        ttk.Label(bar3, text="Survive (S):").pack(side="left")
        self.e_survive = ttk.Entry(bar3, width=8)
        self.e_survive.insert(0, "23")
        self.e_survive.pack(side="left", padx=4)
        ttk.Button(bar3, text="应用规则", command=self.apply_rule).pack(side="left", padx=4)
        ttk.Label(bar3, text="空格=运行/暂停  S=单步  C=清空  R=随机",
                  foreground="gray").pack(side="right")

        root.bind("<space>", lambda e: self.toggle())
        root.bind("s", lambda e: self.step_once())
        root.bind("S", lambda e: self.step_once())
        root.bind("c", lambda e: self.clear())
        root.bind("C", lambda e: self.clear())
        root.bind("r", lambda e: self.random_fill())
        root.bind("R", lambda e: self.random_fill())

        self.put_gun()
        self.draw_all()
        self.loop()

    # ---------- 核心演化 ----------
    def next_gen(self):
        B, S = self.birth, self.survive
        g = self.grid
        new = [[0] * COLS for _ in range(ROWS)]
        for y in range(ROWS):
            for x in range(COLS):
                n = (g[y-1][x-1] + g[y-1][x] + g[y-1][(x+1) % COLS] +
                     g[y][x-1] + g[y][(x+1) % COLS] +
                     g[(y+1) % ROWS][x-1] + g[(y+1) % ROWS][x] + g[(y+1) % ROWS][(x+1) % COLS])
                if g[y][x]:
                    new[y][x] = 1 if n in S else 0
                else:
                    new[y][x] = 1 if n in B else 0
        self.grid = new
        self.generation += 1

    # ---------- 渲染 ----------
    def draw_all(self):
        self.canvas.delete("all")
        self.rect_ids = [[None] * COLS for _ in range(ROWS)]
        pop = 0
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x]:
                    pop += 1
                    self.canvas.create_rectangle(
                        x * CELL, y * CELL, x * CELL + CELL - 1, y * CELL + CELL - 1,
                        fill="#4ade80", outline="#22c55e")
        self.info.config(text=f"第 {self.generation} 代 · 存活 {pop}")

    def draw_cell(self, x, y):
        # 增量重绘：简单起见直接重画全部（70x45 很小，足够流畅）
        pass

    # ---------- 交互 ----------
    def cell_at(self, event):
        return min(event.x // CELL, COLS - 1), min(event.y // CELL, ROWS - 1)

    def on_click(self, event):
        x, y = self.cell_at(event)
        self.draw_mode = 0 if self.grid[y][x] else 1
        self.grid[y][x] = self.draw_mode
        self.draw_all()

    def on_drag(self, event):
        x, y = self.cell_at(event)
        if 0 <= x < COLS and 0 <= y < ROWS and self.grid[y][x] != self.draw_mode:
            self.grid[y][x] = self.draw_mode
            self.draw_all()

    def toggle(self):
        self.running = not self.running
        self.btn_run.config(text="⏸ 暂停" if self.running else "▶ 开始")

    def step_once(self):
        self.next_gen()
        self.draw_all()

    def loop(self):
        if self.running:
            self.next_gen()
            self.draw_all()
        self.root.after(int(self.speed_ms), self.loop)

    def on_speed(self, v):
        # 滑杆向右越快：取反映射
        self.speed_ms = 310 - float(v)

    def clear(self):
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.generation = 0
        self.draw_all()

    def random_fill(self, density=None):
        if density is None:
            density = float(self.density.get()) / 100.0
        self.clear()
        for y in range(ROWS):
            for x in range(COLS):
                self.grid[y][x] = 1 if random.random() < density else 0
        self.draw_all()

    def apply_rule(self):
        try:
            self.birth = {int(c) for c in self.e_birth.get() if c.isdigit()}
            self.survive = {int(c) for c in self.e_survive.get() if c.isdigit()}
        except ValueError:
            pass

    # ---------- 预设图案 ----------
    def stamp(self, ox, oy, cells):
        for dx, dy in cells:
            x, y = (ox + dx) % COLS, (oy + dy) % ROWS
            self.grid[y][x] = 1

    def put_glider(self):
        self.clear()
        self.stamp(COLS // 2, ROWS // 2, [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)])
        self.draw_all()

    def put_pulsar(self):
        self.clear()
        cx, cy = COLS // 2 - 6, ROWS // 2 - 6
        pts = []
        off = [0, 1, 2, 6, 7, 8]
        for dx in off:
            for dy in (4, 5, 10, 11):
                pts += [(dx, dy), (dy, dx)]
        # 上面循环 (dy,dx) 会把 4,5,10,11 也展开，实际就是标准 Pulsar，微调去重即可
        uniq = list({(cx + dx, cy + dy) for dx, dy in pts})
        for x, y in uniq:
            self.grid[y % ROWS][x % COLS] = 1
        self.draw_all()

    def put_day_night(self):
        """Day & Night 规则 + 半满开局，一键出效果"""
        self.e_birth.delete(0, "end")
        self.e_birth.insert(0, "3678")
        self.e_survive.delete(0, "end")
        self.e_survive.insert(0, "34678")
        self.apply_rule()
        self.density.set(50)
        self.random_fill(density=0.50)

    def put_gun(self):
        self.clear()
        gun = [(0, 4), (0, 5), (1, 4), (1, 5), (10, 4), (10, 5), (10, 6),
               (11, 3), (11, 7), (12, 2), (12, 8), (13, 2), (13, 8),
               (14, 5), (15, 3), (15, 7), (16, 4), (16, 5), (16, 6),
               (17, 5), (20, 2), (20, 3), (20, 4), (21, 2), (21, 3),
               (21, 4), (22, 1), (22, 5), (24, 0), (24, 1), (24, 5),
               (24, 6), (34, 2), (34, 3), (35, 2), (35, 3)]
        self.stamp(5, ROWS // 2 - 5, gun)
        self.draw_all()


if __name__ == "__main__":
    root = tk.Tk()
    LifeGame(root)
    root.mainloop()
