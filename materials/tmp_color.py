# -*- coding : utf-8-*-
'''
对图像进行压缩的软件
@Authors:
    Alla, ytding, yxDu, hWu, yjMa
@class
    CompressPic 压缩图片的过程
    Process 图像处理过程：将图片和np.ndarray间转换，保存图片和预览

!!Attention!!
如果修改了函数的输入输出，请在注释中写明
因为没写过这个软件的完整版，多有疏漏，请多包涵qwq
'''
import sys
import os
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
import time
import cv2  # pip install opencv-python==4.5.4.58 -i https://pypi.douban.com/simple
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
'''
     5/8 改动部分：
        class CompressPic()中：
        添加成员变量color和彩色图像压缩compressColor()模块
        getSnakeOrder()添加了color变量值更新相关部分，返回变化snake_order=[[b,g,r], ..., [b,g,r]];
        length();
        compress()中参数p相关的语句;
        compressPic()添加了彩色图像压缩部分；
'''


'''
图像压缩类
@params
    in_pic_array(np.ndarray类型) 输入的512*512灰度图像转为的数组
@return
    compress_rate 压缩效率(getCompressRate函数)
    running_time 执行时间(getRunningTime函数)
'''


class CompressPic():
    def __init__(self, input_pic=None) -> None:
        self.input_pic = input_pic
        self.N = 512
        self.n = 512 * 512 + 1
        self.compress_rate = None
        self.running_time = None
        self.min_length = None
        self.aver_bit = None
        self.color = 0 # 5/8 20yjma添加 用于判断图像是彩色/灰度图，默认0（灰度图）

    '''
        5/8 修改by20yjma:添加了图像是否是彩色的记号变量self.color的更新
        获得蛇形序列函数
    @return
        snake_order(list) 512*512灰度图像转为的数组的一维蛇形序列
    '''

    def getSnakeOrder(self):
        snake_order = []  # 创建一个空列表，用于存储输出结果
        snake_order.append([0, 0, 0])  # 下标从1开始
        flag = 1  # 用于控制蛇形输出的方向
        # 遍历图像的每一行
        for i in range(self.N):
            # 如果方向标志为1，则从左往右遍历该行的像素
            if flag == 1:
                for j in range(self.N):
                    snake_order.append((self.input_pic[i][j]).tolist())  # 将该像素添加到输出数组中
                    if self.color == 0 and len(set(self.input_pic[i][j])) != 1:
                        self.color = 1
                flag -= 1  # 改变方向标志，以便下一行从右往左遍历
            # 如果方向标志为-1，则从右往左遍历该行的像素
            else:
                for j in range(self.N - 1, -1, -1):
                    snake_order.append((self.input_pic[i][j]).tolist())  # 将该像素添加到输出数组中
                    if self.color == 0 and len(set(self.input_pic[i][j])) != 1:
                        self.color = 1
                flag += 1  # 改变方向标志，以便下一行从左往右遍历
        return snake_order  # 返回包含所有像素的数组

    '''
        计算像素值所需要的存储位数，即存储i，至少需要k位
        @params 
            i  像素值
        @return
            k 像素点所需要的存储位数
            '''

    def length(self,i):
        k = 1
        i = i / 2
        while i > 0:
            k += 1
            i = i // 2
        return k

    '''
        5/8 修改by20yjma: p[i]是存储第i个像素点像素值所需的最小位数
        基于动态规划的图像压缩算法
        @params 
            n  像素点的个数+1
            p(np.ndarray) 512*512灰度图像转为的数组的一维蛇形序列
            s(list)  s[i]记录前i个数字的最优处理方式得到的最优解
            b(list)  b[i]记录第i段每个像素的位数
            l(list)   l[i]记录第i段有多少个像素
        @return
            s(list)
        '''
    def compress(self, n, p, s, b, l):
        lmax = 256  # 每段所包含元素的最大个数
        header = 11  # 段首大小
        start_time = time.time()  # 记录开始执行时间
        s[0] = 0
        for i in range(1, n+1):
            b[i] = p[i]
            bmax = b[i]
            s[i] = s[i - 1] + bmax
            l[i] = 1
            for j in range(2, lmax + 1):
                if j <= i:
                    if bmax < p[i - j + 1]:
                        bmax = p[i - j + 1]
                    if s[i] > s[i - j] + j * bmax + header:
                        s[i] = s[i - j] + j * bmax + header
                        l[i] = j
                        b[i] = bmax
        self.running_time = time.time() - start_time
        input_size = 512 * 512 * 8
        output_size = s[self.n-1]
        self.compress_rate = 1-output_size / input_size
        return s

    '''
        计算压缩后有多少段
         @params 
            n  像素点的个数+1
            b(list)  b[i]记录第i段每个像素的位数
            l(list)   l[i]记录第i段有多少个像素
        @return
            i-1  压缩后的段数
    '''
    def traceBack(self, n, l, b):
        stack = []
        stack.append(l[n])
        stack.append(b[n])
        while n != 0:
            n = n - l[n]
            stack.append(l[n])
            stack.append(b[n])
        i = 0
        while len(stack) > 0:
            b[i] = stack[-1]
            stack.pop()
            l[i] = stack[-1]
            stack.pop()
            i += 1
        return i - 1

    '''
        将压缩信息输出到output/result.txt文件中
    '''

    def out(self, m, min_len, l, b):
        i = 0
        # 获取当前文件的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
        # 整合txt文件
        txt_path = os.path.join(base_path, 'result.txt')
        f = open(txt_path, "w+")
        self.min_length = min_len
        self.aver_bit = min_len / (512 * 512)
        f.write("the minimal length：" + str(min_len) + "\n")
        f.write("the average of bits each pixel needed to store：" + str(min_len / (512 * 512)) + "\n")
        f.write("the whole number of segments:" + str(m) + "\n")
        for i in range(i + 1, m + 1):
            f.write("the " + str(i) + " segment" + str(l[i]) + "elements\t\t" + "which need to: " + str(b[i]) + " bit(s)\n")
        f.close()

    '''
        5/8 修改：加入彩色图像压缩部分
        对图像进行压缩
    '''

    def compressPic(self):
        if self.input_pic is None:
            raise ValueError("Input picture is not provided")
        img_list = self.getSnakeOrder()  # 图像 RGB(list)
        s = [0] * self.n  # 记录前i个数字的最优处理方式得到的最优解
        b = [0] * self.n  # 记录第i段每个像素的位数
        l = [0] * self.n  # 记录第i段有多少个像素
        p =[]
        # 灰度图压缩
        if self.color == 0:
            print("开始进行灰度图片压缩")
            for pix in img_list:
                p.append(self.length(pix[0]))  # 获取每个像素点，灰度值存储所需位数的列表p
            # p = [0, 255, 1, 5, 2, 1, 2]  # test
            # print("图像的灰度序列为：")
            # for i in range(1, self.n):
            #     print(str(p[i]) + " ")
            s = self.compress(self.n-1, p, s, b, l)
            m = self.traceBack(self.n-1, l, b)
            self.out(m, s[self.n - 1], l, b)
        if self.color == 1:
            print("开始进行彩色图片压缩")
            color_p = []
            for pix in img_list:
                color_p.append(3*(self.length(max(pix))))
            s = self.compressColor(self.n-1, color_p, s, b, l)
            m = self.traceBack(self.n-1,l,b)
            self.out(m, s[self.n-1], l, b)

    '''
        返回压缩效率
    '''

    def getCompressRate(self):
        return self.compress_rate

    '''
        返回压缩算法执行时间
    '''

    def getRunningTime(self):
        return self.running_time

    def getminlen(self):
        return self.min_length

    def getaverbit(self):
        return self.aver_bit

    '''
            compressColor()    彩色图像压缩方法
            p=[ [b,g,r], ..., [b,g,r] ]
    '''
    def compressColor(self, n, p, s, b, l):
        start_time = time.time()
        lmax = 512 # 每段所包含像素的最大个数
        header = self.length(lmax)+self.length(max(p))
        s[0] = 0
        for i in range(1, n+1):
            b[i] = p[i]
            bmax = b[i]
            s[i] = s[i - 1] + bmax
            l[i] = 1
            for j in range(2, lmax + 1):
                if j <= i:
                    if bmax < p[i - j + 1]:
                        bmax = p[i - j + 1]
                    if s[i] > s[i - j] + j * bmax+header:
                        s[i] = s[i - j] + j * bmax + header
                        l[i] = j
                        b[i] = bmax
        self.running_time = time.time() - start_time
        # print("compress l array：")
        # print(l)
        # print("b array：")
        # print(b)
        # print("s array: ")
        # print(s)
        input_size = 512 * 512 * 24
        output_size = s[n]
        self.compress_rate = 1-output_size / input_size
        return s


'''
    功能入口
'''

'''
    UI类
'''


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 700)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        # self.pushButton.setGeometry(QtCore.QRect(30, 50, 121, 51))
        # self.pushButton.setObjectName("pushButton")

        self.pushButton_compress = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_compress.setGeometry(QtCore.QRect(30, 170, 121, 51))
        self.pushButton_compress.setObjectName("pushButton_compress")

        self.pushButton_saveImage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_saveImage.setGeometry(QtCore.QRect(30, 300, 121, 51))
        self.pushButton_saveImage.setObjectName("pushButton_saveImage")

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(40, 410, 91, 41))
        self.label.setObjectName("label")

        # self.label_imagethen = QtWidgets.QLabel(self.centralwidget)
        # self.label_imagethen.setGeometry(QtCore.QRect(1000, 40, 512, 512))
        # self.label_imagethen.setFrameShape(QtWidgets.QFrame.Box)
        # self.label_imagethen.setObjectName("label_imagethen")
        # self.label_imagethen.setScaledContents(True)  # 图片填充整个框

        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(40, 480, 91, 41))
        self.label_2.setObjectName("label_2")

        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(120, 415, 191, 31))
        self.textBrowser.setObjectName("textBrowser")

        self.textBrowser_2 = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser_2.setGeometry(QtCore.QRect(160, 485, 191, 31))
        self.textBrowser_2.setObjectName("textBrowser_2")

        self.label_image = QtWidgets.QLabel(self.centralwidget)
        self.label_image.setGeometry(QtCore.QRect(450, 40, 512, 512))
        self.label_image.setFrameShape(QtWidgets.QFrame.Box)
        self.label_image.setObjectName("label_image")
        self.label_image.setScaledContents(True)  # 图片填充整个框

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # self.pushButton.clicked.connect(self.openImage)

        self.label_imagePath = QtWidgets.QLabel(self.centralwidget)
        # self.label_imagePath.setGeometry(QtCore.QRect(570, 60, 150, 100))
        self.label_imagePath.setObjectName("label_imagePath")
        self.label_imagePath.setWordWrap(True)

        self.pushButton_saveImage.clicked.connect(self.saveImage)
        self.pushButton_compress.clicked.connect(self.compress)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        # self.pushButton.setText(_translate("MainWindow", "选择图片"))
        self.pushButton_compress.setText(_translate("MainWindow", "开始压缩"))
        self.pushButton_saveImage.setText(_translate("MainWindow", "保存图片"))
        self.label.setText(_translate("MainWindow", "最小长度"))
        # self.label_imagethen.setText(_translate("MainWindow", "压缩后预览"))
        self.label_2.setText(_translate("MainWindow", "平均每个像素所需要的存储位数"))
        self.label_image.setText(_translate("MainWindow", "压缩后浏览"))  # 其实是前

    def openImage(self):  # 选择本地图片上传
        global imgName  # 这里为了方便别的地方引用图片路径，我们把它设置为全局变量
        imgName, imgType = QFileDialog.getOpenFileName(self.centralwidget, "打开图片", "",
                                                       "*.jpg;;*.png;;All Files(*)")  # 弹出一个文件选择框，第一个返回值imgName记录选中的文件路径+文件名，第二个返回值imgType记录文件的类型
        jpg = QtGui.QPixmap(imgName).scaled(self.label_image.width(),
                                            self.label_image.height())  # 通过文件路径获取图片文件，并设置图片长宽为label控件的长宽
        self.label_image.setPixmap(jpg)  # 在label控件上显示选择的图片
        self.label_imagePath.setText(imgName)  # 显示所选图片的本地路径
        return imgName

    def saveImage(self):  # 保存图片到本地
        screen = QApplication.primaryScreen()
        pix = screen.grabWindow(self.label_image.winId())
        fd, type = QFileDialog.getSaveFileName(self.centralwidget, "保存图片", "", "*.jpg;;*.png;;All Files(*)")
        pix.save(fd)

    def printf(self, mes):
        self.textBrowser.append(mes)  # 在指定的区域显示提示信息
        self.cursot = self.textBrowser.textCursor()
        self.textBrowser.moveCursor(self.cursot.End)
        # QtWidgets.QApplication.processEvents()

    def printf2(self, mes2):
        self.textBrowser_2.append(mes2)  # 在指定的区域显示提示信息
        self.cursot2 = self.textBrowser.textCursor()
        self.textBrowser.moveCursor(self.cursot2.End)

    def compress(self):  # 压缩图片
        self.openImage()
        print(imgName)
        img = cv2.imread(imgName)
        test = CompressPic(img)
        test.compressPic()  # 调用算法进行压缩，压缩结果保存在output/result.txt文件中
        compress_rate = test.getCompressRate()  # 获取压缩效率
        running_time = test.getRunningTime()  # 获取执行时间
        min_length = test.getminlen()
        aver_bit = test.getaverbit()
        print("压缩算法压缩效率：" + str(compress_rate))
        print("压缩算法执行时间：" + str(running_time))
        print("最小长度：" + str(min_length))
        print("平均每个像素：" + str(aver_bit))
        Ui_MainWindow.printf(self, str(min_length))
        Ui_MainWindow.printf2(self, str(aver_bit))


if __name__ == '__main__':
    # 执行ui界面
    app = QtWidgets.QApplication(sys.argv)
    formObj = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(formObj)
    formObj.show()
    sys.exit(app.exec_())

    # compress test
    # img = cv2.imread(imgName, 0)
    # # print("img array: ")
    # # print(img)
    # # np.savetxt("output/beforeCompress.txt", img, fmt='%d', delimiter=',')
    #
    # # 压缩调用示例如下
    # test = CompressPic(img)
    # test.compressPic()   # 调用算法进行压缩，压缩结果保存在output/result.txt文件中
    # compress_rate = test.getCompressRate()  # 获取压缩效率
    # running_time = test.getRunningTime()  # 获取执行时间
    # print("压缩算法压缩效率：" + str(compress_rate))
    # print("压缩算法执行时间：" + str(running_time))
