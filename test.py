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


def main(html, year_month):
    # 创建解析器并解析HTML
    parser = TableParser()
    parser.feed(html)

    results = []

    for row in parser.rows:
        # 确保行数据包含必要字段
        if "description" not in row or "phone" not in row:
            continue

        original_content = re.sub(r'\s+', ' ', row["description"]).strip()
        phone = row["phone"]

        # 提取类型（提供车/求车）
        car_type = "提供车" if "提供车" in original_content else "求车"

        # 提取出发地和目的地
        departure, destination = None, None
        arrow_match = re.search(r'【.*?：(.+?)→(.+?)】', original_content)
        if arrow_match:
            departure = arrow_match.group(1)
            destination = arrow_match.group(2)

        # 提取时间（日期）
        time = None
        # 匹配完整日期时间：例如 "6月8号早上9点"
        full_match = re.search(r'(\d{1,2})月(\d{1,2})[号日].*?(\d{1,2})点', original_content)
        if full_match:
            month = full_match.group(1).zfill(2)
            day = full_match.group(2).zfill(2)
            hour = full_match.group(3).zfill(2)
            full_date_str = f"{year_month}-{day} {hour}:00:00"
            try:
                dt = datetime.strptime(full_date_str, "%Y-%m-%d %H:%M:%S")
                time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                time = None
        else:
            # 只匹配日+小时：例如 "8号下午5点"
            day_hour_match = re.search(r'(\d{1,2})[号日].*?(\d{1,2})点', original_content)
            if day_hour_match:
                day = day_hour_match.group(1).zfill(2)
                hour = day_hour_match.group(2).zfill(2)
                full_date_str = f"{year_month}-{day} {hour}:00:00"
                try:
                    dt = datetime.strptime(full_date_str, "%Y-%m-%d %H:%M:%S")
                    time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    time = None
            else:
                # 处理“今天”、“明天”
                relative_match = re.search(r'(今|明)天.*?(\d{1,2})点', original_content)
                if relative_match:
                    today = datetime.today()
                    offset = 0 if relative_match.group(1) == '今' else 1
                    target_day = (today + timedelta(days=offset)).day
                    hour = relative_match.group(2).zfill(2)
                    full_date_str = f"{year_month}-{target_day:02d} {hour}:00:00"
                    try:
                        dt = datetime.strptime(full_date_str, "%Y-%m-%d %H:%M:%S")
                        time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        time = None

        # 提取人数
        num_people = None
        num_match = re.search(r'(\d+)\s*个?坐?位', original_content)
        if num_match:
            num_people = f"{num_match.group(1)}"

        # 构建字典结构
        data_dict = {
            "类型": car_type,
            "出发地": departure,
            "目的地": destination,
            "时间": time,
            "人数": num_people,
            "联系电话": phone,
            "原字段内容": original_content
        }
        results.append(data_dict)

    return {
        "result": results
    }


if __name__ == '__main__':
    html_content = '''
    <div class="rich_media_content js_underline_content autoTypeSetting24psection" id="js_content">
 <table style="width:573px;">
  <tbody>
   <tr style="height:81.00pt;">
    <td data-colwidth="573" width="573">
     <p>
      <span style="font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span leaf="">
        <span style="color: rgb(61, 167, 66);" textstyle="">
         【温馨提示】
        </span>
       </span>
      </span>
      <span leaf="">
       <br/>
      </span>
     </p>
     <section>
      <span leaf="">
       <span style="color: rgb(61, 167, 66);" textstyle="">
        1、请拼车的用户千万不要预付押金，如果有车主需要押金请交于广昌帮，广昌帮代为收取。
       </span>
      </span>
      <span leaf="">
       <br/>
      </span>
      <span leaf="">
       <span style="color: rgb(61, 167, 66);" textstyle="">
        2、上车前可以拍下车主车牌、车型发给亲朋好友，减少风险、安全出行。祝好友出行安全、愉快！
       </span>
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <p style="white-space: normal;text-align: center;text-indent: 0em;margin-bottom: 24px;line-height: normal;">
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;text-align: justify;">
   <span leaf="">
    <span style="font-size: 36px;color: rgb(255, 0, 0);" textstyle="">
     会员区发布
    </span>
   </span>
  </span>
 </p>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       【提供车，南昌——广昌】6月6号下午5点30左右南昌出发前往广昌，私家顺风车，全程高速，还有3个位置，联系电话，微信15080309585
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       15080309585
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <p>
  <span leaf="">
   <span style="font-size: 50px;" textstyle="">
    普通区
   </span>
   <span style="font-size: 50px;color: rgb(0, 0, 0);" textstyle="">
    免费
   </span>
  </span>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span data-pm-slice='1 1 ["para",{"tagName":"p","attributes":{"style":"white-space: normal;text-align: center;text-indent: 0em;margin-bottom: 24px;line-height: 1em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
        <br/>
       </span>
      </span>
     </span>
    </span>
   </span>
  </span>
 </p>
 <p>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span data-pm-slice='1 1 ["para",{"tagName":"p","attributes":{"style":"white-space: normal;text-align: center;text-indent: 0em;margin-bottom: 24px;line-height: 1em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
        <span style="font-size: 24px;color: rgb(0, 0, 0);font-weight: bold;" textstyle="">
         【2025年6月9日】
        </span>
       </span>
      </span>
     </span>
    </span>
   </span>
  </span>
 </p>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       【提供车：东莞→广昌】6月10号，出发私家车途径惠州，河源，有需要的朋友可以联系，电话18296469705
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       18296469705
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：东莞→广昌】私家车，10号早上出发。有需要的朋友请联系，☎️15798001516
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       15798001516
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】今天上午随时出发回东莞，还有四个位，石碣镇周边有需要请联系，微信同号，电话 18825772684
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       18825772684
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】途径河源、惠州、6月10号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15179496333微信同号，老刘
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       15179496333
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州、佛山、中山、珠海】6月10号早上8点出发，途经广州包接包送传祺大商务有需要的联系18279454568微信同号
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       18279454568
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】10号早上广昌出发广州全程高速，私家新车 Suv还有位置联系电话：15397889018微信同号
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       15397889018
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6月10号明天上午去广州，私家车，有去广州的可以联系，电话 ：15070492356
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       15070492356
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州太和】6月10号出发去广州，早上出发，有几个车位，有需要坐车的老板可以的联系13104890558
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13104890558
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州太和】6月10号早上9点出发，私家车，新车，车上一个人，宽松，捎点油钱，联系电话：13172090909
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13172090909
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州太和大源】
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
      <span leaf="">
       明天6月10号早上8：30左右出发，有3个位置，联系电话：18379659802
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       18379659802
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→揭阳】11号早上出发，电话13695109724
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13695109724
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→昆山，上海】6月10号早上6-7点出发。可以带3人，电话13328058118。
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13328058118
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→普宁】6月10号上午八点多出发，可以坐2人，出去的老乡联系18000780786
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       18000780786
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→普宁】今天，有空位，有雲要提前联系电18907942558
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       18907942558
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳】6月10号早上8点出发，广昌去深圳，途径河源，惠州，全新SUV私家车，全程高速，方便快捷，联系电话:13538133140微信同号
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13538133140
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳】6月10号早上出发，广昌去深圳，途经，惠州，全新SUV私家车，全程高速，有需要的朋友可以联系，电话☎️:13530121561微信同号
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13530121561
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳】6月11日早上7：30—8：00点钟发车，现在还有两个坐位，如有一起回深圳的，请联系电话，18823768976，微信同号。
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       18823768976
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳宝安】6月10号早上出发，广昌回深圳宝安途经：河源、惠州，全程高速，有需要的朋友可以联系，电话:13237501686微信同号
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13237501686
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→州太和】6月10号早上8点左右，还有位置，私人轿车，有需要的联系：13828065657
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13828065657
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月10号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系电话☎13926014559
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13926014559
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳、惠州、河源→广昌】6月10号早上出‬发回广昌，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       13197887480
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳横岗→广昌】6月10日明天早上出发，私家车有三个坐位，联系电话18397843008
      </span>
     </section>
    </td>
    <td>
     <section>
      <span leaf="">
       18397843008
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       【提供车：东莞→广昌】6月10号，出发私家车途径惠州，河源，有需要的朋友可以联系，电话18296469705
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       18296469705
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：甘竹，广昌→广州太和】6月10号早上8-9点，有4个位置，有需要的联系：13828065657，微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13828065657
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月10日上午9点10分出发。3个位。联系人刘女士电话15374340400
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15374340400
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月9号出发.联系电话.18322981684
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18322981684
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】明天10号早上出发广昌回东莞还有位置，全新豪华SUV商务车，途径河源，惠州有需要的朋友可以联系，电话15979585770小张
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15979585770
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞高埗】明天下上午10号奔驰SUV，还可以坐3人18929281002陈先生
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18929281002
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→佛山】6月10号11号出发还有位，电话13601643805
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13601643805
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州、佛山、中山、珠海】6月10号早上8点出发，途经广州包接包送传祺大商务有需要的联系18279454568微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18279454568
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】10号早上9点出发广昌出发广州全程高速，私家小汽车还有位置联系电话：13647946511微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13647946511
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】10号早上广昌出发广州全程高速，私家新车 Suv还有位置联系电话：15397889018微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15397889018
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6月10号明天上午去广州，私家车，有去广州的可以联系，电话 ：15070492356
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15070492356
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州市白云区太和镇】6月10号早上9点左右出发，还有三个位置SUV新车，联系电话13104890558
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13104890558
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州太和大源】6月10号，上午出发广州还有3个位置，私家车
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
      <span leaf="">
       有需要的老乡请联系电话☎15920936271
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15920936271
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
      <span leaf="">
       <br/>
      </span>
     </span>
     <section>
      <span leaf="">
       【提供车：广昌→揭阳】6月9号晚上出发，联系13907049855
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13907049855
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→昆山】6月10号出发，可以坐1个人13372151687
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13372151687
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→普宁】10号下午，5点左右出发，有需要的联系13250668709
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13250668709
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳】6月10号早上8点出发，广昌去深圳，途径河源，惠州，全新SUV私家车，全程高速，方便快捷，联系电话:13538133140微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13538133140
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳】6月10号早上出发，广昌去深圳，途经，惠州，全新SUV私家车，全程高速，有需要的朋友可以联系，电话☎️:13530121561微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13530121561
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳宝安】6月10号早上出发，广昌回深圳宝安途经：河源、惠州，全程高速，有需要的朋友可以联系，电话:13237501686微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13237501686
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→苏州】10一早出发，还有3个位置，电话18662189850
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18662189850
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→苏州】6月10或11号早上出发广昌县城一苏州浒关，吴江附近都可以，能带3一4个人电话13979477781陈
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13979477781
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月10号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系电话☎13926014559
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13926014559
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳、惠州、河源→广昌】6月10号早上出‬发回广昌，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13197887480
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳→广昌】6月9号下午1点左右出发，有3个座位，联系电话：18802670588
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18802670588
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：中山，佛山， 广州→广昌】6月10日9点左右出发高速直达，有需要的朋友可以联系我。电话13690502272.小强。
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13690502272
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
        <br/>
       </span>
      </span>
     </span>
    </span>
   </span>
  </span>
 </section>
 <p>
  <span leaf="">
   <br/>
  </span>
 </p>
 <p>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
        <span style="font-size: 24px;color: rgb(0, 0, 0);font-weight: bold;" textstyle="">
         【2025年6月8日】
        </span>
       </span>
      </span>
     </span>
    </span>
   </span>
  </span>
 </p>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span data-pm-slice="0 0 []" style='color: rgb(26, 27, 28);font-family: mp-quote, -apple-system-font, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;font-size: 14px;font-style: normal;font-variant-ligatures: normal;font-variant-caps: normal;font-weight: 400;letter-spacing: normal;orphans: 2;text-align: start;text-indent: 0px;text-transform: none;widows: 2;word-spacing: 0px;-webkit-text-stroke-width: 0px;white-space: pre-line;background-color: rgb(246, 247, 248);text-decoration-thickness: initial;text-decoration-style: initial;text-decoration-color: initial;display: inline !important;float: none;'>
       <span leaf="">
        【提供车：抚州→广昌】6月9日早上6点出发，有2个位置，电话:19136894646（微信同号）
       </span>
      </span>
     </section>
     <section>
      <span leaf="">
       【提供车：东莞→广昌】6月9号早上8点左右出发，深圳回广昌，途经惠州，河源，全新SUV私家车，方便快捷，全程高速，联系电话：13590386498微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       19136894646
      </span>
     </section>
     <section>
      <span leaf="">
       <br/>
      </span>
     </section>
     <section>
      <span leaf="">
       13590386498
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月 9号上午随时出发回东莞，还有四个位，石碣镇周边有需要请联系，微信同号，电话 18825772684
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18825772684
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月9号，途经，惠州，河源，私家车，全程高速，有需要的朋友可以联系，电话:18296469705
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18296469705
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】明天9号早上出发广昌回东莞还有位置，全新豪华SUV商务车，途径河源，惠州有需要的朋友可以联系，电话15979585770小张
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15979585770
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州、佛山、中山、珠海】6月9号早上8点出发，途经广州包接包送传祺大商务有需要的联系18279454568微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18279454568
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】（6月9号〉明天早上10点出发广州还有位私家车高速直达，有需要的朋友请联系电话:☎️ 18902892389
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18902892389
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】（6月9号〉明天早上8点出发广州还有位私家车高速直达，有需要的朋友请联系电话:☎️ 18870444698
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18870444698
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→昆山，上海】6月10号早上6-7点出发。可以带3人，电话13328058118。
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13328058118
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→昆山】6月10号出发，可以坐4个人13372151687
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13372151687
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→普宁】6月10号上午出发，可以坐3人，联系18000780786
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18000780786
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→普宁】明天6月9号：8点左右出发，有4个位置有需要的老乡请18296498975
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18296498975
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→泉州晋江】 6月9号上午出发，私家车，还有4个位置，联系电话18379477388，
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18379477388
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳龙岗，东莞凤岗】9/10号，可以坐四人，有回深圳龙岗和东莞凤岗的老乡可以联系电话15167029066/微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15167029066
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→苏州新浒花园】11号或者12号出发，有3个位置有回苏州的老乡请联系我，电话13771621728
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13771621728
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州→广昌】9号早上广州出发广昌全程高速，私家新车大型suv.还有位置联系电话：15397889018微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15397889018
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月9号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系电话☎13926014559
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13926014559
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州林安物流园→广昌】6月9号，星期一，明天上午9点左右出发，私家车全新SUV还有三个位置，联系电话☎:微信同号13148990271
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13148990271
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州太和大源→广昌】（6月9号）明天上午广州出发，顺风车还有位置，有回去的老板请电15070492356
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15070492356
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：南昌→广昌】广汽传祺（正规商务7坐出租车）商务车空间大，乘坐舒适）8号上午或者下午随时南昌回广昌全程高速，途径各大医院，机场
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
      <span leaf="">
       ，西站，火车站，东站，八一广场，乘车安全有保障，电话：13767600996余师傅
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13767600996
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳→广昌】6月9号早上8点左右出发，深圳回广昌，途经惠州，河源，全新SUV私家车，方便快捷，全程高速，联系电话：13538133140微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13538133140
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       【提供车，广州——回广昌】6月9号明天早上8点左右有回广昌的朋友可以联系我13426520055
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       13426520055
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：抚州→广昌】6月9日早上6点出发，有4个位置，电话:19136894646（微信同号）
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       19136894646
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       提供车：东莞→广昌】8号上午出发，私家车高速直达，还有4个位置，车内干净整洁，有需要请联系 13790281148
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13790281148
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：东莞→广昌】9号早上出发全程高速，私家车 还有位置联系电话：18179456295
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18179456295
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：抚州→广昌】(6月8号下午12点→4点左右）随时:抚州出发→广昌:联系:☎️电话:微信同号:15879827878
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15879827878
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→，抚州，南昌、南昌机场】 明天（上4—8点）广昌出发南昌各大医院，机场，八一广场附近:火车站，学校:各大地铁口。17187971888羊面岭胡师
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       17187971888
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月9号，途经，惠州，河源，私家车，全程高速，有需要的朋友可以联系，电话:18296469705
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18296469705
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】明天9号早上出发广昌回东莞还有位置，全新豪华SUV商务车，途径河源，惠州有需要的朋友可以联系，电话15979585770小张
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15979585770
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→抚州】（6月9号早上6→9点左右）随时广昌出发→抚州☎️电话:微信同号15879827878
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15879827878
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→抚州】6月8号下午出发
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
      <span leaf="">
       ,SUV私家车还有位置，有需要的请联系我.18823459358
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18823459358
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→抚州】6月9号早上6点至9点左右（高速直达） 出发抚州，有需要请联系☎️17779466767微信 同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       17779466767
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州花都区狮岭镇】6月8号下午出发，还有2个位置。电话13332815686李
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13332815686
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州花都区狮岭镇】6月8号下午出发，还有2个位置。电话13332815686李
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13332815686
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→揭阳】6月9号晚上出发，联系13907049855
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13907049855
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌，昌北机场，西站】全新商务车出租车，明天（凌晨4~5点）广昌一南昌各地铁口 包接送，承接小件快运，全程高速！联系电话19179417755李师傅微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       19179417755
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌、抚州】6月9号早上7——9点出发，传祺大商务，途经各大医院、学校、西站、机场、地铁站有需要的联系18279454568微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18279454568
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】(明天)早上凌晨4点至早上8点左右出发南昌，昌北机场，南昌西站、火车站、象湖一附，各大医院，各大学校，八一广场附近，可带小件货。联系电话13767600996余师傅，微信同号。
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13767600996
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】（正规合法营运车）明天凌晨4点--8点左右出发去南昌，经过昌北机场，南昌西站，火车站，各大医院，各大学校，欢迎来电！☎️
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
      <span leaf="">
       13263089688微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13263089688
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】6月9号早上4-5点左右，广昌出发昌北机场，八一广场附近，各大医院大商务车，有需要的可以提前联系：18879473134
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18879473134
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】9号回南昌，电话微信18680055063
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18680055063
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】正规七座出租车（6月9号）早上4点,出发南昌各个医院包接包送。1234线地铁口，八一广场，机场、西站等！全程高速。联系电话☎️18179424628微信同号！
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18179424628
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌机场】明天早上4一5点左右出发去南昌，经过昌北机场，南昌站，一附、二附医院、省妇幼保健院、省中医院，第三医院、省儿童医院.眼科，医口腔医院等医院，八一大道1234地铁口，各大学院校。联系电话：15179421828符师傅微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15179421828
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳、惠州、河源】6月 9号早上出‬发回深圳，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13197887480
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌一东莞］6月9日下午1点30分出发。3个位，可帮忙开车人最佳。联系人刘女士电话15374340400 【提供车：广昌→南昌】8号下午6点在在出发，有3个座位私家车，电话15807041984
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15807041984
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州→广昌】9号早上广州出发广昌全程高速，私家新车大型suv.还有位置联系电话：15397889018微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15397889018
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月9号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系电话☎13926014559
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13926014559
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州林安物流园→广昌】6月9号，星期一，上午9点左右出发，私家车全新SUV还有三个位置，联系电话☎:微信同号13148990271
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13148990271
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州太和大源→广昌】（6月9号）明天上午广州出发，顺风车还有位置，有回去的老板请电15070492356
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15070492356
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：南昌→广昌】6月8号，南昌回广昌还有位置，豪华商务车，全程高速，有需要的可以联系13758453431微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13758453431
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：南昌→广昌】广汽传祺（正规商务7坐出租车）商务车空间大，乘坐舒适）8号上午或者下午随时南昌回广昌全程高速，途径各大医院，机场
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
      <span leaf="">
       ，西站，火车站，东站，八一广场，乘车安全有保障，电话：13767600996余师傅
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13767600996
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：上海→广昌】6月8号晚上八点出发，有2个座位，联系电话：18719847918
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18719847918
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳→广昌】6月9号早上8点左右出发，深圳回广昌，途经惠州，河源，全新SUV私家车，方便快捷，全程高速，联系电话：13538133140微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13538133140
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <p>
  <span leaf="">
   <br/>
  </span>
 </p>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
        <span style="font-size: 24px;color: rgb(0, 0, 0);font-weight: bold;" textstyle="">
         【2025年6月6日】
        </span>
       </span>
       <table style="border-collapse:collapse;width:399.77pt;">
        <tbody>
         <tr style="height:18.00pt;">
          <td data-colwidth="389" style="height: 18pt;" width="389">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              【提供车：东莞→广昌】途径河源、惠州、8号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15979599856
             </span>
            </span>
           </section>
          </td>
          <td data-colwidth="144" width="144">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              15979599856
             </span>
            </span>
           </section>
          </td>
         </tr>
         <tr style="height:18.00pt;">
          <td data-colwidth="389" style="height:18.00pt;">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              【提供车：广昌→广州】6月8号上午广昌出发广州，私家车大空间，高速直达，有需要的朋友请联系电话:15720901443
             </span>
            </span>
           </section>
          </td>
          <td data-colwidth="144">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              15720901443
             </span>
            </span>
           </section>
          </td>
         </tr>
         <tr style="height:18.00pt;">
          <td data-colwidth="389" style="height:18.00pt;">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              【提供车：广昌→广州】6月8号早上广昌出发广州全程高速，私家新车 Suv还有位置联系电话：15397889018微信同号
             </span>
            </span>
           </section>
          </td>
          <td data-colwidth="144">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              15397889018
             </span>
            </span>
           </section>
          </td>
         </tr>
         <tr style="height:18.00pt;">
          <td data-colwidth="389" style="height:18.00pt;">
           <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              【提供车：广昌→广州太和大源】6月8号早上广昌出发广州全程高速还有位置联系电话☎13926014559
             </span>
            </span>
           </span>
          </td>
          <td data-colwidth="144">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              13926014559
             </span>
            </span>
           </section>
          </td>
         </tr>
         <tr style="height:18.00pt;">
          <td data-colwidth="389" style="height:18.00pt;">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              【提供车：广昌→深圳宝安】6 月 8 号早上出发，广昌回深圳宝安区，个人私家车，有需要的朋友可以联系，电话:17722515437 微信同号
             </span>
            </span>
           </section>
          </td>
          <td data-colwidth="144">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              17722515437
             </span>
            </span>
           </section>
          </td>
         </tr>
         <tr style="height:18.00pt;">
          <td data-colwidth="389" style="height:18.00pt;">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              【提供车：广州→广昌】（6月8号），早上9点左右出发广昌，私家车大空间，还有位置，有回的老乡请联系18000282659微信同号
             </span>
            </span>
           </section>
          </td>
          <td data-colwidth="144">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              18000282659
             </span>
            </span>
           </section>
          </td>
         </tr>
         <tr style="height:18.00pt;">
          <td data-colwidth="389" style="height:18.00pt;">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              【提供车：广州→广昌】6月8号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系17770491668微信同号
             </span>
            </span>
           </section>
          </td>
          <td data-colwidth="144">
           <section>
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
              17770491668
             </span>
            </span>
           </section>
          </td>
         </tr>
        </tbody>
       </table>
      </span>
     </span>
    </span>
   </span>
  </span>
 </section>
 <table style="border-collapse:collapse;width:533px;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：常州，无锡，苏州，杭州→广昌】6月8号走全新商务车，空间大，还有位置还能带点小货，需要的联系电话微信同号13358187716。
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13358187716
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞→广昌】6月7号，下午5点左右出发私家车途径惠州，河源，有需要的朋友可以联系，电话18296469705
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18296469705
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞→广昌】6月8号早上回广昌，私家车。联系‬电话17796376512
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        17796376512
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→东莞】明天8号早上出发广昌回东莞还有位置，全新豪华SUV商务车，途径河源，惠州有需要的朋友可以联系，电话15979585770小张
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15979585770
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→东莞黄江】6月8号早上出发，联系电话13767606639
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13767606639
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州】6月8号明天上午去广州，私家车，有去广州的可以联系，电话 ：15070492356
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15070492356
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州】6月8号早上广昌出发广州全程高速，私家新车 Suv还有位置联系电话：15397889018微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15397889018
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州太和】8号出发，私家车全程高速还有3个位置，联系电话：13600050540微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13600050540
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州太和大源】6月8号早上广昌出发广州全程高速还有位置联系电话☎13926014559
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13926014559
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广州→广昌】（6月8号〉明天早上9点出发广昌还有位私家车高速直达，有需要的朋友请联系电话:☎️ 18379667813
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18379667813
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广州→广昌】6🈷️8号下午广州回广昌，SUV私家车，有需要的朋友提前联系：13528493167
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13528493167
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广州林安物流园→广昌】6月9号，星期一，上午9点左右出发，私家车全新SUV还有三个位置，联系电话☎:微信同号13148990271
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13148990271
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：惠州→广昌】（6月8号〉明天早上9点出发广昌还有位私家车高速直达，有需要的朋友请联系电话:18816830338
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18816830338
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：上海→广昌】6月7号-6月10号出发，有4个座位，联系电话：18719847918
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18719847918
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳、惠州、河源→广昌】6月8号早上出‬发回广昌，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13197887480
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳宝安→广昌】6月8号早上出发，深圳宝安回广昌，途经，惠州，河源，全程高速，有需要的朋友可以联系，电话:13237501686微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13237501686
       </span>
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车，南昌——广昌】6月6号下午5点30左右南昌出发前往广昌，私家顺风车，全程高速，还有3个位置，联系电话，微信15080309585
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15080309585
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：常州，无锡，苏州，杭州→广昌】6月8号走全新商务车，空间大，还有位置还能带点小货，需要的联系电话微信同号13358187716。
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13358187716
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞→广昌】6月7号，下午5点左右出发私家车途径惠州，河源，有需要的朋友可以联系，电话18296469705
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18296469705
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞→广昌】途径河源、惠州、6月8号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15179496333微信同号，老刘
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15179496333
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞→广昌】途径河源、惠州、8号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15979599856
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15979599856
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→东莞】明天8号早上出发广昌回东莞还有位置，全新豪华SUV商务车，途径河源，惠州有需要的朋友可以联系，电话15979585770小张
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15979585770
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→东莞黄江】6月8号早上出发，联系电话13767606639
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13767606639
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州】6.7号明天上午10.30点到11点左右出发，4个坐位，电话号码18575837899
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18575837899
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州】6月8号明天上午去广州，私家车，有去广州的可以联系，电话 ：15070492356
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15070492356
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州】6月8号早上广昌出发广州全程高速，私家新车 Suv还有位置联系电话：15397889018微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15397889018
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州太和大源】6月8号早上广昌出发广州全程高速还有位置联系电话☎13926014559
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13926014559
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→深圳丹竹头】6月8日明天早上9点左右出发，有1个座位，需要的联系电话：13424224087
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13424224087
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→苏州，无锡，昆山】7号下午出发，有4个座位，联系电话：15251570078
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15251570078
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：上海→广昌】6月7号-6月10号出发，有4个座位，联系电话：18719847918
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18719847918
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳、惠州、河源→广昌】6月8号早上出‬发回广昌，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13197887480
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳→广昌】6月8号早上8点左右出发，深圳回广昌，途经惠州，河源，全新SUV私家车，方便快捷，全程高速，联系电话：13538133140微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13538133140
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳宝安→广昌】6月8号早上出发，深圳宝安回广昌，途经，惠州，河源，全程高速，有需要的朋友可以联系，电话:13237501686微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13237501686
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳龙岗→广昌】8号早上出发私家车，2个位置，电话13925288648
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13925288648
       </span>
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
        <br/>
       </span>
      </span>
     </span>
     <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
      <span style="font-size: 24px;color: rgb(0, 0, 0);font-weight: bold;" textstyle="">
       【2025年6月6日】
      </span>
     </span>
    </span>
   </span>
  </span>
 </section>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       【提供车：常州，无锡，苏州，杭州→广昌】6月7号走全新商务车，空间大，还有位置还能带点小货，需要的联系电话微信同号13358187716。
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       13358187716
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：东莞→广昌】途径河源、惠州、6月7号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15179496333微信同号，老刘
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15179496333
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：抚州→广昌】(6月6号下午12点→4点左右）随时:抚州出发→广昌:联系:☎️电话:微信同号:15879827878
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15879827878
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：抚州→广昌】6月6号，下午11-3左右出发，联系电话☎:微信同号15079470077
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15079470077
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：抚州→广昌】6月6号中午12点至3点左右（高速直达）出发广昌，有需要请联系:17779466767微信同号！
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       17779466767
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：抚州→广昌】顺风车：6月6号11点-13点左右出发，《全程高速》，有4个座位，联系电：13237503277
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13237503277
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月7号，途经，惠州，河源，私家车，全程高速，有需要的朋友可以联系，电话:18296469705
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18296469705
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月7号上午八九点出发，需要的联系电话18970411476
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18970411476
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞黄江】6月8号早上出发，联系电话13767606639
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13767606639
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】（6月7号〉明天早上8点出发广州还有位私家车高速直达，有需要的朋友请联系电话:☎️18870444698
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18870444698
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6～7号早上8点到9点出发，私家车有3个座位。电话13647946511（微信同号）
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13647946511
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6月7号，早上8点半左右出发广州，还有位置，有回广州的老乡请联系17770491668微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       17770491668
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州大源】7号早上出发有3个位，私家车有需要的请联系13711301686
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13711301686
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州大源】7号早上出发有3个位，私家车有需要的请联系13826104819微信同号。谢谢
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13826104819
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州太和】6月6日（今天）上午九点左右从广昌出发去广州太和，进口私家越野车有需要的请联系13828416818
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13828416818
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州太和大源】6月7号早上广昌出发广州全程高速还有位置联系电话☎13926014559
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13926014559
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌，昌北机场，西站】全新商务车出租车，明天（凌晨4~5点）广昌一南昌各地铁口包接送，承接小件快运，全程高速！联系电话19179417755李师傅微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       19179417755
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌，机场】7号（凌晨4点～5点）广昌出发，南昌各大医院，机场，八一广场附近:火车站，学校:各大地铁口。19880051252微信同号，
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       19880051252
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌、机场】（正规合法商务车）明早4点左右去南昌包接送、经过南昌机场、西站、火车站，1234号地铁口，及各大学校、各大医院！☎️尖峰李师傅：15979599263微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15979599263
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】(明天)早上凌晨4点至早上8点左右出发南昌，昌北机场，南昌西站、火车站、象湖一附，各大医院，各大学校，八一广场附近，可带小件货。联系电话13767600996余师傅，微信同号。
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13767600996
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】（正规合法营运车）明天凌晨4点--8点左右出发去南昌，经过昌北机场，南昌西站，火车站，各大医院，各大学校，欢迎来电！☎️13263089688微信同号
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13263089688
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】全新广汽传祺商务车。空间大乘坐舒适！明天凌晨四点至早上八点出发南昌各大医院，机场，学校，八一广场附近，全程高速！有需要的朋友可以联系！联系电话:15879827163（揭师傅）微信同号！
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       15879827163
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌】私家车6月6晚上8.左右出发电话/微信:李15979560866
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       15979560866
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→南昌机场】明天早上4一5点左右出发去南昌，经过昌北机场，南昌站，一附、二附医院、省妇幼保健院、省中医院，第三医院、省儿童医院.眼科，医口腔医院等医院，八一大道1234地铁口，各大学院校。联系电话：15179421828符师傅微信同号
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       15179421828
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳、惠州、河源】6月7号早上出‬发回深圳，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13197887480
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳宝安】6月7号早上出发，广昌回深圳宝安途经：河源、惠州，全程高速，有需要的朋友可以联系，电话:13237501686微信同号
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13237501686
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州→广昌】7号早上广州出发广昌全程高速，私家新车大型suv.还有位置联系电话：15397889018微信同号
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       15397889018
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月7号，早上出发回广昌，顺风车，，全程高速，有需要的朋友可以提前联系，电话：18779456458
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       18779456458
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州太和→广昌】6月6号出发，私家车还有3个位置，有需要的联系：13724068115
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13724068115
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州太和大源→广昌】（6月7号）明天上午广州出发，顺风车还有位置，有回去的老板请电15070492356
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       15070492356
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：揭阳→广昌】明天6月7号早上出发，私家车可坐3人联系电话：15840708748
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       15840708748
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：南昌、南昌机场→广昌】6号上午，中午，下午南昌回广昌，经过八一广场，一附，二附，中医院，儿童医院，周边，商务车，还有位置有需要的联系：13617942668微信同号
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13617942668
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：南昌→广昌】6月6号上午10-4点左右昌北机场，八一广场附近回广昌，大商务车，还有位置有需要的朋友可以提前联系：18879473134，
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       18879473134
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳→广昌】6月7号早上8点左右出发，深圳回广昌，途经惠州，河源，全新SUV私家车，方便快捷，全程高速，联系电话：13538133140微信同号
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13538133140
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
       <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
        <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
         <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
          <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
           <br/>
          </span>
         </span>
        </span>
       </span>
      </span>
      <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
       <span style="font-size: 24px;color: rgb(0, 0, 0);font-weight: bold;" textstyle="">
        【2025年6月5日】
       </span>
      </span>
     </span>
    </span>
   </span>
  </span>
 </section>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       【提供车：；深圳→广昌】6月6号下午4点出发途经，河源，惠州，深圳，全新私家车，方便快捷，联系电话:18779406775
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       18779406775
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：东莞→广昌】明天6号早上东莞回广昌全新豪华SUV还有位置，途径河源，惠州有需要的朋友可以联系，电话15979585770微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15979585770
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月6号，途经，惠州，河源，私家车，全程高速，有需要的朋友可以联系，电话:18296469705
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18296469705
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】6月6号上午，电话微信同号：13728306728
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13728306728
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→抚州】6月6号下午2.50左右出发，个人私家车，联系电话：13133729332
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13133729332
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6月6号明天上午去广州，私家车，有去广州的可以联系，电话 ：15070492356
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15070492356
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6月6号上午广昌出发广州，私家车大空间，高速直达，有需要的朋友请联系电话:15720901443
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15720901443
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州太和】6月6日（明天）上午九点左右从广昌出发去广州太和，进口私家越野车有需要的请联系13828416818
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13828416818
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→普宁】明天，有空位，有雲要提前联系电18907942558
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18907942558
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→上海】私家车，6 月 6号明天早上走可以坐3人，需要联系18979459711
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18979459711
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→苏州】6-7号随时可以走、还有两个位置.联系电话18136950598
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18136950598
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州→广昌】（6月6号〉明天早上9点出发广昌还有位私家车高速直达，有需要的朋友请联系电话:☎️ 18379667813
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18379667813
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州→广昌】6月6号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系17770491668微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       17770491668
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月6号，早上8点半左右出发广昌，还有3个位置，私家车
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
      <span leaf="">
       有回广昌的老乡请联系电话☎15920936271
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15920936271
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月6号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系电话☎13926014559
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13926014559
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：揭阳→广昌】6月7号早上出发，私家车可坐3人联系电话：15840708748
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15840708748
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：昆山→广昌】6月6日，上午7点左右出发，‬私家车！走高速联路‬系电话19179470378微信同号。
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       19179470378
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳、惠州、河源→广昌】6月6号早上出‬发回广昌，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13197887480
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳→广昌】6月6号早上出发，深圳回广昌，途经，惠州，全新SUV私家车，全程高速，有需要的朋友可以联系，电话:18979427463微信同号
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18979427463
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：苏州→广昌】6号一早出发，还有2个位置，电话18662189850
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       18662189850
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：苏州→广昌】7号或者8号早上出发，有3位子，需要联系15850360866
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15850360866
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
       <br/>
      </span>
      <table style="border-collapse:collapse;width:399.77pt;">
       <tbody>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height: 18pt;" width="389">
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:35px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:51px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:63px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→抚州】6月6号下午2.50左右出发，个人私家车，联系电话：13133729332
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144" width="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13133729332
            </span>
           </span>
          </section>
         </td>
        </tr>
       </tbody>
      </table>
      <table style="border-collapse:collapse;width:399.77pt;">
       <tbody>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height: 18pt;" width="389">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：东莞→广昌】明天6号早上东莞回广昌全新豪华SUV还有位置，途径河源，惠州有需要的朋友可以联系，电话15979585770微信同号
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144" width="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15979585770
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：抚州→广昌】(6月5号下午3点→5点左右）随时:抚州出发→广昌:联系:☎️电话:微信同号:15879827878
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15879827878
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:25px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:35px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <span style="mso-ignore:vglayout;margin-left:0px;margin-top:0px;width:2px;height:63px;visibility:visible;">
           <span leaf="">
            <br/>
           </span>
          </span>
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：抚州→广昌】6月5号，下午11-3左右出发，联系电话☎:微信同号15079470077
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15079470077
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→东莞】6月6号，出发广昌回东莞，途经，惠州，河源，私家车，全程高速，有需要的朋友可以联系，电话:18296469705
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18296469705
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→东莞】6月6号上午，电话微信同号：13728306728
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13728306728
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→广州】6月6号上午广昌出发广州，私家车大空间，高速直达，有需要的朋友请联系电话:15720901443
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15720901443
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→广州太和】6月6日（明天）上午九点左右从广昌出发去广州太和，进口私家越野车有需要的请联系13828416818
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13828416818
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→惠州平南】6月8号，惠州回广昌，有三个位置需要的朋友可以联系，电话15279463871
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15279463871
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广州→广昌】（6月6号〉明天早上9点出发广昌还有位私家车高速直达，有需要的朋友请联系电话:☎️ 18379667813
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18379667813
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广州→广昌】6月5号（下午1点）出发回广昌，全新私家车，有3位置，电话:13560288068
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13560288068
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广州→广昌】6月6号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系17770491668微信同号
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             17770491668
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广州大源→广昌】6月6号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系电话☎13926014559
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13926014559
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：杭州→广昌】6月6号随时可以走，电话13407946763
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13407946763
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：杭州→广昌】6月6号早上7点到8点出发，有回去的请联系15157178369
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15157178369
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：南昌→广昌】6月5号上午10-5点左右昌北机场，八一广场附近回广昌，大商务车，还有位置有需要的朋友可以提前联系：18879473134，
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18879473134
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：南昌→广昌】6月5号上午或下午出发回广昌，私家车全程高速，有座位，有回广昌的朋友尽快联系，电话：15179421828
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15179421828
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：南昌→广昌】广汽传祺（正规商务7坐出租车）商务车空间大，乘坐舒适）5号上午或者下午随时南昌回广昌全程高速，途径各大医院，机场
            </span>
           </span>
           <span style="mso-spacerun:yes;">
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
             </span>
            </span>
           </span>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             ，西站，火车站，东站，八一广场，乘车安全有保障，电话：13767600996余师傅
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13767600996
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：南昌→广昌】明天6月6日下午6点回广昌，宽敞SUV全程高速13097214180微信同号。
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13097214180
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：南丰→广昌】动车站回来6月5号下午出发，顺风车还有位置，联系电话微信：13217948695
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13217948695
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：宁波→广昌】6月6日早上出发，还有2个座位，联系电话：13867861582
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13867861582
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：深圳、惠州、河源→广昌】6月6号早上出‬发回广昌，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13197887480
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：深圳→广昌】6月6号早上8点左右出发，深圳回广昌，途经惠州，河源，全新SUV私家车，方便快捷，全程高速，联系电话：13538133140微信同号
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13538133140
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：苏州→广昌】6号早上出发，私家小车，位置多需要的联系电话18379657379
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18379657379
            </span>
           </span>
          </section>
         </td>
        </tr>
       </tbody>
      </table>
     </span>
    </span>
   </span>
  </span>
 </section>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：常州，无锡，苏州，杭州→广昌】6月6号走全新商务车，空间大，还有位置还能带点小货，需要的联系电话微信同号13358187716。
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13358187716
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞→广昌】明天6号早上东莞回广昌全新豪华SUV还有位置，途径河源，惠州有需要的朋友可以联系，电话15979585770微信同号
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15979585770
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→东莞】途径河源、惠州、6月6号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15179496333微信同号，老刘
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15179496333
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6月6号上午广昌出发广州，私家车大空间，高速直达，有需要的朋友请联系电话:15720901443
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15720901443
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→广州】6月6号早上广昌出发广州全程高速，私家新车 Suv还有位置联系电话：15397889018微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15397889018
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→杭州】6月6号，电话.13237941757
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13237941757
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→揭阳】6月6号早上去揭阳自家车 顺带 有需要联系:15179426221微信同号！
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       15179426221
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广昌→深圳宝安】6月6号早上出发，广昌回深圳宝安途经：河源、惠州，全程高速，有需要的朋友可以联系，电话:13237501686微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13237501686
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州→广昌】6月5号（下午1点）出发回广昌，全新私家车，有3位置，电话:13560288068
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       13560288068
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州→广昌】6月6号（上午8-9点）出发回广昌，全新私家车SUV，有3位置，电话:19925896455
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       19925896455
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州大源→广昌】6月6号，早上8点半左右出发广昌，还有位置，有回广昌的老乡请联系电话☎13926014559
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13926014559
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：广州太和→广昌】 5号下午1点左右出发，还有3个位置，全程高速。要去广昌的请联系13078876367
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13078876367
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：杭州→广昌】6月6号早上7点到8点出发，有回去的请联系15157178369
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       15157178369
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：揭阳→广昌】6月5号晚上出发，联系电话13907049855
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13907049855
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳、惠州、河源→广昌】6月6号早上出‬发回广昌，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13197887480
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       【提供车：深圳→广昌】6月6号早上8点左右出发，深圳回广昌，途经惠州，河源，全新SUV私家车，方便快捷，全程高速，联系电话：13538133140微信同号
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       13538133140
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span data-pm-slice='1 1 ["para",{"tagName":"section","attributes":{},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
       <br/>
      </span>
      <span data-pm-slice="0 0 []" style='color: rgb(26, 27, 28);font-family: mp-quote, -apple-system-font, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;font-size: 14px;font-style: normal;font-variant-ligatures: normal;font-variant-caps: normal;font-weight: 400;letter-spacing: normal;orphans: 2;text-align: start;text-indent: 0px;text-transform: none;widows: 2;word-spacing: 0px;-webkit-text-stroke-width: 0px;white-space: pre-line;background-color: rgb(246, 247, 248);text-decoration-thickness: initial;text-decoration-style: initial;text-decoration-color: initial;display: inline !important;float: none;'>
       <span leaf="">
        <br/>
       </span>
      </span>
     </span>
    </span>
   </span>
  </span>
 </section>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→东莞】6月6号上午，电话微信同号：13728306728
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13728306728
       </span>
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span data-pm-slice='1 1 ["para",null,"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
       <span style="font-size: 24px;color: rgb(0, 0, 0);font-weight: bold;" textstyle="">
        【2025年6月4日】
       </span>
      </span>
     </span>
    </span>
   </span>
  </span>
 </section>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        提供车，广昌到普宁6月6号上午岀发，全程高速，电话15323221864
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144" width="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15323221864
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        ［提供车苏州到广昌］6月6日出发，可以带3个人，有需要的可以联系13024580968
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13024580968
       </span>
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span data-pm-slice='1 1 ["para",null,"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
       <br/>
      </span>
      <table style="border-collapse:collapse;width:399.77pt;">
       <tbody>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height: 18pt;" width="389">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：东莞→广昌】6号早上东莞回广昌全新豪华SUV还有位置，途径河源，惠州有需要的朋友可以联系，电话15979585770微信同号
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144" width="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15979585770
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：东莞→广昌】6月5号早上回广昌，私家车。联系‬电话17796376512
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             17796376512
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：东莞→广昌】6月5日早上东莞市百茂物流园到广昌有3个位置，电话13802450856
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13802450856
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：东莞→广昌】途径河源、惠州、6月5号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15179496333微信同号，老刘
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15179496333
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：东莞百茂物流园→广昌】6月5号早上八点东莞回广昌，私家车，还有座位，有东莞回广昌的老板请联系18665063782(余)
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18665063782
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：东莞高埗，博罗县石湾镇园洲镇→广昌】5号6号，随时出发，私家车可带4人有2个就走，请联系 13925589078
            </span>
           </span>
           <span style="mso-spacerun:yes;">
            <span leaf="">
             <span style="color: rgb(0, 0, 0);" textstyle="">
             </span>
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13925589078
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→常州，无锡，苏州，杭州】6月5号走全新商务车，空间大，还有位置还能带点小货，有需要的联系电话微信同号13358187716
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13358187716
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→佛山】6月5日中午或6月6日早上出发，联系电话：15350406383
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15350406383
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→广州】6号6号早上8点到9点出发，私家车有3个座位。电话13647946511（微信同号）
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13647946511
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→广州】6月5号上午广昌出发广州，私家车大空间，高速直达，有需要的朋友请联系电话:15720901443
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15720901443
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→广州太和】6月5号随时出发，私家小轿车有3个位置！有需要的请联系电话：19194926184
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             19194926184
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→广州太和大源】6月5号早上广昌出发广州全程高速还有位置联系电话☎13926014559
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13926014559
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→揭阳，汕头，潮安】6月5号上午出发，有3个座位，私家车联系电话：18379665525李 （微信同号）
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18379665525
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→揭阳】6月6号早上去揭阳自家车 顺带 有需要联系:15179426221微信同号！
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15179426221
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→昆山，太仓国际物流园】6月5日上午出发，还有3个位置，老司机私家车，SUV全程高速，联系电话：159 3295 3844
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             159 3295 3844
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→深圳、东莞、惠州】6月5号出发还有4个位置最好行李少点 ，联系电话：15821248365
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15821248365
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→深圳】6🈷️5号晚上12点左右广昌到深圳，SUV私家车，有需要的朋友提前联系：13528493167
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13528493167
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→深圳】6月5号早上8点出发，广昌去深圳，途径河源，惠州，全新SUV私家车，全程高速，方便快捷，联系电话:13538133140微信同号
            </span>
           </span>
          </section>
         </td>
         <td data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13538133140
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→深圳】6月5号早上出发，广昌去深圳，途经，惠州，全新SUV私家车，全程高速，有需要的朋友可以联系，电话☎️:13530121561微信同号
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13530121561
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广昌→中山，珠海】私家车，还有4个座位，6月5号上午8点出发，还有4个座位联系电话15279493259游。
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15279493259
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广州→广昌】5号早上广州出发广昌全程高速，私家新车大型suv.还有位置联系电话：15397889018微信同号
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             15397889018
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：广州太和→广昌】3人，6月6日出发晚7点，联系电话13928714347，私家车
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13928714347
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <br/>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <br/>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：揭阳→广昌】6月5号晚上或6号上午出发，联系电话13907049855
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13907049855
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：昆山→广昌】6月6日，上午7:30点左右出发，‬私家车！走高速联路‬系电话19179470378微信同号。
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             19179470378
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：昆山苏州→广昌】6月6号出发，私家顺风车，有3个位置需要的朋友可以联系13826076952
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13826076952
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：上海，松江→广昌】6号早上出发，SUV车，还有3个位置，最好来一位会开车的老司机，有需要请联系吴:13023495995
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13023495995
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：深圳→广昌】5号早上8左右出发，有3个座位，联系电话：18665383909
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18665383909
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：深圳→广昌】6月5号早上，深圳回广昌，私家车丰田SUV，全程高速方便快捷，途径惠州有需要的朋友可以联系，电话13340188438
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             13340188438
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：深圳→广昌】6月5号早上出发，深圳回广昌，途经，惠州，全新SUV私家车，全程高速，有需要的朋友可以联系，电话:18979427463微信同号
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18979427463
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：私家车广州大源太和→广昌】6月6号早上8：30左右出发，有3个位置，联系电话：18379659802
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18379659802
            </span>
           </span>
          </section>
         </td>
        </tr>
        <tr style="height:18.00pt;">
         <td data-colwidth="389" style="height:18.00pt;">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             【提供车：苏州→广昌】6号早上出发，私家小车，位置多需要的联系电话18379657379
            </span>
           </span>
          </section>
         </td>
         <td align="right" data-colwidth="144">
          <section>
           <span leaf="">
            <span style="color: rgb(0, 0, 0);" textstyle="">
             18379657379
            </span>
           </span>
          </section>
         </td>
        </tr>
       </tbody>
      </table>
     </span>
    </span>
   </span>
  </span>
 </section>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞→广昌】途径河源、惠州、6月5号早上出发。全新SUV私家车，全程‬高速、联系‬电话☎️15179496333微信同号，老刘
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144" width="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15179496333
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：东莞高埗→广昌】私家车6月5日早上8-9点出发，有3个位置，联系电话：18926517740
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18926517740
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→东莞】明天5号早上出发广昌回东莞还有位置，全新豪华SUV商务车，途径河源，惠州有需要的朋友可以联系，电话15979585770小张
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15979585770
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州、佛山、中山、珠海】6月5号早上8点出发，途经广州包接包送传祺大商务有需要的联系18279454568微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18279454568
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州】6月5号，早上8点半左右出发广州，还有位置，有回广州的老乡请联系17770491668微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        17770491668
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州】6月5号明天上午去广州，私家车，有去广州的可以联系，电话 ：15070492356
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15070492356
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→广州太和大源】6月5号早上广昌出发广州全程高速还有位置联系电话☎13926014559
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13926014559
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→惠州平南】6月8号，惠州回广昌，有三个位置需要的朋友可以联系，电话15279463871
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15279463871
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→揭阳】6月6号早上去揭阳自家车 顺带 有需要联系:15179426221微信同号！
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15179426221
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→上海】6月5日一早出发，还有三―四个位置，电话13817271238
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13817271238
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→深圳、东莞、惠州】6月5号出发还有4个位置最好行李少点 ，联系电话：15821248365
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15821248365
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→深圳、惠州、河源】6月 5号早上出‬发回深圳，途经河源，惠州，全新超大空间私家商务车，全程‬高速、联系‬电话13197887480微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13197887480
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→深圳】6月5号晚上广昌到深圳，SUV私家车，有需要的朋友提前联系：18306646244
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18306646244
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→深圳】6月5号早上8点出发，广昌去深圳，途径河源，惠州，全新SUV私家车，全程高速，方便快捷，联系电话:13538133140微信同号
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13538133140
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→深圳】6月5号早上出发，广昌去深圳，途经，惠州，全新SUV私家车，全程高速，有需要的朋友可以联系，电话☎️:13530121561微信同号
       </span>
      </span>
     </section>
    </td>
    <td data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13530121561
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广昌→深圳丹竹头】6月5上午出发深圳丹竹头，还有位置，联系电话15207045266微信同号
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15207045266
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广州→广昌】（6月5号〉明天早上9点出发广昌还有位私家车高速直达，有需要的朋友请联系电话:18870444698
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18870444698
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：广州→广昌】5号早上广州出发广昌全程高速，私家新车大型suv.还有位置联系电话：15397889018微信同号
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15397889018
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：杭州→广昌】6月5号上午出发。还有两个位置，18688430616
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18688430616
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：上海，松江→广昌】5号到6号早上出发，SUV车，还有3个位置，最好来一位会开车的老司机，有需要请联系吴:13023495995
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13023495995
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳→广昌】5号早上8左右出发，有3个座位，联系电话：18665383909
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18665383909
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳→广昌】6月5号早上，深圳回广昌，私家车丰田SUV，全程高速方便快捷，途径惠州有需要的朋友可以联系，电话13340188438
       </span>
      </span>
      <span style="mso-spacerun:yes;">
       <span leaf="">
        <span style="color: rgb(0, 0, 0);" textstyle="">
        </span>
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        13340188438
       </span>
      </span>
     </section>
    </td>
   </tr>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height:18.00pt;">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        【提供车：深圳→广昌】6月5号早上出发，深圳回广昌，途经，惠州，全新SUV私家车，全程高速，有需要的朋友可以联系，电话:18979427463微信同号
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        18979427463
       </span>
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <table style="border-collapse:collapse;width:399.77pt;">
  <tbody>
   <tr style="height:18.00pt;">
    <td data-colwidth="389" style="height: 18pt;" width="389">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        提供车，广昌到普宁6月5号上午岀发，全程高速，电话15323221864
       </span>
      </span>
     </section>
    </td>
    <td align="right" data-colwidth="144" width="144">
     <section>
      <span leaf="">
       <span style="color: rgb(0, 0, 0);" textstyle="">
        15323221864
       </span>
      </span>
     </section>
    </td>
   </tr>
  </tbody>
 </table>
 <section>
  <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
   <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
    <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
     <span style="color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;">
      <span data-pm-slice='1 1 ["para",null,"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"},"node",{"tagName":"span","attributes":{"style":"color: rgb(255, 0, 0);font-size: var(--articleFontsize);letter-spacing: 0.034em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="" style='color:rgba(0, 0, 0, 0.9);font-size:17px;font-family:"mp-quote", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;line-height:1.6;letter-spacing:0.034em;font-style:normal;font-weight:normal;'>
       <br/>
      </span>
     </span>
    </span>
   </span>
  </span>
 </section>
 <section>
  <span data-pm-slice='1 1 ["para",{"tagName":"p","attributes":{"style":"white-space: normal;text-align: left;text-indent: 0em;margin-bottom: 24px;line-height: 1em;"},"namespaceURI":"http://www.w3.org/1999/xhtml"}]' leaf="">
   <br/>
  </span>
 </section>
 <p style="display: none;">
  <mp-style-type data-value="3">
  </mp-style-type>
 </p>
</div>

    '''
    year_month = "2025-06"

    # 执行数据提取
    extracted_data = main(html_content, year_month)

    print(extracted_data)

    # 输出JSON结果
    # print(json.dumps(extracted_data, ensure_ascii=False, indent=2))