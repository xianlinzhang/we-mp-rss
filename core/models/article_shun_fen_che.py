from .base import Base, Column, String, Integer, DateTime, Text, MEDIUMTEXT

# 顺风车数据表
class ArticleShunFenChe(Base):
    __tablename__ = 'articles_shun_fen_che'
    # 定义 id 字段，作为主键，同时创建索引
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    car_type = Column(String(255))
    departure = Column(String(500))
    destination = Column(String(500))
    time_str = Column(String(500))
    original_content = Column(Text)
    hours_str = Column(String(255))
    phone = Column(String(255))
    num_people = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
