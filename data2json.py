from functools import reduce
import pandas as pd
import os
import json
from util import is_number, is_number_list


def getTitle(inloc, Elecount, list1, row):
    title_list = []
    for j in range(inloc + 1, len(list1[0])):
        if list1[0][j] == "":
            list1[0][j] = list1[0][j - 1]

    for j in range(inloc + 1, len(row)):
        titley = ''
        for x in range(0, Elecount + 1):
            titley = titley + str(list1[x][j])
            titley = titley.replace('\n', '')
        title_list.append(titley)
    return title_list


def excels2json(excel_folder, out_json):
    # 将所有表格以行名为索引记录到字典里，输出json文件
    excelall = os.listdir(excel_folder)
    data_all = {}
    for excel in excelall:
        data_excel = {}
        xlsx = pd.ExcelFile(os.path.join(excel_folder, excel))
        sheet1 = pd.read_excel(xlsx, 'Sheet1', header=None, keep_default_na=False)
        list1 = sheet1.values.tolist()  # 以行为元素的列表
        a = -1
        Elecount = 0
        inlocList = []

        flag = True
        for row in list1:  # 格式处理
            a = a + 1
            if a == 0:
                title = str(row[0])
                continue
            else:
                if row[0] == "":
                    row[0] = list1[a - 1][0]
                if flag:
                    if str(row[0]) == title and a + 1 < len(list1) and str(list1[a + 1][0]) != title and str(
                            list1[a - 1][0]) == title:
                        Elecount = Elecount + 1
                    else:
                        flag = False
            if len(row) < 5 and row[-1] == '':
                continue
            if type(row[0]) == str:
                row[0] = row[0].replace('\n', '')
            j = len(row) - 1
            while j > 0:
                if type(row[j]) == str:
                    row[j] = row[j].replace(',', '')
                if row[j] == '未披露':
                    row[j] = float(-1)
                if row[j] == '-':
                    row[j] = 0
                if (is_number(row[j])):
                    row[j] = float(row[j])
                j = j - 1
            inloc = 0
            while inloc + 1 < len(row) and row[inloc + 1] != '' and row[inloc + 1] != '-' and type(row[inloc + 1]) == str:
                inloc = inloc + 1
            if inloc == len(row) - 1:
                continue
            if inloc > 0:
                row[inloc] = reduce(lambda x, y: str(x) + str(y), row[0:inloc + 1])
            row[inloc] = row[inloc].replace('\n', '')
            if isinstance(row[inloc], str) and is_number_list(row[inloc + 1:len(row)]):
                data_excel[row[inloc]] = row[inloc + 1:len(row)]
                inlocList.append(inloc)

        if data_excel:
            data_excel['title'] = getTitle(min(inlocList), Elecount, list1, row)
            data_all[excel] = data_excel

    with open(out_json, 'w+', encoding='utf-8') as fp:
        json.dump(data_all, fp, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    tables_folder = "tables"
    out_json_path = "data_all_v2.json"
    excels2json(tables_folder, out_json_path)



