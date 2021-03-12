# -*- coding: utf-8 -*-
import os, sys, traceback
from threading import Thread

import requests
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextBrowser
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon

response = None


# 继承QThread，重写run方法，包含自定义信号，在子线程中修改控件信息
class MySingal(QObject):
    text_print = pyqtSignal(QTextBrowser, str)


# GUI
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        # 导入ui
        cwd = os.getcwd()
        ui_path = os.path.join(cwd, r'resources\httptest.ui')
        ico_path = os.path.join(cwd, r'resources\httptest.png')
        loadUi(ui_path, self)
        self.setWindowIcon(QIcon(ico_path))

        # 导入自定义信号
        self.ms = MySingal()
        # 请求附带消息模式
        self.staue = 'params'
        # 控件响应
        self.ui.buttonsend.clicked.connect(self.sendRequest)
        self.ui.buttonadd.clicked.connect(self.addOneHeader)
        self.ui.buttondel.clicked.connect(self.delOneHeader)
        self.ui.RadioGroup.buttonClicked.connect(self.checkparam)
        self.ui.buttonclear.clicked.connect(self.cleanResponse)
        self.ms.text_print.connect(self.printToGui)

    def sendRequest(self):
        # 禁用发送按钮
        self.ui.buttonsend.setEnabled(False)

        method = self.ui.boxMethod.currentText()
        url = self.ui.editUrl.text()
        headers = {}
        rowcount = self.ui.tableHeader.rowCount()
        if rowcount > 0:
            for onerow in range(rowcount):
                key = self.ui.tableHeader.item(onerow, 0).text()
                value = self.ui.tableHeader.item(onerow, 1).text()
                if key.strip() == '' or value.strip() == '':
                    break
                headers[key] = value
        if len(headers) == 0:
            headers = None
        payload = self.ui.editParam.toPlainText()
        if payload.strip() == '':
            payload = None
        else:
            payload = eval(payload)

        s = requests.Session()
        req = requests.Request()
        if self.staue == 'params':
            req = requests.Request(method, url, headers=headers, params=payload)
        elif self.staue == 'data':
            req = requests.Request(method, url, headers=headers, data=payload)
        elif self.staue == 'files':
            req = requests.Request(method, url, headers=headers, files=payload)
        elif self.staue == 'json':
            req = requests.Request(method, url, headers=headers, json=payload)
        prepared = s.prepare_request(req)

        # 刷新ui线程
        self.pretty_print_request(prepared)

        # 创建新的线程去执行发送方法，
        # 服务器慢，只会在新线程中阻塞
        # 不影响主线程

        request_thread = Thread(target=self.threadSend, args=(s, prepared))
        request_thread.setDaemon(True)
        request_thread.start()

    # 新线程入口函数
    def threadSend(self, s, prepared):
        try:
            r = s.send(prepared)
            r.encoding = 'utf-8'
            # print(r)
            self.pretty_print_response(r)
            # 启用发送按钮
            self.ui.buttonsend.setEnabled(True)
        except Exception:
            # print(traceback.format_exc())
            # 启用发送按钮
            self.ms.text_print.emit(self.ui.textresponse, traceback.format_exc())
            self.ui.buttonsend.setEnabled(True)

    # def isresponse(self):

    def addOneHeader(self):
        rowcount = self.ui.tableHeader.rowCount()
        self.ui.tableHeader.insertRow(rowcount)

    def delOneHeader(self):
        currentrow = self.ui.tableHeader.currentRow()
        self.ui.tableHeader.removeRow(currentrow)

    def checkparam(self):
        self.staue = self.ui.RadioGroup.checkedButton().text()

    def cleanResponse(self):
        self.ui.textresponse.clear()

    def printToGui(self, ui, text):
        ui.append(str(text))
        ui.ensureCursorVisible()

    # 格式化打印
    def pretty_print_request(self, req):
        text = '{}\n{}\r\n{}\r\n{}\r\n'.format(
            '-----------Requests-----------',
            'url:' + req.url,
            req,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        )
        # print(text)
        self.ms.text_print.emit(self.ui.textresponse, text)
        return text

    def pretty_print_response(self, req):
        text = '{}\n{}\r\n{}\r\n'.format(
            '-----------Response-----------',
            req,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        ) + '\r\n-----------End-----------\r\n' + req.content.decode('utf-8')
        # print(text)
        self.ms.text_print.emit(self.ui.textresponse, text)
        return text


# Main
if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        mainWindow = MainWindow()
        mainWindow.show()
        sys.exit(app.exec_())
    except Exception:
        print(traceback.format_exc())
