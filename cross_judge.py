# -*- coding: utf-8 -*-
# Date        : 2023/2/21
# Author      : Chen Xuekai
# Description : 从json存储的表格中合并校验同名字段，根据规则校验跨表勾稽

import json
import re
import numpy as np
import fitz
import pdfplumber
from util import is_number_list, equal_check, locate_chart_info

general_field_name = ["其他", "合计", "小计", "1年以内", "1-2年", "2-3年"]


# 判断列表是否是字典索引列表的子集
def listindir(list_a, all_dict):
    for ele in list_a:
        if ele not in all_dict:
            return False
    return True


def checklen(list_a, all_dict):
    n = len(all_dict[list_a[0]][0])
    for name in list_a:
        if len(all_dict[name]) != 1:  # 字段有多个数字列表
            return False
        if len(all_dict[name][0]) != n:  # 有其他字段的数字列表长度不相等
            return False
    return n


# 同名字段跨表校验 + 得到倒排表inverted_list + 整合字段词典json_data2
# TODO 目前同字段名校验准确率最低，因为很可能字段名相同但说的不是一个东西，导致数据不同
def precheck_and_get_dict(chart_data, pdf, doc, cross_result):
    json_data = {}
    inverted_list = {}  # 倒排表 {字段：所属表格}
    for excel_name, chart in chart_data.items():
        for field_name, field_value in chart.items():
            # 排除非数字列表 或 ”合计“等字段
            if (not is_number_list(field_value)) or (field_name in general_field_name):
                continue
            elif field_name not in json_data:
                json_data[field_name] = [field_value]
                inverted_list[field_name] = [excel_name]
            else:  # json中已有同名字段数据，与每个字段数据比对，若可以匹配，则定位；若匹配错误，则加入字段数据
                for idx, exist_value in enumerate(json_data[field_name]):
                    # 校验正确，输出[]；校验错误，输出[1,2]；未配对，输出“字段匹配错误”，加入列表
                    check_result = equal_check(exist_value, field_value)
                    if check_result != "字段匹配错误":
                        if not check_result:  # check_result为空表示校验正确
                            true_or_false = "正确"
                        else:
                            true_or_false = "错误"
                            print(f"规则：{field_name} = {field_name}")
                            print(exist_value)
                            print(field_value)
                            print("出错列：", check_result)
                            print()
                        # 定位
                        up_table_info = locate_chart_info(pdf, doc, inverted_list[field_name][idx], [field_name], [len(exist_value)+1], [check_result])
                        down_table_info = locate_chart_info(pdf, doc, excel_name, [field_name], [len(field_value)+1], [check_result])
                        cross_item = {
                            "名称": true_or_false,
                            "规则": field_name + " = " + field_name,
                            "上勾稽表": up_table_info,
                            "下勾稽表": down_table_info
                        }
                        cross_result.append(cross_item)
                    if check_result:  # 校验错误或未匹配的数字列表都加入备选
                        json_data[field_name].append(field_value)
                        inverted_list[field_name].append(excel_name)  # 倒排表添加元素
    return json_data, inverted_list, cross_result


def judge_from_rule(chart_data2, rules, pdf, doc, inverted_list, cross_result, inner_result):
    # 规则四则运算判断，之中可能包含表内校验

    for xsltype, rule2 in rules.items():
        uprule2, downrule2 = rule2['uprule'], rule2['downrule']
        # 解析勾稽规则，查字典取值并运算，返回校验结果
        for up_field, down_field in zip(uprule2, downrule2):
            if down_field == up_field:  # 同字段名已经校验完毕
                continue
            down_field_list = re.split(' [+\-*/] ', down_field)
            operators = re.findall('[+\-*/]', down_field)
            # TODO 优化此处代码
            if up_field in chart_data2 and listindir(down_field_list, chart_data2):  # 所有字段名都在字典中
                down_total = np.array(chart_data2[down_field_list[0]][0])  # TODO 若chart_data2[down_field_list[0]]有多个列表，应循环遍历
                down_value_len = checklen(down_field_list, chart_data2)  # 确保每个相加的数字列表长度都相等
                if not down_value_len:
                    continue
                for up_value in chart_data2[up_field]:
                    up_total = np.array(up_value)
                    if down_value_len == len(up_value):
                        # 进行四则运算
                        for ele_idx in range(len(operators)):
                            element = np.array(chart_data2[down_field_list[ele_idx + 1]][0])
                            if operators[ele_idx] == '+':
                                down_total += element
                            elif operators[ele_idx] == '-':
                                down_total -= element
                            elif operators[ele_idx] == '*':
                                down_total *= element
                            elif operators[ele_idx] == '/':
                                down_total /= element
                        # 校验
                        check_result = equal_check(up_total, down_total)
                        if check_result != "字段匹配错误":
                            if not check_result:  # check_result为空表示校验正确
                                true_or_false = "正确"
                            else:
                                true_or_false = "错误"
                                print(f"规则：{up_field} = {down_field}")
                                print(up_total)
                                print(down_total)
                                print("出错列：", check_result)
                                print()

                            # 定位
                            up_table_info = locate_chart_info(pdf, doc, inverted_list[up_field][0], [up_field], [len(up_total) + 1], [check_result])
                            # TODO 考虑循环表格的问题，目前当所有下勾稽表字段都在一个表中；应该遍历所有字段共同出现的所有表
                            down_tables = [inverted_list[down_name][0] for down_name in down_field_list]
                            col_len_list = [len(down_total) + 1 for i in range(len(down_field_list))]
                            check_result_list = [check_result for i in range(len(down_field_list))]
                            down_table_info = locate_chart_info(pdf, doc, down_tables[0], down_field_list, col_len_list, check_result_list)

                            json_item = {
                                "名称": true_or_false,
                                "规则": up_field + " = " + down_field,
                                "上勾稽表": up_table_info,
                                "下勾稽表": down_table_info
                            }
                            if xsltype == "跨表":
                                cross_result.append(json_item)
                            elif xsltype == "表内":
                                inner_result.append(json_item)

    return cross_result, inner_result


if __name__ == "__main__":
    from extract_rule import get_rule
    import time
    print("正在进行跨表勾稽关系校验......")
    start = time.time()
    path = "预披露 景杰生物 2022-12-02  1-1 招股说明书_景杰生物.pdf"
    field_data_path = 'table_content.json'
    with open(field_data_path, 'r', encoding='utf8') as fp:
        field_data = json.load(fp)
    highlight_pdf = "Articulation_out/cross_highlight.pdf"
    output_file1 = "Articulation_out/try_precheck.json"
    output_file2 = "Articulation_out/try_rule.json"
    cross_result = []
    inner_result = []
    doc = fitz.open(path)
    pdf = pdfplumber.open(path)

    # 校验
    rule_dic = get_rule('rules')
    print()
    json_data2, inverted_list, cross_result = precheck_and_get_dict(field_data, pdf, doc, cross_result)
    cross_result, inner_result = judge_from_rule(json_data2, rule_dic, pdf, doc, inverted_list, cross_result, inner_result)

    # 存储
    with open(output_file1, 'w', encoding='utf-8') as f:
        json.dump(cross_result, f, ensure_ascii=False)
    with open(output_file2, 'w', encoding='utf-8') as f:
        json.dump(inner_result, f, ensure_ascii=False)
    doc.save(highlight_pdf)
    pdf.close()
    doc.close()

    print("跨表勾稽关系校验完毕，用时：{:.2f}秒".format(time.time() - start))
