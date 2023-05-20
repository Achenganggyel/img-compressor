'''
对图像进行压缩的软件
<<<<<<< HEAD
@Authors:
    Alla, ytding, yxDu, hWu, yjMa
@class
    CompressPic 压缩图片的过程
    UI_MainWindow 界面

!!Attention!!
如果修改了函数的输入输出，请在注释中写明
'''
import sys
import numpy as np
import math
import time
import os
import cv2   # pip install opencv-python==4.5.4.58 -i https://pypi.douban.com/simple
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow,QFileDialog, QMessageBox
import ctypes
from numpy.ctypeslib import as_ctypes
# 在Winodws API中的LoadLibrary可以使用cdll和windll。ctypes.CDLL使用cdecl调用约定，而ctypes.WinDLL使用stdcall调用约定
# 如果windows上把cpp转为.so调用，会出现PermissionError: Error 5
'''
图像压缩类
通过继承QObject实现多线程
@params
    in_pic_array(np.ndarray类型) 输入的512*512灰度图像转为的数组
@return
    compress_rate 压缩效率(getCompressRate函数)
    running_time 执行时间(getRunningTime函数)
'''
class CompressPic(QtCore.QObject):
    result_ready = QtCore.pyqtSignal(dict) # 不能放在__init__中；定义一个信号用于传递字典类型的值

    def __init__(self, input_pic=None) -> None:
        super().__init__()
        self.input_pic = input_pic
        self.N = 512
        self.n = 512*512+1
        self.compress_rate = None
        self.running_time = None
        self.min_length = None
        self.aver_bit = None
        self.is_color = False # 判断是否为彩色图，默认False（灰度图）    
        
    '''
    获得蛇形序列函数
    @return
        snake_order(list) 512*512灰度图像转为的数组的一维蛇形序列
    NOTE 
    1) 优化flag=-1和flag=1整合为取反
    2）使用numpy函数代替for循环
    '''
    def getSnakeOrder(self):
        snake_order = []  # 创建一个空列表，用于存储输出结果
        snake_order.append(0)  # 下标从1开始
        left_flag = True  # 用于控制蛇形输出的方向：是否从左向右，默认为是
        # 遍历图像的每一行
        for i in range(self.N):
            # 如果方向标志为1，则从左往右遍历该行的像素
            if left_flag:
                # 将整行添加到输出数组中
                snake_order = np.append(snake_order, self.input_pic[i][:])
            # 如果方向标志为-1，则从右往左遍历该行的像素
            else:
                # 顺序相反的整行
                snake_tmp = self.input_pic[i,::-1]
                snake_order = np.append(snake_order, snake_tmp)
            # 改变下次更新方向
            left_flag = ~left_flag
        snake_order = list(snake_order)
        return snake_order  # 返回包含所有像素的数组
    '''
    计算像素点所需要的存储位数
    @params 
        i  像素点在p序列中的下标
    @return
        k 像素点所需要的存储位数
    NOTE
    1）使用math库计算i的以2为底的指数并向上取整
    '''
    def length(self, i):
        k = 1
        if i>0:
            # 计算以2为低的指数
            k = math.log(i,2) 
            # 向上取整
            k = math.ceil(k)
        return k

    '''
    将ctypes的数组转为numpy一维数组
    '''
    def cptrToNumpy(self, c_content, length):
        np_arr = np.ctypeslib.as_array(c_content, shape=(length,))
        return np_arr
    
    '''
    基于动态规划的图像压缩算法
    @params 
        n  像素点的个数+1
        【已经弃掉】p(np.ndarray，一维) 512*512灰度图像转为的数组的一维蛇形序列，存储第i个像素点值所需的最小位数
        s(np.ndarray，一维)  s[i]记录前i个数字的最优处理方式得到的最优解
        b(np.ndarray，一维)  b[i]记录第i段每个像素的位数
        l(np.ndarray，一维)  l[i]记录第i段有多少个像素
        color_b_max 3通道和的最大像素
    @return
        s(np.ndarray，一维)
        b(np.ndarray，一维)
        l(np.ndarray，一维)
        m(int)
    NOTE
    1）使用numpy的切片操作和广播机制
    2）使用map函数及列表表达式替代for循环
    3）将一层判断取消，加在外围的j初始化上
    '''
    def compress(self, n, s, b, l):
        if not self.is_color:
            header = 11  # 段首大小
            lmax = 256  # 每段所包含元素的最大个数
        else:
            lmax = 512 # 每段所包含像素的最大个数
            header = self.length(lmax)+self.length(max(b))
        start_time = time.time()  # 记录开始执行时间
        # 获得s[i]
        s[0] = 0
        # 数组的长度
        arr_len = n+1 # length：cpp中的参数，是原来的n+1
        for i in range(1,arr_len):
            s[i] = s[i - 1] + b[i]
        s = np.array(s)
        print('s数组成功\n',s)
        # numpy向量化操作改循环会变得很复杂，慢得离谱
        # XXX 用C代码过渡
        # NOTE .so是linux下的动态链接库，而.dll是windows的
        dynamic_core = ctypes.CDLL('./d_core.dll') # NOTE 如果共享库so不在标准路径/usr/lib，也不需要使用完整的路径
        core = dynamic_core.compressAndTraceBack
        # 将numpy数组转为Ctypes中数组指针
        b_ptr = b.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        print('检查b指针\n',b_ptr)
        s_ptr = s.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        print('检查s指针\n',s_ptr)
        l_ptr = l.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        print('检查l指针\n',l_ptr)
        # 将int数字转为Ctypes类型的int
        arr_len_int = ctypes.c_int(arr_len)
        lmax_int = ctypes.c_int(lmax)
        header_int = ctypes.c_int(header)
        # 定义C++中的结构体
        class dynamic_ans(ctypes.Structure):
            # _fields 用于定义结构体成员的变量（名称）和类型
            _fields_ = [("b", ctypes.POINTER(ctypes.c_float)), # 顺位第一缓冲区
                        ("l", ctypes.POINTER(ctypes.c_float)), # ...第二
                        ("s", ctypes.POINTER(ctypes.c_float)),
                        ("m", ctypes.c_int)]
        # numpy数组转为结构体
        # 告知ctypes：定义接收参数列表
        core.argtypes = [ctypes.POINTER(ctypes.c_float), 
                         ctypes.POINTER(ctypes.c_float), 
                         ctypes.POINTER(ctypes.c_float), 
                         ctypes.c_int, ctypes.c_int, ctypes.c_int]
        # 告知ctypes：core函数的返回值是一个dynamic_ans类型的结构体（返回值将转为该类型
        core.restype = dynamic_ans
        print('开始调用cpp动态链接库')
        ans = core(b_ptr, s_ptr, l_ptr, arr_len_int, lmax_int, header_int)
        # 拆分结果
        m = ans.m
        print(f'm的结果：{m}')
        b_new = self.cptrToNumpy(ans.b, m)
        print(f'获得b_new\n{b_new}')
        l_new = self.cptrToNumpy(ans.l, m)
        print(f'获得l_new\n{l_new}')
        s_new = self.cptrToNumpy(ans.s, arr_len)
        print(f'获得s_new\n{s_new}')
        print(f'测试结果\n\ns:\n{s}\nl:\n{l}\nb:{b}\nm:{m}')

        # exit()
        self.running_time = time.time() - start_time
        input_size = 512 * 512 * 8
        output_size = s[self.n - 1]
        self.compress_rate = 1 - output_size/input_size
        
        print(f'压缩成功，耗费时间{self.running_time}\n')
        return s_new,b_new,l_new, m

    '''
    将压缩信息输出到output/result.txt文件中
    '''
    def out(self, m, min_len, l, b):
        i = 0
        # 获取当前文件的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
        # 整合txt文件
        txt_path = os.path.join(base_path, 'result.txt')
        f = open(txt_path, "w+") # w+在文件不存在时新建
        f.seek(0)  # 定位到文件开头的位置
        f.truncate()  # 清空原有内容
        self.min_length=min_len
        self.aver_bit = min_len / (512 * 512)
        f.write("the minimal length：" + str(min_len) + "\n")
        f.write("the average of bits each pixel needed to store：" + str(min_len / (512 * 512)) + "\n")
        f.write("the whole number of segments:" + str(m) + "\n")
        for i in range(i + 1, m):
            f.write("the " + str(i) + " segment: " + str(l[i]) + "\telements\t\t" + "which need to: " + str(b[i]) + " bit(s)\n")
        f.close()

    '''
    对图像进行压缩
    '''
    def compressPic(self):
        print('成功进入计算线程')
        if self.input_pic is None:
            raise ValueError("Input picture is not provided")
        p = self.getSnakeOrder()  # 获取一维蛇形序列
        s = np.zeros(self.n, dtype=np.float32) # 记录前i个数字的最优处理方式得到的最优解 
        b = np.zeros(self.n, dtype=np.float32) # 记录第i段每个像素的位数
        l = np.ones(self.n, dtype=np.float32) # 记录第i段有多少个像素
        # 灰度图压缩
        if not self.is_color:
            print('开始灰度图压缩')
            b = np.array(list(map(lambda pix:self.length(pix), p))).astype(np.float32) # 没有astype的话，b是int类型会传入错误
        else:
            print('开始彩色图压缩')
            b = np.array(list(map(lambda pix: 3*self.length(max(pix)), p))).astype(np.float32)
        b[0] = 0
        print('b数组成功\n',b)
        print('进入compress函数')
        s, b, l, m = self.compress(self.n-1, s, b, l)

        print(f'这里b\n{b},\n这里l\n{l}\nm的值是{m}')
        self.out(m, s[self.n-1], l, b)
        # 传递结果
        self.threadResult()

    '''
    使用信号/槽将结果（以上4个，字典形式保存）发出
    PyQt常见线程间通信方式
    '''
    def threadResult(self):
        res = {'compress_rate':self.compress_rate,
               'running_time':self.running_time, 
               'min_length':self.min_length,
               'aver_bit':self.aver_bit}
        self.result_ready.emit(res)
'''
UI类
'''
class Ui_MainWindow(object):
    def __init__(self) -> None:
        super().__init__()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Compress the Pic")
        MainWindow.resize(1000, 700)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        # print('断点1')
        self.pushButton_compress = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_compress.setGeometry(QtCore.QRect(30, 170, 121, 51))
        self.pushButton_compress.setObjectName("pushButton_compress")
        # print('断点2')

        self.pushButton_saveImage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_saveImage.setGeometry(QtCore.QRect(30, 300, 121, 51))
        self.pushButton_saveImage.setObjectName("pushButton_saveImage")
        # print('断点3')

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(40, 410, 91, 41))
        self.label.setObjectName("label")
        # print('断点4')

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
        
        # print('断点5')
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        # print('断点6')
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.label_imagePath = QtWidgets.QLabel(self.centralwidget)
        self.label_imagePath.setObjectName("label_imagePath")
        self.label_imagePath.setWordWrap(True)
        # print('断点7')
        self.pushButton_saveImage.clicked.connect(self.saveImage)
        # print('断点8')
        self.pushButton_compress.clicked.connect(self.compress)
        # print('断点9')

    def retranslateUi(self, MainWindow):
        print('retranslateUi函数成功')
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        # self.pushButton.setText(_translate("MainWindow", "选择图片"))
        self.pushButton_compress.setText(_translate("MainWindow", "开始压缩")) 
        self.pushButton_saveImage.setText(_translate("MainWindow", "保存图片"))
        self.label.setText(_translate("MainWindow", "最小长度"))
        # self.label_imagethen.setText(_translate("MainWindow", "压缩后预览"))
        self.label_2.setText(_translate("MainWindow", "平均每个像素所需要的存储位数"))
        self.label_image.setText(_translate("MainWindow", "压缩后浏览"))  #展示的是被压缩的图片

    def openImage(self):  # 选择本地图片上传
        print('openImage函数成功')
        global imgName  # 这里为了方便别的地方引用图片路径，我们把它设置为全局变量
        imgName, imgType = QFileDialog.getOpenFileName(self.centralwidget, "打开图片", "","*.jpg;;*.png;;All Files(*)")  # 弹出一个文件选择框，第一个返回值imgName记录选中的文件路径+文件名，第二个返回值imgType记录文件的类型
        jpg = QtGui.QPixmap(imgName).scaled(self.label_image.width(),self.label_image.height())  # 通过文件路径获取图片文件，并设置图片长宽为label控件的长宽
        self.label_image.setPixmap(jpg)  # 在label控件上显示选择的图片
        self.label_imagePath.setText(imgName)  # 显示所选图片的本地路径
        return imgName

    def saveImage(self):  # 保存图片到本地
        print('saveImage函数成功')
        screen = QApplication.primaryScreen()
        pix = screen.grabWindow(self.label_image.winId())
        fd,type= QFileDialog.getSaveFileName(self.centralwidget, "保存图片", "", "*.jpg;;*.png;;All Files(*)")
        pix.save(fd)

    def printf(self, mes):
        self.textBrowser.clear() # 清空文本框
        self.textBrowser.append(mes)  # 在指定的区域显示提示信息
        self.cursot = self.textBrowser.textCursor()
        self.textBrowser.moveCursor(self.cursot.End)
        # QtWidgets.QApplication.processEvents()
        print('最小长度显示成功')

    def printf2(self,mes2):
        self.textBrowser_2.clear() # 清空文本框
        self.textBrowser_2.append(mes2)  # 在指定的区域显示提示信息
        self.cursot2 = self.textBrowser.textCursor()
        self.textBrowser.moveCursor(self.cursot2.End)
        print('平均每个像素显示成功')

    def isColor(self,img):
        if len(img.shape)<3 or img.shape[2]==1:
            print('这是张灰度图')
            return False
        else:
            print('这是张彩色图')
            return True
        
    def compress(self):  # 压缩图片
        print('compress函数初步成功')
        self.openImage()
        print(imgName)
        # 新建线程
        self.cal_thread = QtCore.QThread()
        img = cv2.imread(imgName, 0)
        self.cal = CompressPic(img)
        self.cal.is_color = self.isColor(img)
        print(f'存入成功：is_color的值为{self.cal.is_color}')
        self.cal.moveToThread(self.cal_thread)
        # 连接线程：调用算法进行压缩，压缩结果保存在./result.txt文件中
        self.cal_thread.started.connect(self.cal.compressPic)
        # 并行获取结果
        self.cal.result_ready.connect(self.updateRes) 
        self.cal.result_ready.connect(self.hide_loading_box) # 使弹窗隐藏
        # 开始线程计算
        self.start_thread()

    def start_thread(self):
        # open loading dialog and start the calculation thread
        self.loading_box = QMessageBox()
        self.loading_box.setText("正在计算，请稍后...") # TODO 让用户能够释放弹窗
        self.loading_box.setWindowTitle("请等待")
        self.loading_box.setStandardButtons(QMessageBox.NoButton)
        self.loading_box.show()

        # 开始线程
        while(not self.cal_thread):
            continue
        print(f'开始计算线程\n当前线程{self.cal_thread}')
        self.cal_thread.start()

    def show_loading_box(self):
        # show loading dialog in the center of the window
        self.loading_box.move(self.geometry().center() - self.loading_box.rect().center())
        self.loading_box.show()

    def hide_loading_box(self):
        # hide loading dialog after calculation is finished
        if self.loading_box.isVisible():
            self.loading_box.hide()

    '''
    @param
        data：访问槽中字典的值
    '''
    def updateRes(self, data):
        print('看看线程结果\n',data)
        compress_rate = data["compress_rate"]  # 获取压缩效率
        running_time = data["running_time"]  # 获取执行时间
        min_length = data["min_length"]
        aver_bit = data["aver_bit"]
        print("压缩算法压缩效率：" + str(compress_rate*100)+" %")
        print("压缩算法执行时间：" + str(running_time)+" s")
        print("最小长度：" + str(min_length)+" bits")
        print("平均每个像素：" + str(aver_bit))
        Ui_MainWindow.printf(self, str(min_length))
        Ui_MainWindow.printf2(self, str(aver_bit))

        # 销毁创建的线程
        self.cal_thread.quit() # 停止线程的事件循环
        self.cal_thread.wait() # 等待线程完成
        self.cal_thread.deleteLater() # 回收线程

if __name__ == '__main__':
    # 执行ui界面
    app = QtWidgets.QApplication(sys.argv)
    formObj = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(formObj)
    formObj.show()
    app.exec() # 使用sys.exit(app.exec_())会闪退
=======
@Authors: 
    Alla, xx, xx, xx
@class
    CompressPic 压缩图片的过程
    Process 图像处理过程：将图片和np.ndarray间转换，保存图片和预览

!!Attention!!
如果修改了函数的输入输出，请在注释中写明
因为没写过这个软件的完整版，多有疏漏，请多包涵qwq
'''
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

'''
图像压缩类
@params
    in_pic_array(np.ndarray类型) 输入的512*512灰度图像转为的数组
@return
    compress_rate 压缩效率
    running_rate 执行效率
    out_pic_array(np.ndarray类型) 压缩后的图像数组
'''
class CompressPic():
    def __init__(self, input_pic=None) -> None:
        pass

'''
图片处理类
包括图片和像素的转换，保存图片和图片预览
'''
class Process():
    def __init__(self) -> None:
        pass

    '''
    加载图片：忘了用什么库
    @params
        in_pic_path(string) 输入图片的路径
    @return
        in_pic() 输入图片的加载结果
    '''
    def loadimg(self):
        pass

    '''
    将512*512（灰度）图像转为np.ndarray格式   
    @params
        in_pic() 输入图片的加载结果
    @return
        in_pic_array(np.ndarray) 图片转为的数组
        注：使用uint8类型存储灰度图像或RGB图像时，
        每个像素元素占用8位（一个字节）空间。
        如果存储更高精度的图像，可选float32等类型。
    '''
    def picToArray(self, in_pic=None) -> np.ndarray:
        pass

    '''
    将np.ndarray转为512*512图像
    @params
        out_pic_array(np.ndarray) 
    @return
        out_pic() 输出图片的加载结果
    '''
    def ArrayToPic(self):
        pass

    '''
    保存文件
    @params
        save_path(string) 压缩后的图像存放位置，默认为output文件夹下
    @output
        isSuccess(boolean) 保存是否成功，默认为失败
    '''
    def savePic(self, save_path='./output/1.jpg') -> None:
        isSuccess = False

    '''
    预览图片    
    #TODO：写界面和预览的讨论下怎么约束哈，如果能直接展示图片就不用showPic
    '''
    def showPic(self) -> None:
        pass

'''
功能入口
'''
if __name__ == '__main__':
    isChoose = False #是否选择了图片，默认为否
    isCompress = False #是否压缩了图片，默认为否
    
    # 界面开始：设计图在materials/页面设计.png中
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setGeometry(800, 800, 400, 300)
    win.setWindowTitle("图像压缩")
    
    # 界面按钮的样式和布局：没显示因为只有定义
    btn_choose=QPushButton("选择图像")
    btn_process=QPushButton("进行压缩")
    btn_clear=QPushButton("重置") # 让程序的状态回到“已选择图像之前”
    style='''
        #
    '''
    # 预览图的样式和布局


    win.show()
    sys.exit(app.exec_())
>>>>>>> 992e0e6ca828a7234b493cc368a7f92c0ecf43ef
