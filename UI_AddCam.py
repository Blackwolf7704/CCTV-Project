#기본 모듈
import cv2
from PyQt6.QtWidgets import *
from PyQt6 import uic

#내부 기능 모듈
import ProgramLog as PL
import Configuration as cf

#변수 목록
#메시지박스의 버튼을 편하게 사용하기 위해 정의
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
    
    #추가 버튼의 이벤트 정의
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
        
        #비디오가 열려 있을 경우 실행
        if temp.isOpened() == True:
            temp.release() #잠시 연결 확인을 했으므로 바로 release를 한다.
            
            #장치 등록을 할 때 경우의 수를 지정
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

    #종료 클릭 버튼을 누를 시, False와 자신의 창을 닫는다.
    def ClickCancelBtn(self):
        self.close()
        return False
        
#장치 추가 함수 및 컨픽에 저장
def AddDevice(CamID):
    #공백 제거
    CamID = CamID.strip()
    
    #기본 장치일 경우, -1을 반환
    if (CamID == "0"):
        return -1
    
    #이미 있는 장치일 경우 False를 반환
    elif (CamID in cf.GetDeviceConf()):
        return False
        
    else:
        cf.AddDeviceConf(CamID)
        
        PL.EventLog("Camera Added [ID : " + CamID + "]", Type="INFO")
        
        return True