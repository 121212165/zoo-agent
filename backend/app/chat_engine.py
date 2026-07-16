import re
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .data import ANIMALS, VENUES, ZOO_INFO, RED_STANDING_PROMPT, QUICK_QUESTIONS
from .route_planner import plan_route, find_nearest_facilities, get_active_animals


class HongshanAgent:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.user_context: Dict = {
            "with_kids": False,
            "duration_hours": 4,
            "current_venue": None,
            "current_position": {"x": 200, "y": 30}
        }

    def _match_animal(self, query: str) -> Optional[str]:
        for aid, animal in ANIMALS.items():
            if animal["name"] in query:
                return aid
            for name in animal["names"]:
                if name in query and len(name) >= 2:
                    return aid
        animal_keywords = {
            "熊猫": "panda", "大熊猫": "panda", "和和": "panda", "九九": "panda", "平平": "panda",
            "考拉": "koala", "无尾熊": "koala", "梧桐": "koala", "柠檬": "koala", "茉莉": "koala", "橙子": "koala", "青柑": "koala", "金桔": "koala",
            "大猩猩": "gorilla", "野菜": "gorilla", "f4": "gorilla", "香椿头": "gorilla", "马兰头": "gorilla", "小蒜头": "gorilla", "枸杞头": "gorilla",
            "杜杜": "white_faced_saki", "白面僧面猴": "white_faced_saki", "花花": "white_faced_saki", "花生": "white_faced_saki",
            "红背须僧面猴": "red_backed_saki", "屁股猴": "red_backed_saki", "阿拉丁": "red_backed_saki", "沙和尚猴": "red_backed_saki",
            "水豚": "capybara", "卡皮巴拉": "capybara",
            "小熊猫": "red_panda", "红熊猫": "red_panda",
            "川金丝猴": "golden_monkey", "金丝猴": "golden_monkey", "瑞瑞": "golden_monkey", "突突": "golden_monkey", "重阳": "golden_monkey", "来福": "golden_monkey", "二万": "golden_monkey",
            "红猩猩": "orangutan", "乐申": "orangutan", "小黑": "orangutan",
            "黑猩猩": "chimpanzee", "乌豆": "chimpanzee",
            "长颈鹿": "giraffe", "圣诞": "giraffe",
            "老虎": "tiger", "东北虎": "tiger", "孟加拉虎": "tiger", "汪小白": "tiger",
            "雪豹": "chinese_cats", "云豹": "chinese_cats", "猞猁": "chinese_cats", "金钱豹": "chinese_cats", "豹": "chinese_cats", "越越": "chinese_cats", "三腿豹": "chinese_cats",
            "大猫": "chinese_cats", "猫科": "chinese_cats",
            "狼": "wolf", "灰狼": "wolf",
            "细尾獴": "meerkat", "狐獴": "meerkat", "獴哥": "meerkat",
            "本土": "native_animals", "貉": "native_animals", "猪獾": "native_animals", "水獭": "native_animals", "豹猫": "native_animals", "獐": "native_animals", "扬子鳄": "native_animals",
            "野猪": "wild_boar", "打工猪": "wild_boar", "明天": "wild_boar",
            "长臂猿": "gibbon", "黄颊长臂猿": "gibbon",
            "棕熊": "bears", "黑熊": "bears", "马来熊": "bears", "老马": "bears", "熊": "bears",
            "犀牛": "rhino", "白犀牛": "rhino",
            "斑马": "zebra",
            "大象": "elephant", "亚洲象": "elephant", "路麦": "elephant", "麦哥": "elephant",
            "犀鸟": "hornbill", "双角犀鸟": "hornbill",
            "环尾狐猴": "lemur", "狐猴": "lemur",
            "袋鼠": "kangaroo",
            "树懒": "sloth"
        }
        for kw, aid in animal_keywords.items():
            if kw in query:
                return aid
        return None

    def _match_venue(self, query: str) -> Optional[str]:
        venue_keywords = {
            "熊猫馆": "panda_house", "猫科馆": "cat_planet", "猫科星球": "cat_planet",
            "中国猫科馆": "cat_planet", "虎区": "tiger_area", "老虎馆": "tiger_area", "虎山": "tiger_area",
            "熊谷": "bear_valley", "熊馆": "bear_valley", "狼馆": "wolf_valley",
            "狼谷": "wolf_valley", "本土区": "native_area", "本土物种": "native_area", "本土保育区": "native_area",
            "细尾獴馆": "meerkat_house", "狐獴馆": "meerkat_house",
            "长颈鹿馆": "giraffe_house", "猴山": "monkey_mountain",
            "考拉馆": "koala_house", "冈瓦纳": "gondwana", "高黎贡": "gaoligong",
            "亚洲灵长": "asian_primate", "亚洲灵长区": "asian_primate", "猩猩馆": "orangutan_house",
            "河马馆": "hippo_house", "大象馆": "elephant_house", "亚洲象馆": "elephant_house",
            "犀鸟园": "hornbill_house", "犀鸟馆": "hornbill_house", "鹤园": "crane_garden",
            "热带鸟馆": "tropical_birds", "獐麂坡": "zhangjipo",
            "鹦鹉馆": "parrot_house", "唐家河": "tangjiahe",
            "非洲之歌": "africa_song", "南门新区": "africa_song", "非洲区": "africa_song",
            "新区": "africa_song", "袋鼠角": "kangaroo_corner", "澳洲区": "kangaroo_corner",
            "猴狐岛": "lemur_island", "狐猴岛": "lemur_island"
        }
        for kw, vid in venue_keywords.items():
            if kw in query:
                return vid
        for vid, venue in VENUES.items():
            if venue["name"].replace("（", "").replace("）", "") in query.replace("（", "").replace("）", ""):
                return vid
        return None

    def _detect_intent(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["路线", "规划", "怎么逛", "怎么玩", "怎么走", "行程", "安排"]):
            return "plan_route"
        if any(w in q for w in ["卫生间", "厕所", "洗手间", "休息", "餐厅", "吃饭", "喝水", "直饮水", "哪里有"]):
            return "find_facility"
        if any(w in q for w in ["现在", "活跃", "喂食", "什么时候", "几点", "时间"]):
            return "check_time"
        if any(w in q for w in ["表演", "动物表演", "马戏"]):
            return "about_performance"
        if any(w in q for w in ["门票", "多少钱", "价格", "开放", "关门", "几点开"]):
            return "zoo_info"
        if any(w in q for w in ["必看", "推荐", "去哪", "值得", "打卡"]):
            return "recommend"
        if any(w in q for w in ["老马", "茉莉", "故事", "为什么", "沈志军", "求报复", "历史"]):
            return "tell_story"
        return "animal_info"

    def _generate_animal_response(self, animal_id: str, query: str) -> str:
        animal = ANIMALS.get(animal_id)
        if not animal:
            return "这个动物我好像不太熟，让我去问问饲养员～"

        venue = VENUES.get(animal["venue"], {})
        response_parts = []
        response_parts.append(f"{animal['emoji']} {animal['name']}")
        if animal["names"]:
            response_parts.append(f"（{'/'.join(animal['names'])}）")
        response_parts.append("\n\n")
        response_parts.append(animal["description"])
        response_parts.append("\n\n")
        response_parts.append(f"📍 位置：{venue.get('name', '未知展区')}")
        if animal.get("feeding_times"):
            response_parts.append(f"\n⏰ 喂食/活跃时间：{'、'.join(animal['feeding_times'])}")
        response_parts.append(f"\n\n{animal['story']}")

        if self.user_context.get("with_kids"):
            if animal_id == "panda":
                response_parts.append("\n\n🐼 给小朋友说：大熊猫一天要拉40次便便哦！它们的便便还是绿色的，因为吃太多竹子啦～")
            elif animal_id == "koala":
                response_parts.append("\n\n🐨 给小朋友说：考拉宝宝会在妈妈的育儿袋里待6个月才出来，就像小袋鼠一样！")
            elif animal_id == "capybara":
                response_parts.append("\n\n🦫 给小朋友说：水豚是世界上脾气最好的动物，谁都可以坐在它背上！")

        return "".join(response_parts)

    def _generate_venue_response(self, venue_id: str) -> str:
        venue = VENUES.get(venue_id)
        if not venue:
            return "这个展区我不太确定在哪里呢..."

        animals_in_venue = []
        for aid in venue.get("animals", []):
            if aid in ANIMALS:
                a = ANIMALS[aid]
                animals_in_venue.append(f"{a['emoji']}{a['name']}（{'/'.join(a['names'][:2])}）")

        parts = [f"## {venue['name']}\n\n"]
        parts.append(venue["description"])
        parts.append(f"\n\n📍 位置：{venue['area']}片区")
        parts.append(f"\n⏱️ 建议游览时间：{venue['duration_min']}分钟")
        if venue.get("steep_slope"):
            parts.append("\n⚠️ 注意：这个展区有坡路，推婴儿车会有点费力气哦")
        if venue.get("indoor"):
            parts.append("\n🏠 室内展区，不怕晒也不怕下雨")
        if venue.get("has_rest"):
            parts.append("\n🪑 附近有休息区")
        if animals_in_venue:
            parts.append(f"\n\n🐾 这里可以看到：{'、'.join(animals_in_venue)}")
        if venue.get("tips"):
            parts.append(f"\n\n💡 小贴士：{venue['tips']}")
        return "".join(parts)

    def _handle_route_planning(self, query: str) -> str:
        duration = self.user_context.get("duration_hours", 4)
        with_kids = self.user_context.get("with_kids", False)
        pref = ""

        hour_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:小时|个小时|h)', query)
        if hour_match:
            duration = float(hour_match.group(1))
            self.user_context["duration_hours"] = duration

        if any(w in query for w in ["孩子", "娃", "小朋友", "小孩", "带娃", "亲子", "宝宝"]):
            with_kids = True
            self.user_context["with_kids"] = True

        if "老人" in query or "老年" in query:
            with_kids = True

        pref_map = {
            "猛兽": "猛兽", "大猫": "猛兽", "猫科": "猛兽", "老虎": "猛兽", "豹子": "猛兽",
            "猴子": "灵长类", "猩猩": "灵长类", "长臂猿": "灵长类", "灵长": "灵长类",
            "鸟": "鸟类", "鹦鹉": "鸟类", "犀鸟": "鸟类",
            "熊猫": "熊猫", "考拉": "考拉", "长颈鹿": "长颈鹿"
        }
        for kw, p in pref_map.items():
            if kw in query:
                pref = p
                break

        entrance = "south" if (with_kids or "南门" in query) else ("north" if "北门" in query else "south")
        if "东门" in query:
            entrance = "east"

        route = plan_route(
            duration_hours=duration,
            with_kids=with_kids,
            with_elderly="老人" in query,
            avoid_slopes=with_kids or "不爬山" in query or "怕累" in query,
            animal_preference=pref,
            start_entrance=entrance
        )

        text = f"🗺️ 为你规划了一条{duration}小时的专属路线！\n\n"
        if with_kids:
            text += "👶 已考虑带娃需求，避开陡坡，安排休息点和小朋友喜欢的动物~\n\n"
        text += f"**推荐路线**：\n{route['route_text']}\n\n"
        text += f"⏱️ 总时长约{route['total_duration_min']}分钟（步行{route['walk_time_min']}分钟+游览{route['visit_time_min']}分钟）\n\n"

        if route["recommendations"]:
            text += "💡 **小贴士**：\n"
            for rec in route["recommendations"]:
                text += f"- {rec}\n"

        text += "\n告诉我你想先去哪里，我给你详细讲讲那里的故事！"
        return text

    def _handle_facility(self, query: str, pos: Optional[Dict] = None) -> str:
        x = pos["x"] if pos else self.user_context["current_position"]["x"]
        y = pos["y"] if pos else self.user_context["current_position"]["y"]

        ftype = "all"
        if any(w in query for w in ["卫生间", "厕所", "洗手间"]):
            ftype = "restroom"
        elif any(w in query for w in ["餐厅", "吃饭", "吃什么"]):
            ftype = "restaurant"
        elif any(w in query for w in ["休息", "坐一坐", "坐一下"]):
            ftype = "rest_area"
        elif any(w in query for w in ["喝水", "直饮水", "水"]):
            ftype = "drinking_water"

        facilities = find_nearest_facilities(x, y, ftype, 3)
        if not facilities:
            return "附近好像没有找到相关设施呢，换个地方看看？"

        type_names = {"restroom": "卫生间", "restaurant": "餐厅", "rest_area": "休息区", "drinking_water": "直饮水点"}
        text = f"📍 为你找到附近的{type_names.get(ftype, '设施')}：\n\n"
        for i, f in enumerate(facilities):
            tn = type_names.get(f["type"], f["type"])
            walk = f["walk_time_min"]
            if walk <= 2:
                dist_text = "就在旁边"
            elif walk <= 5:
                dist_text = f"步行约{walk}分钟"
            else:
                dist_text = f"步行约{walk}分钟"
            text += f"{i+1}. **{f['name']}** ({tn}) - {dist_text}\n"
        return text

    def _handle_active_animals(self, query: str) -> str:
        current_time = datetime.now().strftime("%H:%M")
        if "上午" in query:
            current_time = "10:00"
        elif "下午" in query:
            current_time = "14:30"

        active = get_active_animals(current_time)
        text = f"⏰ 现在是{current_time}左右，这些动物最活跃：\n\n"
        for a in active:
            text += f"{a['emoji']} **{a['name']}**（{'/'.join(a['names'][:2])}）- {a['venue_name']}\n"
            text += f"   {a['reason']}\n\n"
        text += "一般来说上午9-11点是动物最活跃的时候，下午很多动物会午休哦～"
        return text

    def _handle_performance_question(self) -> str:
        return """**红山从2011年起就取消了所有动物表演** 🚫

这是中国第一家取消动物表演的动物园。在沈志军园长看来，动物园不是人类的娱乐场，而是物种保护机构和教育机构。

动物表演的本质是强迫动物做出违背天性的动作来取悦人类，这和红山"尊重动物天性"的理念是完全相悖的。

不过你可以看到更精彩的——那就是动物们**自然的行为**：
🐾 看大猩猩纳库检查场地安全（首领的责任感）
🐾 看长臂猿在树冠间荡来荡去（真正的"两岸猿声啼不住"）
🐾 看饲养员给大猫做丰容（动物展现野外捕猎的智慧）
🐾 看水豚泡澡（治愈力满分的自然行为）

这些比任何表演都好看，因为这才是动物本来的样子 🌿"""

    def _handle_zoo_info(self, query: str) -> str:
        if any(w in query for w in ["门票", "多少钱", "价格"]):
            return f"""🎫 **门票信息**
- 成人票：{ZOO_INFO['ticket_price']['adult']}元
- 学生票：{ZOO_INFO['ticket_price']['student']}元（凭有效证件）
- 免票：{ZOO_INFO['ticket_price']['child_free']}儿童、{ZOO_INFO['ticket_price']['senior_free']}老人
- 60岁以上老人、军人、残疾人等凭证件免费

⏰ **开放时间**：{ZOO_INFO['open_time']}-{ZOO_INFO['close_time']}（{ZOO_INFO['stop_entry_time']}停止入园）
📞 咨询电话：{ZOO_INFO['phone']}
📍 地址：{ZOO_INFO['address']}

🚇 交通：地铁1号线红山动物园站到北门最方便！如果带娃推荐从南门（新区）进，坡少省力～"""
        else:
            return f"""⏰ **开放时间**：{ZOO_INFO['open_time']}-{ZOO_INFO['close_time']}（{ZOO_INFO['stop_entry_time']}停止入园）
🏞️ 园区面积：{ZOO_INFO['area']}（很大！建议穿舒服的鞋子）
🐾 动物数量：{ZOO_INFO['animal_count']}
🎫 成人票{ZOO_INFO['ticket_price']['adult']}元，学生半价，1.4米以下/60岁以上免费

**特别提醒**：
- 园区有三座山（大红山、小红山、放牛山），全程要爬坡，穿舒适的鞋！
- 南门（2025年新开放的新区）坡最缓，推婴儿车/带老人推荐从南门进
- 园内电瓶车20元/人，可以坐4站"""

    def _handle_recommend(self) -> str:
        return """🌟 **红山必看T0级展区**（错过等于没来！）：

1. **非洲之歌（南门新区）** 🦒🦍🦓
   2025年新开的王牌！野菜F4大猩猩、长颈鹿、斑马、白犀牛，平缓好走

2. **中国猫科馆** 🐆
   大陆首个入围Zoolex的展区，雪豹/云豹/猞猁，上午10点丰容最活跃

3. **大熊猫馆** 🐼
   三只熊猫和和/九九/平平，干饭时间：8:30、12:00、14:30、16:30

4. **考拉馆** 🐨
   华东唯一有考拉的城市动物园！节假日8:30有称重互动

5. **冈瓦纳展区** 🐒🦫
   网红杜杜（白面僧面猴）+佛系水豚，悬浮栈道超有氛围

6. **高黎贡展区** 🐼
   小熊猫的天堂，空中栈道近距离看小煤球，还能听到长臂猿叫

7. **狼谷** 🐺
   沉浸式设计，清晨/傍晚雨后可能听到狼嚎！

8. **本土物种保育区** 🐗
   红山最有特色的展区之一，打工猪"明天"在这里上班

**经典路线推荐**：南门进→非洲之歌→考拉馆→冈瓦纳→高黎贡→猩猩馆→熊猫馆→猫科馆→狼谷→北门出，约4小时"""

    def _handle_story(self, query: str) -> str:
        if "老马" in query or "马来熊" in query:
            return """**老马的故事** 🐻

老马是一只马来熊，1989年出生，2022年最后一天在红山安详离开，活了33岁——相当于人类90多岁。

以前红山的熊馆是传统坑式，游客站在高处往下看，老马有严重的刻板行为：它会一直仰着头，站着向游客讨要食物。

2021年熊谷改造完成，整座山头都给了熊。已经32岁高龄的老马第一次走上草地，沈园长后来回忆说："初到户外运动场的时候，它迈着悠闲的步伐，累了会半倚在石头边休息喘气，看看花、看看蝴蝶。"

2022年冬天老马身体变差，饲养员给它蓄了暖暖的稻草窝，加了暖灯和油灯，把它最爱吃的糊糊做成温热的。12月31日，老马在稻草中安祥离世。熊馆员工集体为它写了讣告，看哭了无数人。

老马的一生，就是红山场馆改造和动物福利进步的缩影。

> "动物福利永远没有天花板。"——沈志军"""

        elif "茉莉" in query or "考拉" in query and "白血病" in query:
            return """**考拉茉莉的故事** 🐨

茉莉（Merindah）是2018年从澳大利亚来到红山的第一批考拉，是红山考拉家族的" founding mother"。

她的名字"茉莉"和伴侣"梧桐"是从188位市民取的500多个名字里选出来的，充满南京特色。在红山的7年里，茉莉生下了柠檬、柚子、金桔、橙子、青柑、六宝六个宝宝，组成了热闹的考拉家族。

饲养员每天要处理几百斤桉树叶（考拉只吃桉树叶，而且非常挑），还要根据每只考拉的喜好分拣投喂，精心记录它们吃的怎么样、拉的怎么样。

但考拉这个物种面临一个残酷的现实：几乎所有北部考拉都携带考拉逆转录病毒（KoRV），这让它们极易患上白血病。目前国际上没有有效疗法。茉莉的两个孩子柚子和金桔已经先后因此病离世。

2025年1月12日茉莉食欲明显下降，1月14日早上7点30分，她在睡梦中平静离开了。饲养员一直怀抱着她，给她喂最爱吃的桉树嫩叶。

茉莉的故事也提醒我们：野外考拉正面临栖息地丧失、森林大火等威胁，2022年澳大利亚政府已将它们列为"濒危"。保护考拉，我们能做的还有很多 🌿"""

        elif "沈志军" in query or "求报复" in query or "疫情" in query:
            return """**那个"求报复"的园长** 🎤

2020年疫情闭园51天，红山亏损超过2000万——作为全国唯一自收自支的省会动物园，没有财政拨款，所有收入都靠门票。

沈志军园长在一席做了场演讲，说："有人说疫情过后会有一波报复性出游，可是我等了三个多月，还没有多少人来报复我。"

这句话火了。不是因为卖惨，而是因为人们看到了一个真心为动物着想的动物园——2011年取消动物表演、2014年取消付费投喂、花十几年自筹资金改造场馆给动物更好的家。

花蚀在走遍中国56家动物园后评价红山是"国内进步最快的动物园"。

现在的红山年接待近800万人次，但他们始终记得：**动物园不是娱乐场，是保护机构和教育机构。**"""

        elif "为什么没有动物表演" in query or "取消表演" in query:
            return self._handle_performance_question()
        else:
            return """红山有太多动人的故事了，你想听听哪个？

🐻 **老马的故事**——那只33岁的马来熊，场馆改造后第一次看到蝴蝶
🐨 **茉莉的故事**——考拉妈妈和她的六个宝宝，以及考拉种族面临的困境
🎤 **沈园长"求报复"**——2020年疫情那场打动无数人的演讲
🦍 **野菜F4**——四只大猩猩跨越10年保育接力来到南京的故事
🐗 **打工猪明天**——被救助的小野猪如何成为红山"优秀员工"
🦒 **长颈鹿自主迁徙**——为什么饲养员让孕晚期的长颈鹿自己走400米

直接告诉我你想听哪个吧！"""

    def chat(self, user_message: str, position: Optional[Dict] = None) -> str:
        query = user_message.strip()

        if position:
            self.user_context["current_position"] = position

        if any(w in query for w in ["带娃", "有孩子", "带小孩", "亲子"]):
            self.user_context["with_kids"] = True
        if any(w in query for w in ["2小时", "两小时"]):
            self.user_context["duration_hours"] = 2
        elif any(w in query for w in ["3小时", "三小时"]):
            self.user_context["duration_hours"] = 3
        elif any(w in query for w in ["4小时", "四小时", "半天"]):
            self.user_context["duration_hours"] = 4
        elif any(w in query for w in ["6小时", "六小时", "一整天", "全天"]):
            self.user_context["duration_hours"] = 6

        intent = self._detect_intent(query)

        if intent == "plan_route":
            return self._handle_route_planning(query)
        elif intent == "find_facility":
            return self._handle_facility(query, position)
        elif intent == "check_time":
            return self._handle_active_animals(query)
        elif intent == "about_performance":
            return self._handle_performance_question()
        elif intent == "zoo_info":
            return self._handle_zoo_info(query)
        elif intent == "recommend":
            return self._handle_recommend()
        elif intent == "tell_story":
            return self._handle_story(query)

        animal_id = self._match_animal(query)
        if animal_id:
            return self._generate_animal_response(animal_id, query)

        venue_id = self._match_venue(query)
        if venue_id:
            return self._generate_venue_response(venue_id)

        if any(w in query for w in ["你好", "hi", "hello", "在吗", "开始"]):
            return f"""你好呀！我是你的红山专属陪逛向导小红山 🐾

这里是中国最有温度的动物园——2011年全国首家取消动物表演，一切以动物福利为底线。

**你可以问我：**
🗺️ "帮我规划4小时亲子路线"
🐼 "熊猫馆在哪？什么时候最活跃？"
🐨 "给我讲讲考拉茉莉的故事"
🚻 "附近有卫生间吗？"
🚫 "为什么红山没有动物表演？"
🌟 "红山有哪些必看的？"

或者直接说你感兴趣的动物/展区，我给你讲它们的故事！"""

        if any(w in query for w in ["谢谢", "感谢", "多谢"]):
            return "不客气呀！祝你在红山玩得开心，记得慢慢逛、静静看，每只动物都有自己的故事 🌿 有其他问题随时叫我~"

        return f"""这个问题我得去问问饲养员～ 你可以换个方式问我哦！

比如：
- 直接说动物名字："熊猫""考拉""杜杜""老马"
- 问地点："冈瓦纳在哪""猫科馆怎么去"
- 问路线："帮我规划路线""带娃怎么逛"
- 问设施："卫生间在哪""哪里可以吃饭"
- 问故事："讲讲沈园长的故事""茉莉是谁"

我会把红山的故事一个一个讲给你听 🐾"""

    def trigger_venue_guide(self, venue_id: str) -> str:
        venue = VENUES.get(venue_id)
        if not venue:
            return ""

        animals = []
        for aid in venue.get("animals", []):
            if aid in ANIMALS:
                a = ANIMALS[aid]
                animals.append(f"{a['emoji']}{a['name']}")

        greetings = [
            f"欢迎来到{venue['name']}！",
            f"你现在在{venue['name']}啦～",
            f"到{venue['name']}了！"
        ]
        text = random.choice(greetings) + "\n\n"
        text += venue["description"]

        if animals:
            text += f"\n\n🐾 这里有{'、'.join(animals)}"

        if venue.get("tips"):
            text += f"\n\n💡 {venue['tips']}"

        animal_id = venue.get("animals", [None])[0] if venue.get("animals") else None
        if animal_id and animal_id in ANIMALS and random.random() > 0.4:
            a = ANIMALS[animal_id]
            text += f"\n\n{a['emoji']} 悄悄告诉你：{a['story'][:120]}..."

        return text

    def get_welcome(self) -> str:
        from .data import WELCOME_MESSAGE
        return WELCOME_MESSAGE

    def get_quick_questions(self) -> List[str]:
        return QUICK_QUESTIONS
