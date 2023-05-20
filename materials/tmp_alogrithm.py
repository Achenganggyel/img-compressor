'''
对图像进行压缩的软件
@Authors: 
    Alla, ytding, xx, xx
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
import time
import cv2   # pip install opencv-python==4.5.4.58 -i https://pypi.douban.com/simple

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
        self.n = 512*512+1
        self.compress_rate = None
        self.running_time = None

    '''
    获得蛇形序列函数
    @return
        snake_order(list) 512*512灰度图像转为的数组的一维蛇形序列
    '''
    def getSnakeOrder(self):
        snake_order = []  # 创建一个空列表，用于存储输出结果
        snake_order.append(0)  # 下标从1开始
        flag = 1  # 用于控制蛇形输出的方向
        # 遍历图像的每一行
        for i in range(self.N):
            # 如果方向标志为1，则从左往右遍历该行的像素
            if flag == 1:
                for j in range(self.N):
                    snake_order = np.append(snake_order, self.input_pic[i][j])  # 将该像素添加到输出数组中
                flag = -1  # 改变方向标志，以便下一行从右往左遍历
            # 如果方向标志为-1，则从右往左遍历该行的像素
            else:
                for j in range(self.N-1, -1, -1):
                    snake_order = np.append(snake_order, self.input_pic[i][j])  # 将该像素添加到输出数组中
                flag = 1  # 改变方向标志，以便下一行从左往右遍历
        # print("p array:")
        # print(snake_order)
        # test
        # arr = np.array([[1, 2, 3, 3], [1, 2, 3, 4], [1, 3, 3, 2], [1, 2, 3, 4]])
        # snake_order = []
        # snake_order.append(0)
        # flag = 1  # 用于控制蛇形输出的方向
        # # 遍历图像的每一行
        # for i in range(4):
        #     # 如果方向标志为1，则从左往右遍历该行的像素
        #     if flag == 1:
        #         for j in range(4):
        #             snake_order = np.append(snake_order, arr[i][j])  # 将该像素添加到输出数组中
        #         flag = -1  # 改变方向标志，以便下一行从右往左遍历
        #     # 如果方向标志为-1，则从右往左遍历该行的像素
        #     else:
        #         for j in range(3, -1, -1):
        #             snake_order = np.append(snake_order, arr[i][j])  # 将该像素添加到输出数组中
        #         flag = 1  # 改变方向标志，以便下一行从左往右遍历
        # print("p array:")
        # print(snake_order)
        return snake_order  # 返回包含所有像素的数组

    '''
        计算像素点所需要的存储位数
        @params 
            i  像素点在p序列中的下标
        @return
            k 像素点所需要的存储位数
            '''
    def length(self, i):
        k = 1
        i = i/2
        while i>0:
            k += 1
            i = i//2
        return k

    '''
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
            b[i] = self.length(p[i])
            bmax = b[i]
            s[i] = s[i - 1] + bmax + header
            l[i] = 1
            for j in range(2, lmax+1):
                if j <= i:
                    if bmax < self.length(p[i-j+1]):
                        bmax = self.length(p[i-j+1])
                    if s[i] > s[i-j] + j * bmax + header:
                        s[i] = s[i - j] + j * bmax + header
                        l[i] = j
                        b[i] = bmax
        # print("compress l array：")
        # print(l)
        # print("b array：")
        # print(b)
        # print("s array: ")
        # print(s)
        self.running_time = time.time() - start_time
        input_size = 512 * 512 * 8
        output_size = s[self.n - 1]
        self.compress_rate = output_size / input_size
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
        return i-1

    '''
        将压缩信息输出到output/result.txt文件中
    '''
    def out(self, m, min_len, l, b):
        i = 0
        f = open("result.txt", "w+")
        f.seek(0)  # 定位到文件开头的位置
        f.truncate()  # 清空原有内容
        f.write("最小长度：" + str(min_len) + "\n")
        f.write("平均每个像素所需要的存储位数：" + str(min_len / (512 * 512)) + "\n")
        f.write("共分成" + str(m) + "段" + "\n")
        for i in range(i + 1, m + 1):
            f.write("第" + str(i) + "段含有" + str(l[i]) + "个元素\t\t" + "需要存储的位数为：" + str(b[i]) + "\n")
        f.close()
        # print("最小长度：" + str(min_len))
        # print("平均每个像素所需要的存储位数：" + str(min_len/(512*512)))
        # print("共分成" + str(m) + "段")
        # for i in range(i+1, m+1):
        #     print("第" + str(i) + "段含有" + str(l[i]) + "个元素     " + "需要存储的位数为：" + str(b[i]))

    '''
        对图像进行压缩
    '''
    def compressPic(self):
        if self.input_pic is None:
            raise ValueError("Input picture is not provided")
        p = self.getSnakeOrder()  # 获取一维蛇形序列
        # p = [0, 255, 1, 5, 2, 1, 2]  # test
        s = [0]*self.n  # 记录前i个数字的最优处理方式得到的最优解
        b = [0]*self.n  # 记录第i段每个像素的位数
        l = [0]*self.n  # 记录第i段有多少个像素
        # print("图像的灰度序列为：")
        # for i in range(1, self.n):
        #     print(str(p[i]) + " ")
        s = self.compress(self.n-1, p, s, b, l)
        m = self.traceBack(self.n-1, l, b)
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

'''
功能入口
'''
if __name__ == '__main__':
    # compress test
    img = cv2.imread("../pic/test1.jpg", 0)
    # print("img array: ")
    # print(img)
    # np.savetxt("output/beforeCompress.txt", img, fmt='%d', delimiter=',')

    # 压缩调用示例如下
    test = CompressPic(img)
    test.compressPic()   # 调用算法进行压缩，压缩结果保存在output/result.txt文件中
    compress_rate = test.getCompressRate()  # 获取压缩效率
    running_time = test.getRunningTime()  # 获取执行时间
    print("压缩算法压缩效率：" + str(compress_rate))
    print("压缩算法执行时间：" + str(running_time))



