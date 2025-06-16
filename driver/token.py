from core.config import Config,cfg
wx_cfg = Config("./data/wx.data")
def set_token(data:any):
    """
    设置微信登录的Token和Cookie信息
    :param data: 包含Token和Cookie信息的字典
    """
    cfg.set("token", data.get("token", ""))
    wx_cfg.set("cookies", data.get("cookies_str", ""))
    cfg.set("cookie_expiry", data.get("cookie_expiry", {}))
    wx_cfg.save_config()
def get(key:str,default:any=None):
    wx_cfg.get(f"{key}",default)