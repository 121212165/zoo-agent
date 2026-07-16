import sys
import os
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    print("=" * 60)
    print("第二轮测试：API集成测试")
    print("=" * 60)
    
    errors = []
    tests_passed = 0
    
    print("\n1. 测试欢迎接口 /api/welcome")
    try:
        r = requests.get(f"{BASE_URL}/api/welcome", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert "quick_questions" in data
        print(f"  ✓ 欢迎接口正常，快捷问题{len(data['quick_questions'])}个")
        tests_passed += 1
    except Exception as e:
        errors.append(f"欢迎接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n2. 测试动物园信息接口 /api/info")
    try:
        r = requests.get(f"{BASE_URL}/api/info", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["zoo_info"]["ticket_price"]["adult"] == 40
        print(f"  ✓ 动物园信息正常，{data['venues_count']}个场馆，{data['animals_count']}种动物")
        tests_passed += 1
    except Exception as e:
        errors.append(f"动物园信息接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n3. 测试地图数据接口 /api/map")
    try:
        r = requests.get(f"{BASE_URL}/api/map", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "venues" in data
        assert "facilities" in data
        venues_count = len(data["venues"])
        print(f"  ✓ 地图数据正常，{venues_count}个场馆")
        assert "africa_song" in data["venues"], "缺少非洲之歌"
        assert "panda_house" in data["venues"], "缺少熊猫馆"
        assert "gondwana" in data["venues"], "缺少冈瓦纳"
        print(f"  ✓ 核心场馆都在地图上")
        tests_passed += 1
    except Exception as e:
        errors.append(f"地图数据接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n4. 测试动物列表接口 /api/animals")
    try:
        r = requests.get(f"{BASE_URL}/api/animals", timeout=5)
        assert r.status_code == 200
        data = r.json()
        animals_count = len(data["animals"])
        print(f"  ✓ 动物列表正常，共{animals_count}种动物")
        assert "panda" in data["animals"], "缺少大熊猫"
        assert "koala" in data["animals"], "缺少考拉"
        assert "gorilla" in data["animals"], "缺少大猩猩"
        assert "white_faced_saki" in data["animals"], "缺少杜杜"
        print(f"  ✓ 明星动物都在列表中")
        tests_passed += 1
    except Exception as e:
        errors.append(f"动物列表接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n5. 测试单个动物详情接口 /api/animals/{id}")
    try:
        r = requests.get(f"{BASE_URL}/api/animals/panda", timeout=5)
        assert r.status_code == 200
        panda = r.json()
        assert "和和" in panda["names"]
        assert "九九" in panda["names"]
        assert "平平" in panda["names"]
        print(f"  ✓ 大熊猫详情正常：{'/'.join(panda['names'])}")
        
        r = requests.get(f"{BASE_URL}/api/animals/koala", timeout=5)
        koala = r.json()
        assert "梧桐" in koala["names"]
        print(f"  ✓ 考拉详情正常：{'/'.join(koala['names'][:3])}...")
        
        r = requests.get(f"{BASE_URL}/api/animals/gorilla", timeout=5)
        gorilla = r.json()
        assert "香椿头" in gorilla["names"]
        print(f"  ✓ 大猩猩详情正常：{'/'.join(gorilla['names'])}")
        tests_passed += 1
    except Exception as e:
        errors.append(f"动物详情接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n6. 测试聊天接口 /api/chat - 基础对话")
    try:
        test_cases = [
            ("你好", "问候"),
            ("杜杜是谁", "杜杜查询"),
            ("帮我规划路线", "路线规划"),
            ("门票多少钱", "门票查询"),
            ("为什么没有动物表演", "理念查询"),
        ]
        for msg, desc in test_cases:
            r = requests.post(f"{BASE_URL}/api/chat", json={"message": msg}, timeout=10)
            assert r.status_code == 200
            data = r.json()
            assert "response" in data
            assert len(data["response"]) > 10
            print(f"  ✓ {desc}：回复正常 ({len(data['response'])}字符)")
        tests_passed += 1
    except Exception as e:
        errors.append(f"聊天接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n7. 测试聊天接口 - 路线规划返回route_data")
    try:
        r = requests.post(f"{BASE_URL}/api/chat", json={"message": "帮我规划4小时亲子路线"}, timeout=10)
        data = r.json()
        assert data["route_data"] is not None
        route = data["route_data"]
        assert "stops" in route
        assert len(route["stops"]) >= 3
        print(f"  ✓ 路线规划返回正常：{len(route['stops'])}个站点，总时长{route['total_duration']}分钟")
        for stop in route["stops"][:3]:
            print(f"    - {stop['emoji']} {stop['name']}")
        tests_passed += 1
    except Exception as e:
        errors.append(f"路线规划数据失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n8. 测试专用路线规划接口 /api/route/plan")
    try:
        r = requests.post(f"{BASE_URL}/api/route/plan", json={
            "duration_hours": 3,
            "with_kids": True,
            "start_entrance": "south"
        }, timeout=10)
        assert r.status_code == 200
        route = r.json()
        assert len(route["stops"]) >= 3
        print(f"  ✓ 专用路线规划接口正常：{len(route['stops'])}个站点")
        tests_passed += 1
    except Exception as e:
        errors.append(f"专用路线规划接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n9. 测试活跃动物接口 /api/active-animals")
    try:
        r = requests.get(f"{BASE_URL}/api/active-animals?time=10:00", timeout=5)
        assert r.status_code == 200
        active = r.json()
        assert len(active) >= 3
        print(f"  ✓ 活跃动物接口正常：10:00有{len(active)}种动物活跃")
        tests_passed += 1
    except Exception as e:
        errors.append(f"活跃动物接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n10. 测试附近设施接口 /api/nearby-facilities")
    try:
        r = requests.post(f"{BASE_URL}/api/nearby-facilities?facility_type=restroom&limit=3", 
                          json={"x": 90, "y": 420}, timeout=5)
        assert r.status_code == 200
        facs = r.json()
        assert len(facs) >= 1
        print(f"  ✓ 附近设施接口正常：南门附近找到{len(facs)}个卫生间")
        tests_passed += 1
    except Exception as e:
        errors.append(f"附近设施接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n11. 测试场馆列表接口 /api/venues")
    try:
        r = requests.get(f"{BASE_URL}/api/venues", timeout=5)
        assert r.status_code == 200
        venues = r.json()
        assert len(venues) >= 20
        print(f"  ✓ 场馆列表接口正常：{len(venues)}个场馆")
        tests_passed += 1
    except Exception as e:
        errors.append(f"场馆列表接口失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n12. 测试前端页面访问 /")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        assert r.status_code == 200
        assert "红山" in r.text or "hongshan" in r.text.lower() or "<html" in r.text.lower()
        print(f"  ✓ 前端页面可访问")
        tests_passed += 1
    except Exception as e:
        errors.append(f"前端页面访问失败: {e}")
        print(f"  ❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print("第二轮集成测试总结")
    print("=" * 60)
    total_tests = 12
    print(f"通过: {tests_passed}/{total_tests}")
    
    if errors:
        print(f"\n❌ 发现{len(errors)}个错误:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print(f"\n🎉 第二轮API集成测试全部通过！")
        return True

if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)
