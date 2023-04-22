import math


class Object:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y

    def distance_to(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)



class CheckTool:
    def __init__(self):
        pass

    """ Tạo name grid với với numerate, một cột sẽ giữ nguyên và hàng sẽ tăng dần từ 0 tới number_name được ghi
        Nếu reserve = True thì hàng sẽ giữ nguyên và cột sẽ tăng dần từ 0 tới number_name được ghi"""
    def create_name_grid(fix="", number_name=11,start = None, to= None, reserve = False):
        list_name = []
        if reserve == False:
            for i, c in enumerate(str(fix)*(number_name)):
                list_name.append(f"grid_{i}_{c}")
            return list_name[start:to]
        else:
            for i, c in enumerate(str(fix)*(number_name)):
                list_name.append(f"grid_{c}_{i}")
            return list_name[start:to]

    def distance(x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

class RectangularArea:
    def __init__(self, idx1, idx2, x1, y1, x2, y2):
        self.left = min(x1, x2)
        self.top = min(y1, y2)
        self.right = max(x1, x2)
        self.bottom = max(y1, y2)
        self.index = (idx1, idx2)
        self.index_name = "grid_{}_{}" .format(idx1, idx2)
        self.objects = {}
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

    """ kiểm tra đối tượng có đang trong grid không """
    def contains(self, x, y):
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    """ thêm đối tượng và thông tin vào grid """
    def add_object(self, obj_id, frame, datetime, coords):
        self.objects[obj_id] = [frame, datetime, coords, None, None, None]

    """ loại bỏ id đối tượng ra khỏi grid (id này có trong class) """
    def remove_object(self, obj_id):
        if obj_id in self.objects:
            del self.objects[obj_id]

    """ kiểm tra object id này có từng trong grid không """
    def check_object(self, obj_id):
        return obj_id in self.objects

    """ Lấy tọa độ tâm của grid """
    def get_grid_center_cood(self):
        return (int((self.x1 + self.x2) / 2)), (int((self.y1 + self.y2) / 2))

    """ Lấy tọa độ góc trên và góc dưới của grid"""
    def get_grid_cood(self):
        return (self.x1, self.y1, self.x2, self.y2)

    """ Lấy tên của grid"""
    def get_grid_name(self):
        return f"({self.index[0]}, {self.index[1]})"

    """ Nếu grid hiện tại không nằm trong root grid, tiến hành xem xét khu vực 2 grid kế bên và 3 grid phía sau xe
        _ TH1: nếu grid nào có cùng id xe và frame gần nhất thì sẽ dùng nó để tính vận tốc tức thời
        _ TH2 :trường hợp frame lớn nhất gây ra việc chia 0 gây vô nghiệm thì lấy frame lớn thứ hai,...
        _ Th3: nếu tòa bộ frame không có => xóa id này trong grid hiện tại, và root grid """
    def calculate_instant_speed(self,obj_id, dict_grids, root = None):
        i, j = self.index[0], self.index[1]
        if i in [0,1,2,4]:
            grids_around = []
            grids_around.append("grid_{}_{}" .format(i-1, j))
            grids_around.append("grid_{}_{}" .format(i+1, j))
            grids_around.append("grid_{}_{}" .format(i, j+1))
            grids_around.append("grid_{}_{}" .format(i-1, j+1))
            grids_around.append("grid_{}_{}" .format(i+1, j+1))
        else:
            grids_around = []
            grids_around.append("grid_{}_{}" .format(i-1, j))
            grids_around.append("grid_{}_{}" .format(i+1, j))
            grids_around.append("grid_{}_{}" .format(i, j-1))
            grids_around.append("grid_{}_{}" .format(i+1, j-1))
            grids_around.append("grid_{}_{}" .format(i-1, j-1))

        info_grids = [dict_grids[grid] for grid in grids_around if grid in dict_grids]
        if not info_grids:
            return

        root_grids_with_obj = [root_grid for root_grid in info_grids if obj_id in root_grid.objects]
        if root_grids_with_obj:
            max_frames_coords = [(root_grid.objects[obj_id][0], root_grid.objects[obj_id][2]) for root_grid in root_grids_with_obj]
            sorted_max_frames_coords = sorted(max_frames_coords, key=lambda x: x[0])

            for h_frame, h_coor in sorted_max_frames_coords:
                distance = CheckTool.distance(h_coor[0],h_coor[1],self.objects[obj_id][2][0],self.objects[obj_id][2][1])
                time_diff = self.objects[obj_id][0] - h_frame

                if time_diff != 0:
                    self.objects[obj_id][3] = round((distance*0.035)*3.6/((self.objects[obj_id][0] - h_frame)/30),2)
                    print("Xe ", obj_id, "đã vào grid ({}, {}) có vận tốc là {} km/h".format(self.index[0], self.index[1], self.objects[obj_id][3]))
                    return

            # Nếu index hiện tại không nằm trong root grid thì sẽ remove id này ra khỏi root
            # Sau đó sẽ đi qua từng root grid và remove id khỏi root grid => sẽ không còn thông tin id này
            # Điều này để đảm bảo id được duy trì ổn định
            if len(root) > 0 and (self.index_name not in root):
                self.remove_object(obj_id)
                for root_grid in (dict_grids[root_grid] for root_grid in root):
                    root_grid.remove_object(obj_id)
                print("KHÔNG CÓ FRAME XUNG QUANH ĐỂ TÍNH => XÓA ID XE {} NÀY".format(obj_id))
                return

        else:
            print("Xe ", obj_id, "trong grid ({}, {}) không thể tính vận tốc".format(self.index[0], self.index[1]))

    """ Hàm này sẽ giúp thu thập vận tốc trung bình không gian
        Vận tốc trung bình không gian sẽ được tính dựa trên chiều dài quan trắc
        Tức từ khi bắt đầu vào root grid cho tới khi vừa chạm end grid"""
    def calculate_spatial_speed(self,obj_id, root_grids, dict_grids):
        frame_end = self.objects[obj_id][0]
        frame_start = None
        for grid in root_grids:
            if (grid in dict_grids) and (dict_grids[grid].check_object(obj_id)):
                frame_start = dict_grids[grid].objects[obj_id][0]
                break

        if frame_start is None:
            return

        distance = 320 * 0.02
        time = (frame_end - frame_start) / 30
        self.objects[obj_id][4] = round(distance*3.6 / time, 2)
        print(f"Xe {obj_id} có vận tốc trung bình không gian là {self.objects[obj_id][4]} km/h")

        "Dùng phần code dưới đây khi bắt đầu thu thập data, vì nó sẽ giúp giảm lượng dữ liệu sau khi thu xong"
        # [dict_grids[grid].remove_object(obj_id) for grid in dict_grids]
        # print("Đã del xong all object")

    """ Gán vị trí làn hiện tại cho id khi vào grid cuối """
    def add_name_lane(self,obj_id,grid_under, grid_on):
        if self.index_name in grid_under:
            self.objects[obj_id][5] = 'Under'
        elif self.index_name in grid_on:
            self.objects[obj_id][5] = 'On'



    """ Hiển thị thông tin nếu có đối tượng vào grid """
    def show_objects(self):
        print("Xe ", self.objects, "đã vào grid ({}, {})".format(self.index[0], self.index[1]))

