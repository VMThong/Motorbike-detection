# Motorbike-detection

## motorbike_project.py
Project Information:
+ This project utilizes the YOLOv4 model that has been trained with over 200 images of motorcycles to detect objects in each frame of a video. To assign an ID to the motorcycles detected by the YOLOv4 model, the project uses the object_detection and deep_sort libraries, which were obtained from the Object Detection course on pysource.com. The area for tracking the motorcycles is divided into 99 grid cells to record information about the motorcycles as they enter each cell to support the calculation of various metrics.
+ The motorcycle coordinates collected from the YOLOv4 model and the IDs of each motorcycle will be used to calculate the instant and average spatial velocities of the motorcycles. The velocity information of each motorcycle will be displayed in the video to help determine the velocity of the motorcycle as it moves through different grid cells.
+ This project is still being developed and modified to collect various other metrics.

## grid.py
+ This file will contain classes to support recording the ID and coordinates of motorcycles.
+ The classes inside also have functions to support analysis for calculating motorcycle speed.

## motorbike_project_demo.py
+ This project is a demo version of motorbike_project.py to implement initial ideas.
+ The data collection scope is limited to 6 regions with 3 regions for the upper lane and 3 regions for the lower lane.
+ The collected information includes the average spatial velocity, motorbike ID, entry and exit time from the region, and the current lane position of the motorbike.
+ After being collected, the data will be pushed into PostgreSQL.
