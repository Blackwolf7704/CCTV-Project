#기본 제공 모듈
import time, os

#내부 모듈
import Initialization as Init

#로그파일 이름
LogName = "ProgramLog.log"

#로그 파일의 경로 지정
LogDirLoc = "data/log/"
LogDir = Init.MainLoc + LogDirLoc
LogLocation = LogDir + LogName

#포맷 형식을 딕셔너리로 해서 변경 불가하게 한다.
Format_Type = { 0:"ERROR", 1:"WARNING", 2:"ALERT", 3:"INFO" , 4:"DEBUG"}

#발생하는 이벤트에 대한 로그 기록
#파일을 함수에서 열고 닫는 이유는 프로그램의 안정성 때문에 사용한다.
#또한, 파일이 열려 있는 동안에 안에 있는 내용물을 확인할 수 없기 때문에 함수 안에서 열고 닫는 것을 채택했다.
def EventLog(message, Type=None):
    #로그 파일 열기
    LogFile = open(LogLocation, 'a', encoding='UTF-8')
    
    #현재 시간에 대한 로그 포맷 (년월일 AM/PM 시분초)
    NowTime = GetTime(1)
    
    #FORMAT
    if(Format_Type[0] == Type):   Format = "[" + NowTime + "] [ERROR] : " + message + "\n"
    elif(Format_Type[1] == Type): Format = "[" + NowTime + "] [WARNING] : " + message + "\n"
    elif(Format_Type[2] == Type): Format = "[" + NowTime + "] [ALERT] : " + message + "\n"
    elif(Format_Type[3] == Type): Format = "[" + NowTime + "] [INFO] : " + message + "\n"
    elif(Format_Type[4] == Type): Format = "[" + NowTime + "] [DEBUG] : " + message + "\n"
    else:
        Format = "[" + NowTime + "] : " + message + "\n"
    
    LogFile.write(Format)
    LogFile.close()

#프로그램이 켜질 때, 종료될 때 로그 기록
def onStarted():
    #초기 로그 파일은 무조건 오버라이딩
    F = open(LogLocation, 'w', encoding='UTF-8')
    F.close()
    
    #이벤트 로그에 시작을 기록함
    EventLog("Program Started", "INFO")
    
#프로그램이 종료될 때, 로그 기록 및 파일명 변경
def onEnded():
    EventLog("Program Ended", "INFO")
    
    #로그 기록이 끝난 파일의 이름 변경
    try: os.rename(LogLocation, LogDir + Init.StartTime + ".log")
    except Exception as EMessage: print(EMessage)
    
#로그 전체를 불러오는 함수
def GetNowLog():
    Temp = open(LogLocation, "r")
    res = Temp.readlines()
    Temp.close()
    
    return res

#로그 파일의 가장 마지막 부분을 읽어온다.
def GetLastLog():
    Temp = open(LogLocation, "r")
    res = Temp.readlines()
    Temp.close()

    res = res[len(res) - 1].strip()
    
    return res
    
#지정된 포맷에 따른 현재 시간값 반환
def GetTime(Type=1):
    if Type == 0: return time.strftime("%Y-%m-%d %p %H:%M:%S", time.localtime()) #YYYY-MM-DD AM/PM HH:MM:SS 형식
    else:         return time.strftime("%Y-%m-%d_%H%M%S", time.localtime())      #YYYY-MM-DD_HHMMSS 형식