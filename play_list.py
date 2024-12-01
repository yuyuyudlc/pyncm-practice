import tkinter as tk
from tkinter import ttk
import json
import os

class PlayList:
    def __init__(self, root, tree_results, player_instance):
        self.root = root
        self.tree_results = tree_results
        self.player_instance = player_instance
        self.playlists = {}
        self.current_playlist = None
        
        # 创建保存歌单的文件夹
        if not os.path.exists('playlists'):
            os.makedirs('playlists')
            
        self.load_playlists()
        
    def load_playlists(self):
        """加载所有歌单"""
        try:
            with open('playlists/playlists.json', 'r', encoding='utf-8') as f:
                self.playlists = json.load(f)
        except FileNotFoundError:
            self.save_playlists()
            
    def save_playlists(self):
        """保存歌单"""
        with open('playlists/playlists.json', 'w', encoding='utf-8') as f:
            json.dump(self.playlists, f, ensure_ascii=False, indent=4)
            
    def create_playlist(self, name):
        """创建新歌单"""
        if name not in self.playlists:
            self.playlists[name] = []
            self.save_playlists()
            return True
        return False
        
    def add_to_playlist(self, playlist_name, song_info):
        """添加歌曲到歌单"""
        if playlist_name in self.playlists:
            # 检查歌曲是否已经在歌单中
            if not any(song['id'] == song_info['id'] for song in self.playlists[playlist_name]):
                self.playlists[playlist_name].append(song_info)
                self.save_playlists()
                return True
        return False
        
    def remove_from_playlist(self, playlist_name, song_id):
        """从歌单中移除歌曲"""
        if playlist_name in self.playlists:
            self.playlists[playlist_name] = [
                song for song in self.playlists[playlist_name] 
                if song['id'] != song_id
            ]
            self.save_playlists()
            
    def delete_playlist(self, name):
        """删除歌单"""
        if name in self.playlists:
            del self.playlists[name]
            self.save_playlists()
            
    def show_playlist_window(self):
        """显示歌单窗口"""
        playlist_window = tk.Toplevel(self.root)
        playlist_window.title("歌单管理")
        playlist_window.geometry("400x600")
        
        # 创建歌单框架
        create_frame = ttk.LabelFrame(playlist_window, text="创建歌单")
        create_frame.pack(fill="x", padx=5, pady=5)
        
        name_var = tk.StringVar()
        ttk.Entry(create_frame, textvariable=name_var).pack(side="left", padx=5, pady=5)
        ttk.Button(
            create_frame,
            text="创建歌单",
            command=lambda: self.handle_create_playlist(name_var.get())
        ).pack(side="left", padx=5, pady=5)
        
        # 歌单列表
        list_frame = ttk.LabelFrame(playlist_window, text="我的歌单")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.playlist_tree = ttk.Treeview(list_frame, columns=("name",), show="headings")
        self.playlist_tree.heading("name", text="歌单名称")
        self.playlist_tree.pack(fill="both", expand=True)
        
        # 更新歌单列表
        self.update_playlist_tree()
        
        # 添加右键菜单
        self.create_context_menu(playlist_window)
        
    def update_playlist_tree(self):
        """更新歌单列表显示"""
        for item in self.playlist_tree.get_children():
            self.playlist_tree.delete(item)
        for name in self.playlists.keys():
            self.playlist_tree.insert("", "end", values=(name,))
            
    def create_context_menu(self, window):
        """创建右键菜单"""
        self.context_menu = tk.Menu(window, tearoff=0)
        self.context_menu.add_command(label="查看歌单", command=self.view_playlist)
        self.context_menu.add_command(label="删除歌单", command=self.handle_delete_playlist)
        
        self.playlist_tree.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.playlist_tree.identify_row(event.y)
        if item:
            self.playlist_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def handle_create_playlist(self, name):
        """处理创建歌单"""
        if name.strip():
            if self.create_playlist(name):
                self.update_playlist_tree()
                
    def handle_delete_playlist(self):
        """处理删除歌单"""
        selected = self.playlist_tree.selection()
        if selected:
            playlist_name = self.playlist_tree.item(selected[0])['values'][0]
            self.delete_playlist(playlist_name)
            self.update_playlist_tree()
            
    def view_playlist(self):
        """查看歌单内容"""
        selected = self.playlist_tree.selection()
        if not selected:
            return
            
        playlist_name = self.playlist_tree.item(selected[0])['values'][0]
        
        # 创建新窗口显示歌单内容
        view_window = tk.Toplevel(self.root)
        view_window.title(f"歌单: {playlist_name}")
        view_window.geometry("600x400")
        
        # 创建按钮框架
        button_frame = tk.Frame(view_window)
        button_frame.pack(pady=5)
        
        # 添加播放全部按钮
        ttk.Button(
            button_frame,
            text="播放全部",
            command=lambda: self.play_all_songs(songs_tree, playlist_name)
        ).pack(side=tk.LEFT, padx=5)
        
        # 添加播放选中按钮
        ttk.Button(
            button_frame,
            text="播放选中",
            command=lambda: self.play_song_from_playlist(songs_tree)
        ).pack(side=tk.LEFT, padx=5)
        
        # 添加下一首按钮
        ttk.Button(
            button_frame,
            text="下一首",
            command=lambda: self.play_next_song(songs_tree)
        ).pack(side=tk.LEFT, padx=5)
        
        # 创建树形视图显示歌曲
        songs_tree = ttk.Treeview(view_window, columns=("id", "name"), show="headings")
        songs_tree.heading("id", text="歌曲ID")
        songs_tree.heading("name", text="歌曲名称")
        songs_tree.pack(fill="both", expand=True)
        
        # 添加歌曲到树形视图
        for song in self.playlists[playlist_name]:
            songs_tree.insert("", "end", values=(song['id'], song['name']))
            
    def play_song_from_playlist(self, songs_tree):
        """从歌单播放选中的歌曲"""
        selected = songs_tree.selection()
        if selected and self.player_instance:
            song_id = songs_tree.item(selected[0])['values'][0]
            # 更新搜索结果树形视图
            self.tree_results.delete(*self.tree_results.get_children())
            song_name = songs_tree.item(selected[0])['values'][1]
            self.tree_results.insert("", "end", values=(song_id, song_name))
            # 选中新插入的项目
            new_item = self.tree_results.get_children()[0]
            self.tree_results.selection_set(new_item)
            # 使用现有的播放方法
            self.player_instance.play_selected_song(self.tree_results)
            
    def play_all_songs(self, songs_tree, playlist_name):
        """播放歌单中的所有歌曲"""
        if not self.playlists[playlist_name]:
            return
        
        # 清空搜索结果树形视图
        self.tree_results.delete(*self.tree_results.get_children())
        
        # 添加歌单中的所有歌曲到搜索结果
        for song in self.playlists[playlist_name]:
            self.tree_results.insert("", "end", values=(song['id'], song['name']))
        
        # 选中第一首歌并开始播放
        first_item = self.tree_results.get_children()[0]
        self.tree_results.selection_set(first_item)
        self.player_instance.play_selected_song(self.tree_results)
        
        # 设置播放完当前歌曲后自动播放下一首
        self.player_instance.set_playlist_mode(True)
        
    def play_next_song(self, songs_tree):
        """播放下一首歌曲"""
        current_selection = songs_tree.selection()
        if not current_selection:
            return
        
        current_item = current_selection[0]
        all_items = songs_tree.get_children()
        current_index = all_items.index(current_item)
        
        # 检查是否有下一首
        if current_index + 1 < len(all_items):
            next_item = all_items[current_index + 1]
            songs_tree.selection_set(next_item)
            self.play_song_from_playlist(songs_tree)
        else:
            tk.messagebox.showinfo("提示", "已经是最后一首歌了")
