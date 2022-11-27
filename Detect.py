#Detect Code
import cv2
import numpy as np
import torch, torchvision

# Constants.
INPUT_WIDTH = 640           #입력 너비
INPUT_HEIGHT = 640          #입력 높이

#NMS (Non-Maximum Suppression) 수치이다.
#값이 높거나, 작으면 상자의 개수가 줄어든다. (https://wikidocs.net/142645)
NMS_THRESHOLD = 0.45
stride = 32

#Model Load
Model_Name = "detect.onnx"

import onnxruntime
session = onnxruntime.InferenceSession(Model_Name)
im = torch.zeros((1, 3, 640, 640)).cpu().numpy()
warm = session.run([session.get_outputs()[0].name], {session.get_inputs()[0].name:im})[0]


'''
#Exe_Build
import onnxruntime
import Initialization as Init
session = onnxruntime.InferenceSession(Init.resource_path("./Model/" + Model_Name))
im = torch.zeros((1, 3, 640, 640)).cpu().numpy()
warm = session.run([session.get_outputs()[0].name], {session.get_inputs()[0].name:im})[0]
'''

def Detect(frame, MIN_Accuracy):
    #https://towardsdatascience.com/tensors-and-arrays-2611d48676d5
    #텐서 형식이 ndarray보다 성능 개선이 있다.
    
    #전처리 과정 (Yolov5 에서 추출) 각 함수의 추출한 부분 나열
    ################################
    #augmentations.py (LETTERBOX)
    input_shape = frame.shape[:2]
    set_shape = (640, 640)
    
    dw, dh = set_shape[1] - input_shape[1], set_shape[0] - input_shape[0]
    
    dw /= 2
    dh /= 2
    
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))

    im = [cv2.copyMakeBorder(frame, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114,114,114))]
    
    ################################
    #detect im data
    im = np.stack(im, 0)

    img = im[..., ::-1].transpose((0, 3, 1, 2))  # BGR to RGB, BHWC to BCHW
    img = np.ascontiguousarray(img)
    
    im = torch.from_numpy(img)
    im = im.float()
    im /= 255
    
    ################################
    #common.py (FORWARD)
    im = im.cpu().numpy()
    pred = session.run([session.get_outputs()[0].name], {session.get_inputs()[0].name:im})[0]
    pred = torch.tensor(pred)

    ################################
    #non_max_suppression.py
    #정확도가 기준을 넘는지 검사한다 (반환형은 True / False)
    bs = pred.shape[0]
    xc = pred[..., 4] > MIN_Accuracy

    res = [torch.zeros((0, 6), device=pred.device)] * bs
    for xi, x in enumerate(pred):
        # Pred의 True 값만 x에 넣는다.
        x = x[xc[xi]]
        
        # Compute conf
        x[:, 5:] *= x[:, 4:5]
        
        #box
        box = convertaxis(x[:, :4])
        
        conf, j = x[:, 5:].max(1, keepdim=True)
        x = torch.cat((box, conf, j.float()), 1)[conf.view(-1) > MIN_Accuracy]
        
        # Batched NMS
        c = x[:, 5:6] * (0 if False else 7680)  # classes
        boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
        i = torchvision.ops.nms(boxes, scores, NMS_THRESHOLD)  # NMS
        
        res[xi] = x[i]

    ################################
    #process predictions
    Accuracy = []
    
    for i, det in enumerate(res):
        if len(det):
            pad = (set_shape[1] - input_shape[1]) / 2, (set_shape[0] - input_shape[0]) / 2
            det[:, [0, 2]] -= pad[0]
            det[:, [1, 3]] -= pad[1]
            
            for *xyxy, conf, cls in reversed(det):
                p1, p2 = (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3]))
                
                Accuracy.append(conf.item())
                cv2.rectangle(frame, p1, p2, (0,0,255), 2)
                
    return frame, Accuracy
            

def convertaxis(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y