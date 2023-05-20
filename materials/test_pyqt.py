'''
用于测试PyQt的线程运行
'''
from PyQt5.QtCore import pyqtSignal, QThread, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QLabel
import sys

class Calculator(QObject):
    result_ready = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def perform_calculation(self):
        # some calculation here
        result = 0
        self.result_ready.emit(result)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # create calculator object and move it to a new thread
        self.calculation_thread = QThread()
        self.calculator = Calculator()
        self.calculator.moveToThread(self.calculation_thread)
        self.calculation_thread.started.connect(self.calculator.perform_calculation)

        # connect result_ready signal of the calculator to update GUI
        self.calculator.result_ready.connect(self.update_gui)
        self.calculator.result_ready.connect(self.hide_loading_box)

        # start the thread when the button is clicked
        button = QPushButton("Start Thread", self)
        button.clicked.connect(self.start_thread)

        # add label to show the result in GUI
        self.result_label = QLabel("", self)
        self.result_label.move(20, 50)
        
    def start_thread(self):
        # open loading dialog and start the calculation thread
        self.loading_box = QMessageBox()
        self.loading_box.setText("正在计算，请稍后...")
        self.loading_box.setWindowTitle("请等待")
        self.loading_box.setStandardButtons(QMessageBox.NoButton)
        self.loading_box.show()

        self.calculation_thread.start()

    def show_loading_box(self):
        # show loading dialog in the center of the window
        self.loading_box.move(self.geometry().center() - self.loading_box.rect().center())
        self.loading_box.show()

    def hide_loading_box(self):
        # hide loading dialog after calculation is finished
        if self.loading_box.isVisible():
            self.loading_box.hide()


    def update_gui(self, result):
        # update the GUI with the calculation result
        self.result_label.setText("Result: " + str(result))

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())