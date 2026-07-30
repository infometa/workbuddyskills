#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

show_help() {
    cat <<'EOF'
🖊️  social-copywriter — 社交媒体文案生成器

用法:
  copy.sh moments "场景" [--mood happy|sad|funny|deep|show-off|food|travel|work]
  copy.sh weibo   "话题"
  copy.sh twitter "topic"
  copy.sh instagram "topic"
  copy.sh birthday "名字"
  copy.sh holiday  "节日"
  copy.sh food     "菜名/餐厅"
  copy.sh travel   "地点"
  copy.sh daily
  copy.sh festival "节日"         节日营销文案（热点借势）
  copy.sh brand "品牌" "调性"      品牌文案风格设定
  copy.sh thread "主题"           Twitter/微博长线程创作
  copy.sh viral "主题"            病毒式传播文案
  copy.sh cta-optimize "文案"     CTA转化优化（FOMO/社会证明/紧迫感）
  copy.sh help

示例:
  copy.sh moments "周末" --mood happy
  copy.sh weibo "打工人日常"
  copy.sh twitter "productivity tips"
  copy.sh instagram "sunset vibes"
  copy.sh birthday "小明"
  copy.sh food "寿司"
  copy.sh travel "京都"
  copy.sh daily
  copy.sh festival "中秋"
  copy.sh brand "星巴克" "温暖"
  copy.sh thread "AI对就业的影响"
  copy.sh viral "健身打卡"
EOF
}

CMD="${1:-help}"

if [ "$CMD" = "help" ] || [ "$CMD" = "--help" ] || [ "$CMD" = "-h" ]; then
    show_help
    exit 0
fi

python3 - "$@" <<'PYTHON_SCRIPT'
# -*- coding: utf-8 -*-
import sys
import random

# Emoji helper - use codepoints to avoid encoding issues in heredoc
E = {
    "sun": "\u2600\ufe0f",
    "sparkles": "\u2728",
    "candy": "\U0001f36c",
    "camera": "\U0001f4f8",
    "rainbow": "\U0001f308",
    "clover": "\U0001f340",
    "yellow_heart": "\U0001f49b",
    "rain": "\U0001f327\ufe0f",
    "fallen_leaf": "\U0001f342",
    "hug": "\U0001f917",
    "new_moon": "\U0001f311",
    "ocean": "\U0001f30a",
    "joy": "\U0001f602",
    "rofl": "\U0001f923",
    "wink": "\U0001f61c",
    "skull": "\U0001f480",
    "upside_down": "\U0001f643",
    "trophy": "\U0001f3c6",
    "sunrise": "\U0001f305",
    "seedling": "\U0001f33f",
    "telescope": "\U0001f52d",
    "rail": "\U0001f6e4\ufe0f",
    "yoga": "\U0001f9d8",
    "nail": "\U0001f485",
    "sunglasses": "\U0001f60e",
    "star2": "\U0001f31f",
    "gem": "\U0001f48e",
    "plate": "\U0001f37d\ufe0f",
    "drool": "\U0001f924",
    "yum": "\U0001f60b",
    "pizza": "\U0001f355",
    "heart": "\u2764\ufe0f",
    "check": "\u2705",
    "muscle": "\U0001f4aa",
    "brick": "\U0001f9f1",
    "coffee": "\u2615",
    "laptop": "\U0001f4bb",
    "wrench": "\U0001f527",
    "plant": "\U0001fab4",
    "film": "\U0001f39e\ufe0f",
    "book": "\U0001f4d6",
    "cloud": "\u2601\ufe0f",
    "airplane": "\u2708\ufe0f",
    "earth": "\U0001f30d",
    "camera2": "\U0001f4f7",
    "map": "\U0001f5fa\ufe0f",
    "postcard": "\U0001f305",
    "tent": "\u26fa",
    "footprints": "\U0001f463",
    "cake": "\U0001f382",
    "party": "\U0001f389",
    "balloon": "\U0001f388",
    "pie": "\U0001f370",
    "kiss_heart": "\U0001f496",
    "cheers": "\U0001f942",
    "blush": "\U0001f970",
    "confetti": "\U0001f38a",
    "sparkle": "\U0001f4ab",
    "house": "\U0001f3e0",
    "fireworks": "\U0001f387",
    "star_eyes": "\U0001f929",
    "star5": "\u2b50",
    "pot": "\U0001f372",
    "beer": "\U0001f37a",
    "chart": "\U0001f4c8",
    "relieved": "\U0001f60c",
    "smile": "\U0001f604",
    "bird": "\U0001f426",
    "art": "\U0001f3a8",
    "sunny": "\U0001f31e",
    "cherry_blossom": "\U0001f338",
    "moon": "\U0001f319",
    "zzz": "\U0001f4a4",
    "rock": "\U0001f91f",
    "sunflower": "\U0001f33b",
    "fire": "\U0001f525",
    "hibiscus": "\U0001f33a",
    "maple": "\U0001f343",
    "rocket": "\U0001f680",
    "daisy": "\U0001f33c",
    "grin": "\U0001f60a",
    "ufo": "\U0001f6f8",
    "pink_heart": "\U0001f496",
    "clap": "\U0001f44f",
    "leaf": "\U0001f33f",
    "sunset": "\U0001f304",
    "think": "\U0001f914",
    "thought": "\U0001f4ad",
    "eye": "\U0001f440",
    "melon": "\U0001f349",
    "pin": "\U0001f4cc",
    "pen": "\u270d\ufe0f",
    "ice": "\U0001f9ca",
    "memo": "\U0001f4dd",
}


# ============================================================
# Templates
# ============================================================

MOMENTS_TEMPLATES = {
    "happy": [
        "{scene}，今天的快乐值已充满 " + E["sun"] + E["sparkles"],
        "生活偶尔也会递来一颗糖 " + E["candy"] + " {scene}",
        "{scene} | 把这份好心情存档 " + E["camera"],
        "没什么特别的，就是突然觉得很开心 " + E["grin"] + " {scene}",
        "{scene}，嘴角疯狂上扬的一天 " + E["rainbow"],
        "今日份的小确幸 " + E["check"] + " {scene}",
        "允许一切发生，今天全是好事 " + E["clover"] + " {scene}",
        "{scene} — 快乐是自己给的 " + E["yellow_heart"],
    ],
    "sad": [
        "{scene}，允许自己偶尔脆弱一下 " + E["rain"],
        "今天不太行。{scene}",
        "{scene} | 没事，会过去的 " + E["fallen_leaf"],
        "情绪低谷也是生活的一部分 " + E["new_moon"] + " {scene}",
        "{scene}，给自己一个拥抱吧 " + E["hug"],
        "偶尔沉默，不代表不快乐 " + E["ocean"] + " {scene}",
    ],
    "funny": [
        "{scene} " + E["joy"] + " 笑死我了哈哈哈哈哈",
        "没有人能在{scene}面前保持严肃 " + E["rofl"],
        "{scene}，人间清醒but人间迷惑 " + E["wink"],
        "社死现场回顾：{scene} " + E["skull"],
        "{scene} | 谁懂啊家人们 " + E["upside_down"],
        "建议全国推广：{scene} " + E["trophy"] + E["joy"],
    ],
    "deep": [
        "{scene}。万物皆有裂痕，那是光照进来的地方 " + E["sunrise"],
        "慢慢来，比较快。{scene} " + E["seedling"],
        "{scene} — 人间值得，但需要你自己去发现 " + E["telescope"],
        "做自己就好，世界会为你让路 " + E["rail"] + " {scene}",
        "{scene}。把期待放低，把生活过好 " + E["seedling"],
        "不必事事通透，糊涂也是一种智慧 " + E["yoga"] + " {scene}",
    ],
    "show-off": [
        "不经意间的凡尔赛：{scene} " + E["nail"] + E["sparkles"],
        "{scene}，也没有很厉害啦（假装淡定）" + E["trophy"],
        "低调低调…但忍不住了 " + E["sunglasses"] + " {scene}",
        "{scene} | 努力终于被看见了 " + E["star2"],
        "随便晒一下，不要太羡慕哦 " + E["gem"] + " {scene}",
        "{scene}，小小成就，不值一提（但还是想说）" + E["sparkles"],
    ],
    "food": [
        "今日份的胃部满足 " + E["plate"] + " {scene}",
        "{scene}，卡路里是什么？不认识 " + E["drool"],
        "人生苦短，先吃为敬 " + E["cheers"] + " {scene}",
        "被{scene}治愈的一天 " + E["yum"],
        "{scene} | 减肥从明天开始 " + E["pizza"],
        "唯有美食不可辜负 " + E["heart"] + " {scene}",
    ],
    "travel": [
        "在{scene}，把自己还给世界 " + E["earth"],
        "{scene} | 眼睛在旅行，心也是 " + E["camera2"],
        "世界那么大，先去{scene}看看 " + E["airplane"],
        "用脚步丈量{scene}的温度 " + E["map"],
        "{scene}，每一帧都是壁纸级别 " + E["art"],
        "旅途的意义，在{scene}找到了答案 " + E["sunrise"],
    ],
    "work": [
        "打工人打工魂 " + E["muscle"] + " {scene}",
        "{scene}，搬砖使我快乐（大概吧）" + E["brick"],
        "今天也是元气满满的打工日 " + E["coffee"] + " {scene}",
        "{scene} | 认真工作的样子最帅 " + E["laptop"],
        "努力搬砖中…{scene} " + E["wrench"],
        "{scene}，工位上的风景也不错 " + E["plant"],
    ],
}

MOMENTS_DEFAULT = [
    "{scene}，记录生活的碎片 " + E["camera"],
    "日常 | {scene} " + E["cloud"],
    "{scene}，平淡即是真 " + E["seedling"],
    "今天的关键词：{scene} " + E["sparkles"],
    "{scene} — 生活的样子 " + E["film"],
    "把{scene}装进相册里 " + E["book"],
]

WEIBO_TEMPLATES = [
    "#{topic}# 今天来聊聊{topic}，你们怎么看？" + E["think"] + " 每个人都有自己的理解，但我觉得这件事值得深思。欢迎评论区讨论~",
    "#{topic}# {topic}这事儿吧，说大不大说小不小，但确实戳到了很多人的痛点。你有同感吗？转发说说你的想法 " + E["thought"],
    "#{topic}# 关于{topic}，分享一个新的视角 " + E["eye"] + " 有时候换个角度看问题，一切都不一样了。#日常思考#",
    "#{topic}# 一觉醒来{topic}上热搜了？来来来，理性吃瓜 " + E["melon"] + " 大家冷静分析一下~ #热搜日常#",
    "#{topic}# 认真说，{topic}真的值得每个人关注一下。不是贩卖焦虑，是真心觉得重要 " + E["pin"],
    "#{topic}# 刚经历了{topic}，有感而发 " + E["pen"] + " 生活处处是素材，记录一下此刻的想法。#碎碎念#",
    "#{topic}# 说一个关于{topic}的冷知识 " + E["ice"] + " 可能90%的人都不知道。看完记得点赞收藏！#涨知识#",
    "#{topic}# 今日份的{topic}打卡 " + E["check"] + " 坚持做一件事最难的不是开始，而是不放弃。#自律生活#",
]

TWITTER_TEMPLATES = [
    "Hot take: {topic} is going to change everything. We're just not ready for it yet.",
    "The thing about {topic} that nobody talks about: it's actually simpler than you think.",
    "Unpopular opinion: {topic} isn't the problem. Our approach to it is.",
    "Spent the morning deep-diving into {topic}. Mind = blown. Here's what I learned:",
    "If you're not paying attention to {topic} right now, you're already behind.",
    "The best advice I ever got about {topic}: start before you're ready.",
    "{topic} in 2024 hits different. The game has changed and I'm here for it.",
    "Three things I wish I knew about {topic} sooner: 1) It compounds. 2) Consistency > intensity. 3) Just start.",
    "Everyone's talking about {topic} but missing the real point entirely.",
    "Reminder: {topic} doesn't have to be complicated. Keep it simple, stay consistent.",
]

INSTAGRAM_TEMPLATES = [
    "Living for this {topic} moment " + E["sparkles"] + "\n\n#{{topic_tag}} #lifestyle #vibes #mood #instagood #photooftheday #explore #trending #aesthetic #love #beautiful #inspiration #daily #life #moments #instadaily #goodvibes #blessed",
    "Found my happy place " + E["heart"] + " {topic}\n\n#{{topic_tag}} #happy #joy #blessed #grateful #lifestyle #vibes #aesthetic #mood #instamood #instalife #explore #trending #lovethis #beautiful #amazing",
    "{topic} state of mind " + E["seedling"] + "\n\n#{{topic_tag}} #mindset #lifestyle #aesthetic #vibes #mood #instagood #photooftheday #instadaily #explore #trending #beautiful #love #inspiration #peaceful #calm",
    "This is what {topic} looks like " + E["camera"] + "\n\n#{{topic_tag}} #photography #aesthetic #vibes #mood #instagood #explore #trending #beautiful #lifestyle #daily #instapic #picoftheday #amazing #love",
    "Chasing {topic} and good vibes only " + E["sun"] + "\n\n#{{topic_tag}} #goodvibes #positivity #lifestyle #aesthetic #vibes #instagood #explore #trending #mood #beautiful #happy #love #daily #instadaily",
    "The art of {topic} " + E["art"] + "\n\n#{{topic_tag}} #art #creative #aesthetic #lifestyle #vibes #instagood #explore #trending #beautiful #mood #inspiration #instadaily #photooftheday #love",
]

BIRTHDAY_TEMPLATES = [
    E["cake"] + " {name}，生日快乐！\n愿你新的一岁，所求皆所愿，所行皆坦途。\n永远年轻，永远热泪盈眶 " + E["sparkles"],
    E["party"] + " {name} 生日快乐！\n又是崭新的一岁，愿你眼里有光、心中有爱、脚下有路。\n干杯，为更好的你 " + E["cheers"],
    E["star2"] + " 亲爱的{name}，生日快乐！\n愿你的每一天都被温柔以待，\n未来的日子里，快乐加倍，烦恼减半 " + E["yellow_heart"],
    E["balloon"] + " {name}！今天是你的主场！\n愿所有的美好都在今天排队向你涌来~\n生日快乐，永远可爱！" + E["blush"],
    E["pie"] + " {name}，又长大一岁啦！\n新的一岁要更勇敢、更自由、更快乐。\n生日快乐，未来可期 " + E["rainbow"],
    E["kiss_heart"] + " {name} 生日快乐！\n不祝你一帆风顺，祝你乘风破浪后依然笑着。\n这一岁，做最酷的自己 " + E["sunglasses"],
]

HOLIDAY_TEMPLATES = [
    E["confetti"] + " {holiday}快乐！\n愿这个{holiday}带给你满满的幸福和温暖 " + E["sparkles"] + "\n好好享受假期吧~",
    E["sparkles"] + " {holiday}到了！\n在这个特别的日子里，愿你被世界温柔以待。\n{holiday}快乐 " + E["heart"],
    E["party"] + " {holiday}快乐！\n放下手机（看完这条再放），好好过节！\n愿你{holiday}期间吃好喝好心情好 " + E["smile"],
    E["star2"] + " 又到{holiday}了，时间真快。\n无论在哪里，愿你被爱包围。\n{holiday}快乐，阖家幸福 " + E["house"],
    E["sparkle"] + " {holiday}的仪式感不能少！\n愿这个{holiday}成为你今年最美好的记忆之一。\n节日快乐 " + E["fireworks"],
]

FOOD_TEMPLATES = [
    E["plate"] + " 今日美食鉴赏：{food}\n色香味俱全，每一口都是满足。\n减肥的事…明天再说吧 " + E["drool"],
    E["star_eyes"] + " 被{food}彻底征服了！\n这个味道，值得专门发一条朋友圈。\n强烈推荐，五星好评 " + E["star5"] * 5,
    E["pot"] + " {food}yyds！\n人间烟火气，最抚凡人心。\n一个人也要好好吃饭 " + E["heart"],
    E["yum"] + " 今天的快乐是{food}给的！\n干饭人干饭魂，干饭都是人上人。\n光盘行动 " + E["check"],
    E["beer"] + " 和{food}的完美邂逅 " + E["sparkles"] + "\n美食是生活的仪式感，\n每一餐都值得被认真对待 " + E["camera"],
    E["coffee"] + " {food}打卡成功！\n味蕾的满足感直接拉满 " + E["chart"] + "\n下次还来，谁也拦不住我 " + E["relieved"],
]

TRAVEL_TEMPLATES = [
    E["airplane"] + " 打卡{place}！\n世界很大，幸好我来了这里。\n眼前的风景，比照片美一万倍 " + E["sunset"],
    E["earth"] + " {place}之旅 Day 1\n放下所有，只管感受。\n旅行的意义，就是成为故事本身 " + E["sparkle"],
    E["camera2"] + " {place}的每一帧都是壁纸\n走过的路都算数，看过的风景都是收获。\n这里，值得你亲自来一趟 " + E["sparkles"],
    E["map"] + " 在{place}迷路了…但谁在乎呢？\n最美的风景往往在计划之外。\n旅行教会我：接受一切意外 " + E["leaf"],
    E["sunrise"] + " 从{place}寄出一张明信片\n给未来的自己：记得这种自由的感觉。\n世界那么大，继续走下去 " + E["footprints"],
    E["tent"] + " {place}旅行手记\n有些地方，去过之后就再也放不下了。\n这里就是其中之一 " + E["heart"],
]

DAILY_TEMPLATES = [
    E["coffee"] + " 新的一天，新的可能。\n不必每天都进步，但要每天都出发 " + E["sunny"],
    E["seedling"] + " 慢慢来，一切都来得及。\n急什么呢，花总会开的 " + E["cherry_blossom"],
    E["sparkles"] + " 你现在的气质里，藏着你走过的路、读过的书和爱过的人。",
    E["moon"] + " 夜深了，给自己一个温柔的晚安。\n明天又是全新的开始 " + E["zzz"],
    E["rainbow"] + " 生活不会永远甜，但永远会有甜的瞬间。\n抓住它们 " + E["rock"],
    E["sun"] + " 做一个温暖的人，不卑不亢，清澈善良。",
    E["sunflower"] + " 把每一个平凡的日子，过成值得回忆的时光 " + E["sparkles"],
    E["muscle"] + " 你比你想象的更强大。\n咬咬牙，就过去了 " + E["fire"],
    E["hibiscus"] + " 与其追赶时间，不如好好感受当下。\n此刻即是最好的时刻 " + E["yoga"],
    E["star2"] + " 人生没有白走的路，每一步都算数。\n继续加油吧 " + E["rocket"],
    E["daisy"] + " 今天也要做一个可爱的人哦 " + E["grin"] + "\n开心是一天，不开心也是一天，不如开开心心的~",
    E["ufo"] + " 宇宙很大，生活很小。\n但你很重要 " + E["pink_heart"],
    E["coffee"] + " 早安。又是充满可能性的一天。\n去做那些让你眼睛发光的事 " + E["sparkles"],
    E["maple"] + " 接受不完美的自己，是成长的开始。\n你已经很棒了 " + E["clap"],
]


def generate_moments(args):
    scene = args[0] if args else "日常"
    mood = "default"
    for i, a in enumerate(args):
        if a == "--mood" and i + 1 < len(args):
            mood = args[i + 1]
            break

    templates = MOMENTS_TEMPLATES.get(mood, MOMENTS_DEFAULT)
    picks = random.sample(templates, min(3, len(templates)))
    print("🖊️  朋友圈文案 | 场景: {} | 心情: {}\n".format(scene, mood))
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(scene=scene)))
        print()


def generate_weibo(args):
    topic = args[0] if args else "日常"
    picks = random.sample(WEIBO_TEMPLATES, min(3, len(WEIBO_TEMPLATES)))
    print(E["memo"] + " 微博文案 | 话题: {}\n".format(topic))
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(topic=topic)))
        print()


def generate_twitter(args):
    topic = args[0] if args else "life"
    picks = random.sample(TWITTER_TEMPLATES, min(3, len(TWITTER_TEMPLATES)))
    print(E["bird"] + " Twitter/X Copy | Topic: {}\n".format(topic))
    for idx, t in enumerate(picks, 1):
        text = t.format(topic=topic)
        char_count = len(text)
        print("{}. {} [{}/280]".format(idx, text, char_count))
        print()


def generate_instagram(args):
    topic = args[0] if args else "life"
    topic_tag = topic.lower().replace(" ", "").replace("-", "")
    picks = random.sample(INSTAGRAM_TEMPLATES, min(3, len(INSTAGRAM_TEMPLATES)))
    print(E["camera2"] + " Instagram Copy | Topic: {}\n".format(topic))
    for idx, t in enumerate(picks, 1):
        text = t.format(topic=topic).replace("{topic_tag}", topic_tag)
        print("{}. {}".format(idx, text))
        print()


def generate_birthday(args):
    name = args[0] if args else "朋友"
    picks = random.sample(BIRTHDAY_TEMPLATES, min(3, len(BIRTHDAY_TEMPLATES)))
    print(E["cake"] + " 生日祝福 | 送给: {}\n".format(name))
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(name=name)))
        print()


def generate_holiday(args):
    holiday = args[0] if args else "节日"
    picks = random.sample(HOLIDAY_TEMPLATES, min(3, len(HOLIDAY_TEMPLATES)))
    print(E["party"] + " 节日祝福 | {}\n".format(holiday))
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(holiday=holiday)))
        print()


def generate_food(args):
    food = args[0] if args else "美食"
    picks = random.sample(FOOD_TEMPLATES, min(3, len(FOOD_TEMPLATES)))
    print(E["plate"] + " 美食文案 | {}\n".format(food))
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(food=food)))
        print()


def generate_travel(args):
    place = args[0] if args else "远方"
    picks = random.sample(TRAVEL_TEMPLATES, min(3, len(TRAVEL_TEMPLATES)))
    print(E["airplane"] + " 旅行文案 | 目的地: {}\n".format(place))
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(place=place)))
        print()


def generate_daily(args):
    picks = random.sample(DAILY_TEMPLATES, min(3, len(DAILY_TEMPLATES)))
    print(E["sparkles"] + " 今日份心灵鸡汤\n")
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t))
        print()


FESTIVAL_TEMPLATES = {
    "春节": [
        E["fireworks"] + " 新年快乐！{f}到，万事胜意！\n愿新的一年，所有美好都如约而至。\n{f}快乐，阖家幸福 " + E["house"],
        E["confetti"] + " {f}的年味就是这个味道！\n一家人在一起，就是最好的团圆。\n{f}快乐，新年大吉 " + E["sparkles"],
        E["party"] + " 辞旧迎新，{f}快乐！\n过去的就让它过去，新年新希望。\n愿你{f}红包拿到手软 " + E["yellow_heart"],
    ],
    "中秋": [
        E["moon"] + " {f}快乐！\n月圆人团圆，最美的风景是回家的路。\n今晚的月亮，替我给想念的人说声{f}快乐 " + E["heart"],
        E["pie"] + " {f}的仪式感：月饼+赏月+想你。\n不管在哪里，抬头看月亮，我们就在一起。\n{f}快乐 " + E["sparkles"],
    ],
    "情人节": [
        E["pink_heart"] + " {f}快乐！\n最好的爱情，是和你一起变成更好的人。\n今天的甜蜜，留给最特别的你 " + E["sparkles"],
        E["heart"] + " {f}不只属于恋人，也属于每一个爱自己的人。\n今天，请对自己好一点 " + E["star2"],
    ],
    "圣诞节": [
        E["sparkles"] + " Merry Christmas! {f}快乐！\n叮叮当叮叮当，铃儿响叮当~\n愿{f}的温暖陪伴你整个冬天 " + E["house"],
        E["party"] + " {f}许愿：世界和平、身体健康、发大财！\n愿圣诞老人记住你的地址 " + E["star2"],
    ],
    "国庆节": [
        E["fireworks"] + " {f}快乐！祖国生日快乐！\n七天假期，你打算怎么过？\n不管去哪，开心最重要 " + E["rainbow"],
        E["confetti"] + " {f}出游第一站打卡！\n人人人人你人人人人\n但快乐不会因为人多而减少 " + E["sun"],
    ],
    "母亲节": [
        E["pink_heart"] + " {f}快乐，妈妈！\n世界上最温暖的词，就是「妈妈」。\n今天请大声说出你的爱 " + E["heart"],
        E["sparkles"] + " {f}到了，致我最伟大的女超人。\n小时候你牵着我的手，长大了换我牵着你。\n{f}快乐 " + E["blush"],
    ],
    "父亲节": [
        E["muscle"] + " {f}快乐！\n爸爸的爱沉默但深沉，\n他不善表达，但从不缺席。\n今天跟老爸说一声：谢谢你 " + E["heart"],
    ],
    "万圣节": [
        E["skull"] + " Happy Halloween! {f}快乐！\n今晚不给糖就捣蛋~\n最吓人的其实是……明天要上班 " + E["joy"],
    ],
    "元宵节": [
        E["confetti"] + " {f}快乐！\n团团圆圆吃汤圆，\n新年的第一个月圆之夜，把最好的祝福送给你 " + E["moon"],
    ],
    "default": [
        E["confetti"] + " {f}快乐！\n在这个特别的日子里，\n愿所有美好都不期而遇。\n节日快乐，开心每一天 " + E["sparkles"],
        E["party"] + " {f}到了！\n放下忙碌，好好过节。\n生活需要仪式感，{f}快乐 " + E["heart"],
        E["star2"] + " {f}的正确打开方式：\n吃好喝好玩好心情好。\n节日快乐，要开心哦 " + E["rainbow"],
    ],
}

BRAND_TONE_MAP = {
    "高端": {
        "desc": "Premium / Luxury",
        "traits": ["克制", "质感", "留白", "意境"],
        "templates": [
            "不止于{brand}，是一种生活态度。",
            "{brand}，为懂得的人而来。",
            "时间会证明，{brand}值得等待。",
            "少即是多。{brand}，不多说。",
            "{brand}，让每一个细节都有意义。",
        ],
        "do": ["用短句", "留白多", "不用感叹号", "用意象而非直白描述"],
        "dont": ["不要用网络用语", "不要用过多emoji", "不要打折促销语气", "不要用大量感叹号"],
    },
    "年轻": {
        "desc": "Youthful / Trendy",
        "traits": ["活力", "潮流", "互动", "大胆"],
        "templates": [
            "{brand}，年轻就要不一样！",
            "跟着{brand}，做最酷的自己 " + E["fire"],
            "{brand}，who cares? I do! " + E["sunglasses"],
            "今天也是被{brand}种草的一天 " + E["sparkles"],
            "{brand}出新品了！第一个冲的人在哪？" + E["rocket"],
        ],
        "do": ["用网络热词", "多互动提问", "大胆用emoji", "制造FOMO"],
        "dont": ["不要太正式", "不要长篇大论", "不要老气横秋", "不要说教"],
    },
    "专业": {
        "desc": "Professional / Expert",
        "traits": ["权威", "数据", "深度", "信任"],
        "templates": [
            "{brand}，用专业说话。",
            "源自{brand}的专业解决方案。",
            "{brand}，{brand}领域的深度实践者。",
            "选择{brand}，选择可靠。",
            "{brand}，让数据告诉你答案。",
        ],
        "do": ["引用数据", "体现专业性", "使用行业术语", "案例展示"],
        "dont": ["不要太感性", "不要用网络梗", "不要夸大其词", "不要过于随意"],
    },
    "温暖": {
        "desc": "Warm / Caring",
        "traits": ["亲切", "关怀", "故事", "共鸣"],
        "templates": [
            "{brand}，温暖每一个平凡的日子 " + E["sun"],
            "有{brand}陪伴的时光，都值得珍藏 " + E["heart"],
            "{brand}，把关心放在你看得见的地方。",
            "每一份{brand}，都是用心的表达 " + E["seedling"],
            "{brand}相信，最好的东西值得等待 " + E["relieved"],
        ],
        "do": ["讲故事", "用温暖的语气", "关注用户感受", "适当用emoji"],
        "dont": ["不要太商业化", "不要冷冰冰", "不要只说产品功能", "不要急于推销"],
    },
    "default": {
        "desc": "General / Balanced",
        "traits": ["平衡", "专业", "亲切", "可信"],
        "templates": [
            "{brand}，值得信赖的选择。",
            "选择{brand}，选择更好的生活。",
            "{brand}，始终为你。",
        ],
        "do": ["保持一致性", "突出品牌优势", "用户导向"],
        "dont": ["不要风格混乱", "不要过度承诺"],
    },
}

THREAD_TEMPLATES_CN = [
    {
        "platform": "微博",
        "structure": [
            "【1/{total}】{topic}，这个话题我想好好聊聊。先说结论：（核心观点）" + E["pin"],
            "【2/{total}】首先，为什么{topic}这么重要？（背景+数据）",
            "【3/{total}】第一个关键点：（论点1+案例）",
            "【4/{total}】第二个关键点：（论点2+案例）",
            "【5/{total}】第三个关键点：（论点3+案例）",
            "【6/{total}】所以，关于{topic}，我的建议是：（行动建议）\n同意的转发，不同意的评论区聊 " + E["think"],
        ],
    },
]

THREAD_TEMPLATES_EN = [
    {
        "platform": "Twitter/X",
        "structure": [
            "A thread on {topic} " + E["pin"] + "\n\nI've spent a lot of time thinking about this. Here's what I've learned:\n\n(1/{total})",
            "First, let's understand why {topic} matters.\n\n(Key context + data point)\n\n(2/{total})",
            "The first key insight:\n\n(Point 1 + supporting evidence)\n\n(3/{total})",
            "The second insight (this one surprised me):\n\n(Point 2 + real example)\n\n(4/{total})",
            "The third insight:\n\n(Point 3 + practical application)\n\n(5/{total})",
            "TL;DR on {topic}:\n\n1. (Summary point 1)\n2. (Summary point 2)\n3. (Summary point 3)\n\nIf this was helpful, retweet the first tweet " + E["heart"] + "\n\n(6/{total})",
        ],
    },
]

VIRAL_TEMPLATES = [
    {
        "type": "争议型（Controversy）",
        "hook": "关于{topic}，我要说一个可能得罪人的观点…",
        "mechanism": "争议引发讨论→评论区战争→算法推送更多人看到",
        "template": "「{topic}」的真相，可能会让你不舒服。\n\n我的观点：（大胆但有理有据的观点）\n\n为什么这么说？因为……\n\n同意的点赞，不同意的评论区说你的理由 " + E["think"],
        "tips": ["有争议但不要过火", "用数据或案例支撑", "预设评论区辩论点"],
    },
    {
        "type": "清单型（Listicle）",
        "hook": "关于{topic}，收藏这一篇就够了！",
        "mechanism": "高收藏率→算法判断为优质内容→持续推送",
        "template": "【建议收藏】关于{topic}的终极指南 " + E["pin"] + "\n\n1️⃣ 第一点（最重要的）\n2️⃣ 第二点\n3️⃣ 第三点\n4️⃣ 第四点\n5️⃣ 第五点\n\n觉得有用的收藏+转发，帮助更多人 " + E["heart"],
        "tips": ["标题强调「收藏」", "内容真的有干货", "结尾引导收藏转发"],
    },
    {
        "type": "故事型（Story）",
        "hook": "关于{topic}，我想讲一个真实的故事…",
        "mechanism": "故事引发共鸣→用户代入感→转发分享",
        "template": "去年这个时候，我还在{topic}上走弯路…\n\n（故事开头）\n直到有一天，（转折点）……\n\n现在回头看，（感悟总结）\n\n如果你也有类似经历，评论区聊聊 " + E["hug"],
        "tips": ["故事要真实可信", "有转折和情绪起伏", "结尾引发共鸣"],
    },
    {
        "type": "挑战型（Challenge）",
        "hook": "我敢说99%的人不知道{topic}的这个秘密…",
        "mechanism": "挑战读者认知→好奇心驱动→完播率高→传播",
        "template": "关于{topic}的一个小测试 " + E["think"] + "\n\n请问：（一个反常识的问题）\n\nA. ……\nB. ……\nC. ……\n\n答案你绝对想不到→评论区揭晓 " + E["eye"],
        "tips": ["问题要反常识", "答案确实出人意料", "利用评论区制造悬念"],
    },
    {
        "type": "工具型（Utility）",
        "hook": "我整理了{topic}的所有资源，免费分享！",
        "mechanism": "免费资源→用户为了获取而转发→裂变传播",
        "template": "【免费分享】{topic}必备资源包 " + E["sparkles"] + "\n\n包含：\n📌 （资源1）\n📌 （资源2）\n📌 （资源3）\n📌 （资源4）\n\n获取方式：转发+评论「要」\n我会私信发给你 " + E["check"],
        "tips": ["资源要真实有价值", "门槛设为转发+评论", "及时私信兑现承诺"],
    },
]


def generate_festival(args):
    festival = args[0] if args else "节日"
    # Match known festival
    templates = None
    for key in FESTIVAL_TEMPLATES:
        if key != "default" and key in festival:
            templates = FESTIVAL_TEMPLATES[key]
            break
    if templates is None:
        templates = FESTIVAL_TEMPLATES["default"]

    picks = random.sample(templates, min(3, len(templates)))
    print(E["party"] + " 节日营销文案 | {}\n".format(festival))
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(f=festival)))
        print()

    # Marketing angle
    print("---")
    print(E["pin"] + " 营销借势建议：")
    print("  1. 提前3-5天开始预热")
    print("  2. 结合品牌特色定制文案")
    print("  3. 设计节日专属视觉素材")
    print("  4. 推出限时活动/折扣")
    print("  5. 用户UGC互动（晒照/故事征集）")
    print()


def generate_brand(args):
    brand = args[0] if args else "品牌"
    tone = args[1] if len(args) > 1 else "default"

    tone_lower = tone.lower()
    tone_data = None
    for key in BRAND_TONE_MAP:
        if key in tone_lower or tone_lower in key:
            tone_data = BRAND_TONE_MAP[key]
            break
    if tone_data is None:
        tone_data = BRAND_TONE_MAP["default"]

    templates = tone_data["templates"]
    picks = random.sample(templates, min(3, len(templates)))

    print(E["art"] + " 品牌文案风格 | {} × {}\n".format(brand, tone_data["desc"]))

    print("品牌调性关键词：{}".format("、".join(tone_data["traits"])))
    print()

    print("--- 文案示例 ---")
    for idx, t in enumerate(picks, 1):
        print("{}. {}".format(idx, t.format(brand=brand)))
        print()

    print("--- DO (建议) ---")
    for item in tone_data["do"]:
        print("  " + E["check"] + " " + item)

    print()
    print("--- DON'T (避免) ---")
    for item in tone_data["dont"]:
        print("  " + E["pin"] + " " + item)
    print()


def generate_thread(args):
    topic = args[0] if args else "话题"
    total = 6

    print(E["memo"] + " 长线程文案 | {}\n".format(topic))

    print("--- 微博版本 ---")
    for template in THREAD_TEMPLATES_CN:
        print("平台: {}  |  共{}条\n".format(template["platform"], total))
        for i, t in enumerate(template["structure"]):
            print("  {}".format(t.format(topic=topic, total=total)))
            print()

    print("--- Twitter/X版本 ---")
    for template in THREAD_TEMPLATES_EN:
        print("Platform: {}  |  {} tweets\n".format(template["platform"], total))
        for i, t in enumerate(template["structure"]):
            print("  {}".format(t.format(topic=topic, total=total)))
            print()

    print("--- " + E["pin"] + " Thread写作技巧 ---")
    print("  1. 第一条是生死线——必须有钩子")
    print("  2. 每条独立可读，但串起来是完整故事")
    print("  3. 最后一条引导转发第一条（扩大传播）")
    print("  4. 控制在5-10条，太长会流失读者")
    print("  5. 每条加入空行，提升阅读体验")
    print()


def generate_viral(args):
    topic = args[0] if args else "话题"

    picks = random.sample(VIRAL_TEMPLATES, min(3, len(VIRAL_TEMPLATES)))
    print(E["fire"] + " 病毒式传播文案 | {}\n".format(topic))

    for idx, v in enumerate(picks, 1):
        print("--- 方案{}: {} ---".format(idx, v["type"]))
        print("  钩子: {}".format(v["hook"].format(topic=topic)))
        print("  传播机制: {}".format(v["mechanism"]))
        print()
        print("  文案模板:")
        for line in v["template"].format(topic=topic).split("\n"):
            print("    {}".format(line))
        print()
        print("  技巧:")
        for tip in v["tips"]:
            print("    " + E["check"] + " {}".format(tip))
        print()

    print("--- " + E["pin"] + " 病毒传播核心公式 ---")
    print("  传播力 = 情绪价值 × 实用价值 × 社交货币")
    print("  • 情绪价值：让人笑/哭/愤怒/惊讶")
    print("  • 实用价值：让人觉得「转发收藏有用」")
    print("  • 社交货币：让人转发后显得有见识/有品味")
    print()


def generate_cta_optimize(args):
    copy_text = args[0] if args else ""
    if not copy_text:
        print("请提供文案内容。用法: copy.sh cta-optimize \"你的文案\"")
        import sys
        sys.exit(1)

    print("=" * 60)
    print(E["fire"] + " CTA转化优化分析")
    print("=" * 60)
    print("")
    print(E["memo"] + " 原始文案：")
    print("  「{}」".format(copy_text))
    print("")
    print("-" * 60)
    print("")

    # 分析维度
    dimensions = [
        {
            "name": E["eye"] + " FOMO（错过恐惧）",
            "desc": "制造稀缺感和紧迫感，让用户害怕错过",
            "check": "原文是否有限时/限量/独家等稀缺信号？",
            "enhance": [
                "加「仅限今天」「最后__个名额」「限时免费」",
                "加倒计时暗示：「明天恢复原价」「活动即将截止」",
                "加独家感：「仅限粉丝」「私域专属」「内部价」",
            ],
            "rewrite": "【限时福利】{} \u2014\u2014 仅限今天，错过再等一年！".format(copy_text),
        },
        {
            "name": E["clap"] + " 社会证明（从众心理）",
            "desc": "展示其他人的选择和评价，降低决策门槛",
            "check": "原文是否有用户数量/好评/案例等社会证明？",
            "enhance": [
                "加数据：「已有10万+人选择」「好评率98%」",
                "加证言：「用户A说：______」",
                "加权威：「被__推荐」「行业Top10都在用」",
            ],
            "rewrite": "{} \u2014\u2014 已有10万+用户亲测有效，好评率98%！".format(copy_text),
        },
        {
            "name": E["rocket"] + " 行动号召（CTA按钮）",
            "desc": "明确告诉用户下一步做什么，降低行动成本",
            "check": "原文是否有明确的行动指引？",
            "enhance": [
                "加明确动作：「点击下方链接」「扫码领取」「评论区扣1」",
                "降低门槛：「免费试用」「无需注册」「1分钟搞定」",
                "加利益钩子：「领取专属福利」「免费送你一份指南」",
            ],
            "rewrite": "{} \U0001f449 现在扫码，免费领取专属资料包！".format(copy_text),
        },
        {
            "name": E["fire"] + " 紧迫感（时间压力）",
            "desc": "创造时间压力，推动立即行动而非拖延",
            "check": "原文是否有时间限制或截止日期？",
            "enhance": [
                "加时间线：「今晚24点截止」「仅剩最后3小时」",
                "加后果：「过期后恢复原价¥999」「名额满了就关闭」",
                "加变化预告：「下周开始涨价」「即将下架」",
            ],
            "rewrite": "\u26a0\ufe0f {} \u2014\u2014 \u4eca\u665a24\u70b9\u622a\u6b62\uff0c\u8fc7\u671f\u6062\u590d\u539f\u4ef7\uff01\u8d76\u7d27\u4e0a\u8f66\uff01".format(copy_text),
        },
    ]

    for i, dim in enumerate(dimensions, 1):
        print("  {}/4 {}".format(i, dim["name"]))
        print("  " + "\u2500" * 50)
        print("  \u539f\u7406\uff1a{}".format(dim["desc"]))
        print("  \u68c0\u67e5\uff1a{}".format(dim["check"]))
        print("")
        print("  \u2728 \u4f18\u5316\u65b9\u6cd5\uff1a")
        for e in dim["enhance"]:
            print("    + {}".format(e))
        print("")
        print("  \u2705 \u6539\u5199\u793a\u4f8b\uff1a")
        print("    {}".format(dim["rewrite"]))
        print("")
        print("")

    print("-" * 60)
    print("")
    print(E["sparkles"] + " \u7ec8\u6781\u4f18\u5316\u7248\uff08\u56db\u5408\u4e00\uff09\uff1a")
    print("")
    print("  \U0001f525 {}".format(copy_text))
    print("")
    print("  \u2728 \u5df2\u6709\u8d85\u8fc710\u4e07\u4eba\u5728\u7528\uff0c\u597d\u8bc4\u7387\u9ad8\u8fbe98%\uff01")
    print("  \u23f0 \u9650\u65f6\u798f\u5229\uff1a\u4eca\u5929\u514d\u8d39\uff0c\u660e\u5929\u6062\u590d\u539f\u4ef7\uffe5999")
    print("  \U0001f449 \u73b0\u5728\u5c31\u626b\u7801\u9886\u53d6\uff0c\u4ec5\u5269\u6700\u540e37\u4e2a\u540d\u989d\uff01")
    print("")
    print("-" * 60)
    print(E["pin"] + " CTA\u8f6c\u5316\u516c\u5f0f\uff1a")
    print("  \u8f6c\u5316\u7387 = \u4ef7\u503c\u611f\u77e5 \u00d7 \u4fe1\u4efb\u5ea6 \u00d7 \u7d27\u8feb\u611f \u00f7 \u884c\u52a8\u6210\u672c")
    print("")
    print("  \u2022 \u63d0\u5347\u4ef7\u503c\u611f\u77e5\uff1a\u8ba9\u7528\u6237\u89c9\u5f97\u300c\u8fd9\u4e2a\u5bf9\u6211\u6709\u7528\u300d")
    print("  \u2022 \u5efa\u7acb\u4fe1\u4efb\u5ea6\uff1a\u7528\u6570\u636e/\u6848\u4f8b/\u6743\u5a01\u8ba9\u7528\u6237\u300c\u76f8\u4fe1\u4f60\u300d")
    print("  \u2022 \u5236\u9020\u7d27\u8feb\u611f\uff1a\u8ba9\u7528\u6237\u89c9\u5f97\u300c\u73b0\u5728\u4e0d\u884c\u52a8\u5c31\u4f1a\u4e22\u300d")
    print("  \u2022 \u964d\u4f4e\u884c\u52a8\u6210\u672c\uff1a\u8ba9\u7528\u6237\u89c9\u5f97\u300c\u505a\u8d77\u6765\u5f88\u7b80\u5355\u300d")
    print("")


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: copy.sh <command> [args]")
        print("运行 copy.sh help 查看详情")
        sys.exit(1)

    cmd = args[0]
    rest = args[1:]

    commands = {
        "moments": generate_moments,
        "weibo": generate_weibo,
        "twitter": generate_twitter,
        "instagram": generate_instagram,
        "birthday": generate_birthday,
        "holiday": generate_holiday,
        "food": generate_food,
        "travel": generate_travel,
        "daily": generate_daily,
        "festival": generate_festival,
        "brand": generate_brand,
        "thread": generate_thread,
        "viral": generate_viral,
        "cta-optimize": generate_cta_optimize,
    }

    func = commands.get(cmd)
    if func is None:
        print("未知命令: {}".format(cmd))
        print("运行 copy.sh help 查看详情")
        sys.exit(1)

    func(rest)


if __name__ == "__main__":
    main()
PYTHON_SCRIPT
echo ""
echo "  Powered by BytesAgain | bytesagain.com | hello@bytesagain.com"
