# -*- coding:utf-8 -*-

"""
    Million Heroes
"""


import multiprocessing
from multiprocessing import Event
from multiprocessing import Pipe

import win32api
import pythoncom
from PIL import ImageFilter
from threading import Thread
import time
from argparse import ArgumentParser

import re
import operator
from functools import partial
from terminaltables import AsciiTable
import win32com.client

from config import api_key
from config import api_version
from config import app_id
from config import app_key
from config import app_secret
from config import data_directory
from config import enable_chrome
from config import image_compress_level
from config import prefer
from config import crop_areas
from config import reg
from core.Colored import *
from core.android import analyze_current_screen_text
from core.android import save_screen
from core.Slicer import *
from core.ios import analyze_current_screen_text_ios
from core.baiduzhidao import baidu_count
from core.baiduzhidao import zhidao_tree
from core.bingqa import bing_count
from core.zhihuqa import zhihu_count
from core.soqa import so_count
from core.check_words import parse_false
from core.airplayscr import check_exsit
from core.chrome_search import run_browser
from core.ocr.baiduocr import get_text_from_image as bai_get_text
from core.ocr.spaceocr import get_text_from_image as ocrspace_get_text

global isNegativeQuestion
global origQuestion
isNegativeQuestion = False
origQuestion = ""
con = printcon()

if prefer[0] == "baidu":
    get_text_from_image = partial(bai_get_text,
                                  app_id=app_id,
                                  app_key=app_key,
                                  app_secret=app_secret,
                                  api_version=api_version,
                                  timeout=5)
elif prefer[0] == "ocrspace":
    get_test_from_image = partial(ocrspace_get_text, api_key=api_key)

def parse_args():
    parser = ArgumentParser(description="Million Hero Assistant")
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=5,
        help="default http request timeout"
    )
    return parser.parse_args()

def parse_question_and_answer(text_list):
    global origQuestion
    question = ""
    start = 0
    for i, keyword in enumerate(text_list):
        question += keyword
        if "?" in keyword:
            start = i + 1
            break
        elif "？" in keyword: # 增加中文问号判断
            start = i + 1
            break
        elif keyword.endswith("."):
            start = i + 1
            break
        elif keyword.endswith("。"):
            start = i + 1
            break
    real_question = question.split(".")[-1] #去除题号的点
    origQuestion = real_question
    # 新增题目模式识别
    global isNegativeQuestion
    isNegativeQuestion = False
    if real_question.find(',')>=0:
        real_question_judge = real_question.split(',')[-1]
    else:
        real_question_judge = real_question.split('，')[-1]
    if real_question_judge.find('没有')>=0 or real_question_judge.find('未')>=0 or real_question_judge.find('不')>=0 or real_question_judge.find('是错')>=0:
        isNegativeQuestion = True
        real_question = real_question.replace('没有','有')
        real_question = real_question.replace('未', '')
        real_question = real_question.replace('还未', '已')
        real_question = real_question.replace('不', '')
        real_question = real_question.replace('是错', '是对')
    question, true_flag = parse_false(real_question)
    # 增加识别异常符号处理
    for ii in range(start,len(text_list)):
        text_list[ii] = re.sub(reg, "", text_list[ii])
        text_list[ii] = text_list[ii].lower()
    return true_flag, real_question, question, text_list[start:]

def pre_process_question(keyword):
    """
    strip charactor and strip ?
    :param question:
    :return:
    """
    for char, repl in [("“", ""), ("”", ""), ("？", "")]:
        keyword = keyword.replace(char, repl)
    keyword = keyword.split(r"．")[-1]
    keywords = keyword.split(" ")
    keyword = "".join([e.strip("\r\n") for e in keywords if e])
    return keyword

class SearchThread(Thread):
    def __init__(self, question,answer,timeout,delword,engine,numofquery=10):
        Thread.__init__(self)
        self.question = question
        self.answer = answer
        self.timeout = timeout
        self.engine = engine
        self.delword = delword
        self.numofquery = numofquery
    def run(self):
        if self.engine == 'baidu':
            self.result = baidu_count(self.question,self.answer,delword=self.delword,timeout=self.timeout,numofquery=self.numofquery)
        elif self.engine == 'bing':
            self.result = bing_count(self.question,self.answer,delword=self.delword,timeout=self.timeout)
        elif self.engine == 'zhihu':
            self.result = zhihu_count(self.question, self.answer,delword=self.delword, timeout=self.timeout)
        elif self.engine == 'so':
            self.result = so_count(self.question, self.answer,delword=self.delword, timeout=self.timeout)
        elif self.engine == 'zhidaotree':
            self.result = zhidao_tree(self.question, self.answer, timeout=self.timeout)
        elif self.engine == 'speaker':
            speakword(self.answer)
        else:
            self.result = zhihu_count(self.question, self.answer,delword=self.delword, timeout=self.timeout)
    def get_result(self):
        return self.result

def speakword(word):
    pythoncom.CoInitialize()
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Speak(word)

def speak(word):
    thds = SearchThread(0, word, 0, 0, 'speaker')
    thds.setDaemon(True)
    thds.start()

def main():
    args = parse_args()
    timeout = args.timeout

    speak("欢迎使用答题辅助器！")
    print(""" 
    请先选择您是否需要开启Chrome浏览器辅助
    它可以帮助您展示更多信息，但是也会降低结果匹配效率
    输入 1 开启，输入 2 不开启，输入其它默认不开启。
    """)
    chrome_sw = input("请输入数字: ")
    if chrome_sw == "1":
        enable_chrome = True
    elif chrome_sw == "2":
        enable_chrome = False
    else:
        enable_chrome = False

    if enable_chrome:
        closer = Event()
        noticer = Event()
        closer.clear()
        noticer.clear()
        reader, writer = Pipe()
        browser_daemon = multiprocessing.Process(
            target=run_browser, args=(closer, noticer, reader,))
        browser_daemon.daemon = True
        browser_daemon.start()

    def __inner_job():
        global isNegativeQuestion,origQuestion
        start = time.time()
        if game_platform==2:
            text_binary = analyze_current_screen_text(
                directory=data_directory,
                compress_level=image_compress_level[0],
                crop_area = crop_areas[game_type]
            )
        else:
            text_binary = analyze_current_screen_text_ios(
                directory=data_directory,
                compress_level=image_compress_level[0],
                crop_area=crop_areas[game_type]
            )
        keywords = get_text_from_image(
            image_data=text_binary,
        )
        if not keywords:
            print("本题不能识别，请尽快自行作答！")
            return

        true_flag, real_question, question, answers = parse_question_and_answer(keywords)
        orig_answer = answers
        # 分词预处理
        allanswers = ''
        optioncount = 0
        isNewAlgUsable = False
        for i in answers:
            allanswers = allanswers + i
            optioncount += 1
        repeatanswers = get_repeat_num_seq(allanswers)
        maxlen = 0
        delword = '' # 预分词目标：找到选项中的重复部分，提升选项之间的差异性
        if optioncount>=3:
            isNewAlgUsable = True
        if isNewAlgUsable:
            for (d,x) in repeatanswers:
                if x>=3 and len(d)>maxlen:
                    maxlen = len(d)
                    delword = d

        print("")
        print("*" * 40)
        print('题目： ' + origQuestion)
        print("*" * 40)

        # notice browser
        if enable_chrome:
            writer.send(question)
            noticer.set()

        search_question = pre_process_question(question)
        search_question_1 = search_question + " " + answers[0].replace(delword,"")
        search_question_2 = search_question + " " + answers[1].replace(delword,"")
        search_question_3 = search_question + " " + answers[2].replace(delword,"")
        thd1 = SearchThread(search_question, answers, timeout, delword, 'baidu')
        thd2 = SearchThread(search_question, answers, timeout, delword, 'bing')
        thd3 = SearchThread(search_question, answers, timeout, delword, 'zhihu')
        thd7 = SearchThread(search_question, answers, timeout, delword, 'so')
        if isNewAlgUsable:
            thd4 = SearchThread(search_question_1, answers, timeout, delword, 'baidu', numofquery=10)
            thd5 = SearchThread(search_question_2, answers, timeout, delword, 'baidu', numofquery=10)
            thd6 = SearchThread(search_question_3, answers, timeout, delword, 'baidu', numofquery=10)

        # 创立3并发线程
        if __name__ == '__main__':
            thd1.setDaemon(True)
            thd1.start()
            thd2.setDaemon(True)
            thd2.start()
            thd3.setDaemon(True)
            thd3.start()
            thd7.setDaemon(True)
            thd7.start()
            if isNewAlgUsable:
                thd4.setDaemon(True)
                thd4.start()
                thd5.setDaemon(True)
                thd5.start()
                thd6.setDaemon(True)
                thd6.start()
            # 顺序开启3线程
            thd1.join()
            thd2.join()
            thd3.join()
            thd7.join()
            if isNewAlgUsable:
                thd4.join()
                thd5.join()
                thd6.join()
            # 等待3线程执行结束
        summary = thd1.get_result()
        summary2 = thd2.get_result()
        summary3 = thd3.get_result()
        summary7 = thd7.get_result()
        if isNewAlgUsable:
            summary4 = thd4.get_result()
            summary5 = thd5.get_result()
            summary6 = thd6.get_result()
        # 获取线程执行结果

        # 下面开始合并结果并添加可靠性标志
        creditFlag = True
        credit = 0
        summary_t = summary
        for i in range(0,len(summary)):
            summary_t[answers[i]] += summary2[answers[i]]
            #summary_t[answers[i]] += summary3[answers[i]]
            summary_t[answers[i]] += summary7[answers[i]]
            credit += summary_t[answers[i]]
        if credit < 2:
            creditFlag = False
        if isNegativeQuestion == False:
            summary_li = sorted(summary_t.items(), key=operator.itemgetter(1), reverse=True)
        else:
            summary_li = sorted(summary_t.items(), key=operator.itemgetter(1), reverse=False)

        if isNewAlgUsable:
            summary_newalg = dict()
            a = ((summary_t[orig_answer[0]]) + (summary4[orig_answer[0]]+0.1)) * ((summary5[orig_answer[0]] + summary6[orig_answer[0]])+0.1)
            b = ((summary_t[orig_answer[1]]) + (summary5[orig_answer[1]]+0.1)) * ((summary4[orig_answer[1]] + summary6[orig_answer[1]])+0.1)
            c = ((summary_t[orig_answer[2]]) + (summary6[orig_answer[2]]+0.1)) * ((summary4[orig_answer[2]] + summary5[orig_answer[2]])+0.1)
            a = "%.2f" % a
            b = "%.2f" % b
            c = "%.2f" % c
            summary_newalg.update({orig_answer[0]: float(a)})
            summary_newalg.update({orig_answer[1]: float(b)})
            summary_newalg.update({orig_answer[2]: float(c)})

        data = [("选项", "权重", "相似度")]
        topscore = 0
        for ans, w in summary_li:
            if w > topscore:
                topscore = w
        for ans, w in summary_li:
            if isNegativeQuestion==False:
                data.append((ans, w, summary_newalg[ans]))
            else:
                data.append((ans, topscore-w, summary_newalg[ans]))
        table = AsciiTable(data)
        print(table.table)
        print("")

        end = time.time()
        print("分析结果 耗时 {0} 秒 听语音更靠谱".format("%.1f" % (end - start)))
        print("*" * 40)
        print("")
        if creditFlag == False:
            print("     ！！！ 本题预测结果不是很可靠，请慎重  ！！！")
        if isNegativeQuestion==True:
            print("     --- 本题是否定提法，程序已帮您优化结果！ ---")
        if true_flag:
            print("      √ 混合算法建议 ： ", summary_li[0][0],' (第',orig_answer.index(summary_li[0][0])+1,'项)')
        else:
            print("      √ 混合算法建议 ： ", summary_li[0][0])

        # 测试：新匹配算法
        if isNewAlgUsable:
            if isNegativeQuestion == False:
                summary_li2 = sorted(summary_newalg.items(), key=operator.itemgetter(1), reverse=True) #True
            else:
                summary_li2 = sorted(summary_newalg.items(), key=operator.itemgetter(1), reverse=False) #False
            print("      √ 关联算法建议 ：  ", summary_li2[0][0],' (第',orig_answer.index(summary_li2[0][0])+1,'项)')
            if orig_answer.index(summary_li2[0][0]) == orig_answer.index(summary_li[0][0]) and creditFlag==True:
                print("      √ 【 双算法解答一致，选择 第",orig_answer.index(summary_li[0][0])+1,"项 答案 ！】")
                speak("第{}项{}".format(orig_answer.index(summary_li[0][0])+1,summary_li[0][0]))
                print("      ×   排除选项  ：  ", summary_li2[-1][0])
            elif creditFlag==False:
                speak("谨慎第{}项谨慎".format(orig_answer.index(summary_li2[0][0]) + 1))
                print("      ×   排除选项  ：  ", summary_li2[-1][0])
            else:
                speak("谨慎第{}项谨慎".format(orig_answer.index(summary_li2[0][0]) + 1))
                print("      ×   排除选项  ：  ", summary_li[-1][0])
        else:
            speak("谨慎第{}项谨慎".format(orig_answer.index(summary_li[0][0])+1))
            print("选项识别有些问题，新算法此题未开启")
            print("      ×   排除选项  ：  ", summary_li[-1][0])


        # 输出知识树
        thdtree = SearchThread(search_question, answers, timeout, delword, 'zhidaotree')
        thdtree.setDaemon(True)
        thdtree.start()
        thdtree.join()
        summary_tree = thdtree.get_result()
        print("")
        print("")
        print("辅助知识树")
        print("*" * 40)
        for ans in summary_tree:
            print(ans)

        save_screen(
            directory=data_directory
        )

    print("""
    原作者：GitHub/smileboywtu forked since 2018.01.10
    Branch版本：V4.0    Branch作者：GitHub/leyuwei
    Branch改进： 修正提问问题的判断，新增语音播报！
                修正正则过滤表达式，优化结果显示效果，新增分词
                Chrome浏览器开启自定义，(* 测试)全新匹配算法
                
    请选择答题节目: 
      1. 百万英雄    2. 冲顶大会
    """)
    game_type = input("输入游戏编号: ")
    if game_type == "1":
        game_type = '百万英雄'
    elif game_type == "2":
        game_type = '冲顶大会'
    else:
        game_type = '百万英雄'

    print("""
    操作平台的一些说明：如果您是iOS，则必须使用您的电脑创建WiFi热点并将您的iOS设备连接到该热点，
                      脚本即将为您打开投屏软件，您需要按照软件的提示进行操作。
                      如果您使用的是Android则无需担心，将您的设备使用数据线连接电脑，开启Adb
                      调试即可正常使用该脚本。
    请选择您的设备平台：
            1. iOS
            2. Android
    """)

    game_platform = input("输入平台编号: ")
    if game_platform == "1":
        game_platform = 1
        if check_exsit()==0:
            print("正在唤醒投屏软件，请同意管理员权限并按照软件要求将您的iOS设备投放在电脑屏幕上，最后再回到该脚本进行操作。")
            win32api.ShellExecute(0, 'open', 'airplayer.exe', '', '', 0)
        else:
            print("投屏软件已经启动。")
    elif game_platform == "2":
        game_platform = 2
    else:
        game_platform = 1

    while True:
        print("""
    -----------------------------
    请在答题开始前运行程序，
    答题开始的时候按Enter预测答案
                """)

        enter = input("按Enter键开始，按ESC键退出...")
        if enter == chr(27):
            break
        try:
            __inner_job()
        except Exception as e:
            print("截图分析过程中出现故障，请确认设备是否连接正确（投屏正常），网络是否通畅！")
            speak("出现问题！")

    if enable_chrome:
        reader.close()
        writer.close()
        closer.set()
        time.sleep(3)


if __name__ == "__main__":
    main()
