'''
추가해야 할 목록
1. 로그 출력, read
2. 카메라 번호 설정
5. onMenualAlert 이벤트 수정 => 서버 처리
https://catloaf.tistory.com/66?category=950060
'''

#기본 모듈
import cv2, sys
import time
import datetime as dt

#PyQt 모듈
from PyQt6.QtWidgets import *
from PyQt6 import QtGui
from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PIL import ImageQt

#카메라 추가 UI
import UI_AddCam as UIAC
import UI_Configuration as UICF

#내부 기능 모듈
import ProgramLog as PL
import Configuration as cf
import Detect as DT

#변수 목록
QMBS = QMessageBox.StandardButton
SystemImgSaveLoc = "./images/System_Alert/"
UserImgSaveLoc = "./images/User_Alert/"

#클래스 간에 공통적으로 사용하는 전역변수
class Main():
    config = cf.GetProgramConf()
    
    Screenshoot_Delay = config['SC_Delay']
    Accuracy = config['Accuracy']

#UI 연결 (Exe Build)
#import Initialization as Init
#UI_Main = uic.loadUiType(Init.resource_path("./UI/Main.ui"))[0]

#UI 연결
UI_Main = uic.loadUiType("./UI/Main.ui")[0]

#스레드 종료
#https://investox.tistory.com/entry/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%A9%80%ED%8B%B0%EC%93%B0%EB%A0%88%EB%93%9C-%EC%98%A4%EB%A5%98%EC%97%86%EC%9D%B4-%EC%A2%85%EB%A3%8C%ED%95%98%EA%B8%B0-QThread-GUI

#카메라 출력 스레드
class PrintCamera(QThread):
    #메인 UI와 스레드 간의 통신을 하기 위한 변수
    changePixmap = pyqtSignal(QPixmap)
    
    #스레드의 시작 부분
    def __init__(self, cid):
        super().__init__()
        self.work = True
        self.CamID = cid
        self.showRes = 0
        
        PL.EventLog("PrintCamera Thread init success!", "INFO")
    
    #스레드의 실제 작동 부위
    def run(self):        
        c = cv2.VideoCapture(self.CamID, cv2.CAP_DSHOW)
            
        while self.work:
            r, img = c.read()
            
            if r:
                t = dt.datetime.now()
                t = list(map(int, t.strftime("%H,%M,%S").split(",")))

                checktime = (t[0] * 360 + t[1] * 60 + t[2]) % Main.Screenshoot_Delay == 0
                
                h, w, ch = img.shape
                
                #DT 모듈에서 이미지 전처리, 정확도는 사용자가 지정한다.
                #또한, copy 함수를 통해 오버로딩 에러를 방지한다. https://powerofsummary.tistory.com/230
                img, Acc = DT.Detect(img.copy(), Main.Accuracy)
                    
                #전처리된 이미지를 RGB로 변환 후 qt 이미지에 출력한다.
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = QtGui.QImage(img.data, w, h, ch * w, QImage.Format.Format_RGB888)
                res = QPixmap.fromImage(img.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio))
                
                #정확도를 불러와서, 사람이 감지가 되면 스크린샷을 찍는다.
                if(len(Acc) != 0 and checktime):
                    ScreenShoot(res)

                if(self.showRes == 1):
                    self.changePixmap.emit(res)
                
                #10ms의 지연을 준다.
                cv2.waitKey(10)
                
        c.release()
        
    def SetShow(self, Type):
        if(Type):
            self.showRes = 1
        else:
            self.showRes = 0

    #스레드를 오류 없이 종료하기 위함
    def stop(self):
        PL.EventLog("PrintCamera Thread Ended", "INFO")
        self.work = False
        self.quit()
        self.wait(1000)
                
#로그 실시간 업데이트 스레드
class GetLog(QThread):
    LogUpdate = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.work = True 
        PL.EventLog("Logging Thread Started", "INFO")
    
    def run(self):
        while self.work:
            text = PL.GetLastLog()

            if text != None:
                self.LogUpdate.emit(text)
                time.sleep(1)

    def stop(self):
        PL.EventLog("Logging Thread Ended", "INFO")
        self.work = False
        self.quit()
        self.wait(1000)
        
class AddCam(QThread):    
    def __init__(self):
        super().__init__()
        
    def run(self):
        self.s = UIAC.AddCamUI()
        self.s.exec()
        
        if(self.s.QL_Value.text() != "" and self.s.QL_Value.text() != None):
            return self.s.QL_Value.text(), True

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
        #self.debug()
        
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
            self.logging = GetLog()
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
            
            self.s = AddCam()
            
            try:
                text, res = self.s.run()
            except:
                text = None
            
            if(text != None):
                self.CMB_Camera.addItem(" " + text)
                
            self.AddCamThreadRunning = 0
                
        elif self.AddCamThreadRunning == 1:
            QMessageBox.critical(self, 'ERROR', "이미 카메라 연결 창이 활성화되어있습니다!!")
            
        '''
        self.s = AC.AddCamUI()
        self.s.exec()
        
        #캠 ID 값을 일시로 저장한 QLabel의 값이 공백 (취소 또는 비정상 값)이 아니라면 실행
        if(self.s.QL_Value.text() != ""):
            self.CMB_Camera.addItem(" " + self.s.QL_Value.text())
            
            PL.EventLog("CAMERA ADDED", "INFO")

        #http://www.gisdeveloper.co.kr/?p=8328
        '''
    def onScreenShoot(self):
        ScreenShoot(self.LB_CamRes.pixmap(), "user")
    
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
        
        for i in range(len(dvc)):
            self.CMB_Camera.addItem(dvc[i])
            
            #기본 카메라에 연결
            if i == 0 and dvc[i] != None:
                self.ConnectingCamera(dvc[i])
                
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
        
        c = cv2.VideoCapture(cid, cv2.CAP_DSHOW)
        
        if c.isOpened() == True:
            self.CamThread[cid] = PrintCamera(cid)
            
            if self.ResShow == 0:
                self.ResShow = 1
                
                self.cap = self.CamThread[cid]
                self.cap.changePixmap.connect(self.update_image)
                self.cap.start()
                self.cap.SetShow(True)
                
            elif self.ResShow == 1:
                self.cap.stop()
                #self.cap.SetShow(False)
                #self.cap.changePixmap.disconnect(self.update_image)
                
                self.cap = self.CamThread[cid]
                self.cap.changePixmap.connect(self.update_image)
                self.cap.start()
                self.cap.SetShow(True)
                
    def debug(self):
        self.CamThread['0'] = PrintCamera(0)
        self.CamThread['1'] = PrintCamera(1)
        
        self.CamThread['0'].start()
        self.CamThread['1'].start()

        
        '''
        if c.isOpened() == True and self.CamearaThreadRunning == 0:
            self.CamearaThreadRunning = 1
            self.CamThread.append(PrintCamera(cid))
            
            self.cap = self.CamThread[len(self.CamThread) - 1]
            self.cap.changePixmap.connect(self.update_image)
            self.cap.start()
            
            #self.CamThread[len(self.CamThread)-1].changePixmap.connect(self.update_image)
        
        elif c.isOpened() == True and self.CamearaThreadRunning == 1:
            self.cap.ShowResSet()
            
            self.CamThread.append(Printcamera(cid))
            self.cap = self.CamThread[len(self.CamThread - 1)]
            self.cap.changePixmap.connect(self.update_image)
            self.cap.start()
            
        if c.isOpened() == True and self.CamearaThreadRunning == 0:
            self.CamearaThreadRunning = 1
            
            self.capture = PrintCamera(cid)
            self.capture.changePixmap.connect(self.update_image)
            self.capture.start()
            
        #기존 스레드가 작동중일 경우, 스레드를 종료후, 다른 스레드로 재시작
        #오버로딩 현상 해결
        elif c.isOpened() == True and self.CamearaThreadRunning == 1:
            self.capture.stop()
            self.capture = PrintCamera(cid)
            self.capture.changePixmap.connect(self.update_image)
            self.capture.start()
            
        else:
            QMessageBox.critical(self, 'ERROR', "카메라에 연결할 수 없습니다!!")
        '''
            
def ScreenShoot(image, Type="system"):
    img = ImageQt.fromqpixmap(image)
    
    if(Type == "system"):
        img.save(SystemImgSaveLoc + PL.GetTime() + '.png')
        PL.EventLog("System ScreenShoot Saved")
    elif(Type == "user"):
        img.save(UserImgSaveLoc + PL.GetTime() + '.png')
        PL.EventLog("User ScreenShoot Saved")
    
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
