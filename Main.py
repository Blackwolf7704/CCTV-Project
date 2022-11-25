#기본 모듈
import sys, time

#내부 모듈
import Initialization as Init
import ProgramLog as PL

#앱 시작을 위한 모듈
from PyQt6.QtWidgets import QApplication

if __name__ == "__main__":    
    #초기화 성공 시, 메인 프로그램 실행
    if Init.onLoad() == True:
        #프로그램 로그 시작
        PL.onStarted()
        
        #UI를 import 해서 실제 GUI 표시
        import UI_Main
        
        app = QApplication(sys.argv)
        
        myWindow = UI_Main.MainGUI()
        myWindow.show()
        app.exec()
    
    else:
        print("프로그램을 실행할 수 없습니다.")