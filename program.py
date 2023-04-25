'''
对图像进行压缩的软件
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