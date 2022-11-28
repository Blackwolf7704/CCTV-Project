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
    
    width = 0
    height = 0

#UI 연결 (Exe Build)
#import Initialization as Init
#UI_Main = uic.loadUiType(Init.resource_path("./UI/Main.ui"))[0]

#UI 연결
UI_Main = uic.loadUiType("./UI/Main.ui")[0]

#https://doc.qt.io/qtforpython-6/api.html
#https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/index.html#module-PySide6.QtWidgets

#메인 UI
class MainGUI(QMainWindow, UI_Main):
    AddCamThreadRunning = 0
    ConfigurationRunning = 0
    CamThread = {}
    Show_Cam_Device = None
    
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
        #self.BTN_DEBUG.clicked.connect(self.debug)
        
        #로그 업데이트 스레드 생성 및 시작
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
                self.ConnectingCamera(text)
                
            self.AddCamThreadRunning = 0
                
        elif self.AddCamThreadRunning == 1:
            QMessageBox.critical(self, 'ERROR', "이미 카메라 연결 창이 활성화되어있습니다!!")
            
    #스크린샷을 찍었을 때, 사용자 스크린샷을 찍게 한다.
    def onScreenShoot(self):
        ScreenShoot(self.LB_CamRes.pixmap(), "user")
    
    #설정 변경 함수이다.
    def onConfiguration(self):
        #설정 변경 창이 띄워져 있지 않을 경우에 실행
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
    
    #카메라를 변경할 때 작동되는 함수
    def onCameraChange(self):
        self.ShowCamera(self.CMB_Camera.currentText())
    
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

        #기본 카메라 장치 연결
        self.ShowCamera(dvc["0"])
            
    #QT 시그널 정의 (카메라의 결과를 보여주는데 사용한다.)
    @pyqtSlot(QPixmap)
    def update_image(self, img):
        self.LB_CamRes.setPixmap(img)
        
    #카메라 연결 및 스레드 시작
    def ConnectingCamera(self, dvcid):
        cid = dvcid

        try:
            cid = int(dvcid)
        except:
            cid = str(dvcid)
        
        #카메라가 열려 있는지 확인
        try:
            c = cv2.VideoCapture(cid, cv2.CAP_DSHOW)
        except:
            return False

        #카메라가 정상적으로 열려 있고, 스레드에 없을 경우에만 실행
        if c.isOpened() == True and cid not in self.CamThread:
            c.release() #일시적인 사용이므로 릴리즈한다.
            
            self.CamThread[cid] = PrintCamera(cid)
                
            self.cap = self.CamThread[cid]
            self.cap.start()

            return True
    
    #카메라 결과 보여주기
    def ShowCamera(self, dvcid):
        #장치의 ID를 int 값으로 변환한다. (USB 카메라)
        try:
            cid = int(dvcid)
        except:
            cid = str(dvcid)

        #기존에 카메라 출력 연결이 있으면 해제한다. (감지는 계속된다.)
        try:
            self.Show_Cam_Device.changePixmap.disconnect()
        except:
            pass

        #현재 카메라 ID의 결과를 출력한다.
        self.cap = self.CamThread[cid]
        self.cap.changePixmap.connect(self.update_image)
        
        #출력되는 장치를 저장한다.
        self.Show_Cam_Device = self.cap
        
        #출력되는 카메라의 ID 지정
        self.LB_CamNum.setText("Camera " + str(cid))

#카메라 출력 스레드
class PrintCamera(QThread):
    #메인 UI와 스레드 간의 통신을 하기 위한 변수
    changePixmap = pyqtSignal(QPixmap)
    
    #스레드의 시작 부분
    def __init__(self, cid):
        super().__init__()
        self.work = True
        self.CamID = cid
    
    #스레드의 실제 작동 부위
    def run(self):
        PL.EventLog("Detect Start [Cam ID : " + str(self.CamID) + "]", "INFO")
        
        cam = cv2.VideoCapture(self.CamID, cv2.CAP_DSHOW)
        
        while self.work:            
            r, img = cam.read()
            
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
                res = QPixmap.fromImage(img.scaled(Main.width, Main.height, Qt.AspectRatioMode.KeepAspectRatio))
                
                #정확도를 불러와서, 사람이 감지가 되면 스크린샷을 찍는다.
                if(len(Acc) != 0 and checktime):
                    ScreenShoot(res)

                #결과를 반환한다.
                self.changePixmap.emit(res)
                
                #10ms의 지연을 준다.
                cv2.waitKey(10)
                
            else:
                break
                
        cam.release()

    #스레드를 오류 없이 종료하기 위함
    def stop(self):
        PL.EventLog("Detect Ended [Cam ID : " + str(self.CamID) + "]", "INFO")
        self.work = False
        self.quit()
        self.wait(1000)
                
#로그 실시간 업데이트 클래스
class GetLog(QThread):
    LogUpdate = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.work = True 
    
    def run(self):
        while self.work:
            text = PL.GetLastLog()

            if text != None:
                self.LogUpdate.emit(text)
                time.sleep(1)

    def stop(self):
        PL.EventLog("Logging Ended!", "INFO")
        self.work = False
        self.quit()
        self.wait(1000)

#카메라 추가 클래스
class AddCam(QThread):    
    def __init__(self):
        super().__init__()
        
    def run(self):
        self.s = UIAC.AddCamUI()
        self.s.exec()
        
        if(self.s.QL_Value.text() != "" and self.s.QL_Value.text() != None):
            return self.s.QL_Value.text(), True

#이미지 저장 함수
def ScreenShoot(image, Type="system"):
    img = ImageQt.fromqpixmap(image)
    
    if(Type == "system"):
        img.save(SystemImgSaveLoc + PL.GetTime() + '.png')
        PL.EventLog("System ScreenShoot Saved")
    elif(Type == "user"):
        img.save(UserImgSaveLoc + PL.GetTime() + '.png')
        PL.EventLog("User ScreenShoot Saved")