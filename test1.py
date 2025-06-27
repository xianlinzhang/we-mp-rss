import json
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser

# 自定义HTML解析器类
class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_row = {}
        self.rows = []
        self.in_td = False
        self.in_section = False
        self.in_span = False
        self.current_cell = ""

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.current_row = {}
        elif tag == "td":
            self.in_td = True
            self.current_cell = ""
        elif tag == "section" and self.in_td:
            self.in_section = True
        elif tag == "span" and self.in_td:
            self.in_span = True

    def handle_endtag(self, tag):
        if tag == "tr":
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag == "td":
            # 第一个td是描述内容，第二个是电话号码
            if "description" not in self.current_row:
                self.current_row["description"] = self.current_cell.strip()
            else:
                self.current_row["phone"] = self.current_cell.strip()
            self.in_td = False
            self.in_section = False
            self.in_span = False

    def handle_data(self, data):
        # 仅收集直接在span或section标签内的文本
        if self.in_span or self.in_section:
            self.current_cell += data

# 自定义HTML解析器类
class SectionMultiParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_section = False
        self.current_text = ""
        self.rows = []
        self.current_row = {}

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            self.in_section = True
            self.current_row = {}
            self.current_text = ""

    def handle_endtag(self, tag):
        if tag == "section" and self.in_section:
            self.in_section = False
            self._flush_current_text()  # 处理 section 结束时剩余内容

    def handle_data(self, data):
        if self.in_section:
            self.current_text += data

    def handle_startendtag(self, tag, attrs):
        if self.in_section and tag == "br":
            self._flush_current_text()  # 遇到 <br> 时视为换行/新数据行

    def _flush_current_text(self):
        cleaned_text = re.sub(r'\s+', ' ', self.current_text).strip()
        if cleaned_text:
            self.current_row = {"description": cleaned_text}
            self.rows.append(self.current_row)
            self.current_text = ""  # 清空当前缓存

def convert_to_24_hour(hour, period):
    """将时间段转换为24小时制"""
    hour = int(hour)
    if period in ["下午", "晚上"] and hour < 12:
        return hour + 12
    elif period == "上午" and hour == 12:
        return 0
    elif period == "中午":
        return 12
    elif period in ["凌晨", "早上"] and hour < 12:
        return hour
    elif hour == 12 and period in ["下午", "晚上"]:
        return 12
    return hour

def parse_time_string(text, base_date=None):
    """
    解析自然语言中的时间信息，返回 datetime 对象
    支持格式：
      - 【提供车：广昌→广州】6月8号下午5点30左右出发
      - 【提供车：广昌→广州】明天下午3点30分出发
      - 【提供车：广昌→广州】今天上午10点
    """
    if base_date is None:
        base_date = datetime.today()
    else:
        # 将类似 "2025-06" 的字符串转换为 datetime 对象
        base_date = datetime.strptime(base_date, "%Y-%m-%d")

    # 年
    year = base_date.year

    # 日期月份
    month_absolute_match = re.search(r'(\d{1,2})月', text)

    if month_absolute_match:
        month = month_absolute_match.group(1)
    else:
        month  = base_date.month

    # 日期天
    date_absolute_match = re.search(r'(\d{1,2})[号日]', text)
    if date_absolute_match:
        day = date_absolute_match.group(1)
    else:
        return None

    try:
        target_date = datetime(year=int(year), month=int(month), day=int(day))
    except ValueError:
        return None


    # 返回最终时间对象
    return target_date

def parse_hours_string(text):

    # 时间小时
    time_hours_match = re.search(r'(\d{1,2})点', text)
    if time_hours_match:
        hour = time_hours_match.group(1)
    else:
        hour = None

    # 时间段
    period_match = re.search(r'(早上|上午|中午|下午|晚上|凌晨)', text)
    period = period_match.group(1) if period_match else ''

    # 时间分钟
    time_minute_match = re.search(r'(\d{1,2})分', text)
    if time_minute_match:
        minute = time_minute_match.group(1)
    else:
        minute = '00'

    if hour:
        return f"{period}{hour}:{minute}"
    else:
        return f"{period}"

def clean_non_chinese(s):
    return re.sub(r'^[^\u4e00-\u9fa5]+|[^\u4e00-\u9fa5]+$', '', s)

def extract_route_info(description):
    """
    提取出发地和目的地
    示例：【提供车：东莞→广昌】 → {'car_type': '提供车', 'departure': '东莞', 'destination': '广昌'}
    """
    route_match = re.search(r'【(.*?)：(.*?)→(.*?)】', description)
    if route_match:
        car_type = route_match.group(1)
        departure = route_match.group(2)
        destination = route_match.group(3)
    else:
        # 提取类型（提供车/求车）
        car_type = "提供车" if "提供车" in description else "求车"
        # 提取出发地和目的地
        departure, destination = None, None
        arrow_match = re.search(r'【.*?：(.+?)(?:→|到)(.+?)】', description)
        if arrow_match:
            departure = arrow_match.group(1)
            destination = arrow_match.group(2)

    if departure:
        departure = clean_non_chinese(departure)

    if destination:
        destination = clean_non_chinese(destination)

    return {
        "类型": car_type,
        "出发地": departure,
        "目的地": destination
    }

def extract_people_count(description):
    """提取人数信息"""
    num_match = re.search(r'(\d+|[一二三四五六七八九十]+)\s*个?[坐|座|人|位]', description)
    chinese_num_map = {
        '一': '1',
        '二': '2',
        '三': '3',
        '四': '4',
        '五': '5',
        '六': '6',
        '七': '7',
        '八': '8',
        '九': '9',
        '十': '10'
    }

    if num_match:
        raw_num = num_match.group(1)
        # 转换为阿拉伯数字
        if raw_num in chinese_num_map:
            num_people = chinese_num_map[raw_num]
        else:
            num_people = raw_num
        return num_people
    return None


def clean_and_extract_phone(text):
    # 去除所有空白字符（包括空格、换行、制表符等）
    cleaned_text = re.sub(r'\s+', '', text)

    # 提取11位手机号
    match = re.search(r'1[3-9]\d{9}', cleaned_text)

    return match.group() if match else ""

def main(html, year_month):

    # 格式1
    parser = TableParser()
    parser.feed(html)

    if not parser.rows:
        # 格式2
        parser = SectionMultiParser()
        parser.feed(html)

    results = []

    for row in parser.rows:

        # 确保行数据包含必要字段
        if "description" not in row:
            continue

        original_content = re.sub(r'\s+', ' ', row["description"]).strip().replace(' ', '')

        # 根据内容解析手机号
        if "phone" not in row:
            phone = clean_and_extract_phone(original_content)
        else:
            phone = clean_and_extract_phone(row["phone"])

        # 没有手机号，跳过本行
        if not phone:
            continue

        # 提取路线信息
        route_info = extract_route_info(original_content)

        # 提取时间
        time = parse_time_string(original_content, year_month)
        time_str = time.strftime("%Y-%m-%d") if time else None

        # 提取时间
        hours_str = parse_hours_string(original_content)

        # 提取人数
        num_people = extract_people_count(original_content)

        # 构建结果字典
        data_dict = data_dict = {
            "car_type": route_info.get("类型"),
            "departure": route_info.get("出发地"),
            "destination": route_info.get("目的地"),
            "time_str": time_str,
            "hours_str": hours_str,
            "num_people": num_people,
            "phone": phone,
            "original_content": original_content
        }

        results.append(data_dict)

    return {"result": results}







def test_section_multi():
    with open('test_section_multi.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
    year_month = "2025-06"

    # 执行数据提取
    extracted_data = main(html_content, year_month)

    # print(extracted_data)
    # 输出JSON结果
    print(json.dumps(extracted_data, ensure_ascii=False, indent=2))


def test_table():
    with open('test_table.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
    year_month = "2025-06"
    # 执行数据提取
    extracted_data = main(html_content, year_month)

    # print(extracted_data)
    # 输出JSON结果
    print(json.dumps(extracted_data, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    # test_section_multi()
    test_table()
    # print(clean_and_extract_phone('【提供车：广昌→抚州】6月28号上午6点 - -出发抚州，新七座商务车，电话微信同号☎️133 6794 9982谢师傅，！'))