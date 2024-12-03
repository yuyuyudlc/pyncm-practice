import tkinter as tk
from tkinter import ttk
from login import LoginWindow
from search_and_player import SearchAndPlayer
from utils import center_window
from play_list import PlayList


class MusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云音乐播放器")
        # 设置窗口最小尺寸
        self.root.minsize(1026, 731)
        self.root.geometry("1026x731")
        # 设置窗口背景色
        self.root.configure(bg='#f0f0f0')
        center_window(self.root, 1026, 731)

        # 隐藏主窗口，登录成功后显示
        self.root.withdraw()

        # 初始化播放器和其他控件
        self.player_instance = None
        self.playlist_instance = None
        self.create_widgets()

        # 打开登录窗口
        self.open_login_window()

    def open_login_window(self):
        """打开登录窗口"""
        LoginWindow(self.root, self.login_success)

    def login_success(self):
        """登录成功后回调函数"""
        self.root.deiconify()  # 显示主窗口
        self.player_instance = SearchAndPlayer(
            self.root,
            self.progress_bar,
            self.lyrics_text,
            self.album_cover_label,
            self.label_current_length,
            self.label_total_length,
            self.tree_results
        )
        self.playlist_instance = PlayList(self.root, self.tree_results, self.player_instance)

    def create_widgets(self):
        """创建主窗口的控件"""
        # 设置统一的样式
        style = ttk.Style()
        style.configure('TButton', padding=6)
        style.configure('TEntry', padding=5)
        style.configure('TProgressbar', thickness=8)

        # 左侧布局
        frame_left = tk.Frame(self.root, bg='#f0f0f0')
        frame_left.pack(side="left", fill="both", expand=True, padx=15)

        # 搜索框部分
        frame_search = tk.LabelFrame(frame_left, text="搜索歌曲", padx=15, pady=15, bg='#f0f0f0')
        frame_search.pack(pady=15, fill="x")

        # 美化搜索框和按钮
        tk.Label(frame_search, text="歌曲名称:", bg='#f0f0f0').grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.entry_search = ttk.Entry(frame_search, width=35)
        self.entry_search.grid(row=0, column=1, padx=8, pady=8)
        
        self.btn_search = ttk.Button(
            frame_search,
            text="搜索",
            command=lambda: self.player_instance.search_songs(self.tree_results, self.entry_search)
        )
        self.btn_search.grid(row=0, column=2, padx=8, pady=8)

        # 搜索结果列表
        frame_results = tk.LabelFrame(frame_left, text="搜索结果", padx=15, pady=15, bg='#f0f0f0')
        frame_results.pack(pady=15, fill="both", expand=True)

        # 美化树形视图
        style.configure("Treeview", rowheight=25, font=('Arial', 10))
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        self.tree_results = ttk.Treeview(frame_results, columns=("song_id", "description"), show="headings")
        self.tree_results.heading("song_id", text="歌曲ID")
        self.tree_results.heading("description", text="描述")
        self.tree_results.column("song_id", width=100)
        self.tree_results.column("description", width=350)
        self.tree_results.pack(fill="both", expand=True)

        # 分页按钮
        frame_pagination = tk.Frame(frame_left, bg='#f0f0f0')
        frame_pagination.pack(pady=10)

        self.btn_prev_page = ttk.Button(
            frame_pagination,
            text="上一页",
            command=lambda: self.player_instance.prev_page(self.tree_results)
        )
        self.btn_prev_page.grid(row=0, column=0, padx=8)

        self.btn_next_page = ttk.Button(
            frame_pagination,
            text="下一页",
            command=lambda: self.player_instance.next_page(self.tree_results)
        )
        self.btn_next_page.grid(row=0, column=1, padx=8)

        # 控制钮部分
        frame_controls = tk.Frame(frame_left, bg='#f0f0f0')
        frame_controls.pack(pady=15)

        self.btn_play = ttk.Button(
            frame_controls,
            text="播放",
            command=lambda: self.player_instance.play_selected_song(self.tree_results)
        )
        self.btn_play.grid(row=0, column=0, padx=12)

        self.btn_pause = ttk.Button(frame_controls, text="暂停", command=self.toggle_pause)
        self.btn_pause.grid(row=0, column=1, padx=12)

        self.btn_playlist = ttk.Button(
            frame_controls,
            text="歌单",
            command=self.show_playlist
        )
        self.btn_playlist.grid(row=0, column=2, padx=12)

        self.btn_add_to_playlist = ttk.Button(
            frame_controls,
            text="添加到歌单",
            command=self.add_to_playlist
        )
        self.btn_add_to_playlist.grid(row=0, column=3, padx=12)

        # 进度条
        self.progress_bar = ttk.Progressbar(frame_left, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=20)
        self.progress_bar["value"] = 0
        self.progress_bar.bind("<ButtonRelease-1>", self.seek_song)
        
        # 时间标签
        '''加个注释玩玩'''
        time_frame = tk.Frame(frame_left, bg='#f0f0f0')
        time_frame.pack()
        self.label_current_length = tk.Label(time_frame, text="当前时间: 00:00", bg='#f0f0f0')
        self.label_current_length.pack(side=tk.LEFT, padx=10)
        self.label_total_length = tk.Label(time_frame, text="总时长: 00:00", bg='#f0f0f0')
        self.label_total_length.pack(side=tk.LEFT, padx=10)

        # 右侧歌词显示区域
        frame_lyrics = tk.LabelFrame(self.root, text="歌词", padx=15, pady=15, bg='#f0f0f0')
        frame_lyrics.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        # 专辑封面显示
        self.album_cover_label = tk.Label(frame_lyrics, bg='#f0f0f0')
        self.album_cover_label.pack(side=tk.TOP, pady=10)

        # 歌词文本框
        self.lyrics_text = tk.Text(
            frame_lyrics, 
            wrap=tk.WORD, 
            state=tk.DISABLED, 
            font=("Arial", 12),
            bg='#ffffff',
            relief="solid",
            borderwidth=1
        )
        self.lyrics_text.pack(side=tk.LEFT, fill="both", expand=True)

        # 滚动条
        self.scrollbar = ttk.Scrollbar(frame_lyrics, command=self.lyrics_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lyrics_text.config(yscrollcommand=self.scrollbar.set)

    def toggle_pause(self):
        """切换播放与暂停"""
        if self.player_instance:
            self.player_instance.toggle_pause()

    def seek_song(self, event):
        """调整播放进度"""
        if self.player_instance:
            self.player_instance.seek_song(event)

    def show_playlist(self):
        """显示歌单窗口"""
        if self.playlist_instance:
            self.playlist_instance.show_playlist_window()

    def add_to_playlist(self):
        """添加当前选中的歌曲到歌单"""
        if not self.playlist_instance:
            return
        
        selected = self.tree_results.selection()
        if not selected:
            return
        
        # 创建添加到歌单的窗口
        add_window = tk.Toplevel(self.root)
        add_window.title("添加到歌单")
        add_window.geometry("300x400")
        
        # 创建歌单列表
        playlist_list = ttk.Treeview(add_window, columns=("name",), show="headings")
        playlist_list.heading("name", text="选择歌单")
        playlist_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 显示所有歌单
        for name in self.playlist_instance.playlists.keys():
            playlist_list.insert("", "end", values=(name,))
        
        def add_to_selected_playlist():
            selected_playlist = playlist_list.selection()
            if selected_playlist:
                playlist_name = playlist_list.item(selected_playlist[0])['values'][0]
                song_item = self.tree_results.item(selected[0])
                song_info = {
                    'id': song_item['values'][0],
                    'name': song_item['values'][1]
                }
                if self.playlist_instance.add_to_playlist(playlist_name, song_info):
                    add_window.destroy()
        
        ttk.Button(
            add_window,
            text="添加",
            command=add_to_selected_playlist
        ).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicDownloaderApp(root)
    root.mainloop()