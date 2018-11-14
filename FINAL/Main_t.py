#!/usr/bin/python

# General system related libraries
import time
import pytictoc
import matplotlib.pyplot as plt
import  os

# Calaculatin and data manipulation libraries:
import numpy as np
import pandas as pd
import pickle

# Project modules
from Track_calculations import cone_finder, extrapolate_points
import LIDAR
import IMU
import utilities
import cProfile

# pd.set_option('display.max_columns', 500)

# USER PARAMETERS:
WORK_MODE = 1           # offline(reading data from pickle_file) = 0 , online(recording to pickle_file) = 1
FOV = 160               # field of view
NUM_OF_LASERS = 16      # VLP-16 Lidar
NUM_OF_POINTS = 384     # number of points in each lidar packet
NUM_OF_IMU_DATA = 7     # Yaw/Pitch/Roll/Lon/Lat/Alt/Timestamp
PATH = '/home/avinoam/Desktop/'
TEST_NAME = 'test' #time.strftime("%X_%d.%m.%y")

#files names
IMU_CSV =           PATH + 'IMU_' + TEST_NAME + '.csv'
IMU_INTERPOLATED =  PATH + 'IMU_after_interpolation_'+TEST_NAME+'.csv'
LIDAR_CSV =         PATH + 'LIDAR_' + TEST_NAME + '.csv'
CONES_CSV =         PATH + 'CONES_' + TEST_NAME + '.csv'
LIDAR_w_IMU_Cor =   PATH + 'Lidar_w_IMU_Correction_' + TEST_NAME + '.csv'
IMU_PKL =           PATH + 'imu_rec_' + TEST_NAME + '.pkl'
LIDAR_PCAP =         PATH + 'lidar_rec_' + TEST_NAME + '.pcap'


class joint_feeder:
    def __init__(self):
        if WORK_MODE: # online_mode
            self.lidar_feeder = LIDAR.vlp16_online_feeder(LIDAR_PCAP, FOV)
            self.imu_feeder = IMU.vn200_online_feeder(IMU_PKL)
        else:   # offline mode
            self.lidar_feeder = LIDAR.vlp16_offline_feeder(LIDAR_PCAP)
            self.imu_feeder = IMU.vn200_offline_feeder(IMU_PKL)

    def close_joint_feeder(self, N_packets):
        if WORK_MODE: # online_mode
            time.sleep(1) # giving time to write the last packet
            self.lidar_feeder.close_socket()
            self.imu_feeder.close_imu()
            print ('Done!!! - {} frames has been recorded'.format(N_packets))
        else:
            print ('Done!!! - {} frames has been decrypted'.format(N_packets))


    def get_world_coordinate(self, xyz_cones, time_stamp):
        imu_data = self.imu_feeder.get_packet()
        xyz_world = extrapolate_points(xyz_cones, imu_data, time_stamp)
        # print(xyz_world)
        return xyz_world

def main():

    if not os.path.isdir(PATH):
        print('Error- the PATH you have entered dosen\'t exists')
        exit(0)
    #timeout = int(input('Please enter a desired recording time (in seconds): ')) # seconds

    feeder = joint_feeder()
    lidar_decoder = LIDAR.vlp16_decoder(feeder.lidar_feeder)

    #N_frames =  timeout * 10    #  10 frames per sec (velo working freq is 10Hz)
    N_frames = 100
    t = pytictoc.TicToc()
    t.tic()

    for packet in range(N_frames):
        # utilities.print_progress(packet, N_frames-1)
        decoded_frame, time_stamp = lidar_decoder.get_full_frame()
        frame = np.reshape(decoded_frame, (decoded_frame.shape[0]*decoded_frame.shape[1],decoded_frame.shape[2]))
        timestamp_list = np.reshape(time_stamp, (len(time_stamp)*NUM_OF_POINTS,1))
        # df_packet = pd.DataFrame(new_packet)
        xyz_cones = cone_finder(frame, timestamp_list, FOV)
        # if np.all(xyz_cones) == None:
        #     continue
        # else:
        #     # print(xyz_cones)
        #     xyz_world =
        # if  feeder.get_world_coordinate(xyz_cones, time_stamp)
        #     cone_to_csv = pd.DataFrame(xyz_cones)
        #     cone_to_csv.to_csv(CONES_CSV, header= ['X', 'Y', 'Z'], mode= 'a')
    t.toc()
    feeder.close_joint_feeder(N_frames)

if __name__ == '__main__':
    main()