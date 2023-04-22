import cv2
import numpy as np
import datetime
from object_detection import ObjectDetection
from deep_sort.deep_sort import Deep
from grid import RectangularArea, CheckTool

# Load Object Detection
od = ObjectDetection("yolov4-custom_last.weights", "yolov4_test.cfg")
od.load_class_names("classes.txt")
od.load_detection_model(image_size=832, # 416 - 1280
                        nmsThreshold=0.4,
                        confThreshold=0.3)

# Load Object Tracking Deep Sort
deep = Deep(max_distance=0.7,
            nms_max_overlap=1,
            n_init=3,
            max_age=15,
            max_iou_distance=0.7)
tracker = deep.sort_tracker()

mask = cv2.imread(r'D:\Project\Motorbike project\source code\new_mask.jpeg')
cap = cv2.VideoCapture("xemay_xoay_ngang_lan.mp4")

# Biến ______________________________________________________________________________________________
frame_count = 0 # Để ghi frame khi xe vào từng vùng, bắt đầu từ frame 0
timestamp = datetime.datetime(2019, 10, 30, 8, 0, 0, 000000) #Thời gian dự định tạo, bắt đầu lúc 8:00 ngày 2019/12/30
# Biến ______________________________________________________________________________________________

# Vẽ grid ____________________________________________________________________________________________
n_rows = 11
n_cols = 9

cell_width = 40
cell_height = 30

x_start = 577
y_start = 288

grids = {} # Nơi trữ biến grid với key: là tên grid - value: class grid
root_grids_on = CheckTool.create_name_grid(8,number_name=5)
root_grids_under = CheckTool.create_name_grid(0,number_name=11,start=5)
end_grids_on = CheckTool.create_name_grid(0,number_name=5)
end_grids_under = CheckTool.create_name_grid(8,number_name=11,start=5)

for r in range(n_rows):
    y1 = y_start + r * cell_height
    y2 = y_start + (r+1) * cell_height
    for c in range(n_cols):
        x1 = x_start + c * cell_width
        x2 = x_start + (c+1) * cell_width
        grids[f"grid_{r}_{c}"] = RectangularArea(r, c, x1, y1, x2, y2) #Tạo biến hàng loạt và chứa trong dict
        # print("grid {}, {}".format(r,c),x1, y1, x2, y2)
# Vẽ grid ____________________________________________________________________________________________


while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1
    timestamp += datetime.timedelta(seconds=1/30)
    frame_region = cv2.bitwise_and(frame,mask)
    """ 1. Object Detection """
    (class_ids, scores, boxes) = od.detect(frame_region)
    # for class_id, score, box in zip(class_ids, scores, boxes):
    #     x, y, w, h = box
    #     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    """ 2. Object Tracking """
    features = deep.encoder(frame_region, boxes)
    detections = deep.Detection(boxes, scores, class_ids, features)

    tracker.predict()
    (class_ids, object_ids, boxes) = tracker.update(detections)

    for class_id, object_id, box in zip(class_ids, object_ids, boxes):

        (x, y, x2, y2) = box
        class_name = od.classes[class_id]
        color = od.colors[class_id]

        if class_name in ["motorbike"]:
            color = od.colors[class_id]
            cx = int((x + x2) / 2)
            cy = int((y + y2) / 2)
            cv2.circle(frame, (cx, cy), 4, color, -1)
            cv2.circle(frame_region, (cx, cy), 4, color, -1)
            cv2.putText(frame, str(object_id), (cx -10 , cy ), 0, 0.60, (0, 0, 255), 2)
            cv2.putText(frame_region, str(object_id), (cx -10 , cy), 0, 0.60, (0, 0, 255), 2)


            # Đang có vấn đề ở đây
            current_grid = None
            for k1, v1 in grids.items():
                # Nếu không trong grids thì lướt
                if not v1.contains(cx, cy):
                    continue

                # Nếu trong grids gốc (root_grids) thì thêm thông tin vào grid gốc
                if ((k1 in root_grids_on) or (k1 in root_grids_under)) and (v1.check_object(object_id) == False):
                    v1.add_object(object_id, frame_count, timestamp, [cx, cy])
                # Nếu grids hiện tại không phải grid gốc thì check xem id có trong root grids gốc thì mới thêm, không thì không thêm
                else:
                    root_object_exist = sum(root_grid.check_object(object_id) for root_grid in (grids[key] for key in root_grids_on + root_grids_under))
                    end_object_exist = 1 if v1.index_name in end_grids_on + end_grids_under else 0


                    if (v1.check_object(object_id) == False) and (root_object_exist > 0):
                        v1.add_object(object_id, frame_count, timestamp, [cx, cy])
                        v1.calculate_instant_speed(object_id,grids,root_grids_on+root_grids_under)
                        if end_object_exist > 0:
                            v1.calculate_spatial_speed(object_id,root_grids_on+root_grids_under,grids)
                            v1.add_name_lane(object_id,end_grids_under,end_grids_on)
                            v1.show_objects()

                    elif (v1.check_object(object_id) == True) and (root_object_exist > 0) and (end_object_exist > 0):
                        cv2.putText(frame, str(v1.objects[object_id][4]) +" km/h", (cx - 20, cy+28), 0, 0.50, (255, 100, 0), 2)
                        cv2.putText(frame_region, str(v1.objects[object_id][4]) +" km/h", (cx - 25 , cy+28), 0, 0.50, (255, 100, 0), 2)

                    # Nếu có rồi thì hiển thị tốc độ đã được lưu vào từ trước ra
                    elif (v1.check_object(object_id) == True) and (root_object_exist > 0) and (end_object_exist == 0):
                        cv2.putText(frame, str(v1.objects[object_id][3]) +" km/h", (cx - 20, cy+28), 0, 0.50, (255, 0, 0), 2)
                        cv2.putText(frame_region, str(v1.objects[object_id][3]) +" km/h", (cx - 25 , cy+28), 0, 0.50, (255, 0, 0), 2)




        cv2.rectangle(frame, (x, y), (x2, y2), color, 2)
        # cv2.rectangle(frame, (x, y), (x + len(class_name) * 20, y - 30), color, -1)
        # cv2.putText(frame, class_name + " " + str(object_id), (x, y - 10), 0, 0.75, (255, 255, 255), 2)

        cv2.rectangle(frame_region, (x, y), (x2, y2), color, 2)
        # cv2.rectangle(frame_region, (x, y), (x + len(class_name) * 20, y - 30), color, -1)
        # cv2.putText(frame_region, class_name + " " + str(object_id), (x, y - 10), 0, 0.75, (255, 255, 255), 2)


    # Vẽ grid ____________________________________________________________________________________________
    for _,v2 in grids.items():
        cv2.rectangle(frame_region, (v2.get_grid_cood()[0], v2.get_grid_cood()[1]), (v2.get_grid_cood()[2], v2.get_grid_cood()[3]), (0, 255, 0), thickness=2)
        cv2.rectangle(frame, (v2.get_grid_cood()[0], v2.get_grid_cood()[1]), (v2.get_grid_cood()[2], v2.get_grid_cood()[3]), (0, 255, 0), thickness=2)
        cv2.putText(frame_region, v2.get_grid_name(), (v2.get_grid_center_cood()[0]- 20,v2.get_grid_center_cood()[1]), 0, 0.40, (255, 255, 255), 1)
        cv2.putText(frame, v2.get_grid_name(), (v2.get_grid_center_cood()[0] -20,v2.get_grid_center_cood()[1]), 0, 0.40, (255, 255, 255), 1)


    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)
    cv2.imshow("Frame Region", frame_region)

    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
