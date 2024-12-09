import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import requests
import vlc
from pyncm.apis import track, cloudsearch
from pyncm.apis.track import GetTrackLyrics


class SearchAndPlayer:
    def __init__(self, root, progress_bar, lyrics_text, album_cover_label, label_current_length, label_total_length, tree_results):
        self.root = root
        self.progress_bar = progress_bar
        self.lyrics_text = lyrics_text
        self.album_cover_label = album_cover_label
        self.label_current_length = label_current_length
        self.label_total_length = label_total_length
        self.tree_results = tree_results

        self.player = vlc.MediaPlayer()
        self.current_audio_url = None
        self.is_paused = False
        self.total_length = 0
        self.current_page = 1
        self.song_name = ""
        self.lyrics = []
        self.current_lyric_index = 0
        self.songs_per_page = 10
        self.playlist_mode = False
        self.current_playing_index = None

    def search_songs(self, tree_results, entry_search):
        """搜索歌曲"""
        self.song_name = entry_search.get().strip()
        if not self.song_name:
            messagebox.showwarning("输入错误", "请输入歌曲名称！")
            return
        self.load_search_results(tree_results)

    def load_search_results(self, tree_results):
        """加载搜索结果到树视图中"""
        tree_results.delete(*tree_results.get_children())
        choices = self.get_song_choices(self.song_name, self.current_page)
        if choices:
            for song_id, description in choices:
                tree_results.insert("", "end", values=(song_id, description))
        else:
            messagebox.showinfo("结果", "未找到相关歌曲。")

    def get_song_choices(self, song_name, page):
        """获取歌曲的搜索结果"""
        offset = (page - 1) * self.songs_per_page
        result = cloudsearch.GetSearchResult(song_name, limit=self.songs_per_page, offset=offset, stype=1)
        if 'result' in result and 'songs' in result['result']:
            songs = result['result']['songs']
            return [(song['id'], f"{song['name']} - {', '.join(a['name'] for a in song['ar'])}") for song in songs]
        return []

    def prev_page(self, tree_results):
        """上一页搜索结果"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_search_results(tree_results)

    def next_page(self, tree_results):
        """下一页搜索结果"""
        self.current_page += 1
        self.load_search_results(tree_results)

    def get_audio_url(self, song_id):
        """获取歌曲的音频 URL"""
        try:
            audio_info = track.GetTrackAudio(song_id, bitrate=320000)
            if 'data' in audio_info and audio_info['data']:
                return audio_info['data'][0].get('url')
            return None
        except Exception as e:
            messagebox.showerror("错误", f"获取音频 URL 时发生错误: {e}")
            return None

    def fetch_lyrics(self, song_id):
        """获取歌曲歌词"""
        try:
            response = GetTrackLyrics(song_id)
            if response['code'] == 200:
                raw_lyrics = response.get('lrc', {}).get('lyric', '未找到歌词')
                return self.parse_lyrics(raw_lyrics)
            else:
                return []
        except Exception as e:
            messagebox.showerror("错误", f"获取歌词时发生错误: {e}")
            return []

    def parse_lyrics(self, raw_lyrics):
        """解析歌词"""
        lyrics = []
        for line in raw_lyrics.splitlines():
            if line.startswith("[") and "]" in line:
                timestamp, text = line.split("]", 1)
                timestamp = timestamp.strip("[]")
                minutes, seconds = map(float, timestamp.split(":"))
                time_in_seconds = minutes * 60 + seconds
                lyrics.append((time_in_seconds, text.strip()))
        return lyrics

    def display_lyrics(self):
        """显示歌词"""
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete(1.0, tk.END)
        for _, text in self.lyrics:
            self.lyrics_text.insert(tk.END, text + "\n")
        self.lyrics_text.config(state=tk.DISABLED)

    def display_album_cover(self, song_id):
        """显示专辑封面"""
        try:
            song_detail = track.GetTrackDetail(song_id)
            if 'songs' in song_detail and song_detail['songs']:
                album_cover_url = song_detail['songs'][0]['al']['picUrl']
                if album_cover_url:
                    response = requests.get(album_cover_url)
                    image_data = Image.open(BytesIO(response.content))
                    image_data = image_data.resize((100, 100), Image.Resampling.LANCZOS)
                    album_cover = ImageTk.PhotoImage(image_data)
                    self.album_cover_label.config(image=album_cover)
                    self.album_cover_label.image = album_cover
                    return
        except Exception as e:
            messagebox.showerror("错误", f"加载专辑封面失败: {e}")
        
        # 如果获取失败，显示默认图片
        self.album_cover_label.config(image='')
        self.album_cover_label.image = None

    def play_selected_song(self, tree_results):
        """播放选中的歌曲"""
        selected_item = tree_results.selection()
        if not selected_item:
            messagebox.showwarning("未选择", "请选择一首歌曲！")
            return

        song_id, song_description = tree_results.item(selected_item[0], "values")
        # 保存当前播放的歌曲名称
        self.song_name = song_description
        
        audio_url = self.get_audio_url(int(song_id))
        if audio_url:
            self.current_audio_url = audio_url
            self.player.set_media(vlc.Media(audio_url))
            self.player.play()
            self.is_paused = False

            # 获取专辑封面并显示
            self.display_album_cover(int(song_id))

            # 获取歌词并显示
            self.lyrics = self.fetch_lyrics(int(song_id))
            self.display_lyrics()

            threading.Thread(target=self.update_progress_bar, daemon=True).start()
        else:
            messagebox.showerror("错误", "未能获取音频 URL。")

    def toggle_pause(self):
        """切换播放和暂停"""
        if self.is_paused:
            self.player.play()
            self.is_paused = False
        else:
            self.player.pause()
            self.is_paused = True

    def update_progress_bar(self):
        """更新进度条和播放时间"""
        while True:
            time.sleep(0.1)  # 更频繁地检查以提高响应性
            if self.player.is_playing():
                self.total_length = self.player.get_length() / 1000
                current_time = self.player.get_time() / 1000
                if self.total_length > 0:
                    progress = (current_time / self.total_length) * 100
                    self.progress_bar["value"] = progress
                    self.label_current_length.config(text=f"当前时间: {self.format_time(current_time)}")
                    self.label_total_length.config(text=f"总时长: {self.format_time(self.total_length)}")
                    self.highlight_current_lyric(current_time)
                    
                    # 在歌曲结束前1秒预加载并播放下一首
                    if self.playlist_mode and (self.total_length - current_time) <= 1:
                        self.prepare_and_play_next()
                        break  # 退出当前歌曲的进度条更新���环

    def prepare_and_play_next(self):
        """准备并播放下一首歌曲"""
        current_items = self.tree_results.get_children()
        current_selection = self.tree_results.selection()
        
        if not current_selection:
            return
        
        current_index = current_items.index(current_selection[0])
        if current_index + 1 < len(current_items):
            next_item = current_items[current_index + 1]
            next_song_id = self.tree_results.item(next_item)['values'][0]
            next_song_description = self.tree_results.item(next_item)['values'][1]
            
            # 预加载下一首歌曲的URL
            next_audio_url = self.get_audio_url(int(next_song_id))
            if next_audio_url:
                # 更新选中状态
                self.tree_results.selection_set(next_item)
                self.song_name = next_song_description
                
                # 创建并播放新的Media
                next_media = vlc.Media(next_audio_url)
                self.player.set_media(next_media)
                self.player.play()
                
                # 更新界面显示
                self.display_album_cover(int(next_song_id))
                self.lyrics = self.fetch_lyrics(int(next_song_id))
                self.display_lyrics()
                
                # 启动新的进度条更新线程
                threading.Thread(target=self.update_progress_bar, daemon=True).start()
        else:
            self.playlist_mode = False
            self.root.after(0, lambda: tk.messagebox.showinfo("提示", "播放列表已播放完毕"))

    def highlight_current_lyric(self, current_time):
        """高亮当前歌词并将其居中"""
        # 找到当前播放时间对应的歌词索引
        for i, (start_time, text) in enumerate(self.lyrics):
            if start_time > current_time:
                self.current_lyric_index = max(i - 1, 0)
                break
        else:
            self.current_lyric_index = len(self.lyrics) - 1

         # 清除以前的高亮
        self.lyrics_text.tag_remove("highlight", 1.0, tk.END)

    # 设置新的高亮
        start_index = f"{self.current_lyric_index + 1}.0"
        end_index = f"{self.current_lyric_index + 1}.end"
        self.lyrics_text.tag_add("highlight", start_index, end_index)
        self.lyrics_text.tag_config("highlight", background="yellow")

    # 自动滚动，使高亮的歌词居中
        total_lines = int(self.lyrics_text.index("end-1c").split(".")[0])
        visible_lines = int(self.lyrics_text.winfo_height() / self.lyrics_text.dlineinfo("@0,0")[3])
        center_line = max(0, self.current_lyric_index - visible_lines // 2)
        self.lyrics_text.yview_moveto(center_line / total_lines)

    def seek_song(self, event):
        """调整播放进度"""
        if self.total_length > 0:
            seek_position = (event.x / self.progress_bar.winfo_width()) * self.total_length
            self.player.set_time(int(seek_position * 1000))

    @staticmethod
    def format_time(seconds):
        """格式化时间"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def set_playlist_mode(self, enabled):
        """设置是否启用播放列表模式"""
        self.playlist_mode = enabled
        
    def play_next_song(self):
        """播放下一首歌曲"""
        if not self.playlist_mode:
            return
        
        current_items = self.tree_results.get_children()
        if not current_items:
            return
        
        current_selection = self.tree_results.selection()
        if not current_selection:
            next_index = 0
        else:
            current_index = current_items.index(current_selection[0])
            if current_index + 1 < len(current_items):
                next_index = current_index + 1
            else:
                self.root.after(0, lambda: tk.messagebox.showinfo("提示", "已经是最后一首歌了"))
                self.playlist_mode = False
                return
        
        next_item = current_items[next_index]
        self.tree_results.selection_set(next_item)
        self.play_selected_song(self.tree_results)
