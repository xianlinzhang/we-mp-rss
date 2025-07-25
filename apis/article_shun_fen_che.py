import random
import re
import string

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel
from sqlalchemy import or_

from core.auth import get_current_user
from core.db import DB
from core.match_area.match import match_words
from core.wx import search_Biz
from .base import success_response, error_response
from datetime import datetime
from core.config import cfg
from core.res import save_avatar_locally
router = APIRouter(prefix=f"/free-ride", tags=["顺风车数据管理"])
def UpdateArticle(art:dict):
            return DB.add_article(art)


def clean_and_extract_phone(text):
    # 去除所有空白字符（包括空格、换行、制表符等）
    cleaned_text = re.sub(r'\s+', '', text)

    # 提取11位手机号
    match = re.search(r'\b\d{11}\b', cleaned_text)
    return match.group() if match else ""

@router.get("/search/{kw}", summary="搜索顺风车")
async def search_mp(
    kw: str = "",
    limit: int = 5,
    offset: int = 0
):
    session = DB.get_session()
    try:
        result = search_Biz(kw)
        data={
            'list':result.get('list'),
            'page':{
                'limit':limit,
                'offset':offset
            },
            'total':result.get('total')
        }
        return success_response(data)
    except Exception as e:
        print(f"搜索公众号错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message=f"搜索公众号失败,请重新扫码授权！{str(e)}",
            )
        )

@router.get("", summary="获取顺风车列表")
async def get_mps(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    phone: str = Query(""),
    car_type: str = Query(""),
    departure: str = Query(""),
    destination: str = Query(""),
    time_str: str = Query(""),
):
    session = DB.get_session()
    try:
        from core.models.article_shun_fen_che import ArticleShunFenChe
        query = session.query(ArticleShunFenChe)
        if kw:
            query = query.filter(ArticleShunFenChe.original_content.ilike(f"%{kw}%"))

        if phone:
            query = query.filter(ArticleShunFenChe.phone.ilike(f"%{phone}%"))

        if car_type:
            query = query.filter(ArticleShunFenChe.car_type.ilike(f"%{car_type}%"))

        if departure:
            query = query.filter(ArticleShunFenChe.departure.ilike(f"%{departure}%"))

        if destination:
            query = query.filter(ArticleShunFenChe.destination.ilike(f"%{destination}%"))

        if time_str:
            query = query.filter(ArticleShunFenChe.time_str.ilike(f"%{time_str}%"))

        total = query.count()
        mps = query.order_by(ArticleShunFenChe.created_at.desc()).limit(limit).offset(offset).all()
        return success_response({
            "list": [{
                "id": mp.id,
                "original_content": mp.original_content,
                "car_type": mp.car_type,
                "departure": mp.departure,
                "destination": mp.destination,
                "time_str": mp.time_str,
                "hours_str": mp.hours_str,
                "phone": mp.phone,
                "num_people": mp.num_people,
                "created_at": mp.created_at.isoformat()
            } for mp in mps],
            "page": {
                "limit": limit,
                "offset": offset,
                "total": total
            },
            "total": total
        })
    except Exception as e:
        print(f"获取顺风车列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="获取顺风车列表失败"
            )
        )


def generate_unique_id(id: int) -> str:
    # 将 id 转换为字符串并获取其长度
    id_str = str(id)
    id_len = len(id_str)

    # 生成剩余长度的随机字符（仅字母和数字）
    remaining_len = max(0, 30 - id_len)  # 确保不会出现负数
    random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=remaining_len))

    # 拼接 id 和随机字符，并截断为 30 个字符
    unique_id = (id_str + random_chars)[:30]

    return unique_id

def toggle_ride_status(current_status: str) -> str:
    """
    切换顺风车状态：求车 <-> 提供车

    参数:
        current_status (str): 当前状态（"求车" 或 "提供车"）

    返回:
        str: 切换后的状态
    """
    if current_status == "求车":
        return "提供车"
    elif current_status == "提供车":
        return "求车"
    else:
        raise ValueError("无效的状态值，只能是 '求车' 或 '提供车'")


def get_related_list(time_str: str, car_type: str, departure: str,destination: str):
    session = DB.get_session()
    try:
        from core.models.article_shun_fen_che import ArticleShunFenChe

        departures = match_words(departure)
        destinations = match_words(destination)

        # print(f" departure 匹配到的关键词：{departures}")
        # print(f" destination 匹配到的关键词：{destinations}")

        query = session.query(ArticleShunFenChe)
        query = query.filter(ArticleShunFenChe.time_str == time_str)
        query = query.filter(ArticleShunFenChe.car_type == (car_type))

        if departures:
            query = query.filter(or_(*[ArticleShunFenChe.departure.ilike(f"%{k}%") for k in departures]))
        else:
            query = query.filter(ArticleShunFenChe.departure.ilike(f"%{departure}%"))

        if destinations:
            query = query.filter(or_(*[ArticleShunFenChe.destination.ilike(f"%{k}%") for k in destinations]))
        else:
            query = query.filter(ArticleShunFenChe.destination.ilike(f"%{destination}%"))

        mps = query.order_by(ArticleShunFenChe.created_at.asc()).all()
        return [{
                "id": mp.id,
                "original_content": mp.original_content,
                "car_type": mp.car_type,
                "departure": mp.departure,
                "destination": mp.destination,
                "time_str": mp.time_str,
                "hours_str": mp.hours_str,
                "phone": mp.phone,
                "num_people": mp.num_people,
                "created_at": mp.created_at.isoformat()
            } for mp in mps]

    except Exception as e:
        print(f"获取数据详情错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="获取数据详情失败"
            )
        )


class MessageTaskCreate(BaseModel):
    original_content: str = ''
    car_type: str = ''
    departure: str = ''
    destination: str = ''
    time_str: str = ''
    hours_str: str = ''
    phone: str = ''
    num_people: str = ''

@router.put("/{mp_id}", summary="更新消息任务")
async def update_mps(
     mp_id: str,
    task_data: MessageTaskCreate = Body(...),
):
    db = DB.get_session()
    """
    更新消息任务

    参数:
        task_id: 要更新的消息任务ID
        task_data: 消息任务更新数据
        db: 数据库会话
        current_user: 当前认证用户

    返回:
        包含更新后消息任务的响应
        404: 消息任务不存在
        400: 请求数据验证失败
        500: 数据库操作异常
    """
    try:
        from core.models.article_shun_fen_che import ArticleShunFenChe
        db_task = db.query(ArticleShunFenChe).filter(ArticleShunFenChe.id == mp_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="ShunFenChe not found")

        if task_data.original_content is not None:
            db_task.original_content = task_data.original_content
        if task_data.car_type is not None:
            db_task.car_type = task_data.car_type
        if task_data.departure is not None:
            db_task.departure = task_data.departure
        if task_data.destination is not None:
            db_task.destination = task_data.destination
        if task_data.time_str is not None:
            db_task.time_str = task_data.time_str
        if task_data.hours_str is not None:
            db_task.hours_str = task_data.hours_str
        if task_data.phone is not None:
            # 只提取手机号
            phone = clean_and_extract_phone(task_data.phone)
            db_task.phone = phone
        if task_data.num_people is not None:
            db_task.num_people = task_data.num_people
        db.commit()
        db.refresh(db_task)
        return success_response(data=db_task)
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))

@router.get("/{mp_id}", summary="获取顺风车详情")
async def get_mp(
    mp_id: str,
    # current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.article_shun_fen_che import ArticleShunFenChe
        # 唯一Id查找数据
        mp_detail = session.query(ArticleShunFenChe).filter(ArticleShunFenChe.unique_id == mp_id).first()

        # 主键Id查找数据
        # if not mp_detail:
        #     mp_detail = session.query(ArticleShunFenChe).filter(ArticleShunFenChe.id == mp_id).first()

        if not mp_detail:
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail=error_response(
                    code=40401,
                    message="数据不存在"
                )
            )

        return success_response({
            "id": mp_detail.id,
            "original_content": mp_detail.original_content,
            "car_type": mp_detail.car_type,
            "departure": mp_detail.departure,
            "destination": mp_detail.destination,
            "time_str": mp_detail.time_str,
            "hours_str": mp_detail.hours_str,
            "phone": mp_detail.phone,
            "num_people": mp_detail.num_people,
            "created_at": mp_detail.created_at.isoformat() if mp_detail.created_at else None,
            "relate_list": get_related_list(mp_detail.time_str, toggle_ride_status(mp_detail.car_type), mp_detail.departure, mp_detail.destination),
        })

    except Exception as e:
        print(f"获取数据详情错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="获取数据详情失败"
            )
        )

@router.post("", summary="添加顺风车")

async def add_mp(
    original_content: str = Body(..., min_length=1, max_length=10000),
    car_type: str = Body(None, max_length=255),
    departure: str = Body(None, max_length=255),
    destination: str = Body(None, max_length=500),
    time_str: str = Body(None, max_length=255),
    hours_str: str = Body(None, max_length=255),
    phone: str = Body(None, max_length=255),
    num_people: str = Body(None, max_length=255)
):
    session = DB.get_session()
    try:
        from core.models.article_shun_fen_che import ArticleShunFenChe
        import time
        now = datetime.now()

        # 只提取手机号
        phone = clean_and_extract_phone(phone)

        # 检查已存在：原始内容
        existing_feed = session.query(ArticleShunFenChe).filter(ArticleShunFenChe.original_content == original_content).first()

        if existing_feed is None:
            # 检查已存在: 手机号和日期
            existing_feed = session.query(ArticleShunFenChe).filter(ArticleShunFenChe.phone == phone, ArticleShunFenChe.time_str == time_str).first()


        if existing_feed:
            # 更新现有记录
            existing_feed.car_type = car_type
            existing_feed.departure = departure
            existing_feed.destination = destination
            existing_feed.phone = phone
            existing_feed.time_str = time_str
            existing_feed.updated_at = now
            session.commit()
        else:
            # 创建新的Feed记录
            new_feed = ArticleShunFenChe(
                original_content=original_content,
                car_type=car_type,
                departure= departure,
                destination=destination,
                time_str=time_str,
                hours_str=hours_str,
                phone=phone,
                num_people=num_people,
                created_at=now,
                updated_at=now,

            )
            session.add(new_feed)
            session.commit()
            new_feed.unique_id = generate_unique_id(new_feed.id)
            session.commit()
            session.refresh(new_feed)
        
        feed = existing_feed if existing_feed else new_feed
            
        return success_response({
            "id": feed.id,
            "original_content": feed.original_content,
            "car_type": feed.car_type,
            "departure": feed.departure,
            "destination": feed.destination,
            "time_str": feed.time_str,
            "hours_str": feed.hours_str,
            "phone": feed.phone,
            "num_people": feed.num_people,
            "created_at": feed.created_at.isoformat()
        })
    except Exception as e:
        session.rollback()
        print(f"添加顺风车错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="添加顺风车失败"
            )
        )
