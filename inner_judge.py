# -*- coding: utf-8 -*-
# Date       ：2023/2/20
# Author     ：Chen Xuekai
# Description：逐表格进行表内勾稽校验

import json
import fitz
import pdfplumber
import numpy as np
from util import equal_check, locate_chart_info


def iseverylist_leneaual(list_a):
    for i in range(len(list_a) - 1):
        if len(list_a[i]) != len(list_a[i + 1]):
            return False
    return True


def inner_check(json_data, pdf, doc, inner_result):
    for chart_name, chart in json_data.items():
        # 表内字段名称列表
        field_list = list(chart.keys())
        # 判定所有数字列表长度是否相等，获取数字列表长度
        if not iseverylist_leneaual(list(chart.values())):
            continue
        else:
            value_len = len(list(chart.values())[0])

        # 二维数字列表
        value_list = list(map(lambda x: [0] * value_len if x == [] else x, list(chart.values())))
        indexlist = [-1]
        for idx, field_name in enumerate(field_list):
            if '合计' in field_name or "小计" in field_name:
                indexlist.append(idx)

        if indexlist != [-1]:
            for sum_row_idx in range(len(indexlist)-1):
                up_total = value_list[indexlist[sum_row_idx + 1]]  # 合计的数值
                start_index = indexlist[sum_row_idx] + 1
                end_index = indexlist[sum_row_idx + 1]
                if start_index >= end_index:  # 两行紧挨着出现合计的情况
                    continue
                down_total = np.sum(np.array(value_list[start_index:end_index]), axis=0)
                check_result = equal_check(up_total, down_total)
                if check_result != "字段匹配错误":
                    up_field = field_list[indexlist[sum_row_idx + 1]]
                    down_field_list = field_list[indexlist[sum_row_idx] + 1:indexlist[sum_row_idx + 1]]
                    down_field = ' + '.join(down_field_list)
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
                    up_table_info = locate_chart_info(pdf, doc, chart_name, [up_field], [len(up_total) + 1], [check_result])
                    # TODO：以下两行代码要简化，能加和的数字列长度都是相等的
                    col_len_list = [len(down_total) + 1 for i in range(len(down_field_list))]  # 所有每行的长度列表
                    check_result_list = [check_result for i in range(len(down_field_list))]  # 每行的错误列
                    down_table_info = locate_chart_info(pdf, doc, chart_name, down_field_list, col_len_list, check_result_list)
                    json_item = {
                        "名称": true_or_false,
                        "规则": up_field + " = " + down_field,
                        "上勾稽表": up_table_info,
                        "下勾稽表": down_table_info
                    }
                    inner_result.append(json_item)
    return inner_result


if __name__ == "__main__":
    import time
    print("正在进行表内勾稽关系校验......")
    start = time.time()
    path = "预披露 景杰生物 2022-12-02  1-1 招股说明书_景杰生物.pdf"
    field_data_path = 'table_content.json'
    highlight_pdf = "Articulation_out/inner_highlight.pdf"
    output_file = "Articulation_out/try_inner.json"
    doc = fitz.open(path)
    pdf = pdfplumber.open(path)
    inner_result = []
    with open(field_data_path, 'r', encoding='utf8') as fp:
        json_data = json.load(fp)

    # 校验
    inner_result = inner_check(json_data, pdf, doc, inner_result)

    # 存储
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(inner_result, f, ensure_ascii=False)
    doc.save(highlight_pdf)
    pdf.close()
    doc.close()

    print("表内勾稽关系校验完毕，用时：{:.2f}秒".format(time.time() - start))
