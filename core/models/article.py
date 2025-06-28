from  .base import Base,Column,String,Integer,DateTime,Text,MEDIUMTEXT
class Article(Base):
    __tablename__ = 'articles'
    id = Column(String(255), primary_key=True)
    mp_id = Column(String(255))
    title = Column(String(500))
    pic_url = Column(String(500))
    url=Column(String(500))
    content = Column(Text)
    description=Column(String(800))
    status = Column(Integer,default=1)
    publish_time = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)  
    is_export = Column(Integer)
    free_ride_status = Column(Integer, default=0)
    content_auto_fetch = Column(Integer, default=0)


