import math
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from .data import VENUES, FACILITIES, ANIMALS


def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def estimate_walk_time(distance: float, slope_factor: float = 1.0) -> int:
    base_speed = 60
    return int(distance / base_speed * slope_factor * 1.3)


def get_venue_score(venue: Dict, preferences: Dict) -> float:
    score = 0.0
    tier_scores = {"T0": 50, "T1": 30, "T2": 10}
    score += tier_scores.get(venue.get("tier", "T2"), 10)

    if preferences.get("with_kids"):
        if venue.get("steep_slope"):
            score -= 20
        popular_animals = ["panda", "koala", "giraffe", "meerkat", "red_panda", "capybara", "gorilla", "lemur"]
        for aid in venue.get("animals", []):
            if aid in popular_animals:
                score += 15
        if venue.get("has_rest"):
            score += 10

    if preferences.get("animal_preference"):
        pref = preferences["animal_preference"]
        for aid in venue.get("animals", []):
            animal = ANIMALS.get(aid, {})
            if pref in animal.get("name", "") or any(pref in n for n in animal.get("names", [])):
                score += 30
            if pref in ["猛兽", "大猫"] and aid in ["tiger", "chinese_cats", "wolf", "bears"]:
                score += 25
            if pref in ["灵长类", "猴子"] and aid in ["orangutan", "chimpanzee", "gibbon", "white_faced_saki", "red_backed_saki", "golden_monkey", "gorilla", "lemur"]:
                score += 25
            if pref in ["鸟类", "鸟"] and venue.get("mountain") == "小红山":
                score += 20

    if preferences.get("avoid_sun") and not venue.get("indoor") and not venue.get("has_rest"):
        score -= 10

    if preferences.get("time_hours", 4) <= 2.5 and venue.get("tier") == "T2":
        score -= 15

    return score


def find_nearest_entrance(venue_id: str) -> Tuple[str, Dict]:
    venue = VENUES[venue_id]
    best_entrance = None
    best_dist = float('inf')
    for entrance in FACILITIES["entrance"]:
        d = calculate_distance(venue["x"], venue["y"], entrance["x"], entrance["y"])
        if d < best_dist:
            best_dist = d
            best_entrance = entrance
    return best_entrance["name"], best_entrance


def plan_route(
    duration_hours: float = 4.0,
    with_kids: bool = False,
    with_elderly: bool = False,
    avoid_slopes: bool = False,
    animal_preference: str = "",
    start_entrance: str = "south",
    current_time: Optional[str] = None
) -> Dict:
    preferences = {
        "time_hours": duration_hours,
        "with_kids": with_kids,
        "with_elderly": with_elderly,
        "avoid_sun": avoid_slopes,
        "avoid_slopes": avoid_slopes or with_kids or with_elderly,
        "animal_preference": animal_preference
    }

    if current_time:
        now = datetime.strptime(current_time, "%H:%M")
    else:
        now = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    total_available_min = int(duration_hours * 60)

    entrance_map = {
        "north": (200, 30, "北门（小红山）"),
        "east": (510, 200, "东门（大红山）"),
        "south": (90, 420, "南门（新区）"),
    }

    if start_entrance not in entrance_map:
        start_entrance = "south" if (with_kids or with_elderly) else "south"

    start_x, start_y, start_name = entrance_map[start_entrance]

    scored_venues = []
    for vid, venue in VENUES.items():
        if preferences["avoid_slopes"] and venue.get("steep_slope"):
            continue
        score = get_venue_score(venue, preferences)
        dist_from_start = calculate_distance(start_x, start_y, venue["x"], venue["y"])
        scored_venues.append((-score, dist_from_start, vid, venue))

    scored_venues.sort(key=lambda x: (x[0], x[1]))

    selected = []
    current_x, current_y = start_x, start_y
    elapsed_min = 0
    remaining_min = total_available_min

    must_see_t0 = [vid for vid, v in VENUES.items() if v["tier"] == "T0"]
    for vid in must_see_t0[:5]:
        if len(selected) >= 7:
            break
        venue = VENUES[vid]
        if preferences["avoid_slopes"] and venue.get("steep_slope") and vid != "panda_house":
            continue
        d = calculate_distance(current_x, current_y, venue["x"], venue["y"])
        walk_time = estimate_walk_time(d, 1.3 if venue.get("steep_slope") else 1.0)
        visit_time = venue["duration_min"]
        total_time = walk_time + visit_time
        if elapsed_min + total_time < remaining_min - 30:
            selected.append({
                "id": vid,
                "name": venue["name"],
                "walk_time": walk_time,
                "visit_time": visit_time,
                "animals": [ANIMALS.get(aid, {}).get("emoji", "") + ANIMALS.get(aid, {}).get("name", "") for aid in venue.get("animals", []) if aid in ANIMALS],
                "tips": venue.get("tips", ""),
                "x": venue["x"],
                "y": venue["y"],
                "tier": venue["tier"]
            })
            elapsed_min += total_time
            current_x, current_y = venue["x"], venue["y"]

    for neg_score, dist, vid, venue in scored_venues:
        if any(s["id"] == vid for s in selected):
            continue
        if elapsed_min >= remaining_min - 40:
            break
        d = calculate_distance(current_x, current_y, venue["x"], venue["y"])
        walk_time = estimate_walk_time(d, 1.3 if venue.get("steep_slope") else 1.0)
        visit_time = venue["duration_min"]
        total_time = walk_time + visit_time
        if elapsed_min + total_time <= remaining_min - 20:
            selected.append({
                "id": vid,
                "name": venue["name"],
                "walk_time": walk_time,
                "visit_time": visit_time,
                "animals": [ANIMALS.get(aid, {}).get("emoji", "") + ANIMALS.get(aid, {}).get("name", "") for aid in venue.get("animals", []) if aid in ANIMALS],
                "tips": venue.get("tips", ""),
                "x": venue["x"],
                "y": venue["y"],
                "tier": venue["tier"]
            })
            elapsed_min += total_time
            current_x, current_y = venue["x"], venue["y"]

    end_entrance = None
    best_end_dist = float('inf')
    for e_name, e_data in [("北门", (200, 30)), ("东门", (510, 200)), ("南门", (90, 420))]:
        d = calculate_distance(current_x, current_y, e_data[0], e_data[1])
        if d < best_end_dist:
            best_end_dist = d
            end_entrance = e_name

    walk_to_end = estimate_walk_time(best_end_dist)

    route_description = []
    current_time_dt = now
    route_description.append(f"📍 {start_name}入园")

    for i, stop in enumerate(selected):
        current_time_dt += timedelta(minutes=stop["walk_time"])
        arr_time = current_time_dt.strftime("%H:%M")
        current_time_dt += timedelta(minutes=stop["visit_time"])
        dep_time = current_time_dt.strftime("%H:%M")
        animals_str = "、".join(stop["animals"]) if stop["animals"] else ""
        desc = f"{i+1}. {stop['name']}"
        if animals_str:
            desc += f"（{animals_str}）"
        desc += f" {arr_time}到，游览约{stop['visit_time']}分钟"
        if stop["tips"]:
            desc += f"\n   💡 {stop['tips']}"
        route_description.append(desc)

    current_time_dt += timedelta(minutes=walk_to_end)
    end_time = current_time_dt.strftime("%H:%M")
    route_description.append(f"🏁 从{end_entrance}出园，预计{end_time}结束")

    total_walk = sum(s["walk_time"] for s in selected) + walk_to_end
    total_visit = sum(s["visit_time"] for s in selected)

    recommended = []
    if with_kids or with_elderly:
        recommended.append("👶 推荐从南门（新区）入园，坡缓省力，推婴儿车友好")
    if duration_hours <= 2.5:
        recommended.append("⏰ 时间较紧，已优先安排T0必看展区")
    if animal_preference:
        recommended.append(f"🎯 已优先安排您感兴趣的{animal_preference}相关展区")

    return {
        "start_entrance": start_name,
        "end_entrance": end_entrance,
        "total_duration_min": total_walk + total_visit,
        "walk_time_min": total_walk,
        "visit_time_min": total_visit,
        "stops": selected,
        "route_text": "\n".join(route_description),
        "recommendations": recommended,
        "current_time": now.strftime("%H:%M")
    }


def find_nearest_facilities(x: int, y: int, facility_type: str = "all", limit: int = 3) -> List[Dict]:
    results = []
    types_to_check = [facility_type] if facility_type != "all" else ["restroom", "restaurant", "rest_area", "drinking_water"]
    for ftype in types_to_check:
        for fac in FACILITIES.get(ftype, []):
            d = calculate_distance(x, y, fac["x"], fac["y"])
            walk = estimate_walk_time(d)
            results.append({
                "type": ftype,
                "name": fac["name"],
                "distance": int(d),
                "walk_time_min": walk,
                "x": fac["x"],
                "y": fac["y"]
            })
    results.sort(key=lambda r: r["distance"])
    return results[:limit]


def get_active_animals(current_time_str: str = "") -> List[Dict]:
    if current_time_str:
        now = datetime.strptime(current_time_str, "%H:%M")
    else:
        now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

    active = []
    for aid, animal in ANIMALS.items():
        is_active = False
        reason = ""
        for ft in animal.get("feeding_times", []):
            ft_clean = ft.split("（")[0].strip()
            try:
                ft_time = datetime.strptime(ft_clean, "%H:%M")
                diff = abs((now - ft_time).total_seconds() / 60)
                if diff <= 45:
                    is_active = True
                    reason = f"喂食时间（{ft}），动物活跃度高！"
                    break
            except:
                pass

        if 9 <= now.hour <= 11 and not is_active:
            if animal.get("category") in ["star", "popular"]:
                is_active = True
                reason = "上午是动物最活跃的时段"

        if is_active:
            venue = VENUES.get(animal["venue"], {})
            active.append({
                "id": aid,
                "name": animal["name"],
                "emoji": animal["emoji"],
                "names": animal["names"],
                "venue_name": venue.get("name", ""),
                "reason": reason,
                "tier": animal["tier"]
            })
    return active[:8]
