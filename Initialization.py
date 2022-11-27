'''
모든 서브 모듈 중에 가장 최상위에 있는 모듈이다.

이 모듈에서 초기화가 제대로 이뤄지지 않으면, ProgramLog, AddCam 등의 모든 개체들이 동작하지 않는다.
반드시 프로그램을 실행할 때 아래의 함수를 실행해야 한다.

Example)
import Initialization as Init
if(Init.onLoad() == True):
    PL.onStarted()
    PL.EventLog("초기화 성공", "INFO")
'''
#기본 모듈
import os, sys, time
import json

#기초 설정 변수
DvcList = "DeviceList.json"
ProgramConf = "main.json"
MainLoc = os.getcwd().replace("\\","/") + "/"

#프로그램 시작 시간 지정 (로그 파일명 변환에 사용됨)
StartTime = time.strftime("%Y%m%d_%H%M%S", time.localtime()) #20221020_142107 과 같은 형식의 포맷지정

#데이터 폴더 및 로그 파일의 존재유무 확인
def onLoad():
    try:
        Integrity_check()
        MakeDirectory()
        MakeConfFile()
        
        #메인 작업 폴더로 되돌아 간다. (모든 경로 오류 방지)
        os.chdir(MainLoc)
        return True
    except:
        return False

#디렉토리 생성
def MakeDirectory():
    try:
        os.chdir(MainLoc + "data")
    except:
        #데이터 폴더 생성후 이동
        os.mkdir(MainLoc + "data")        
        os.chdir(MainLoc + "data")
        
        #data 폴더 안에서 로그 폴더가 생성되게 함
        os.mkdir(os.getcwd() + "/log")
        
        #이미지 폴더 생성, 이미지 폴더는 2가지로 나뉜다.
        os.mkdir(MainLoc + "/images")
        os.chdir(MainLoc + "/images")
        
        os.mkdir(os.getcwd() + "/User_Alert")
        os.mkdir(os.getcwd() + "/System_Alert")

#컨픽 파일 생성
def MakeConfFile():
    #Data 폴더 안에 모든 컨픽 파일이 생기게 함
    SubLoc = MainLoc + "/data/"
    
    try:
        F1 = open(SubLoc + DvcList, "r")
        F2 = open(SubLoc + ProgramConf, "r")
        
        F1.close()
        F2.close()
    except:
        F1 = open(SubLoc + DvcList, "w")
        F2 = open(SubLoc + ProgramConf, "w")
        
        #기본 카메라 장치 지정        
        default_device = { "0" : "0" }
        json.dump(default_device, F1, indent=2)
        
        #기본 설정 지정
        conf = {
            "SC_Delay" : 5,
            "Accuracy" : 0.55,
            "Default_Device" : 0
        }
        
        json.dump(conf, F2, indent=2)
        
        F1.close()
        F2.close()
        
#메인 폴더의 무결성 검사 (폴더가 없는 경우에만 복구한다.)
def Integrity_check():
    mainFiles = [
            "data",
            "data/log",
            "images",
            "images/System_Alert",
            "images/User_Alert"
        ]

    for i in mainFiles:
        if os.path.exists(MainLoc + i) == False:
            if "." not in i:
                os.mkdir(MainLoc + i)
                print("Main Directory", i, "was recreated.")
                print("But previous data was removed.")
                
# .exe파일로 만들시 필요 (Appdata 의 경로)
def resource_path(*relative_Path_AND_File):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(
            sys,
            '_MEIPASS',
            os.path.dirname(os.path.abspath(__file__))
        )
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, *relative_Path_AND_File)