import cv2
import numpy as np
from object_detection import ObjectDetection
from deep_sort.deep_sort import Deep
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, JSON, Text, Float, DateTime
import pandas as pd
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# DATABASE ===================================================================================
# Thông tin database
DATABASE_URI = 'postgresql+psycopg2://postgres:12345678@localhost:5432/MOTORBIKE_INFO'
engine = create_engine(DATABASE_URI)
Base = declarative_base(bind=engine)

class Motorbike(Base):
    __tablename__ = 'speed_motorbike_test'

    id = Column(Integer, primary_key=True)
    speed = Column(Float)
    location = Column(JSON)
    first_time_track = Column(DateTime)
    second_time_track = Column(DateTime)

# Truncate trước khi insert data vào để tránh duplicate
Base.metadata.create_all()
Session = sessionmaker(bind=engine)
session = Session()
session.execute(Motorbike.__table__.delete())
session.commit()
# ============================================================================================


# Load Object Detection
od = ObjectDetection("yolov4-custom_last.weights", "yolov4_test.cfg")
od.load_class_names("classes.txt")
od.load_detection_model(image_size=832, # 416 - 1280
                        nmsThreshold=0.4,
                        confThreshold=0.5)


# Load Object Tracking Deep Sort
deep = Deep(max_distance=0.7,
            nms_max_overlap=1,
            n_init=3,
            max_age=30,
            max_iou_distance=0.7)
tracker = deep.sort_tracker()


cap = cv2.VideoCapture("test.mp4")

# Hỗ trợ ghi file (Tạm thời không cần)
# path = r"D:\\Project\\Motorbike project\\source code\\"
# writer = None
# f = 0

# Biến hỗ trợ
frame_counter = 0 # Để ghi frame khi xe vào từng vùng, bắt đầu từ frame 0
timestamp = datetime.datetime(2012, 10, 30, 8, 0, 0, 000000) #Thời gian dự định tạo, bắt đầu lúc 8:00 ngày 2012/12/30
motorbike_current_location = {} # Ghi lại thông tin motorbike, với key = id của user, và value là list các index location user đã đi qua
mask = cv2.imread("mask1.jpg") # Mask chỉ dùng để detect một phần frame
polygon_PT1 = np.array([(880, 437), (880, 273), (979, 273), (979, 437)]) # PT làn từ phải sáng trái
polygon_PT2 = np.array([(601, 273), (601, 437), (880, 437), (880, 273)])
polygon_PT3 = np.array([(493, 437), (493, 273), (601, 273), (601, 437)])
polygon_TP1 = np.array([(493, 626), (493, 445), (601, 445), (601, 626)]) # TP làn từ trái sang phải
polygon_TP2 = np.array([(880, 445), (601, 445), (601, 626), (880, 626)])
polygon_TP3 = np.array([(880, 445), (980, 445), (980, 626), (880, 626)])

# PT sẽ có index 0,1,2 và TP sẽ có index 3,4,5
all_polygons = [polygon_PT1, polygon_PT2, polygon_PT3, polygon_TP1, polygon_TP2, polygon_TP3]

line_1 = np.array([(601, 0), (601, 720)]) # 2 line để hỗ trợ tính speed
line_2 = np.array([(880, 0), (880, 720)])
all_lines = [line_1, line_2]

# Ghi lại log
PT1_to_PT2 = {} # Chú ý: key = id của user, value = [a,b] với a là value của frame được log, và b là value của datetime được log
PT2_to_PT3 = {}


TP1_to_TP2 = {}
TP2_to_TP3 = {}

speed_motorbike = {}


# Load từng frame
while True:
    ret, frame_orgin = cap.read()
    if not ret:
        break

    frame = cv2.bitwise_and(frame_orgin,mask) # Tạo mask với frame thực

    # Tính thời gian bằng frame và datetime==========================
    frame_counter += 1
    timestamp += datetime.timedelta(seconds=1/30)
    # ===============================================================

    """ 1. Object Detection """
    (class_ids, scores, boxes) = od.detect(frame)
    # for class_id, score, box in zip(class_ids, scores, boxes):
    #     x, y, w, h = box
    #     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)



    """ 2. Object Tracking """
    features = deep.encoder(frame, boxes)
    detections = deep.Detection(boxes, scores, class_ids, features)

    tracker.predict()
    (class_ids, object_ids, boxes) = tracker.update(detections)

    for class_id, object_id, box in zip(class_ids, object_ids, boxes):
        (x, y, x2, y2) = box
        class_name = od.classes[class_id]

        if class_name in ["motorbike"]:
            color = od.colors[class_id]
            cx = int((x + x2) / 2)
            cy = int((y + y2) / 2)
            cv2.circle(frame, (cx, cy), 4, color, -1)
            cv2.circle(frame_orgin, (cx, cy), 4, color, -1)

            # Lấy thông tin history về id polygon của id user, nếu không có id sẽ lấy value là None
            motorbike_previous_location = motorbike_current_location.get(object_id, None)


            # Ta có 6 polygon, kết hợp với enumerate ta sẽ có index
            for polygon_idx, p in enumerate(all_polygons):
                is_inside = cv2.pointPolygonTest(p, (cx, cy), False) # Check xem object hiện tại nằm trong polygon không

                if is_inside > 0 and motorbike_previous_location is None: # Nếu có trong object và không có history
                    motorbike_current_location[object_id] = [polygon_idx] # Cho vào dict của history
                    break

                elif (is_inside > 0) and (polygon_idx not in motorbike_previous_location): # Nếu có trong object và có history
                    #print("Motorbike {} moved from {} to {}".format(object_id, motorbike_previous_location[-1], polygon_idx))

                    # PT 0,1,2
                    # Quy tắc PT mà không có 0 xem như không hợp lệ và remove đi id user trong history
                    # TH1 của PT: Nếu PT (trước) = 0 và PT (Hiện tại) = 1 => Thêm vào PT1_to_PT2 (Có thông tin vùng 1 của PT)
                    # TH2 của PT: Nếu PT (trước) = 0 và 1 và PT (Hiện tại) = 2 => Thêm vào PT2_to_PT3 (Có thông tin vùng 1,2 của PT)
                    if (0 in motorbike_previous_location) and polygon_idx == 1:
                        PT1_to_PT2[object_id] = [frame_counter]
                        PT1_to_PT2[object_id].append(timestamp)
                        motorbike_current_location[object_id].append(1)


                    elif 0 in motorbike_previous_location and 1 in motorbike_previous_location and polygon_idx == 2:
                        PT2_to_PT3[object_id] = [frame_counter]
                        PT2_to_PT3[object_id].append(timestamp)
                        motorbike_current_location[object_id].append(2)
                        # Tính vận tốc xe, độ chính xác phụ thuộc vào 1 pixel = ? meter trong thực tế
                        speed_motorbike[object_id] = round((279*0.035)*3.6/((PT2_to_PT3[object_id][0] - PT1_to_PT2[object_id][0])/30),2)
                        print("Motorbike {} update location {} and speed is {} km/h".format(object_id, 2, speed_motorbike[object_id]))

                        Session = sessionmaker(bind=engine)
                        session = Session()
                        speed_data = {'id': object_id,
                                      'speed': speed_motorbike[object_id],
                                      'location': motorbike_current_location[object_id],
                                      'first_time_track':PT1_to_PT2[object_id][-1],
                                        'second_time_track':PT2_to_PT3[object_id][-1]}
                        # Insert the data
                        motorbike = Motorbike(**speed_data)
                        session.add(motorbike)
                        session.commit()


                    # TP 3,4,5
                    # Quy tắc TP mà không có 3 xem như không hợp lệ và remove đi id user trong history
                    # TH1 của PT: Nếu TP (trước) = 3 và TP (Hiện tại) = 4 => Thêm vào TP1_to_TP2 (Có thông tin vùng 1 của TP)
                    # TH2 của PT: Nếu TP (trước) = 0 và 1 và TP (Hiện tại) = 2 => Thêm vào TP2_to_TP3 (Có thông tin vùng 1,2 của TP)
                    elif (3 in motorbike_previous_location) and polygon_idx == 4:
                        TP1_to_TP2[object_id] = [frame_counter]
                        TP1_to_TP2[object_id].append(timestamp)

                        motorbike_current_location[object_id].append(4)
                    elif 3 in motorbike_previous_location and 4 in motorbike_previous_location and polygon_idx == 5:
                        TP2_to_TP3[object_id] = [frame_counter]
                        TP2_to_TP3[object_id].append(timestamp)

                        motorbike_current_location[object_id].append(5)
                        # Tính vận tốc xe
                        speed_motorbike[object_id] = round((279*0.035)*3.6/((TP2_to_TP3[object_id][0] - TP1_to_TP2[object_id][0])/30),2)
                        print("Motorbike {} update location {} and speed is {} km/h".format(object_id, 5, speed_motorbike[object_id]))

                        Session = sessionmaker(bind=engine)
                        session = Session()
                        speed_data = {'id': object_id,
                                      'speed': speed_motorbike[object_id],
                                      'location': motorbike_current_location[object_id],
                                      'first_time_track':TP1_to_TP2[object_id][-1],
                                        'second_time_track':TP2_to_TP3[object_id][-1]}
                        # Insert the data
                        motorbike = Motorbike(**speed_data)
                        session.add(motorbike)
                        session.commit()




                    # TH xe đi ngược chiều ở TP và PT
                    # TH3 của PT: Nếu PT (hiện tại) = 2 và PT(trước) = None (Hàm ý đi ngược chiều)
                    # => Không add vào PT2_to_PT3 và không check khi vào PT1 và PT2
                    elif 0 not in motorbike_previous_location:
                        del motorbike_current_location[object_id]
                        print("Motorbike {} is deleted".format(object_id))
                        break

                    # TH3 của TP: Nếu TP (hiện tại) = 5 và TP(trước) = None (Hàm ý đi ngược chiều)
                    # => Không add vào PT2_to_PT3 và không check khi vào TP1 và TP2
                    elif 3 not in motorbike_previous_location:
                        print("Motorbike {} is deleted".format(object_id))
                        del motorbike_current_location[object_id]
                        break


                    # Đây là phần loại đi những id không hợp lệ trong dict
                    # TH1: Tức những id mà không bắt đầu từ 0 hoặc 3 sẽ bị loại
                    # TH2: Tiếp theo những id phải nằm trong PT1_to_PT2 hoặc TP1_to_TP2 vì tức những 2 đảm bảo đi qua 2 vùng mới được giữ lại
                    # TH3: Vì vùng 3 rất khó kiểm tra do nhiều id đột ngột mất ở vùng 2 nên không có ở vùng 3
                    # => Nếu độ dài dict mà lớn hơn 2 lần độ dài list ở 2 làn TP và PT thì sẽ tiến hành clear lại một lần nữa
                    # => Sẽ có khả năng nó remove một số id hợp lệ, nhưng nó sẽ remove rất nhiều id thừa
                    # => Ngoài ra cũng cần cho ID vùng 2,3 = id vùng 1,2. Vì những id đảm bảo đi qua cả 3 vùng mới vào được set 2,3
                    motorbike_current_location = {key:value for key,value in motorbike_current_location.items() if (0 in value or 3 in value) and (key in PT1_to_PT2.keys() or key in TP1_to_TP2.keys())}
                    if (len(PT1_to_PT2) > 1) and (len(TP1_to_TP2) > 1) and (len(PT2_to_PT3) > 1) and (len(TP2_to_TP3) > 1):
                        if len(motorbike_current_location) / (len(PT2_to_PT3)+len(TP2_to_TP3)) >= 2:
                            motorbike_current_location = {key:value for key,value in motorbike_current_location.items() if (0 in value or 3 in value) and (key in PT2_to_PT3.keys() or key in TP2_to_TP3.keys())}
                            print("Difference over 2 times")
                            keys_to_remove = []
                            for k in PT1_to_PT2:
                                if k not in PT2_to_PT3:
                                    keys_to_remove.append(k)

                            for k in keys_to_remove:
                                del PT1_to_PT2[k]

                            for k1 in TP1_to_TP2:
                                if k not in TP2_to_TP3:
                                    keys_to_remove.append(k1)

                            for k1 in keys_to_remove:
                                del TP1_to_TP2[k1]



                    print("List after update",motorbike_current_location)
                    print("Id PT region 1 to 2: ", PT1_to_PT2)
                    print("Id PT region 2 to 3: ", PT2_to_PT3)
                    print("Id TP region 1 to 2: ", TP1_to_TP2)
                    print("Id TP region 2 to 3: ", TP2_to_TP3)
                    print("Speed: ", speed_motorbike)


        cv2.rectangle(frame_orgin, (x, y), (x2, y2), color, 2)
        cv2.rectangle(frame, (x, y), (x2, y2), color, 2)
        # cv2.rectangle(frame, (x, y), (x + len(class_name) * 20, y - 30), color, -1)
        # cv2.putText(frame, class_name + " " + str(object_id), (x, y - 10), 0, 0.40, (255, 255, 255), 2)
        cv2.putText(frame_orgin, class_name + " " + str(object_id), (x, y - 10), 0, 0.40, (255, 255, 255), 1)
        cv2.putText(frame, class_name + " " + str(object_id), (x, y - 10), 0, 0.40, (255, 255, 255), 1)
        # Để đảm bảo nếu tập dict của speed có value và object_id phù hợp thì mới vẽ ra để tránh error
        if len(speed_motorbike) > 0 and object_id in speed_motorbike.keys():
            cv2.putText(frame, str(speed_motorbike[object_id]) + " km/h", (x, y + 50), 0, 0.40, (255, 255, 255), 1)
            cv2.putText(frame_orgin, str(speed_motorbike[object_id]) + " km/h", (x, y + 50), 0, 0.40, (255, 255, 255), 1)



    # Vẽ vùng cần xét
    cv2.polylines(frame_orgin, [polygon_PT1], True, (195, 77, 0), 3)
    cv2.polylines(frame_orgin, [polygon_PT2], True, (11, 11, 236), 3)
    cv2.polylines(frame_orgin, [polygon_PT3], True, (195, 77, 0), 3)

    cv2.polylines(frame_orgin, [polygon_TP1], True, (21, 187, 209), 3)
    cv2.polylines(frame_orgin, [polygon_TP2], True, (65, 170, 11), 3)
    cv2.polylines(frame_orgin, [polygon_TP3], True, (21, 187, 209), 3)

    cv2.polylines(frame, [polygon_PT1], True, (195, 77, 0), 3)
    cv2.polylines(frame, [polygon_PT2], True, (11, 11, 236), 3)
    cv2.polylines(frame, [polygon_PT3], True, (195, 77, 0), 3)

    cv2.polylines(frame, [polygon_TP1], True, (21, 187, 209), 3)
    cv2.polylines(frame, [polygon_TP2], True, (65, 170, 11), 3)
    cv2.polylines(frame, [polygon_TP3], True, (21, 187, 209), 3)

    # Vẽ line cần xét
    cv2.line(frame_orgin, line_1[0], line_1[1],(0, 255, 0), 3)
    cv2.line(frame_orgin, line_2[0], line_2[1], (0, 255, 0), 3)

    cv2.line(frame, line_1[0], line_1[1],(0, 255, 0), 3)
    cv2.line(frame, line_2[0], line_2[1], (0, 255, 0), 3)

# Dùng để ghi video ================================================================================================
#     if writer is None:
#         # Constructing code of the codec
#         # to be used in the function VideoWriter
#         fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#
#             # Writing current processed frame into the video file
#             # Pay attention! If you're using Windows, yours path might looks like:
#             # r'videos\result-traffic-cars.mp4'
#             # or:
#             # 'videos\\result-traffic-cars.mp4'
#         writer = cv2.VideoWriter(path + 'result-demo2.mp4', fourcc, 30,(frame.shape[1], frame.shape[0]), True)
#
#         # Write processed current frame to the file
#     writer.write(frame)
# ===================================================================================================================
    cv2.imshow("Frame", frame_orgin)
    # cv2.imshow("Mask", mask)
    # cv2.imshow("Region", frame)

    key = cv2.waitKey(1)
    if key == 27:
        break



cap.release()
# writer.release()
cv2.destroyAllWindows()
