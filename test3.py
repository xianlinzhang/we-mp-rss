def match_words(sentence, word_dict):
    """
    基于自定义词库进行中文分词匹配

    参数:
    sentence (str): 输入的中文句子
    word_dict (set): 包含自定义词汇的集合

    返回:
    list: 匹配到的词汇列表，按出现顺序排列
    """
    # 创建结果列表和临时存储
    result = []
    temp = []

    # 遍历每个字构建可能的词
    for char in sentence:
        # 将当前字符加入临时列表的所有候选项
        temp = [word + char for word in temp] + [char]

        # 检查临时列表中的完整词
        new_temp = []
        for word in temp:
            # 如果是完整词则添加到结果
            if word in word_dict:
                result.append(word)
            else:
                # 只保留可能成为有效词前缀的候选项
                if any(w.startswith(word) for w in word_dict):
                    new_temp.append(word)
        temp = new_temp

    return result


def load_words_from_file(file_path):
    """
    从指定文件中加载词汇，每行一个词汇

    参数:
    file_path (str): 文件路径

    返回:
    set: 包含词汇的集合
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file if line.strip()}
    return words

# 测试用例
if __name__ == "__main__":
    # 从文件加载词库
    file_path = "test3.txt"  # 文件路径
    my_dict = load_words_from_file(file_path)

    # 测试句子
    test_sentence = "广州佛山三水"

    # 执行匹配
    matched = match_words(test_sentence, my_dict)

    # 输出结果
    print("输入句子:", test_sentence)
    print("匹配到的词汇:", matched)
