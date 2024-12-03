import tkinter as tk
from tkinter import ttk, messagebox
from pyncm.apis import track, cloudsearch
from pyncm.apis.login import LoginViaCellphone
import requests
import re


class MusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云音乐下载器")
        self.root.geometry("500x650")

        # 登录状态
        self.is_logged_in = False

        # 创建 UI
        self.create_widgets()

    def create_widgets(self):
        # 登录部分
        frame_login = tk.LabelFrame(self.root, text="登录", padx=10, pady=10)
        frame_login.pack(pady=10, fill="x", padx=10)

        tk.Label(frame_login, text="手机号:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_phone = tk.Entry(frame_login)
        self.entry_phone.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_login, text="密码:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_password = tk.Entry(frame_login, show="*")
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        self.btn_login = tk.Button(frame_login, text="登录", command=self.login)
        self.btn_login.grid(row=2, column=0, columnspan=2, pady=10)

        # 搜索部分
        frame_search = tk.LabelFrame(self.root, text="搜索歌曲", padx=10, pady=10)
        frame_search.pack(pady=10, fill="x", padx=10)

        tk.Label(frame_search, text="歌曲名称:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_search = tk.Entry(frame_search, width=30)
        self.entry_search.grid(row=0, column=1, padx=5, pady=5)

        self.btn_search = tk.Button(frame_search, text="搜索", command=self.search_songs)
        self.btn_search.grid(row=0, column=2, padx=5, pady=5)

        # 搜索结果部分
        frame_results = tk.LabelFrame(self.root, text="搜索结果", padx=10, pady=10)
        frame_results.pack(pady=10, fill="both", expand=True, padx=10)

        self.tree_results = ttk.Treeview(frame_results, columns=("song_id", "description"), show="headings")
        self.tree_results.heading("song_id", text="歌曲ID")
        self.tree_results.heading("description", text="描述")
        self.tree_results.column("song_id", width=80)
        self.tree_results.column("description", width=300)
        self.tree_results.pack(fill="both", expand=True)

        self.btn_download = tk.Button(self.root, text="下载选中歌曲", command=self.download_selected_song)
        self.btn_download.pack(pady=10)

    def login(self):
        phone = self.entry_phone.get()
        password = self.entry_password.get()
        try:
            response = LoginViaCellphone(phone=phone, password=password)
            if response['code'] == 200:
                messagebox.showinfo("成功", "登录成功")
                self.is_logged_in = True
            else:
                messagebox.showerror("错误", f"登录失败: {response.get('message', '未知错误')}")
        except Exception as e:
            messagebox.showerror("错误", f"登录时发生错误: {e}")

    def search_songs(self):
        if not self.is_logged_in:
            messagebox.showwarning("未登录", "请先登录！")
            return

        song_name = self.entry_search.get().strip()
        if not song_name:
            messagebox.showwarning("输入错误", "请输入歌曲名称！")
            return

        self.tree_results.delete(*self.tree_results.get_children())

        choices = self.get_song_choices(song_name)
        if choices:
            for song_id, description in choices:
                self.tree_results.insert("", "end", values=(song_id, description))
        else:
            messagebox.showinfo("结果", "未找到相关歌曲。")

    def get_song_choices(self, song_name):
        search_result = self.get_search_result(song_name, limit=5)
        if 'result' in search_result and 'songs' in search_result['result']:
            songs = search_result['result']['songs']
            choices = []
            for song in songs:
                song_id = song.get('id')
                song_name = song.get('name', '未知歌曲')
                artists = song.get('ar', [])
                artist_names = ", ".join(artist.get('name', '未知艺术家') for artist in artists) if artists else '未知艺术家'
                album_info = song.get('al', {})
                album_name = album_info.get('name', '未知专辑')
                if song_id:
                    choices.append((song_id, f"{song_name} - {artist_names} (专辑: {album_name})"))
            return choices
        return []

    def get_search_result(self, keyword, page=1, limit=10, search_type=1):
        try:
            offset = (page - 1) * limit
            result = cloudsearch.GetSearchResult(keyword, limit=limit, offset=offset, stype=search_type)
            if result.get('code') != 200:
                raise RuntimeError(f"搜索失败，错误信息: {result}")
            return result
        except Exception as e:
            messagebox.showerror("错误", f"搜索时发生错误: {e}")
            return {}

    def download_selected_song(self):
        selected_item = self.tree_results.selection()
        if not selected_item:
            messagebox.showwarning("未选择", "请选择一首歌曲！")
            return

        song_id, description = self.tree_results.item(selected_item[0], "values")
        audio_url = self.get_audio_url(int(song_id))
        if audio_url:
            safe_filename = self.sanitize_filename(f"{description}.mp3")
            self.download_audio(audio_url, safe_filename)
        else:
            messagebox.showerror("错误", "未能获取音频 URL。")

    def get_audio_url(self, song_id):
        try:
            audio_info = track.GetTrackAudio(song_id)
            if 'data' in audio_info and audio_info['data']:
                return audio_info['data'][0].get('url')
            return None
        except Exception as e:
            messagebox.showerror("错误", f"获取音频 URL 时发生错误: {e}")
            return None

    def sanitize_filename(self, filename):
        return re.sub(r'[<>:"/\\|?*]', '', filename)

    def download_audio(self, url, filename):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            messagebox.showinfo("成功", f"音频已保存为: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"下载音频时发生错误: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicDownloaderApp(root)
    root.mainloop()
