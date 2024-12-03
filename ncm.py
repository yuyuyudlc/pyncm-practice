import requests
from pyncm.apis import track, cloudsearch
from pyncm.apis.login import LoginViaCellphone


def login():
    """使用手机号登录网易云音乐"""
    try:
        phone = "19929070870"
        password = "20041227abcd"
        response = LoginViaCellphone(phone=phone, password=password)
        if response['code'] == 200:
            print("登录成功")
            return True
        else:
            print(f"登录失败，错误信息: {response.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"登录时发生错误: {e}")
        return False


def get_offset_by_page_num(page: int, limit: int = 10) -> int:
    """计算分页偏移量"""
    return limit * (page - 1)


def get_search_result(keyword: str, page: int = 1, limit: int = 10, search_type: int = 1) -> dict:
    """通过关键词搜索结果"""
    try:
        offset = get_offset_by_page_num(page, limit)
        result = cloudsearch.GetSearchResult(keyword, limit=limit, offset=offset, stype=search_type)
        if result.get('code') != 200:
            raise RuntimeError(f"搜索失败，错误信息: {result}")
        return result
    except Exception as e:
        print(f"搜索时发生错误: {e}")
        return {}


def get_song_choices(song_name: str):
    """通过歌曲名称获取多个搜索结果供选择"""
    search_result = get_search_result(song_name, limit=5)
    
    # 打印完整响应供调试
    #print("API 响应:", search_result)
    
    if 'result' in search_result and 'songs' in search_result['result']:
        songs = search_result['result']['songs']
        choices = []
        for song in songs:
            song_id = song.get('id')  # 歌曲ID
            song_name = song.get('name', '未知歌曲')  # 歌曲名称
            
            # 提取歌手信息
            artists = song.get('ar', [])  # 使用 'ar' 字段
            artist_names = ", ".join(artist.get('name', '未知艺术家') for artist in artists) if artists else '未知艺术家'

            # 提取专辑信息
            album_info = song.get('al', {})
            album_name = album_info.get('name', '未知专辑')  # 专辑名称

            if song_id:
                # 将歌曲ID、描述信息加入选项
                choices.append((song_id, f"{song_name} - {artist_names} (专辑: {album_name})"))
        
        return choices
    else:
        print(f"未找到歌曲: {song_name}")
        return []


def get_audio_url(song_id: int):
    """通过歌曲 ID 获取音频 URL"""
    try:
        audio_info = track.GetTrackAudio(song_id)
        if 'data' in audio_info and audio_info['data']:
            return audio_info['data'][0].get('url')
        else:
            print(f"未能获取音频 URL: {song_id}")
            return None
    except Exception as e:
        print(f"获取音频 URL 时发生错误: {e}")
        return None


def download_audio(url: str, filename: str):
    """下载音频文件"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"音频已保存为: {filename}")
    except Exception as e:
        print(f"下载音频时发生错误: {e}")


def download_song_by_name(song_name: str):
    """通过歌曲名称下载音频"""
    print(f"开始搜索: {song_name}")
    choices = get_song_choices(song_name)
    if not choices:
        print("未找到相关歌曲。")
        return

    print("搜索结果:")
    for idx, (_, description) in enumerate(choices, start=1):
        print(f"{idx}. {description}")

    try:
        choice = int(input("请选择要下载的歌曲编号: ")) - 1
        if 0 <= choice < len(choices):
            song_id, song_description = choices[choice]
            print(f"已选择: {song_description}")
            audio_url = get_audio_url(song_id)
            if audio_url:
                safe_filename = sanitize_filename(f"{song_description}.mp3")
                download_audio(audio_url, safe_filename)
            else:
                print("音频 URL 获取失败。")
        else:
            print("无效选择。")
    except ValueError:
        print("请输入有效的数字。")
    except Exception as e:
        print(f"处理选择时发生错误: {e}")


def sanitize_filename(filename: str) -> str:
    """移除文件名中的非法字符"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '', filename)


def main():
    """主函数"""
    if not login():
        print("登录失败，程序退出。")
        return

    while True:
        print("\n菜单：\n1. 点歌\n0. 退出")
        try:
            select = int(input("选择操作: "))
            if select == 1:
                song = input("请输入歌曲名称: ").strip()
                if song:
                    download_song_by_name(song)
                else:
                    print("歌曲名称不能为空。")
            elif select == 0:
                print("退出程序。")
                break
            else:
                print("无效选择，请重新输入。")
        except ValueError:
            print("请输入有效的数字。")
        except Exception as e:
            print(f"发生未知错误: {e}")


if __name__ == "__main__":
    main()
