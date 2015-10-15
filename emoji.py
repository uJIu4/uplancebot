# coding: utf-8
# from http://apps.timwhitlock.info/emoji/tables/

def get_emoji_list():
    emoji_list = []
    emoji_list += range(128512, 128591)

    emoji_list+= other_emojis

    return emoji_list

def get_random_emoji():
    emoji_list = get_emoji_list()
    emoji = random.choice(emoji_list)
    #print emoji
    return unichr(emoji)

