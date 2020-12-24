import random


def get_cards_score(cards: []):
    """
    获取手牌点数
    """
    pass


def get_card_number(card):
    """
    获取牌的数字
    """
    pass


def generate_cards(player_count):
    """
    生成玩家手牌
    """
    # 黑红梅方
    card_type = ["a", "b", "c", "d"]
    # 14 代表 A，15 代表 2
    card_num = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    cards_lib = []

    # 生成所有牌
    for card_color in card_type:
        for num in card_num:
            cards_lib.append(card_color + str(num))

    # 洗牌
    random.shuffle(cards_lib)
    random.shuffle(cards_lib)

    # 把给玩家发的牌整理出来
    all_cards = []
    for i in range(0, player_count):
        cards = cards_lib[:1]
        all_cards.append(cards)
        cards_lib = cards_lib[1:]

    # 剩余牌
    remain_cards = cards_lib

    return all_cards, remain_cards
