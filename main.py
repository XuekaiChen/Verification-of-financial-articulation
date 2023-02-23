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
    file_path = "预披露 景杰生物 2022-12-02  1-1 招股说明书_景杰生物.pdf"
    rule_path = "rules"
    tables_folder = "tables"
    json_data_path = "table_content.json"
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
    rule_dict = get_rule(rule_path)

    print("----------------------表格抽取-------------------------")
    extract_all_table(pdf, tables_folder)  # 目前将表格存入excel
    excels2json(tables_folder, json_data_path)  # 存入json文件
    with open(json_data_path, 'r', encoding='utf8') as fp:
        json_data = json.load(fp)

    print("----------------------同名字段跨表校验-------------------------")
    json_data2, inverted_list, cross_result = precheck_and_get_dict(json_data, pdf, doc, cross_result)

    print("----------------------规则校验-------------------------")
    cross_result, inner_result = judge_from_rule(json_data2, rule_dict, pdf, doc, inverted_list, cross_result, inner_result)

    print("----------------------表内校验-------------------------")
    inner_result = inner_check(json_data, pdf, doc, inner_result)

    print("----------------------文表校验-------------------------")
    text_result = text_check(json_data2, pdf, doc, inverted_list, text_result)

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


