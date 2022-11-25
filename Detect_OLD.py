def Detect(frame, MIN_Accuracy):
    #최종 출력될 이미지
    output_Image = frame.copy()

    #모델의 출력 개수
    rows = pred.shape[1]
    
    #이미지 높낮이 계산 (가장 마지막 값은 채널값이므로 제외)
    image_height, image_width = frame.shape[:2]
    x_factor = image_width / INPUT_WIDTH
    y_factor =  image_height / INPUT_HEIGHT

    #정확도에 따른 상자 위치 및 정확도 기록
    confidences = []
    boxes = []
    
    for r in range(rows):
        row = pred[0][r]
        confidence = row[4]
        
        if confidence >= CONFIDENCE_THRESHOLD:
            confidences.append(confidence)
            cx, cy, w, h = row[0], row[1], row[2], row[3]
            left = int((cx - w/2) * x_factor)
            top = int((cy - h/2) * y_factor)
            width = int(w * x_factor)
            height = int(h * y_factor)
            box = np.array([left, top, width, height])
            boxes.append(box)

    #한 개체에 너무 많은 상자가 감지되는 것 제거
    indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, CONFIDENCE_THRESHOLD)
    
    #정확도가 가장 높은 것만 리스트에 저장한다. 전역 변수 사용을 위해 global을 사용했다.
    Accuracy = []

    #최종 상자의 개수 만큼 원본 이미지에 출력
    for i in indices:
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]  

        cv2.rectangle(output_Image, (left, top), (left + width, top + height), (0,0,255), 2)
        
        Accuracy.append(confidences[i])
    
    return output_Image