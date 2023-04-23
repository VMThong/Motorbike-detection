# Motorbike-detection

## motorbike_project.py
Thông tin project
+ Project này sử dụng model YOLOv4 đã được train với hơn 200 tấm hình xe máy để giúp phát hiện đối tượng trong từng frame của video.
+ Để có thể gắn id cho những xe máy đã được phát hiện bằng model YOLOv4, thì project có sử dụng thư viện object_detection và deep_sort.deep_sort 
  được lấy từ khóa học Object Detection của pysource.com.
+ Vùng để track các xe được chia thành 99 ô grid để có thể ghi lại thông tin xe khi đi vào từng ô grid này để hỗ trợ cho việc tính toán các chỉ số.
+ Các tọa độ xe máy thu thập được từ model YOLOv4 và id của từng xe sẽ được sử dụng tính toán vận tốc tức thời và vận tốc trung bình không gian của xe máy.
+ Các thông tin về vận tốc của từng xe sẽ được hiển thị trong video để có thể giúp xác định vận tốc xe khi xe khi di chuyển tới từng ô grid khác nhau.

## grid.py
+ File này sẽ chứa các class để hỗ trợ cho việc ghi lại thông tin id cũng như tọa độ của xe máy.
+ Các class bên trong cũng có các hàm hỗ trợ việc phân tích để tính toán vận tốc xe.
