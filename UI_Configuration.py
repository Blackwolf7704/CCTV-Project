#기본 모듈
from PyQt6.QtWidgets import *
from PyQt6 import uic

#내부 기능 모듈
import Configuration as cf

#변수 목록
QMBS = QMessageBox.StandardButton
form_class = uic.loadUiType("./UI/Config.ui")[0]

#Exe_Build
#import Initialization as Init
#form_class = uic.loadUiType(Init.resource_path("./UI/Config.ui"))[0]

class ConfigUI(QDialog, QWidget, form_class):
    def __init__(self):
        super().__init__()
        
        self.setupUi(self)
        self.show()
        
        self.Btn_OK.clicked.connect(self.ClickOkBtn)
        self.Btn_Cancel.clicked.connect(self.ClickCancelBtn)
        
    #설정 적용 버튼을 눌렀을 때, 실행되는 함수
    def ClickOkBtn(self):
        try:
            config_value = cf.GetProgramConf()
            config_value['SC_Delay'] = int(self.LE_ScDelay.text())
            config_value['Accuracy'] = float(self.LE_Accuracy.text())
            
            cf.SetProgramConf(config_value)
            
            QMessageBox.information(self, "Success", "설정이 적용되었습니다.", QMBS.Yes)
            self.accept()
        except Exception as E:
            QMessageBox.critical(self, "ERROR", "설정을 적용할 수 없습니다!", QMBS.Yes)
    
    #닫기 버튼을 눌렀을 때, 실행되는 함수
    def ClickCancelBtn(self):
        self.close()