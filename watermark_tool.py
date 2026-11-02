# -*- coding: utf-8 -*-
"""
图片水印工具
- 图形化界面（Tkinter）
- 支持单选/多选图片
- 水印类型：文字 / 图片
- 透明度调节
- 平铺模式：疏密度、大小、角度
- 文字水印：颜色选择

设计方向：柔和精致风（暖色、圆润、轻松友好）
"""

import os
import math
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps

# 中文字体备选列表（按平台常见路径尝试；打包后优先用内置字体）
def _bundled_font_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "fonts")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


FONT_CANDIDATES = [
    os.path.join(_bundled_font_dir(), "NotoSansSC-Regular.otf"),  # 打包内置
    os.path.join(_bundled_font_dir(), "NotoSansSC-Regular.ttf"),
    os.path.join(_bundled_font_dir(), "SourceHanSansSC-Regular.otf"),
    "/System/Library/Fonts/PingFang.ttc",          # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",  # macOS
    "C:/Windows/Fonts/msyh.ttc",                   # Windows 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",                 # Windows 黑体
    "C:/Windows/Fonts/simsun.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux 文泉驿
]

UI_FONT = "Microsoft YaHei" if sys.platform.startswith("win") else "PingFang SC"


def find_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def open_image_rgba(path):
    """打开图片并按 EXIF 校正方向，转为 RGBA。"""
    img = Image.open(path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    return img.convert("RGBA")


class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片水印工具")
        self.root.minsize(940, 650)
        self.image_paths = []
        self.preview_photo = None
        self.watermark_image_path = None
        self.wm_preview_photo = None

        # 预览性能优化
        self._preview_job = None      # 防抖定时器
        self._base_cache = {}         # path -> (降采样底图, 缩放比)
        self._wm_img_cache = None     # 缓存已打开的水印图片

        # 科技蓝配色：冷静专业
        self.C = {
            "bg":        "#f4f6fa",  # 页面底色（冷灰白）
            "card":      "#ffffff",  # 卡片
            "primary":   "#2f6bff",  # 主色（科技蓝）
            "primary_dk":"#1f54d6",  # 主色深
            "secondary": "#e9eef7",  # 次级按钮底（浅蓝灰）
            "secondary_tx": "#5a6b82",  # 次级按钮文字
            "danger":    "#d64545",  # 强调（红）
            "text":      "#28323f",  # 正文（冷深灰蓝）
            "sub":       "#8a94a6",  # 次要文字
            "border":    "#e2e7f0",  # 边框
            "tint":      "#eef3fb",  # 浅色填充区（平铺参数面板）
            "tint_bdr":  "#d6e0f0",
            "select":    "#d9e6fd",  # 列表选中色
            "trough":    "#e4eaf4",  # 滑轨颜色
        }
        self.root.configure(bg=self.C["bg"])

        self.build_ui()
        # 窗口尺寸自适应内容，避免初始弹出时设置区被裁切
        self.root.update_idletasks()
        w = max(self.root.winfo_reqwidth(), 940)
        h = self.root.winfo_reqheight() + 10
        self.root.geometry(f"{w}x{h}")

    # ---------------- 通用控件 ----------------
    def styled_button(self, parent, text, command, bg=None, fg="#ffffff",
                      font=(UI_FONT, 11), padx=16):
        """自绘按钮：macOS 原生 tk.Button 背景色常失效，改用 Label 实现"""
        bg = bg or self.C["primary"]
        is_primary = bg == self.C["primary"]
        is_danger = bg == self.C["danger"]
        is_secondary = bg == self.C["secondary"]
        hover = (self.C["primary_dk"] if is_primary else
                 "#a84740" if is_danger else
                 "#d5deec" if is_secondary else bg)
        leave_fg = fg
        hover_fg = self.C["secondary_tx"] if is_secondary else fg

        btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=font,
                       padx=padx, pady=7, cursor="hand2")
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg=hover, fg=hover_fg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg, fg=leave_fg))
        return btn

    def segment_button(self, parent, text, value, variable, command):
        """分段选择按钮（用于水印类型切换），选中态为主色填充"""
        state = {"bg": self.C["secondary"], "fg": self.C["secondary_tx"]}
        btn = tk.Label(parent, text=text, padx=18, pady=6, cursor="hand2",
                       font=(UI_FONT, 11), **state)
        var_self = self

        def refresh():
            if variable.get() == value:
                btn.config(bg=var_self.C["primary"], fg="#ffffff",
                           font=(UI_FONT, 11, "bold"))
            else:
                btn.config(bg=var_self.C["secondary"], fg=var_self.C["secondary_tx"],
                           font=(UI_FONT, 11))

        def on_click():
            variable.set(value)
            # 刷新所有分段按钮，避免双选中态
            for seg in (getattr(var_self, "seg_text", None),
                        getattr(var_self, "seg_image", None)):
                if seg is not None and hasattr(seg, "refresh"):
                    seg.refresh()
            command()

        btn.bind("<Button-1>", lambda e: on_click())
        btn.refresh = refresh
        refresh()
        return btn

    def bind_live(self, widget):
        """让输入控件支持回车确认 + 输入实时刷新预览"""
        widget.bind("<Return>", lambda e: self.update_preview())
        widget.bind("<KeyRelease>", lambda e: self.update_preview())
        return widget

    def card(self, parent, **kw):
        """统一的卡片容器"""
        kw.setdefault("bg", self.C["card"])
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", self.C["border"])
        return tk.Frame(parent, **kw)

    # ---------------- UI ----------------
    def build_ui(self):
        C = self.C

        # 顶部标题栏
        header = tk.Frame(self.root, bg=C["bg"], padx=22)
        header.pack(fill=tk.X, pady=(16, 6))
        tk.Label(header, text="图片水印工具", bg=C["bg"], fg=C["text"],
                 font=(UI_FONT, 17, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="●", bg=C["bg"], fg=C["primary"],
                 font=(UI_FONT, 9)).pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="文字 / 图片水印 · 平铺 · 批量导出",
                 bg=C["bg"], fg=C["sub"],
                 font=(UI_FONT, 10)).pack(side=tk.LEFT)

        # 文件选择工具栏
        top = tk.Frame(self.root, bg=C["bg"], padx=22, pady=8)
        top.pack(fill=tk.X)
        self.styled_button(top, "＋ 选择图片（可多选）", self.choose_images).pack(side=tk.LEFT)
        self.styled_button(top, "移除选中", self.remove_selected,
                           bg=C["secondary"], fg=C["secondary_tx"]).pack(side=tk.LEFT, padx=8)
        self.styled_button(top, "清空列表", self.clear_list,
                           bg=C["secondary"], fg=C["secondary_tx"]).pack(side=tk.LEFT)
        self.count_label = tk.Label(top, text="共 0 张图片", fg=C["sub"],
                                    bg=C["bg"], font=(UI_FONT, 10))
        self.count_label.pack(side=tk.LEFT, padx=16)

        # 中部：左侧文件列表 + 右侧预览
        mid = tk.Frame(self.root, bg=C["bg"], padx=22)
        mid.pack(fill=tk.BOTH, expand=True)

        # 文件列表卡片（含滚动条）
        list_frame = self.card(mid)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14), pady=4)
        tk.Label(list_frame, text="图片列表", bg=C["card"], fg=C["text"],
                 font=(UI_FONT, 11, "bold"), anchor=tk.W,
                 padx=14).pack(fill=tk.X, pady=(10, 4))
        list_body = tk.Frame(list_frame, bg=C["card"])
        list_body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 12))
        self.file_scroll = tk.Scrollbar(list_body, orient=tk.VERTICAL,
                                        bg=C["card"], troughcolor=C["trough"],
                                        activebackground=C["primary"],
                                        highlightthickness=0, bd=0)
        self.file_listbox = tk.Listbox(list_body, width=36, selectmode=tk.EXTENDED,
                                       exportselection=False, bd=0,
                                       bg=C["card"], fg=C["text"],
                                       selectbackground=C["select"],
                                       selectforeground=C["text"],
                                       font=(UI_FONT, 11),
                                       highlightthickness=0,
                                       activestyle="none",
                                       yscrollcommand=self.file_scroll.set)
        self.file_scroll.config(command=self.file_listbox.yview)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_select_file)

        # 预览区卡片
        preview_frame = self.card(mid)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=4)
        tk.Label(preview_frame, text="预览 · 选中图片后实时显示水印效果",
                 bg=C["card"], fg=C["sub"], font=(UI_FONT, 10),
                 anchor=tk.W, padx=14).pack(fill=tk.X, pady=(10, 4))
        self.preview_label = tk.Label(preview_frame, bg=C["tint"],
                                      fg=C["sub"], text="选择图片开始预览")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 12))
        preview_frame.pack_propagate(False)
        preview_frame.configure(height=360)

        # 参数区：左栏主设置 + 右栏平铺参数
        params = self.card(self.root)
        params.pack(fill=tk.X, padx=22, pady=8)
        tk.Label(params, text="水印设置", bg=C["card"], fg=C["primary"],
                 font=(UI_FONT, 11, "bold"), anchor=tk.W,
                 padx=16).grid(row=0, column=0, columnspan=2,
                               sticky=tk.W, pady=(12, 8))

        def lbl(parent, **kw):
            kw.setdefault("fg", C["text"])
            kw.setdefault("font", (UI_FONT, 11))
            kw.setdefault("anchor", tk.E)
            return tk.Label(parent, bg=parent["bg"], **kw)

        def spin(parent, **kw):
            kw.setdefault("relief", tk.FLAT)
            kw.setdefault("bg", C["tint"])
            kw.setdefault("fg", C["text"])
            kw.setdefault("buttonbackground", C["secondary"])
            kw.setdefault("highlightthickness", 1)
            kw.setdefault("highlightbackground", C["border"])
            kw.setdefault("font", (UI_FONT, 11))
            return tk.Spinbox(parent, **kw)

        # ---- 左栏：主设置 ----
        left = tk.Frame(params, bg=C["card"])
        left.grid(row=1, column=0, sticky=tk.NW, padx=(18, 6), pady=(0, 14))
        left.grid_columnconfigure(0, minsize=88)
        left.grid_columnconfigure(1, minsize=250)

        # 水印类型：分段切换按钮
        lbl(left, text="类型").grid(row=0, column=0, sticky=tk.E, pady=7)
        seg = tk.Frame(left, bg=C["card"])
        seg.grid(row=0, column=1, sticky=tk.W)
        self.wm_type = tk.StringVar(value="text")
        self.seg_text = self.segment_button(seg, "文字", "text", self.wm_type, self.on_type_change)
        self.seg_text.pack(side=tk.LEFT)
        self.seg_image = self.segment_button(seg, "图片", "image", self.wm_type, self.on_type_change)
        self.seg_image.pack(side=tk.LEFT, padx=(6, 0))

        # ---- 文字水印设置区（选择"文字"时显示）----
        self.text_frame = tk.Frame(left, bg=C["card"])
        self.text_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        self.text_frame.grid_columnconfigure(0, minsize=88)

        lbl(self.text_frame, text="水印文字").grid(row=0, column=0, sticky=tk.E, pady=7)
        self.text_var = tk.StringVar(value="水印文字")
        self.text_entry = tk.Entry(self.text_frame, textvariable=self.text_var, width=28,
                                   relief=tk.FLAT, bg=C["tint"], fg=C["text"],
                                   insertbackground=C["text"],
                                   highlightthickness=1, highlightbackground=C["border"],
                                   highlightcolor=C["primary"],
                                   font=(UI_FONT, 11))
        self.text_entry.grid(row=0, column=1, sticky=tk.W)
        self.bind_live(self.text_entry)

        lbl(self.text_frame, text="文字大小").grid(row=1, column=0, sticky=tk.E, pady=7)
        size_row = tk.Frame(self.text_frame, bg=C["card"])
        size_row.grid(row=1, column=1, sticky=tk.W)
        self.font_size = tk.IntVar(value=48)
        self.bind_live(spin(size_row, from_=8, to=500, textvariable=self.font_size,
                            width=6, command=self.update_preview)
                       ).grid(row=0, column=0)
        lbl(size_row, text="px", fg=C["sub"], anchor=tk.W).grid(row=0, column=1, sticky=tk.W, padx=(6, 0))

        lbl(self.text_frame, text="文字颜色").grid(row=2, column=0, sticky=tk.E, pady=7)
        color_row = tk.Frame(self.text_frame, bg=C["card"])
        color_row.grid(row=2, column=1, sticky=tk.W)
        self.color_var = tk.StringVar(value="#FF0000")
        self.color_button = self.styled_button(color_row, "选择颜色",
                                               self.choose_color, bg=self.color_var.get(),
                                               font=(UI_FONT, 10), padx=12)
        self.color_button.grid(row=0, column=0)
        self.color_label = lbl(color_row, textvariable=self.color_var, fg=C["sub"], anchor=tk.W)
        self.color_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        # ---- 图片水印设置区（选择"图片"时显示）----
        self.image_frame = tk.Frame(left, bg=C["card"])
        self.image_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        self.image_frame.grid_columnconfigure(0, minsize=88)

        lbl(self.image_frame, text="水印图片").grid(row=0, column=0, sticky=tk.E, pady=7)
        img_row = tk.Frame(self.image_frame, bg=C["card"])
        img_row.grid(row=0, column=1, sticky=tk.W)
        self.wm_img_button = self.styled_button(img_row, "选择图片（支持 PNG 透明底）",
                                                self.choose_watermark_image,
                                                font=(UI_FONT, 10))
        self.wm_img_button.grid(row=0, column=0)
        self.wm_img_label = lbl(img_row, text="未选择", fg=C["sub"], anchor=tk.W)
        self.wm_img_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        # 图片水印大小(%)：始终在图片设置区可见（平铺/非平铺均生效）
        lbl(self.image_frame, text="大小(%)").grid(row=1, column=0, sticky=tk.E, pady=7)
        scale_row = tk.Frame(self.image_frame, bg=C["card"])
        scale_row.grid(row=1, column=1, sticky=tk.W)
        self.wm_scale = tk.IntVar(value=20)
        self.bind_live(spin(scale_row, from_=1, to=100, textvariable=self.wm_scale,
                            width=6, command=self.update_preview)
                       ).grid(row=0, column=0)
        lbl(scale_row, text="相对图片宽度", fg=C["sub"], anchor=tk.W).grid(
            row=0, column=1, sticky=tk.W, padx=(6, 0))

        # 透明度
        lbl(left, text="透明度").grid(row=2, column=0, sticky=tk.E, pady=7)
        op_row = tk.Frame(left, bg=C["card"])
        op_row.grid(row=2, column=1, sticky=tk.W)
        self.opacity = tk.IntVar(value=80)
        self.opacity_scale = tk.Scale(op_row, from_=0, to=100, orient=tk.HORIZONTAL,
                                      variable=self.opacity, length=190,
                                      bg=C["card"], fg=C["text"], troughcolor=C["trough"],
                                      highlightthickness=0, showvalue=False,
                                      sliderrelief=tk.FLAT, width=10,
                                      command=lambda v: self.update_preview())
        self.opacity_scale.grid(row=0, column=0)
        self.opacity_value = tk.Label(op_row, text="80%", bg=C["card"], fg=C["sub"],
                                      font=(UI_FONT, 10), width=4, anchor=tk.W)
        self.opacity_value.grid(row=0, column=1, sticky=tk.W, padx=(6, 0))
        self.opacity.trace_add("write",
                               lambda *_: self.opacity_value.config(text=f"{self.opacity.get()}%"))

        # 平铺开关
        lbl(left, text="平铺水印").grid(row=3, column=0, sticky=tk.E, pady=7)
        self.tile_var = tk.BooleanVar(value=False)
        self.tile_check = tk.Checkbutton(left, text="平铺整个图片（关闭时水印居中）",
                                         variable=self.tile_var,
                                         command=self.on_tile_change, bg=C["card"],
                                         fg=C["text"], font=(UI_FONT, 11),
                                         selectcolor=C["tint"],
                                         activebackground=C["card"],
                                         activeforeground=C["text"])
        self.tile_check.grid(row=3, column=1, sticky=tk.W)

        # ---- 右栏：平铺参数（勾选平铺时显示；大小%已移至图片设置）----
        self.tile_frame = tk.Frame(params, bg=C["tint"], highlightthickness=1,
                                   highlightbackground=C["tint_bdr"])
        self.tile_frame.grid(row=1, column=1, sticky=tk.NW, padx=(14, 18), pady=(4, 14))
        self.tile_frame.grid_columnconfigure(0, minsize=104)

        tk.Label(self.tile_frame, text="平铺参数", bg=C["tint"], fg=C["primary"],
                 font=(UI_FONT, 10, "bold")).grid(row=0, column=0, columnspan=2,
                                                  sticky=tk.W, padx=14, pady=(10, 8))

        def tlbl(text, row):
            tk.Label(self.tile_frame, text=text, bg=C["tint"], fg=C["text"],
                     font=(UI_FONT, 10), anchor=tk.E).grid(row=row, column=0,
                                                           sticky=tk.E, padx=(14, 0), pady=6)

        tlbl("间距(px)", 1)
        self.spacing = tk.IntVar(value=150)
        self.bind_live(spin(self.tile_frame, from_=20, to=2000, textvariable=self.spacing,
                            width=8, command=self.update_preview,
                            font=(UI_FONT, 10))).grid(row=1, column=1, sticky=tk.W, padx=(8, 14))

        tlbl("角度(°)", 2)
        self.angle = tk.IntVar(value=-30)
        self.bind_live(spin(self.tile_frame, from_=-180, to=180, textvariable=self.angle,
                            width=8, command=self.update_preview,
                            font=(UI_FONT, 10))).grid(row=2, column=1, sticky=tk.W, padx=(8, 14))

        # 底部：操作
        bottom = tk.Frame(self.root, bg=C["bg"], padx=22)
        bottom.pack(fill=tk.X, pady=(4, 16))
        self.styled_button(bottom, "应用水印并导出", self.apply_watermark,
                           bg=C["primary"], font=(UI_FONT, 13, "bold"),
                           padx=30).pack(side=tk.RIGHT)
        self.styled_button(bottom, "↻ 刷新预览", self.update_preview,
                           bg=C["secondary"], fg=C["secondary_tx"],
                           font=(UI_FONT, 11)).pack(side=tk.RIGHT, padx=10)

        # 初始化显隐状态
        self.on_tile_change()
        self.on_type_change()

        # 锁定动态区行高：文字与图片切换时不引起布局上下跳动
        self.root.update_idletasks()
        dyn_h = max(self.text_frame.winfo_reqheight(),
                    self.image_frame.winfo_reqheight())
        left.grid_rowconfigure(1, minsize=dyn_h)

    # ---------------- 事件 ----------------
    def choose_images(self):
        paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp *.tiff"), ("所有文件", "*.*")]
        )
        for p in paths:
            if p not in self.image_paths:
                self.image_paths.append(p)
                self.file_listbox.insert(tk.END, os.path.basename(p))
        self.update_count()
        if paths:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(tk.END)
            self.update_preview()

    def remove_selected(self):
        sel = list(self.file_listbox.curselection())
        if not sel:
            return
        first_removed = min(sel)
        for i in sorted(sel, reverse=True):
            self.file_listbox.delete(i)
            self.image_paths.pop(i)
        self.update_count()
        if self.image_paths:
            idx = min(first_removed, len(self.image_paths) - 1)
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(idx)
            self.file_listbox.activate(idx)
            self.file_listbox.see(idx)
            self.update_preview()
        else:
            self.preview_label.config(image="", text="选择图片开始预览")
            self.preview_photo = None

    def clear_list(self):
        self.file_listbox.delete(0, tk.END)
        self.image_paths.clear()
        self._base_cache.clear()
        self.update_count()
        self.preview_label.config(image="", text="选择图片开始预览")
        self.preview_photo = None

    def update_count(self):
        self.count_label.config(text=f"共 {len(self.image_paths)} 张图片")

    def on_select_file(self, _event=None):
        self.update_preview()

    def current_path(self):
        sel = self.file_listbox.curselection()
        if not sel:
            return None
        return self.image_paths[sel[0]]

    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color and color[1]:
            self.color_var.set(color[1])
            btn = self.color_button
            try:
                btn.config(bg=color[1])
            except Exception:
                pass
            # 更新悬停效果为新颜色
            btn.bind("<Enter>", lambda e: btn.config(bg=self.C["primary_dk"]))
            btn.bind("<Leave>", lambda e: btn.config(bg=self.color_var.get()))
            self.update_preview()

    def choose_watermark_image(self):
        path = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp"), ("所有文件", "*.*")]
        )
        if path:
            self.watermark_image_path = path
            self._wm_img_cache = None  # 强制重新加载
            self.wm_img_label.config(text=os.path.basename(path), fg=self.C["text"])
            self.update_preview()

    def on_type_change(self):
        # 注意：grid() 不带参数会回到默认 row0/col0 导致布局错乱，
        # 恢复显示时必须携带原始的 grid 参数
        is_text = self.wm_type.get() == "text"
        if is_text:
            self.text_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W)
            self.image_frame.grid_remove()
        else:
            self.text_frame.grid_remove()
            self.image_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        # 同步分段按钮外观
        if hasattr(self, "seg_text"):
            self.seg_text.refresh()
        if hasattr(self, "seg_image"):
            self.seg_image.refresh()
        self.update_preview()

    def on_tile_change(self):
        if self.tile_var.get():
            self.tile_frame.grid(row=1, column=1, sticky=tk.NW,
                                 padx=(14, 18), pady=(4, 14))
        else:
            self.tile_frame.grid_remove()
        self.update_preview()

    # ---------------- 水印核心 ----------------
    def build_watermark_layer(self, base_size, scale=1.0):
        """生成整图大小的水印图层（RGBA），返回 None 表示无法生成。
        scale: 预览时底图已降采样，水印绝对尺寸参数（字号/间距）按此比例缩小，
        保证预览效果与导出一致；导出时 scale=1。"""
        bw, bh = base_size
        opacity = self.opacity.get() / 100.0
        if opacity <= 0:
            return None

        is_text = self.wm_type.get() == "text"
        tile = self.tile_var.get()
        # 角度仅在平铺模式下生效；非平铺居中不旋转
        angle = self.angle.get() if tile else 0
        scale_pct = self.wm_scale.get()

        # 1) 生成单个水印元素 tile_elem (RGBA)
        if is_text:
            text = self.text_var.get().strip()
            if not text:
                return None
            font_size = max(6, int(self.font_size.get() * scale))
            font = find_font(font_size)
            # 测量文字大小
            tmp = Image.new("RGBA", (10, 10))
            d = ImageDraw.Draw(tmp)
            try:
                bbox = d.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                offset = bbox[:2]
            except AttributeError:
                tw, th = d.textsize(text, font=font)
                offset = (0, 0)
            elem = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
            d = ImageDraw.Draw(elem)
            r, g, b = self._hex_to_rgb(self.color_var.get())
            d.text((10 - offset[0], 10 - offset[1]), text, font=font,
                   fill=(r, g, b, int(255 * opacity)))
            tile_elem = elem
        else:
            if not self.watermark_image_path:
                return None
            # 缓存已打开的水印图片，避免每次重复解码
            if self._wm_img_cache is None or self._wm_img_cache[0] != self.watermark_image_path:
                try:
                    self._wm_img_cache = (self.watermark_image_path,
                                          open_image_rgba(self.watermark_image_path))
                except Exception as e:
                    messagebox.showerror("错误", f"水印图片打开失败：{e}")
                    return None
            wm = self._wm_img_cache[1]
            # 大小：按基准尺寸缩放（相对宽度，天然适配预览降采样）
            target_w = max(20, int(bw * scale_pct / 100))
            ratio = target_w / wm.width
            target_h = max(10, int(wm.height * ratio))
            tile_elem = wm.resize((target_w, target_h), Image.LANCZOS)
            # 应用透明度
            alpha = tile_elem.split()[3].point(lambda a: int(a * opacity))
            tile_elem.putalpha(alpha)

        # 2) 旋转（仅平铺）
        if tile and angle:
            tile_elem = tile_elem.rotate(angle, expand=True,
                                         resample=Image.BICUBIC)

        # 3) 生成整图层
        layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))

        if tile:
            spacing = max(int(self.spacing.get() * scale), 4)
            ew, eh = tile_elem.size
            step_x = ew + spacing
            step_y = eh + spacing
            # 居中偏移，让平铺更美观
            cols = math.ceil(bw / step_x) + 2
            rows = math.ceil(bh / step_y) + 2
            start_x = -((cols - 1) * step_x - bw) // 2
            start_y = -((rows - 1) * step_y - bh) // 2
            for ry in range(rows):
                for rx in range(cols):
                    x = start_x + rx * step_x
                    y = start_y + ry * step_y
                    layer.alpha_composite(tile_elem, (int(x), int(y)))
        else:
            # 居中放置（单个，不旋转）
            elem = tile_elem
            x = (bw - elem.width) // 2
            y = (bh - elem.height) // 2
            layer.alpha_composite(elem, (max(0, x), max(0, y)))

        return layer

    def _hex_to_rgb(self, hexstr):
        try:
            h = hexstr.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        except Exception:
            return (255, 0, 0)

    # ---------------- 预览 ----------------
    def update_preview(self, *_args):
        """带 120ms 防抖的预览调度：切换/输入/拖滑块时合并高频刷新，
        只有停下来才真正渲染，界面始终保持响应。"""
        if self._preview_job is not None:
            self.root.after_cancel(self._preview_job)
        self._preview_job = self.root.after(120, self._render_preview)

    def _render_preview(self):
        self._preview_job = None
        path = self.current_path()
        if not path:
            return

        # 底图缓存：按预览尺寸降采样一次，后续刷新不再解码原图
        entry = self._base_cache.get(path)
        if entry is None:
            try:
                img = open_image_rgba(path)
            except Exception as e:
                self.preview_label.config(image="", text=f"无法打开：{e}")
                return
            ratio = min(1.0, 1400 / max(img.size))
            if ratio < 1.0:
                img = img.resize((max(1, int(img.width * ratio)),
                                  max(1, int(img.height * ratio))), Image.LANCZOS)
            entry = (img, ratio)
            # 简单限制缓存数量
            if len(self._base_cache) > 20:
                self._base_cache.clear()
            self._base_cache[path] = entry

        img, ratio = entry
        layer = self.build_watermark_layer(img.size, scale=ratio)
        if layer is not None:
            img = Image.alpha_composite(img, layer)

        # 缩放到预览区
        label_w = max(self.preview_label.winfo_width(), 400)
        label_h = max(self.preview_label.winfo_height(), 300)
        img.thumbnail((label_w, label_h), Image.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self.preview_photo, text="")

    # ---------------- 导出 ----------------
    def apply_watermark(self):
        if not self.image_paths:
            messagebox.showwarning("提示", "请先选择要添加水印的图片！")
            return
        if self.wm_type.get() == "text" and not self.text_var.get().strip():
            messagebox.showwarning("提示", "请输入水印文字！")
            return
        if self.wm_type.get() == "image" and not self.watermark_image_path:
            messagebox.showwarning("提示", "请选择水印图片！")
            return
        if self.opacity.get() <= 0:
            messagebox.showwarning("提示", "透明度为 0，水印不可见。请调高透明度后再导出。")
            return

        out_dir = filedialog.askdirectory(title="选择导出文件夹")
        if not out_dir:
            return

        success, failed, skipped = 0, [], []
        for path in self.image_paths:
            try:
                img = open_image_rgba(path)
                layer = self.build_watermark_layer(img.size)
                if layer is not None:
                    img = Image.alpha_composite(img, layer)
                name, ext = os.path.splitext(os.path.basename(path))
                ext_lower = ext.lower()
                # PNG/WebP/TIFF 保留透明通道；JPEG 转 RGB；其余默认导出 PNG(RGBA)
                if ext_lower in (".jpg", ".jpeg"):
                    out_ext = ".jpg"
                    out_path = os.path.join(out_dir, f"{name}_watermarked{out_ext}")
                    if os.path.exists(out_path):
                        skipped.append(os.path.basename(out_path))
                    img.convert("RGB").save(out_path, quality=95)
                elif ext_lower in (".png", ".webp", ".tiff", ".tif"):
                    out_ext = ".tiff" if ext_lower == ".tif" else ext_lower
                    out_path = os.path.join(out_dir, f"{name}_watermarked{out_ext}")
                    if os.path.exists(out_path):
                        skipped.append(os.path.basename(out_path))
                    save_kw = {}
                    if out_ext == ".webp":
                        save_kw["quality"] = 95
                    img.save(out_path, **save_kw)
                else:
                    out_path = os.path.join(out_dir, f"{name}_watermarked.png")
                    if os.path.exists(out_path):
                        skipped.append(os.path.basename(out_path))
                    img.save(out_path)
                success += 1
            except Exception as e:
                failed.append(f"{os.path.basename(path)}: {e}")

        msg = f"完成！成功 {success} 张，导出至：\n{out_dir}"
        if skipped:
            msg += "\n\n注意：以下文件已存在并被覆盖：\n" + "\n".join(skipped[:10])
            if len(skipped) > 10:
                msg += f"\n…共 {len(skipped)} 个"
        if failed:
            msg += "\n\n失败：\n" + "\n".join(failed)
        messagebox.showinfo("导出结果", msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()
