import requests
import re
import time

flora_api = {}  # 顾名思义,FloraBot的API,载入(若插件已设为禁用则不载入)后会赋值上


def occupying_function(*values):  # 该函数仅用于占位,并没有任何意义
    pass


send_msg = occupying_function


def init():  # 插件初始化函数,在载入(若插件已设为禁用则不载入)或启用插件时会调用一次,API可能没有那么快更新,可等待,无传入参数
    global send_msg
    send_msg = flora_api.get("SendMsg")
    print("网易云音乐插件 加载成功")


def search_music(search: str, limit: int, offset: int = 0):
    get_search_list = requests.get(url="https://music.163.com/api/search/get", params={"s": search, "type": 1, "limit": limit, "offset": offset})
    search_list = []
    for song_info in get_search_list.json().get("result").get("songs"):
        info_dict = {}
        info_dict.update({"MusicName": song_info.get("name"), "MusicID": song_info.get("id")})
        artists_list = []
        for artists in song_info.get("artists"):
            artists_list.append({"ArtistName": artists.get("name"), "ArtistID": artists.get("id")})
        info_dict.update({"Artists": artists_list, "AlbumName": song_info.get("album").get("name"), "AlbumID": song_info.get("album").get("id")})
        search_list.append(info_dict)
    return search_list


search_result = {}


def event(data: dict):  # 事件函数,FloraBot每收到一个事件都会调用这个函数(若插件已设为禁用则不调用),传入原消息JSON参数
    global search_result
    send_type = data.get("SendType")
    send_address = data.get("SendAddress")
    ws_client = send_address.get("WebSocketClient")
    ws_server = send_address.get("WebSocketServer")
    send_host = send_address.get("SendHost")
    send_port = send_address.get("SendPort")
    uid = data.get("user_id")
    gid = data.get("group_id")
    mid = data.get("message_id")
    msg = data.get("raw_message")
    if msg is not None:
        msg = msg.replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", "&").replace("&#44;", ",")  # 消息需要将URL编码替换到正确内容
        if msg.startswith("/搜歌 "):
            now_time = time.time()
            for key, value in search_result.items():
                if now_time - value.get("SearchTime") > 60:
                    search_result.pop(key)
            search_name = re.search(r"/搜歌 (.*?)( 数量| 偏移|$)", msg).group(1)
            if not search_name.isspace() and search_name != "":
                search_num = re.search(r"数量 (\d+)", msg)
                send_text = ""
                if search_num is not None:
                    search_num = int(search_num.group(1))
                    if search_num > 30:
                        search_num = 30
                        send_text = "数量不能大于 30 哦, 自动指定为 30 , 数量太大了搜索效率会很慢哦\n"
                    elif search_num < 1:
                        search_num = 1
                        send_text = "数量不能小于 1 哦, 自动指定为 1\n"
                else:
                    search_num = 10
                search_offset = re.search(r"偏移 (\d+)", msg)
                if search_offset is not None:
                    search_offset = int(search_offset.group(1))
                    if search_offset > 30:
                        search_offset = 30
                        send_text += "偏移量不能大于 30 哦, 自动指定为 30 , 这么大的偏移量搜不到你想要的结果吧\n"
                    elif search_offset < 0:
                        search_offset = 0
                        send_text += "偏移量不能小于 0 哦, 自动指定为 0\n"
                else:
                    search_offset = 0
                send_msg(send_type, f"{send_text}当前搜索参数:\n内容: {search_name}\n数量: {search_num}\n偏移量: {search_offset}\n\n正在搜索啦, 请等一下哦...", uid, gid, mid, ws_client, ws_server, send_host, send_port)
                search_list = "搜索列表(网易云音乐):\n"
                music_num = 0
                get_search_list = search_music(search_name, search_num, search_offset)
                for song_info in get_search_list:
                    artists = ""
                    for artist in song_info.get("Artists"):
                        artists += f"{artist.get('ArtistName')} / "
                    artists = artists.strip(" / ")
                    music_num += 1
                    search_list += f"{music_num}. {song_info.get('MusicName')} - {artists}\n"
                search_result.update({uid: {"SearchTime": time.time(), "SearchList": get_search_list}})
                send_msg(send_type, f"{search_list}\n请在 1 分钟内点歌才有效哦,\n指令格式为:\n/点歌 + [空格] + [序号(1~{music_num})]", uid, gid, mid, ws_client, ws_server, send_host, send_port)
            else:
                send_msg(send_type, "参数错误, 搜索内容不能为空哦\n正确的指令格式为: /搜歌 + [空格] + [内容] + (可选参数)\n可选参数:\n[空格] + 数量 + [1 <= 数字 <= 30]\n[空格] + 偏移 + [0 <= 数字 <= 30]", uid, gid, mid, ws_client, ws_server, send_host, send_port)
        elif msg.startswith("/点歌 "):
            now_time = time.time()
            for key, value in search_result.items():
                if now_time - value.get("SearchTime") > 60:
                    search_result.pop(key)
            if uid in search_result:
                msg = msg.replace("/点歌 ", "", 1)
                search_list = search_result.get(uid).get("SearchList")
                try:
                    msg = int(msg)
                    if not msg > len(search_list) or not msg < 1:
                        song_info = search_list[msg - 1]
                        artists = ""
                        for artist in song_info.get("Artists"):
                            artists += f"{artist.get('ArtistName')}(艺术家ID: {artist.get('ArtistID')}) / "
                        artists = artists.strip(" / ")
                        send_msg(send_type, f"歌曲详细信息(来自网易云音乐):\n歌名: {song_info.get('MusicName')}\n歌曲ID: {song_info.get('MusicID')}\n艺术家: {artists}\n专辑: {song_info.get('AlbumName')}\n专辑ID: {song_info.get('AlbumID')}\n歌曲信息页链接: https://music.163.com/#/song?id={song_info.get('MusicID')}\n歌曲音频直链: https://music.163.com/song/media/outer/url?id={song_info.get('MusicID')}.mp3", uid, gid, mid, ws_client, ws_server, send_host, send_port)
                        send_msg(send_type, f"[CQ:record,file=https://music.163.com/song/media/outer/url?id={song_info.get('MusicID')}.mp3]", uid, gid, None, ws_client, ws_server, send_host, send_port)
                    else:
                        send_msg(send_type, f"参数错误, 序号应该在 1 ~ {len(search_list)} 哦\n正确的指令格式为:\n/点歌 + [空格] + [序号(1~{len(search_list)})]", uid, gid, mid, ws_client, ws_server, send_host, send_port)
                except ValueError:
                    send_msg(send_type, f"参数错误, 这好像不是序号吧\n正确的指令格式为:\n/点歌 + [空格] + [序号(1~{len(search_list)})]", uid, gid, mid, ws_client, ws_server, send_host, send_port)
            else:
                send_msg(send_type, "你还没有搜歌呢, 先去搜歌吧\n指令格式为: /搜歌 + [空格] + [内容] + (可选参数)\n可选参数:\n[空格] + 数量 + [1 <= 数字 <= 30]\n[空格] + 偏移 + [0 <= 数字 <= 30]", uid, gid, mid, ws_client, ws_server, send_host, send_port)

