#default module
import json

#Custom Module
import Initialization as Init

#Init 모듈에 정의된 값 불러오기
DvcList = Init.DvcList
ProgramConf = Init.ProgramConf
MainLoc = Init.MainLoc

#설정 가져오기
def GetDeviceConf():
    F = open(MainLoc + "data/" + DvcList, "r")
    dvcList = json.load(F)
    F.close()
    
    return dvcList

def AddDeviceConf(DeviceID):
    Data = GetDeviceConf()
    Data[len(Data)] = DeviceID
    
    F = open(MainLoc + "data/" + DvcList, "w")
    json.dump(Data, F, indent=2)
    F.close()

def GetProgramConf():
    F = open(MainLoc + "data/" + ProgramConf, "r")
    data = json.load(F)
    F.close()
    
    return data

def SetProgramConf(Data):
    F = open(MainLoc + "data/" + ProgramConf, "w")
    json.dump(Data, F, indent=2)
    F.close()