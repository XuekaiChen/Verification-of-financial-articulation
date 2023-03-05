# -*- coding: utf-8 -*-
# Date        : 2023/2/21
# Author      : Chen Xuekai
# Description : 招股书勾稽关系校验主函数

"""
分为几个部分：
规则解析（extract_rule.py）：将excel规则解析为嵌套词典规则
表格抽取：pdf_tables_extract.py  TODO：表格直接转json格式
excel表格转json：data2json.py，将json_data2作为主函数公共内容
跨表勾稽：cross_judge.py
表内勾稽：inner_judge.py
文表勾稽：text_judge.py
定位+输出：util.py中的locate相关函数
"""
import os
import time
from pdf_tables_extract import extract_all_table
from extract_rule import get_rule
from data2json import excels2json
from cross_judge import *
from inner_judge import *
from text_judge import *


if __name__ == "__main__":
    start = time.time()
    # file_path = "浙江光华科技股份有限公司首次公开发行股票招股说明书（2021年12月28日报送）.pdf"
    file_path = "预披露 景杰生物 2022-12-02  1-1 招股说明书_景杰生物.pdf"
    rule_path = "rules"
    table_dict_path = "table_dict.json"
    out_folder = "Articulation_out"
    cross_result = []
    inner_result = []
    text_result = []
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    cross_out_path = os.path.join(out_folder, "main_cross.json")
    inner_out_path = os.path.join(out_folder, "main_inner.json")
    text_out_path = os.path.join(out_folder, "main_text.json")
    doc = fitz.open(file_path)
    pdf = pdfplumber.open(file_path)

    print("----------------------规则提取-------------------------")
    rule_dict = get_rule(path=rule_path)

    print("----------------------表格抽取-------------------------")
    # table_dict = extract_all_table(pdf=pdf)
    # json_data = excels2json(table_dict=table_dict)
    with open("table_dict.json", 'r', encoding='utf-8') as fp:
        table_dict = json.load(fp)
    with open("table_content.json", 'r', encoding='utf-8') as fp:
        json_data = json.load(fp)

    print("----------------------同名字段跨表校验-------------------------")
    json_data2, inverted_list, cross_result = precheck_and_get_dict(
        chart_data=json_data,
        pdf=pdf,
        doc=doc,
        cross_result=cross_result
    )

    print("----------------------规则校验-------------------------")
    cross_result, inner_result = judge_from_rule(
        chart_data2=json_data2,
        table_dict=table_dict,
        rules=rule_dict,
        pdf=pdf,
        doc=doc,
        inverted_list=inverted_list,
        cross_result=cross_result,
        inner_result=inner_result
    )

    print("----------------------表内校验-------------------------")
    inner_result = inner_check(
        chart_data=json_data,
        table_dict=table_dict,
        pdf=pdf,
        doc=doc,
        inner_result=inner_result
    )

    print("----------------------文表校验-------------------------")
    text_result = text_check(
        chart_data=json_data2,
        pdf=pdf,
        doc=doc,
        inverted_list=inverted_list,
        text_result=text_result
    )

    # 存储输出json文件
    with open(cross_out_path, 'w', encoding='utf-8') as f:
        json.dump(cross_result, f, ensure_ascii=False)
    with open(inner_out_path, 'w', encoding='utf-8') as f:
        json.dump(inner_result, f, ensure_ascii=False)
    with open(text_out_path, 'w', encoding='utf-8') as f:
        json.dump(text_result, f, ensure_ascii=False)
    doc.save(os.path.join(out_folder, "main_highlight.pdf"))
    pdf.close()
    doc.close()

    print("----------------------勾稽关系校验完毕！------------------------")
    print("用时：{:.2f}秒".format(time.time() - start))
    print("输出文件：", cross_out_path, inner_out_path, text_out_path)


