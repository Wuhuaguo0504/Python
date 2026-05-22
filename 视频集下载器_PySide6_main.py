#  -*- coding: utf-8 -*-

import requests
import re, sys
from tqdm import tqdm
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog
import ui_videos_downloader as ui_vd
import Videos_Down
# import PyQtDarkTheme
# import qdarkstyle


# 【逐玉】视频集的起始集的页面地址。【1-40】
"https://www.estland-service.com/play/176201/3/1.html"
"3000k/hls/mixed.m3u8"

# 【庇护之地】电影的页面地址。【1-1】
"https://dlkcyq.com/vodplay/106775-1-1.html"
"index.m3u8"

# 【用武之地】电影的页面地址。【1-1】
"https://dlkcyq.com/vodplay/109329-1-1.html"
"index.m3u8"


# 获取必要信息：【起始集页面地址；起始集编号，结束集编号，需转换的尾串。】
def get_initInfo():
    # 起始集的页面地址
    first_url = ui.lineE_startAddr.text().strip()
    # 起始集的页面地址为空的话，则返回错误
    if not first_url:
        QMessageBox().warning(Form, "提示", "起始地址必须是一个有效的url!")
        return

    # # 通过字符串特征获取分隔符的位置
    # if ui.radioBtn_endash.isChecked():
    #     p1 = first_url.rfind("-")
    # elif ui.radioBtn_slash.isChecked():
    #     p1 = first_url.rfind("/")
    # else:
    #     raise ValueError("请选择分隔符类型")
    #
    # if p1 == -1:
    #     QMessageBox().warning(Form, "提示", "起始地址格式不正确，缺少分隔符")
    #     return
    #
    # p2 = first_url.rfind(".")
    # if p2 == -1 or p2 <= p1:
    #     raise ValueError("起始地址格式不正确，缺少文件扩展名")
    #
    # try:
    #     start_num = int(first_url[(p1 + 1):p2])
    # except ValueError:
    #     raise ValueError("起始集编号必须是数字")

    # 获取起始集编号【通过正则式】
    pattern = r'(\d+)\.html'
    match = re.search(pattern, first_url)
    if match:
        start_num = int(match.group(1))
    else:
        raise ValueError("起始地址格式不正确，缺少分隔符")

    end_num = ui.lineE_endNum.text().strip()
    if not end_num.isdigit():
        raise ValueError("结束集编号必须是数字")

    end_str = ui.lineE_endStr.text().strip()

    return first_url, start_num, int(end_num), end_str


# 获取视频集的页面地址列表
def source_urls(base_url: str, begin=None, end=None) -> list:
    """
    通过视频集的起始集的页面地址，获取后续视频集的页面地址列表【前提是页面地址编号步长为1】，
    base_url：为起始集的页面地址，
    begin：起始集
    end：最后一集。
    """
    # 获取起始集编号的位置
    p = base_url.find(f"{begin}.html")
    if p == -1:
        raise ValueError("无法找到起始集编号的位置")

    # 通过切片获取视频集页面地址通用字符串
    base_url = base_url[:p]
    return list(map(lambda i: f"{base_url}{i}.html", range(begin, end + 1)))

# 获取指定页面的文本
def get_page_txt(url):
    # 指定请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"获取页面文本出错: {e}")
        return


def get_video_url(txt_content):
    """
    从页面文本中提取视频URL
    txt_content：页面文本
    switch：真实下载地址是否需转换，默认为True，即需要转换。
    """
    # pattern1 = r'"url"\s*:\s*"([^"]*)"'
    # match1 = re.search(pattern1, txt_content)

    # specific_pattern = r'"url":"(.*?index\.m3u8)"'
    global end_str
    specific_pattern = ui.lineE_pattern.text()
    match = re.search(specific_pattern, txt_content)

    if match:
        # 处理转义的斜杠
        url = match.group(1).replace('\\', '')
    else:
        print("未匹配到视频URL")
        return None

    # 视频地址尾串为空的话，则直接返回视频地址；否则，将尾串替换为用户输入的尾串
    if not ui.lineE_endStr.text():
        return url
    else:
        return url.replace("index.m3u8", end_str)


def dict_urls(urls):
    """
    获取视频集每一集的真实下载地址列表，并以字典的形式返回结果。
    urls：视频集从起始集至结束集的页面地址列表
    """
    global start_num
    try:
        # 进度条【字典推导式】
        urls_dict = {i: get_video_url(get_page_txt(url)) for i, url in
                    tqdm(enumerate(urls, start=start_num), desc="正在处理")}
        return urls_dict
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return {}


def get_videos_url():
    try:
        global dic, first_url, start_num, end_num, end_str, videos_list
        first_url, start_num, end_num, end_str = get_initInfo()
        urls = source_urls(first_url, start_num, end_num)
        dic = dict_urls(urls)
        ui.listW_videos.addItems([f"{i}. {url}" for i, url in dic.items()])
        videos_list = [(dic[i], f"{ui.lineE_video_name.text()}_{i}.mp4") for i in range(start_num, end_num + 1)]
    except Exception as e:
        QMessageBox.critical(Form, "错误", f"获取视频列表失败：{str(e)}")

    for i in videos_list:
        print(i)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # # 设置深色主题
    # PyQtDarkTheme.setup_theme("dark")

    # # 👇 应用深色主题 (只需这一行)
    # app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside6"))

    Form = QWidget()
    ui = ui_vd.Ui_Form()
    ui.setupUi(Form)

    # Form.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    Form.show()

    # 显示初始化全局变量
    """first_url 起始集的页面地址；start_num 起始集编号；end_num 结束集编号；
    end_str 尾串；dic 视频集每一集的页面地址字典；videos_list 视频集列表[(url,video_name),(url,video_name),...]"""
    first_url = ""
    start_num = 0
    end_num = 0
    end_str = ""
    dic = {}
    videos_list = []

    # 获取视频集列表按钮：信号与槽函数关联
    ui.btn_getVideosList.clicked.connect(get_videos_url)

    # 选择视频保存目录
    ui.lineE_video_path.setText(QFileDialog.getExistingDirectory(Form, "选择视频保存目录"))

    # 下载按钮：若槽函数带有参数，则需要使用lambda函数将参数传递给槽函数
    ui.btn_download.clicked.connect(
        lambda: Videos_Down.batch_download_m3u8(videos_list,
            rf'{ui.lineE_video_path.text()}', resume=True, shutdown=True))
    sys.exit(app.exec())
