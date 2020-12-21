# -*- coding: utf-8 -*-

GameVersion = "1.2.6"

# 成员信息面板每页条数
member_list_page_item = 20

# 战队信息每页条数
partner_list_page_item = 10

# 记录每页条数
history_list_page_item = 30

# 冠名赛房间信息每页条数
room_list_page_item = 10


# 可以观战的游戏
class CanWatchGame:
    can_watch_game = ["RoomType8", 'RoomType6', "RoomType1", 'RoomType10', 'RoomType4', 'RoomType11', 'RoomType13',
                      'RoomType12', 'RoomType14', 'RoomType16', 'RoomType5', 'RoomType15', 'RoomType18', 'RoomType21',
                      'RoomType22','RoomType23'
                      ]


have_bot_game = {'RoomType6', 'RoomType1', 'RoomType4', 'RoomType8'}


# 战绩
class Record:
    # 战绩记录上限
    record_limit = 30


# 钻石支付类型
class PayType:
    RoomCreator = 0
    AA = 1


# to_do_list类型
class ToDoType:
    tea_house_invite = 'teaHouseInvite'
    add_friend = 'addFriend'
    notice = 'notice'


# 游戏配置，会发送到前端
class GameConfigJson:
    config_json = {}


# 仅服务端用游戏配置
class ServerGameConfigJson:
    config_json = {}


# 默认玩家头像地址
class AccountInfo:
    HeadImageUrl = "http://img1.gamersky.com/image2016/02/20160216_wp_287_7/image055_S.jpg"


class UpgradeTeaHouseRoomCardConsume:
    # 升级冠名赛钻石消耗
    # RoomCardConsume = {1: 0, 2: 300, 3: 500, 4: 1000, 5: 2000}
    RoomCardConsume = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


class RoomType:
    # 炸金花房间
    RoomType1 = "RoomType1"
    # 龙虎斗
    RoomType2 = "RoomType2"
    # 百家乐
    RoomType3 = "RoomType3"
    # 牛牛房间
    RoomType4 = "RoomType4"
    # 麻将
    RoomType5 = "RoomType5"
    # 斗地主
    RoomType6 = "RoomType6"
    # 牌九
    RoomType7 = "RoomType7"
    # 新牌九
    RoomType8 = "RoomType8"
    # 八叉
    RoomType10 = "RoomType10"
    # 洛阳牌九
    RoomType11 = "RoomType11"
    # 划水麻将
    RoomType12 = 'RoomType12'
    # 跑的快
    RoomType13 = "RoomType13"
    # 郑州麻将
    RoomType14 = "RoomType14"
    # 点炮胡
    RoomType15 = "RoomType15"
    # 晃晃麻将
    RoomType16 = 'RoomType16'
    # 潢川麻将
    RoomType18 = 'RoomType18'
    # 平顶山麻将
    RoomType19 = 'RoomType19'
    # 固始麻将
    RoomType20 = 'RoomType20'
    # 商丘麻将
    RoomType21 = 'RoomType21'
    # 济源麻将
    RoomType22 = 'RoomType22'
    # 十点半
    RoomType23 = 'RoomType23'


def get_name_by_type(room_type):
    # 炸金花房间
    if room_type == "RoomType1":
        return "炸金花"
    # 龙虎斗
    elif room_type == "RoomType2":
        return "龙虎斗"
    # 百家乐
    elif room_type == "RoomType3":
        return "百家乐"
    # 牛牛房间
    elif room_type == "RoomType4":
        return "牛牛"
    # 麻将
    elif room_type == "RoomType5":
        return "洛阳杠次"
    # 斗地主
    elif room_type == "RoomType6":
        return "斗地主"
    # 牌九
    elif room_type == "RoomType7":
        return "牌九"
    # 新牌九
    elif room_type == "RoomType8":
        return "牌九"
    # 八叉
    elif room_type == "RoomType10":
        return "八叉"
    # 洛阳牌九
    elif room_type == "RoomType11":
        return "洛阳牌九"
    # 划水麻将
    elif room_type == 'RoomType12':
        return "划水麻将"
    # 跑得快
    elif room_type == "RoomType13":
        return "跑得快"
    # 郑州麻将
    elif room_type == "RoomType14":
        return "郑州麻将"
    # 点炮胡
    elif room_type == "RoomType15":
        return "点炮胡"
    # 晃晃麻将
    elif room_type == 'RoomType16':
        return "晃晃麻将"
    # 潢川麻将
    elif room_type == 'RoomType18':
        return "潢川麻将"
    elif room_type == 'RoomType19':
        return "平顶山麻将"
    elif room_type == 'RoomType20':
        return "固始麻将"
    elif room_type == 'RoomType21':
        return "商丘麻将"
    elif room_type == "RoomType22":
        return "济源麻将"
    elif room_type == "RoomType23":
        return "十点半"
    else:
        return "游戏"


RedeemGift = {1: "10元京东购物卡", 5: "50元话费券", 10: "100元京东购物卡", 50: "500元京东购物卡"}
