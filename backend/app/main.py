from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data import ANIMALS, VENUES, FACILITIES, ZOO_INFO, WELCOME_MESSAGE, QUICK_QUESTIONS
from app.chat_engine import HongshanAgent
from app.route_planner import plan_route, find_nearest_facilities, get_active_animals

app = FastAPI(title="红山森林动物园智能陪逛Agent", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = HongshanAgent()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")


class ChatRequest(BaseModel):
    message: str
    position: Optional[Dict] = None
    user_context: Optional[Dict] = None


class RoutePlanRequest(BaseModel):
    duration: float = 4.0
    duration_hours: float = 4.0
    with_kids: bool = False
    with_elderly: bool = False
    avoid_slopes: bool = False
    animal_preference: str = ""
    animalPreference: str = ""
    start_entrance: str = "south"
    startEntrance: str = "south"
    current_time: Optional[str] = None


class PositionRequest(BaseModel):
    x: int
    y: int


venue_emojis = {
    "africa_song": "🦒",
    "tangjiahe": "🐒",
    "panda_house": "🐼",
    "cat_planet": "🐆",
    "tiger_area": "🐅",
    "bear_valley": "🐻",
    "wolf_valley": "🐺",
    "native_area": "🦊",
    "meerkat_house": "🦡",
    "giraffe_house": "🦒",
    "monkey_mountain": "🐒",
    "koala_house": "🐨",
    "gondwana": "🌴",
    "gaoligong": "🐾",
    "asian_primate": "🐵",
    "orangutan_house": "🦧",
    "hippo_house": "🦛",
    "elephant_house": "🐘",
    "hornbill_house": "🦜",
    "crane_garden": "🦢",
    "tropical_birds": "🦜",
    "zhangjipo": "🦌",
    "parrot_house": "🦜",
    "kangaroo_corner": "🦘",
    "lemur_island": "🐒",
}

facility_emojis = {
    "restroom": "🚻",
    "restaurant": "🍴",
    "rest_area": "🪑",
    "drinking_water": "💧",
    "entrance": "🚪",
}


def transform_venue(vid: str, v: Dict) -> Dict:
    return {
        "id": vid,
        "name": v["name"],
        "description": v.get("description", ""),
        "position": {"x": v["x"], "y": v["y"]},
        "x": v["x"],
        "y": v["y"],
        "area": v.get("area", ""),
        "mountain": v.get("mountain", ""),
        "tier": v.get("tier", "T2"),
        "indoor": v.get("indoor", False),
        "has_rest": v.get("has_rest", False),
        "steep_slope": v.get("steep_slope", False),
        "duration_min": v.get("duration_min", 15),
        "tips": v.get("tips", ""),
        "animals": v.get("animals", []),
        "emoji": venue_emojis.get(vid, "📍"),
    }


def transform_facilities() -> Dict:
    result = {}
    for ftype, flist in FACILITIES.items():
        result[ftype] = []
        for f in flist:
            result[ftype].append({
                "id": f"{ftype}_{len(result[ftype])}",
                "name": f["name"],
                "type": ftype,
                "position": {"x": f["x"], "y": f["y"]},
                "x": f["x"],
                "y": f["y"],
                "emoji": facility_emojis.get(ftype, "📍"),
                "note": f.get("note", ""),
            })
    return result


def transform_animal(aid: str, a: Dict) -> Dict:
    venue = VENUES.get(a["venue"], {})
    return {
        "id": aid,
        "name": a["name"],
        "names": a.get("names", []),
        "emoji": a.get("emoji", "🐾"),
        "venue": a["venue"],
        "venue_id": a["venue"],
        "venue_name": venue.get("name", ""),
        "description": a.get("description", ""),
        "story": a.get("story", ""),
        "feeding_times": a.get("feeding_times", []),
        "tier": a.get("tier", "T2"),
        "category": a.get("category", ""),
    }


def transform_route(route: Dict) -> Dict:
    stops = []
    for s in route.get("stops", []):
        venue_data = VENUES.get(s["id"], {})
        stops.append({
            "id": s["id"],
            "name": s["name"],
            "emoji": venue_emojis.get(s["id"], "📍"),
            "walk_time": s.get("walk_time", 0),
            "suggested_duration": s.get("visit_time", 15),
            "reason": s.get("tips", ""),
            "animals": s.get("animals", []),
            "tier": s.get("tier", "T2"),
            "position": {"x": s.get("x", 0), "y": s.get("y", 0)},
        })

    walk_dist = route.get("walk_time_min", 30) * 60
    total_dur = route.get("total_duration_min", 240)

    names = {
        "北门（小红山）": "北门入园",
        "东门（大红山）": "东门入园",
        "南门（新区）": "南门入园",
    }
    start_name = names.get(route.get("start_entrance", ""), "南门入园")

    end_names = {"北门": "北门出园", "东门": "东门出园", "南门": "南门出园"}
    end_name = end_names.get(route.get("end_entrance", ""), "北门出园")

    stops.insert(0, {
        "id": "start",
        "name": start_name,
        "emoji": "🚪",
        "walk_time": 0,
        "suggested_duration": 0,
        "reason": "",
    })

    stops.append({
        "id": "end",
        "name": end_name,
        "emoji": "🏁",
        "walk_time": 0,
        "suggested_duration": 0,
        "reason": "愉快结束旅程",
    })

    return {
        "name": f"{int(route.get('total_duration_min', 240) / 60)}小时定制游览路线",
        "total_duration": total_dur,
        "walking_distance": walk_dist,
        "stops": stops,
        "route_text": route.get("route_text", ""),
        "recommendations": route.get("recommendations", []),
        "start_entrance": route.get("start_entrance", ""),
        "end_entrance": route.get("end_entrance", ""),
    }


@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/info")
async def get_zoo_info():
    return {
        "zoo_info": ZOO_INFO,
        "venues_count": len(VENUES),
        "animals_count": len(ANIMALS)
    }


@app.get("/api/map")
@app.get("/api/map-data")
async def get_map_data():
    venues_dict = {}
    for vid, v in VENUES.items():
        venues_dict[vid] = transform_venue(vid, v)

    return {
        "venues": venues_dict,
        "facilities": transform_facilities(),
        "zoo_info": ZOO_INFO,
    }


@app.get("/api/animals")
async def get_animals(category: Optional[str] = None):
    animals_dict = {}
    for aid, a in ANIMALS.items():
        if category and a.get("category") != category:
            continue
        animals_dict[aid] = transform_animal(aid, a)
    return {"animals": animals_dict}


@app.get("/api/animals/{animal_id}")
async def get_animal_detail(animal_id: str):
    if animal_id not in ANIMALS:
        raise HTTPException(status_code=404, detail="Animal not found")
    a = ANIMALS[animal_id]
    return transform_animal(animal_id, a)


@app.get("/api/venues")
async def get_venues():
    result = []
    for vid, v in VENUES.items():
        result.append(transform_venue(vid, v))
    return result


@app.get("/api/venues/{venue_id}")
async def get_venue_detail(venue_id: str):
    if venue_id not in VENUES:
        raise HTTPException(status_code=404, detail="Venue not found")
    v = VENUES[venue_id]
    return transform_venue(venue_id, v)


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if req.user_context:
        if req.user_context.get("with_kids"):
            agent.user_context["with_kids"] = True
        if req.user_context.get("duration_hours"):
            agent.user_context["duration_hours"] = req.user_context["duration_hours"]

    response = agent.chat(req.message, req.position)
    quick_questions = agent.get_quick_questions()

    route_data = None
    animal_data = None

    msg_lower = req.message.lower()
    if any(w in msg_lower for w in ["路线", "规划", "怎么逛", "行程", "安排"]):
        duration = agent.user_context.get("duration_hours", 4)
        with_kids = agent.user_context.get("with_kids", False)
        if "2小时" in req.message or "两小时" in req.message:
            duration = 2
        elif "3小时" in req.message or "三小时" in req.message:
            duration = 3
        elif "6小时" in req.message or "六小时" in req.message:
            duration = 6

        r = plan_route(
            duration_hours=duration,
            with_kids=with_kids or "娃" in req.message,
            with_elderly="老人" in req.message,
            avoid_slopes=with_kids or "不爬山" in req.message,
            start_entrance="south" if ("南门" in req.message or with_kids) else ("north" if "北门" in req.message else "south")
        )
        route_data = transform_route(r)

    animal_id = agent._match_animal(req.message)
    if animal_id:
        animal_data = transform_animal(animal_id, ANIMALS[animal_id])

    return {
        "response": response,
        "quick_questions": quick_questions,
        "route_data": route_data,
        "animal_data": animal_data,
        "context": {
            "with_kids": agent.user_context.get("with_kids", False),
            "duration_hours": agent.user_context.get("duration_hours", 4)
        },
        "speak": True
    }


@app.post("/api/route/plan")
@app.post("/api/plan-route")
async def create_route(req: RoutePlanRequest):
    duration = req.duration if req.duration != 4.0 else req.duration_hours
    animal_pref = req.animal_preference if req.animal_preference else req.animalPreference
    start_ent = req.start_entrance if req.start_entrance != "south" else req.startEntrance

    route = plan_route(
        duration_hours=duration,
        with_kids=req.with_kids,
        with_elderly=req.with_elderly,
        avoid_slopes=req.avoid_slopes,
        animal_preference=animal_pref,
        start_entrance=start_ent,
        current_time=req.current_time
    )
    return transform_route(route)


@app.get("/api/active-animals")
async def active_animals(time: Optional[str] = None):
    return get_active_animals(time)


@app.post("/api/nearby-facilities")
async def nearby_facilities(req: PositionRequest, facility_type: str = "all", limit: int = 3):
    return find_nearest_facilities(req.x, req.y, facility_type, limit)


@app.get("/api/venue-guide/{venue_id}")
async def venue_guide(venue_id: str):
    if venue_id not in VENUES:
        raise HTTPException(status_code=404, detail="Venue not found")
    guide_text = agent.trigger_venue_guide(venue_id)
    v = VENUES[venue_id]
    return {
        "venue_id": venue_id,
        "venue_name": v["name"],
        "guide_text": guide_text
    }


@app.get("/api/welcome")
async def welcome():
    return {
        "message": WELCOME_MESSAGE,
        "quick_questions": QUICK_QUESTIONS
    }


if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/css/{file_path:path}")
async def css(file_path: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "css", file_path))


@app.get("/js/{file_path:path}")
async def js(file_path: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "js", file_path))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
