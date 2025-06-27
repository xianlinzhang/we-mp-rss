import datetime

from core.dify_client.models import WorkflowStatus
from core.models.article import Article
from core.db import DB
from core.wx.base import WxGather
from time import sleep
from core.print import print_success,print_error
import random
from sqlalchemy import and_, or_

from core.config import cfg
from core.print import print_success,print_warning


from core.dify_client import Client, models

def deal_free_ride_article(content, date):

    # Initialize the client with your API key
    api_key = cfg.get("gather.deal_free_ride_articles_api_key","app-g5CstYWzhD0j65TvO3aue7oi")

    api_base = cfg.get("gather.deal_free_ride_articles_api_base","http://local1.dify.ai/v1")

    client = Client(
        api_key=api_key,
        api_base=api_base,
    )
    user = "dify-client-python"

    print(api_key, api_base)

    # Create a blocking chat request
    blocking_chat_req = models.WorkflowsRunRequest(
        query="",
        inputs={
            "html": content,
            "today": date,
        },
        user=user,
        response_mode=models.ResponseMode.BLOCKING,
    )


    # Send the chat message
    chat_response = client.run_workflows(blocking_chat_req, timeout=6000)
    print(chat_response)

    return chat_response.data.status



def fetch_need_deal_free_ride_articles():
    """
    查询content为空的文章，调用微信内容提取方法获取内容并更新数据库
    """
    session = DB.get_session()
    ga=WxGather().Model()
    try:

        or_conditions = [
            Article.title.ilike(f"%{term}%") for term in ['求车', '提供车']
        ]

        # 查询content为空的文章
        articles = (session.query(Article)
                    # .filter(Article.id == "2247515628_3")
                    .filter(Article.free_ride_status == 0)
                    .filter(or_(*or_conditions))
                    .all())
        
        if not articles:
            print("没有找到need_deal_free_ride的文章")
            return
        
        for article in articles:

            content = article.content
            push_date = datetime.datetime.fromtimestamp(article.publish_time).strftime("%Y-%m-%d")
            deal_status = deal_free_ride_article(content, push_date)

            if deal_status == WorkflowStatus.SUCCEEDED:
                # 更新内容
                article.free_ride_status = 1
                session.commit()
                print_success(f"成功更新文章 {article.title} 的内容")
            else:
                print_error(f"获取文章 {article.title} 内容失败")
                
    except Exception as e:
        print(f"处理过程中发生错误: {e}")


# from core.task import TaskScheduler
# scheduler=TaskScheduler()
# def start_deal_free_ride_articles():
#     if not cfg.get("gather.deal_free_ride_articles",False):
#         print_warning("自动处理顺风车数据功能未启用")
#         return
#     interval=int(cfg.get("gather.deal_free_ride_articles_auto_interval",120)) # 每隔多少分钟
#     cron_exp=f"*/{interval} * * * *"
#     job_id=scheduler.add_cron_job(fetch_need_deal_free_ride_articles,cron_expr=cron_exp)
#     print_success(f"已添自动处理顺风车数据任务: {job_id}")
#     scheduler.start()
if __name__ == "__main__":
    # fetch_need_deal_free_ride_articles()
    fetch_need_deal_free_ride_articles()