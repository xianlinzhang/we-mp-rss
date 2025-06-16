from driver.wxarticle import Web
# 示例用法
try:
    article_data = Web.get_article_content("https://mp.weixin.qq.com/s/qfe2F6Dcw-uPXW_XW7UAIg")
    print(article_data)
    Web.close()
except Exception as e:
    print(f"错误: {e}")  