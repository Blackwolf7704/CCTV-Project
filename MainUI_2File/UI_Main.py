'''
추가해야 할 목록
2. 카메라 번호 설정
https://catloaf.tistory.com/66?category=950060
'''

#기본 모듈
import cv2, sys

#PyQt 모듈
from PyQt6.QtWidgets import *
from PyQt6 import QtGui
from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PIL import ImageQt

#카메라 추가 UI
import UI_Configuration as UICF

#내부 기능 모듈
import ProgramLog as PL
import Configuration as cf
import sub

#변수 목록
QMBS = QMessageBox.StandardButton
SystemImgSaveLoc = "./images/System_Alert/"
UserImgSaveLoc = "./images/User_Alert/"

#클래스 간에 공통적으로 사용하는 전역변수
class Main():
    config = cf.GetProgramConf()
    
    Screenshoot_Delay = config['SC_Delay']
    Accuracy = config['Accuracy']
    
    width = 0
    height = 0

#UI 연결 (Exe Build)
#import Initialization as Init
#UI_Main = uic.loadUiType(Init.resource_path("./UI/Main.ui"))[0]

#UI 연결
UI_Main = uic.loadUiType("./UI/Main.ui")[0]

#스레드 종료
#https://investox.tistory.com/entry/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%A9%80%ED%8B%B0%EC%93%B0%EB%A0%88%EB%93%9C-%EC%98%A4%EB%A5%98%EC%97%86%EC%9D%B4-%EC%A2%85%EB%A3%8C%ED%95%98%EA%B8%B0-QThread-GUI
#https://doc.qt.io/qtforpython-6/api.html
#https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/index.html#module-PySide6.QtWidgets

#메인 UI
class MainGUI(QMainWindow, UI_Main):
    ResShow = 0
    AddCamThreadRunning = 0
    ConfigurationRunning = 0
    CamThread = {}
    
    def __init__(self):        
        super().__init__()
        
        self.setupUi(self)
        self.onLoad()
        
        #위젯의 크기
        x = QWidget.rect(self.LB_CamRes)
        Main.width = x.width()
        Main.height = x.height()
        
        #특정 객체 클릭 시 함수 작동
        self.Btn_Conf.clicked.connect(self.onConfiguration)
        self.Btn_Screenshot.clicked.connect(self.onScreenShoot)
        self.Btn_AddCamera.clicked.connect(self.AddCamera)
        self.CMB_Camera.activated.connect(self.onCameraChange)
        
        #로그 업데이트 스레드 생성 및 시작 (개선예정)
        try:
            startLog = PL.GetNowLog()
            for i in range(len(startLog)):
                self.TB_LogBrowser.append(startLog[i].strip())
            self.logging = sub.GetLog()
            self.logging.LogUpdate.connect(self.update_log)
            self.logging.start()
            
        except Exception as E:
            #오류 발생시 프로그램 종료
            sys.exit()
            
    #참고 코드 : https://helloezzi.tistory.com/155
    #QTextBrowser이 아닌 str로 변경했어야 한다.
    @pyqtSlot(str)
    def update_log(self, text):
        t = self.TB_LogBrowser.toPlainText().split("\n")
        
        if text != t[len(t)-1]:
            self.TB_LogBrowser.append(text)
    
    #카메라 등록 함수
    def AddCamera(self):
        if self.AddCamThreadRunning == 0:
            self.AddCamThreadRunning = 1
            
            self.s = sub.AddCam()
            
            try:
                text, res = self.s.run()
            except:
                text = None
            
            if(text != None):
                self.CMB_Camera.addItem(" " + text)
                
            self.AddCamThreadRunning = 0
                
        elif self.AddCamThreadRunning == 1:
            QMessageBox.critical(self, 'ERROR', "이미 카메라 연결 창이 활성화되어있습니다!!")
            
    def onScreenShoot(self):
        sub.ScreenShoot(self.LB_CamRes.pixmap(), "user")
    
    def onConfiguration(self):
        if self.ConfigurationRunning == 0:
            self.ConfigurationRunning = 1
            self.s = UICF.ConfigUI()
            self.s.exec()
            
            cfg = cf.GetProgramConf()
            Main.Screenshoot_Delay = cfg['SC_Delay']
            Main.Accuracy = cfg['Accuracy']
            
            self.ConfigurationRunning = 0
        
        elif self.ConfigurationRunning == 1:
            QMessageBox.critical(self, 'ERROR', "이미 설정 창이 활성화되어있습니다!!")
        
    
    def onCameraChange(self):
        self.ConnectingCamera(self.CMB_Camera.currentText())
    
    #창 종료할 때 이벤트 오버라이딩
    def closeEvent(self, event):
        message = "정말 종료하시겠습니까?"
        reply = QMessageBox.question(self, 'Main', message, QMBS.Yes, QMBS.No)
        
        if reply == QMBS.Yes:
            #프로그램 종료 로그 기록
            for key, _ in self.CamThread.items():
                self.CamThread[key].stop()
                
            self.logging.stop()
            PL.onEnded()
            
            #이벤트 수락 후 창이 종료됨.
            event.accept()
        else:
            event.ignore()
    
    #프로그램이 켜질 때, conf 파일에 있는 데이터 자동으로 콤보박스에 등록
    def onLoad(self):
        dvc = cf.GetDeviceConf()
        
        if (len(dvc) == 0):
            return
        
        for i in dvc:
            if(self.ConnectingCamera(dvc[i]) == True):
                self.CMB_Camera.addItem(dvc[i])

        self.ConnectingCamera(dvc['0'])

    #카메라 무한루프 해결
    @pyqtSlot(QPixmap)
    def update_image(self, img):
        self.LB_CamRes.setPixmap(img)
        
    #카메라 연결
    def ConnectingCamera(self, dvcid):
        cid = dvcid

        try:
            cid = int(dvcid)
        except:
            cid = str(dvcid)
        
        try:
            c = cv2.VideoCapture(cid, cv2.CAP_DSHOW)
        except:
            return False

        if c.isOpened() == True:
            self.CamThread[cid] = sub.PrintCamera(cid)
            self.CamThread[cid].start()
            
            if self.ResShow == 0:
                self.ResShow = 1
                
                self.cap = self.CamThread[cid]
                self.cap.changePixmap.connect(self.update_image)
                self.cap.SetShow(True)
                
            elif self.ResShow == 1:
                self.cap.SetShow(False)
                self.cap.changePixmap.disconnect(self.update_image)
                
                self.cap = self.CamThread[cid]
                self.cap.changePixmap.connect(self.update_image)
                self.cap.SetShow(True)
                
            return True

    
############################################################################################
#테스트 함수

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    #프로그램 시작 기록
    PL.onStarted()
    
    #메인 GUI
    myWindow = MainGUI()
    myWindow.show()
    app.exec()
