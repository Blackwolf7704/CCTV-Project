'''
원래는 모든 카메라 디바이스의 이름과 번호를 출력하려 했지만,
카메라 번호를 가져오는 것은 가능해도 ip 카메라 연결이 곤란해서
사용자가 수동으로 카메라 번호를 입력하는 것으로 대체했다.

https://codechacha.com/ko/python-read-write-file/
'''


#기본 모듈
import cv2
from PyQt6.QtWidgets import *
from PyQt6 import uic

#내부 기능 모듈
import ProgramLog as PL
import Configuration as cf

#변수 목록
QMBS = QMessageBox.StandardButton

#Exe_Build
#import Initialization as Init
#form_class = uic.loadUiType(Init.resource_path("./UI/AddCam.ui"))[0]

form_class = uic.loadUiType("./UI/AddCam.ui")[0]

class AddCamUI(QDialog, QWidget, form_class):
    def __init__(self):
        super().__init__()
        
        self.setupUi(self)
        self.show()
        
        #값 저장을 위한 QLabel 숨기기 및 초기화
        self.QL_Value.setText("")
        self.QL_Value.hide()
        
        self.Btn_Cancel.clicked.connect(self.ClickCancelBtn)
        self.Btn_Connect.clicked.connect(self.ClickOkBtn)
    
    def ClickOkBtn(self):        
        CamID = self.TE_CamID.text()
        try:
            CamID = int(CamID)
        except:
            pass
        
        if(CamID==""):
            QMessageBox.critical(self, "ERROR", "값을 입력해 주세요!", QMBS.Yes)
            return
        
        #비디오 연결 확인
        temp = cv2.VideoCapture(CamID, cv2.CAP_DSHOW)
        
        if temp.isOpened() == True:
            temp.release()
            
            if (AddDevice(str(CamID)) == True):
                self.QL_Value.setText(str(CamID))
                QMessageBox.information(self, "Success", "카메라에 성공적으로 연결했습니다.", QMBS.Yes)
                self.accept()
                
            elif (AddDevice(str(CamID)) == False):
                QMessageBox.critical(self, "ERROR", "이미 등록된 카메라 장치입니다!", QMBS.Yes)
                self.TE_CamID.setText("")
                
            else:
                QMessageBox.critical(self, "ERROR", "기본 카메라 장치는 설정 파일에 등록되어 있습니다!", QMBS.Yes)
                self.TE_CamID.setText("")
                
        else:
            QMessageBox.critical(self, "ERROR", "카메라에 연결할 수 없습니다!", QMBS.Yes)
            self.TE_CamID.setText("")

    def ClickCancelBtn(self):
        self.close()
        return False
        
#장치 추가 함수 및 컨픽에 저장
def AddDevice(CamID):
    #공백 제거
    CamID = CamID.strip()
    
    if (CamID == "0"):
        return -1
    
    elif (CamID in cf.GetDeviceConf()):
        return False
        
    else:
        File_conf = open("./data/DeviceList.conf", "a")
        File_conf.write(CamID)
        File_conf.write("\n")
        File_conf.close()
        
        PL.EventLog("Camera Added [ID : " + CamID + "]", Type="INFO")
        
        return True