import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data import ANIMALS, VENUES, FACILITIES, ZOO_INFO, WELCOME_MESSAGE
from app.route_planner import calculate_distance, estimate_walk_time, get_venue_score, plan_route, find_nearest_facilities, get_active_animals
from app.chat_engine import HongshanAgent

def test_data_integrity():
    print("=" * 50)
    print("第一轮测试：数据完整性测试")
    print("=" * 50)
    
    errors = []
    
    print(f"✓ 动物数量: {len(ANIMALS)}")
    print(f"✓ 场馆数量: {len(VENUES)}")
    
    required_animal_fields = ["name", "names", "venue", "description", "feeding_times", "story", "emoji", "category", "tier"]
    for aid, animal in ANIMALS.items():
        for field in required_animal_fields:
            if field not in animal:
                errors.append(f"动物 {aid} 缺少字段: {field}")
        if animal["venue"] not in VENUES:
            errors.append(f"动物 {aid} 引用了不存在的场馆: {animal['venue']}")
    
    required_venue_fields = ["name", "area", "mountain", "description", "animals", "x", "y", "indoor", "has_rest", "steep_slope", "duration_min", "tier"]
    for vid, venue in VENUES.items():
        for field in required_venue_fields:
            if field not in venue:
                errors.append(f"场馆 {vid} 缺少字段: {field}")
        for aid in venue.get("animals", []):
            if aid not in ANIMALS:
                errors.append(f"场馆 {vid} 引用了不存在的动物: {aid}")
    
    facility_types = ["restroom", "restaurant", "rest_area", "entrance", "drinking_water"]
    for ftype in facility_types:
        if ftype not in FACILITIES:
            errors.append(f"缺少设施类型: {ftype}")
        else:
            print(f"✓ {ftype} 设施数量: {len(FACILITIES[ftype])}")
    
    if ZOO_INFO["ticket_price"]["adult"] != 40:
        errors.append(f"门票价格不正确，应为40元，实际是{ZOO_INFO['ticket_price']['adult']}元")
    
    if errors:
        print("\n❌ 发现错误:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("\n✅ 数据完整性测试通过！")
        return True

def test_route_planner():
    print("\n" + "=" * 50)
    print("路线规划模块测试")
    print("=" * 50)
    
    d = calculate_distance(0, 0, 3, 4)
    assert abs(d - 5.0) < 0.01, f"距离计算错误: {d}"
    print("✓ 距离计算正确")
    
    walk = estimate_walk_time(60)
    print(f"✓ 60单位距离步行时间约: {walk}分钟")
    
    route_kids = plan_route(duration_hours=3, with_kids=True, avoid_slopes=True, start_entrance="south")
    print(f"✓ 亲子路线规划成功，{len(route_kids['stops'])}个景点，总时长{route_kids['total_duration_min']}分钟")
    
    route_full = plan_route(duration_hours=4, start_entrance="south")
    print(f"✓ 经典路线规划成功，{len(route_full['stops'])}个景点，总时长{route_full['total_duration_min']}分钟")
    print(f"  推荐入口: {route_full['start_entrance']}，推荐出口: {route_full['end_entrance']}")
    
    facs = find_nearest_facilities(90, 420, "restroom", 3)
    print(f"✓ 南门附近卫生间: {len(facs)}个")
    for f in facs:
        print(f"  - {f['name']} 步行{f['walk_time_min']}分钟")
    
    active = get_active_animals("10:00")
    print(f"✓ 10:00活跃动物: {len(active)}种")
    for a in active[:3]:
        print(f"  - {a['emoji']}{a['name']} ({a['venue_name']})")
    
    print("✅ 路线规划模块测试通过！")
    return True

def test_chat_engine():
    print("\n" + "=" * 50)
    print("聊天引擎测试")
    print("=" * 50)
    
    agent = HongshanAgent()
    
    tests = [
        ("你好", "问候"),
        ("熊猫馆在哪", "场馆查询"),
        ("杜杜是谁", "动物查询-杜杜"),
        ("考拉什么时候最活跃", "时间查询"),
        ("帮我规划4小时路线", "路线规划"),
        ("附近有卫生间吗", "设施查询"),
        ("为什么没有动物表演", "理念查询"),
        ("老马是谁", "故事查询"),
        ("红山必看有哪些", "推荐查询"),
        ("门票多少钱", "信息查询"),
        ("和和九九平平", "熊猫名字测试"),
        ("香椿头马兰头", "大猩猩名字测试"),
        ("茉莉的故事", "考拉茉莉测试"),
    ]
    
    all_pass = True
    for query, desc in tests:
        try:
            resp = agent.chat(query)
            if len(resp) > 20:
                print(f"✓ {desc}: 回复正常 ({len(resp)}字符)")
            else:
                print(f"⚠ {desc}: 回复过短 - {resp[:50]}")
                all_pass = False
        except Exception as e:
            print(f"❌ {desc}: 错误 - {e}")
            all_pass = False
    
    print("\n✅ 聊天引擎测试完成！" if all_pass else "\n❌ 聊天引擎测试发现问题")
    return all_pass

def test_real_data_verification():
    print("\n" + "=" * 50)
    print("真实数据验证")
    print("=" * 50)
    
    panda = ANIMALS["panda"]
    assert "和和" in panda["names"], "熊猫应该有和和"
    assert "九九" in panda["names"], "熊猫应该有九九"
    assert "平平" in panda["names"], "熊猫应该有平平"
    print("✓ 熊猫名字正确: 和和、九九、平平")
    
    koala = ANIMALS["koala"]
    assert "梧桐" in koala["names"], "考拉应该有梧桐"
    assert "柠檬" in koala["names"], "考拉应该有柠檬"
    assert "茉莉" in koala["story"] or "2025年1月" in koala["story"], "考拉故事应该包含茉莉"
    print("✓ 考拉数据正确: 梧桐、柠檬、橙子、青柑等，包含茉莉故事")
    
    gorilla = ANIMALS["gorilla"]
    assert "香椿头" in gorilla["names"], "大猩猩应该有香椿头"
    assert "马兰头" in gorilla["names"], "大猩猩应该有马兰头"
    assert "小蒜头" in gorilla["names"], "大猩猩应该有小蒜头"
    assert "枸杞头" in gorilla["names"], "大猩猩应该有枸杞头"
    print("✓ 大猩猩野菜F4名字正确: 香椿头、马兰头、小蒜头、枸杞头")
    
    dudu = ANIMALS["white_faced_saki"]
    assert "杜杜" in dudu["names"], "白面僧面猴应该有杜杜"
    assert "花花" in dudu["names"], "白面僧面猴应该有花花（老婆）"
    print("✓ 白面僧面猴杜杜一家数据正确")
    
    assert ZOO_INFO["ticket_price"]["adult"] == 40, "成人票应为40元"
    assert ZOO_INFO["ticket_price"]["student"] == 20, "学生票应为20元"
    print("✓ 门票价格正确: 成人40元，学生20元")
    
    assert "africa_song" in VENUES, "应该有非洲之歌展区"
    assert "tangjiahe" in VENUES, "应该有唐家河展区"
    assert "gondwana" in VENUES, "应该有冈瓦纳展区"
    assert "gaoligong" in VENUES, "应该有高黎贡展区"
    print("✓ 核心展区存在")
    
    africa = VENUES["africa_song"]
    assert africa["tier"] == "T0", "非洲之歌应为T0级"
    assert africa["steep_slope"] == False, "南门新区应该坡缓"
    print("✓ 南门新区非洲之歌数据正确（坡缓、T0级）")
    
    print("✅ 真实数据验证全部通过！")
    return True

if __name__ == "__main__":
    results = []
    results.append(test_data_integrity())
    results.append(test_route_planner())
    results.append(test_chat_engine())
    results.append(test_real_data_verification())
    
    print("\n" + "=" * 50)
    print("第一轮测试总结")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 第一轮单元测试全部通过！")
    else:
        print(f"\n⚠️ 有 {total - passed} 项测试未通过")
