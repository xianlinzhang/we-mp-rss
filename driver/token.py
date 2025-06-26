from core.config import Config,cfg
wx_cfg = Config("./data/wx.lic")
def set_token(data:any):
    """
    设置微信登录的Token和Cookie信息
    :param data: 包含Token和Cookie信息的字典
    """
    cfg.set("token", data.get("token", ""))
    wx_cfg.set("token", data.get("token", ""))
    wx_cfg.set("cookie", data.get("cookies_str", ""))
    cfg.set("expiry", data.get("expiry", {}))
    wx_cfg.save_config()
    cfg.save_config()
def get(key:str,default:any=None):
    wx_cfg.get(f"{key}",default)