# -*- coding: utf-8 -*-
"""
Created on Thu Aug  2 08:22:40 2018

@author: lufei
"""
from selenium import webdriver
import time, pytesseract, os, pickle
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from urllib.request import quote
import pandas as pd

def login_with_account(account_path, cookies_path):
    """手机验证登录获取cookies， 需要账号文件路径和cookies文件存放路径"""
    global browser
    # 获取账号
    def get_account(account_path):
        account = []
        try:
            with open(account_path, encoding='UTF-8') as fileaccount:
                accounts = fileaccount.readlines()
                for acc in accounts:
                    account.append(acc.strip())
            return account
        except Exception as err:
            print(err)
            print("请正确在account.txt里面写入账号密码")
            exit()
    account = get_account(account_path)
    # 以豆浆机为例，模拟登陆
    keyword = "豆浆机".encode("gbk")
    browser = webdriver.Chrome()
    browser.get("http://index.baidu.com/?tpl=trend&word=" + quote(keyword))
    # 账号密码登陆
    browser.find_element_by_id("TANGRAM__PSP_4__userName").clear()
    browser.find_element_by_id("TANGRAM__PSP_4__password").clear()
    browser.find_element_by_id("TANGRAM__PSP_4__userName").send_keys(account[0])
    browser.find_element_by_id("TANGRAM__PSP_4__password").send_keys(account[1])
    browser.find_element_by_id("TANGRAM__PSP_4__submit").click()
    time.sleep(5)
    # 手机验证，并发送手机验证码
    browser.find_element_by_id("TANGRAM__14__button_send_mobile").click()
    mobile = input("请输入手机验证码:")
    browser.find_element_by_id("TANGRAM__14__input_vcode").send_keys(mobile)
    browser.find_element_by_id("TANGRAM__14__button_submit").click()
    time.sleep(5)
    cookies = browser.get_cookies()
    time.sleep(5)
    # 保存cookies文件
    with open(cookies_path, "wb") as f:
        pickle.dump(cookies, f)

def login_with_cookies(cookies_path):
    """读取已保存的cookies文件实现免登录"""
    try:
        global browser
        browser = webdriver.Chrome()
        browser.get("http://index.baidu.com")
        browser.maximize_window()
        # 读取cookies文件
        with open(cookies_path, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            browser.add_cookie(cookie)
        browser.refresh()
        print("已加载cookies文件")
    except:
        print("加载cookies文件失败")

def search_by_keyword(keyword, next_=False):
    """在搜索框中输入关键词"""
    if not next_:
        browser.get("http://index.baidu.com/?tpl=trend&word="+quote(keyword[0].encode("gbk")))
    else:
        # 在搜索框中重新输入下一个关键词
        browser.find_element_by_id("schword").clear()
        browser.find_element_by_id("schword").send_keys(keyword)
        browser.find_element_by_id("schsubmit").click()
# =============================================================================
#         # 添加对比词的输入框(auto_gsid_16)id号从16开始
#         id_ = 16
#         for word in keyword[1:]:
#             browser.find_element_by_xpath('//*[@id="adv_pannel"]/div/div[2]/div[1]/a[2]').click()
#             browser.find_element_by_id("auto_gsid_{}".format(id_)).send_keys(word)
#             id_ += 1
#         browser.find_element_by_id("advSearchSubmit").click()
# =============================================================================
        
def select_day(day):
    """构造天数，半年为180天，全部为1000000天"""
    day_dict = {1:'//*[@id="auto_gsid_15"]/div[2]/div[1]/a[1]',
                7:'//*[@id="auto_gsid_15"]/div[2]/div[1]/a[2]',
                30:'//*[@id="auto_gsid_15"]/div[2]/div[1]/a[3]',
                90:'//*[@id="auto_gsid_15"]/div[2]/div[1]/a[4]',
                180:'//*[@id="auto_gsid_15"]/div[2]/div[1]/a[5]',
                1000000:'//*[@id="auto_gsid_15"]/div[2]/div[1]/a[6]'}
    try:    
        browser.find_element_by_xpath(day_dict[day]).click()
    except:
        print("天数标签元素定位失败，等待5秒后再次定位")
        browser.refresh()
        time.sleep(5)
        select_day(day)
        
def create_folder(keyword):
    """创建存放截图的文件夹，以关键字命名"""
    try:
        folder = "_".join(keyword)
        if not os.path.exists(folder):
            os.mkdir(folder)
            print("文件夹创建成功")
        else:
            print("已存在 {} 文件夹".format(folder))
        return folder
    except:
        print("文件夹创建失败")
        return False

def positioning_screenshot(day, folder):
    """确定趋势图的位置后，从初始点开始平移，每走一小步就截屏，然后把包含指数信息的小黑框截出来"""
    # 每次的位移量，由天数确定
    move_by_day = {7: 202.33, 
                   30: 41.68, 
                   90: 13.64, 
                   180: 6.78,
                   1000000:3.37222222}
    # 定位到趋势图位置
    try:
        xoyelement = browser.find_elements_by_css_selector("#trend rect")[2]
        #xoyelement = browser.find_elements_by_xpath('//*[@id="trend"]/svg/rect[4]')
    except:
        print("定位失败")
        return False
    # 初始坐标
    x_0 = 1
    y_0 = 0
    num = 0
#    try:
    for i in range(day):
        ActionChains(browser).move_to_element_with_offset(xoyelement, x_0, y_0).perform()
        # 鼠标移动
        x_0 += move_by_day[day]
        # 留给页面的反应时间，看情况调
        time.sleep(3)
        # 找到图片并记录坐标
        imgelement = browser.find_element_by_xpath('//div[@id="viewbox"]')
        locations = imgelement.location
        # 找到图片大小
        sizes = imgelement.size
        # 构造图片位置
        range_ = (locations['x'], locations['y'],
                  locations['x'] + sizes['width'], locations['y'] + sizes['height'])
        # 截取当前浏览器内容
        browser.save_screenshot(folder + "/" + str(num) + ".png")
        # 打开截图切割，后缀名加上_t区分
        img = Image.open(folder + "/" + str(num) + ".png")
        png = img.crop(range_)
        png.save(folder + "/" + str(num) + "_t.png")
        num += 1
# =============================================================================
#     except:
#         print("截图失败")
#     print("共截取 {} 张".format(num+1))
# =============================================================================
        

# =============================================================================
# # 保存截图后的小图片
# t_folder = "T_" + keyword + "/"
# if not os.path.exists(t_folder):
#     os.mkdir(t_folder)
# =============================================================================

def image_identification(folder, day, save=False, sub_p_save=False, data_pro=True):
    """从文件夹中获取viewbox图片（文件名以_t.csv结尾），识别图片中的日期，指数"""
    list_p = [_ for _ in os.listdir(folder) if _.endswith("_t.png")]
    date_ = []
    index_ = []
    n = 0
    for p in list_p:
        image = Image.open(folder + "/" + p)
        # 将图片扩大一倍
        size = image.size
        key_len = len(folder) * 12.5 + 30
        x_s = 146
        y_s = 58
        # 日期截图
        date_range = (0, 0, 75, size[1]/2)
        date = image.crop(date_range).convert("L")
        date = date.resize((x_s, y_s), Image.ANTIALIAS)
        if sub_p_save:
            date.save(folder + "/" + str(n) + "_td.png")
        # 指数截图
        index_range = (key_len, size[1]/2, key_len + 50, size[1])
        index = image.crop(index_range).convert("L")
        index = index.resize((x_s, y_s), Image.ANTIALIAS)
        if sub_p_save:
            index.save(folder + "/" + str(n) + "_ti.png")
        code_p = pytesseract.image_to_string(index, config="digits")
        code_d = pytesseract.image_to_string(date, config="digits")
        index_.append(code_p)
        date_.append(code_d)
        n += 1
        print("{} 已完成".format(p))
        
    data = pd.DataFrame({"date":date_, "index":index_})

    # 指数处理
    def index_pro(s):
        res = []
        for i, c in enumerate(s):
            if c == "?" or ((c == "3" and i != 0) and s[i-1] == "—"):
                res.append("7")
            elif (c == "3" and i != 0) and s[i-1] == "‘":
                res.append("9")
            elif c == "B" or (((c == "!" or c == "I") and i != 0) and s[i-1] == "E"):
                res.append("8")
            elif c == "S":
                res.append("5")
            elif ((c == ":" or c == ")") and i != 0) and s[i-1] == "E":
                res.append("6")
            elif c == "O":
                res.append("O")
            elif c.isdigit():
                res.append(c)
        return "".join(res)
    
    # 日期处理
    def date_pro(d):
        res = []
        d = d.replace("—", "-")
        for c in d:
            if c.isdigit() or c == "-":
                res.append(c)
        return "".join(res)
    
    if data_pro:
        # 删掉日期为空的行
        data.drop(data[data.date == ''].index, axis=0, inplace=True)
        data["index"] = data["index"].apply(index_pro)
        data["date"] = data.date.apply(date_pro)
        data.sort_values(by="date", inplace=True)
    if save:
        # 保存csv文件，命名规则如下 豆浆机近30天指数.csv
        file_name = "{}近{}天指数.csv".format(folder, day)
        data.to_csv(file_name, encoding="gbk", index=False)
        print("{} 已保存".format(file_name))
    return data

def main(keyword):
    res = {}
    for i, word in enumerate(keyword):
        if i > 0:
            search_by_keyword([word], next_=True)
        else:
            search_by_keyword([word])            
        create_folder([word])
        time.sleep(10)
        select_day(day)
        time.sleep(5)
        folder = create_folder([word])
        if folder:
            positioning_screenshot(day, folder)
            time.sleep(5)
            data = image_identification(folder, day, True)
        res[word] = data
    return res

if __name__ == "__main__":
    start = time.time()
    account_path = ""
    cookies_path = "E:/lufei/baidu_index/cookies.pkl"
    old_path = "指数数据"
    old_csv = [c[:-4] for c in os.listdir(old_path)]
    keyword_dict = {7:[],
                    30:old_csv,
                    90:[],
                    180:[]
                    }
    for day in [30]:
        login_with_cookies(cookies_path)
        keyword = keyword_dict[day]
        data = main(keyword)
    end = time.time()    
    print("总共耗时: {}分钟".format((end-start)/60))
    
# =============================================================================
#     # 重新识别
#     temp = {}
#     day = 90
#     keyword = ["电磁炉", "九阳电炖锅"]
#     for word in keyword:
#         data = image_identification(word, day, data_pro=False)
#         temp[word] = data
# =============================================================================
    
