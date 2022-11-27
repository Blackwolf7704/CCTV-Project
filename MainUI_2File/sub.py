import time, cv2
import datetime as dt

from PyQt6 import QtGui
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

import Detect as DT
import ProgramLog as PL
import Configuration as cf

import UI_AddCam as UIAC

class Main():
    config = cf.GetProgramConf()
    
    Screenshoot_Delay = config['SC_Delay']
    Accuracy = config['Accuracy']
    
    width = 640
    height = 480

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
        
        PL.EventLog("Detect Enabled [Cam ID : " + str(self.CamID) + "]", "INFO")
    
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
                res = QPixmap.fromImage(img.scaled(Main.width, Main.height, Qt.AspectRatioMode.KeepAspectRatio))
                
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
        PL.EventLog("Detect Disabled [Cam ID : " + str(self.CamID) + "]", "INFO")
        self.work = False
        self.quit()
        self.wait(1000)
        
        
#로그 실시간 업데이트 스레드
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
        PL.EventLog("Logging Start!", "INFO")
        self.work = False
        self.quit()
        self.wait(1000)
        
#카메라 추가
class AddCam(QThread):    
    def __init__(self):
        super().__init__()
        
    def run(self):
        self.s = UIAC.AddCamUI()
        self.s.exec()
        
        if(self.s.QL_Value.text() != "" and self.s.QL_Value.text() != None):
            return self.s.QL_Value.text(), True
        
#스크린샷
def ScreenShoot(image, Type="system"):
    img = ImageQt.fromqpixmap(image)
    
    if(Type == "system"):
        img.save(SystemImgSaveLoc + PL.GetTime() + '.png')
        PL.EventLog("System ScreenShoot Saved")
    elif(Type == "user"):
        img.save(UserImgSaveLoc + PL.GetTime() + '.png')
        PL.EventLog("User ScreenShoot Saved")