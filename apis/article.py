from fastapi import APIRouter, Depends, HTTPException, status, Query
from core.auth import get_current_user
from core.db import DB
from core.models.base import DATA_STATUS
from core.models.article import Article
from sqlalchemy import and_, or_
from .base import success_response, error_response
from core.config import cfg
router = APIRouter(prefix=f"/articles", tags=["文章管理"])
@router.api_route("", summary="获取文章列表",methods= ["GET", "POST"], operation_id="get_articles_list")
async def get_articles(
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    status: str = Query(None),
    search: str = Query(None),
    mp_id: str = Query(None)
):
    session = DB.get_session()
    try:
      
        
        # 构建查询条件
        query = session.query(Article)
        
        if status:
            query = query.filter(Article.status == status)
        else:
            query = query.filter(Article.status != DATA_STATUS.DELETED)
        if mp_id:
            query = query.filter(Article.mp_id == mp_id)
        if search:
            # 按空格拆分搜索关键词，并为每个关键词创建 ilike 条件
            search_terms = search.split()
            or_conditions = [
                Article.title.ilike(f"%{term}%") for term in search_terms
            ]
            query = query.filter(or_(*or_conditions))

        # 获取总数
        total = query.count()
        
        # 分页查询（按发布时间降序）
        from sqlalchemy import desc
        articles = query.order_by(desc(Article.publish_time))\
                       .offset(offset)\
                       .limit(limit)\
                       .all()
        # 打印生成的 SQL 语句
        print(query.statement.compile(compile_kwargs={"literal_binds": True}))
        
        # 查询公众号名称
        from core.models.feed import Feed
        mp_names = {}
        for article in articles:
            if article.mp_id and article.mp_id not in mp_names:
                feed = session.query(Feed).filter(Feed.id == article.mp_id).first()
                mp_names[article.mp_id] = feed.mp_name if feed else "未知公众号"
        
        # 合并公众号名称到文章列表
        article_list = []
        for article in articles:
            article_dict = article.__dict__
            article_dict["mp_name"] = mp_names.get(article.mp_id, "未知公众号")
            article_list.append(article_dict)
        
        from .base import success_response
        return success_response({
            "list": article_list,
            "total": total
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取文章列表失败: {str(e)}"
            )
        )

@router.get("/{article_id}", summary="获取文章详情")
async def get_article_detail(
    article_id: str,
    content: bool = False,
    # current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        article = session.query(Article).filter(Article.id==article_id).filter(Article.status != DATA_STATUS.DELETED).first()
        if not article:
            from .base import error_response
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        return success_response(article)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取文章详情失败: {str(e)}"
            )
        )   

@router.delete("/{article_id}", summary="删除文章")
async def delete_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.article import Article
        
        # 检查文章是否存在
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        # 逻辑删除文章（更新状态为deleted）
        article.status = DATA_STATUS.DELETED
        if cfg.get("article.true_delete", False):
            session.delete(article)
        session.commit()
        
        return success_response(None, message="文章已标记为删除")
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"删除文章失败: {str(e)}"
            )
        )