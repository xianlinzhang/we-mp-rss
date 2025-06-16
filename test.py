import asyncio
from driver.wx import WX_API
from driver.success import Success
from threading import Thread
def task():
    code_url=WX_API.GetCode(Success)
    print(f"code url:{code_url}")
    WX_API.QRcode()
    WX_API.Close()

if __name__ == "__main__":
    task()