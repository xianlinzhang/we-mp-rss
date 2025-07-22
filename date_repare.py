from datetime import datetime, timedelta

# 修复跨月的数据日期
def main(current_date_str: str, other_date_str: str) -> dict:

    try:
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
        other_date = datetime.strptime(other_date_str, "%Y-%m-%d")

        delta = (current_date - other_date).days  # 正负代表前后

        if abs(delta) > 15:
            if delta < 0:  # other_date 太晚，减一个月
                # 找到上个月同一天（处理跨年）
                prev_month = (other_date.replace(day=1) - timedelta(days=1)).replace(day=other_date.day)
                other_date = prev_month


        deal_other_date =other_date.strftime("%Y-%m-%d")
    except ValueError:
        deal_other_date = other_date_str


    return {"out": deal_other_date}

if __name__ == '__main__':

    print(main('2025-07-03', '2025-05-30'))

    print(main('2025-07-03', '2025-07-30'))