import imageio
from math import floor,sqrt
from scipy.signal import argrelextrema
import numpy as np

class Lomaliza2017:
    def __init__(self):
        pass

    def FingerPresenceDetection(self):
        pass

    def CalculateMean(self,list):
        sum = 0
        for i in range(len(list)):
            sum = sum + list[i]
        sum = (sum*1.0)/len(list)
        return sum

    def CalculateStd(self,list, mean):
        diff = 0
        for i in range(0,len(list)):
            diff = diff + (mean - list[i]) * (mean - list[i])
        diff = (diff * 1.0)/(len(list))
        std = sqrt(diff)
        return std

    def EachFrameCalculation(self, file_name):
        pic = imageio.imread(file_name)
        image_height = pic.shape[0]
        image_width = pic.shape[1]
        min_height = floor(image_height/10)
        min_width = floor(image_width/10)


        ppg_points_r,ppg_points_g,ppg_points_b = [],[],[]
        x_y = [[0,min_height,0,min_width],[0,min_height,image_width-min_height,image_width],[image_height-min_height,image_height,0,image_width]]
        for i in range(0,len(x_y)):
            for j in range(x_y[i][0],x_y[i][1]):
                for k in range(x_y[i][2],x_y[i][3]):
                    ppg_points_r.append(pic[j,k,0])
                    ppg_points_g.append(pic[j,k,1])
                    ppg_points_b.append(pic[j,k,2])

        mean_r = self.CalculateMean(ppg_points_r)
        std_r = self.CalculateStd(ppg_points_r, mean_r)

        mean_g = self.CalculateMean(ppg_points_g)
        std_g = self.CalculateStd(ppg_points_g, mean_g)

        mean_b = self.CalculateMean(ppg_points_b)
        std_b = self.CalculateStd(ppg_points_b, mean_b)

        if((mean_r-std_r)>128 and (mean_g-std_g)<128  and (mean_b-std_b)<128):
            return 0,mean_r # finger_presence_error False
        else:
            return 1,mean_r # finger_presence_error True

    def AllFrameCalculation(self,directory_prefix,number_of_frames,output_file):
        f = open(output_file,'w')
        f.write('frame,avg_intensity,finger_presence_flag\n')
        ppg_points_b = []
        for k in range(1,number_of_frames+1):
            finger_presence, mean = self.EachFrameCalculation(directory_prefix+'/frame'+str(k)+'.jpg')
            f.write(str(k)+','+str(mean)+','+str(finger_presence)+'\n')
            ppg_points_b.append(mean)
        f.close()
        return ppg_points_b

    def PeakBasedPPGCalculation(self, ppg_points_b, window_length,sampling_freq):
        min_points = floor(window_length*sampling_freq)
        temp = []
        for i in range(0,len(ppg_points_b),min_points):
            l = ppg_points_b[i:min(i+min_points,len(ppg_points_b))]
            ppg = np.array(l)
            peaks = argrelextrema(ppg, np.greater)
            # print(peaks)
            peaks = list(peaks[0])
            peak_values = []
            for j in range(0,len(peaks)):
                idx = peaks[j]+i
                peak_values.append(ppg_points_b[idx])


            # print(peak_values)

            valleys = argrelextrema(ppg, np.less)
            valleys = list(valleys[0])
            valley_values = []
            for j in range(0,len(valleys)):
                idx = valleys[j]+i
                valley_values.append(ppg_points_b[idx])

            peak_avg = None
            if(len(peak_values)>0):
                peak_avg = self.CalculateMean(peak_values)
            valley_avg = None
            if(len(valley_values)>0):
                valley_avg = self.CalculateMean(valley_values)
            if(peak_avg != None and valley_avg != None):
                mid_point = (peak_avg+valley_avg)/2.0
                for j in range(i,min(i+min_points,len(ppg_points_b))):
                    if(ppg_points_b[j] > mid_point):
                        temp.append(j)
            else:
                if(len(peak_values) == 0):
                    max_val = 0
                    max_idx = -1
                    for j in range(i,min(i+min_points,len(ppg_points_b))):
                        if(max_val<ppg_points_b[j]):
                            max_val = ppg_points_b[j]
                            max_idx = j
                    temp.append(max_idx)
                else:
                    for j in range(i,min(i+min_points,len(ppg_points_b))):
                        if(len(peak_values)>0 and ppg_points_b[j] == peak_values[0]):
                            temp.append(j)
                            break
        beat_points = []
        for i in range(0,len(temp)):
            if(len(beat_points) == 0):
                beat_points.append(temp[i])
            else:
                if((temp[i] - beat_points[len(beat_points)-1]) == 1):
                    if(ppg_points_b[beat_points[len(beat_points)-1]] < ppg_points_b[temp[i]]):
                        beat_points[len(beat_points)-1] = temp[i]
                else:
                    beat_points.append(temp[i])
        print("beat frames = ",beat_points)
        S = []
        T = 0.05 # threshold T
        l = []
        for i in range(1,len(beat_points)):
            S.append((beat_points[i]-beat_points[i-1])/(sampling_freq*1.0))
        cnt = 0
        while True:
            cnt = cnt + 1
            print("iteration: ",cnt,"S: ",S)
            l.clear()
            A = self.CalculateMean(S)
            print("average  = ",A)
            l.clear()
            for i in range(0,len(S)):
                g = abs(S[i]-A)
                if(g>T):
                    l.append(i)
            for i in range(len(l)-1,-1,-1):
                del S[l[i]]
            if(len(l) == 0):
                break
            print(len(S))
        if(len(S)>0):
            A = self.CalculateMean(S)
            HR = (60.0)/(A)
            print("HR = ",HR)
        else:
            print("S got empty")

    def GetThePPGPoints(self,file_name):
        ppg_points_b = []
        with open(file_name,'r') as file:
            lines = file.readlines()
            for i in range(1,len(lines)):
                l = lines[i].strip().split(',')[1]
                ppg_points_b.append(float(l))
        return ppg_points_b

object = Lomaliza2017()

directory_prefix = 'E:\Research\Smartphone-heart-beat\Dataset\Red-Object-Detection\Heart-Rate-Measure\heart-rate-measure\Paper-Clean-Data' # all the frames should be in this folder
number_of_frames =  900 # ('frame0.jpg, frame1.jpg, frame2.jpg, etc.')
output_file = 'Results.csv'
ppg_points_b = object.AllFrameCalculation(directory_prefix, number_of_frames, output_file) # PPG intensity will be stored in output_file
#ppg_points_b = object.GetThePPGPoints('E:\Research\Smartphone-heart-beat\Dataset\Red-Object-Detection\Heart-Rate-Measure\heart-rate-measure\Paper-Clean-Data\\red-pixels.csv') # give the PPG intesity file's path
window_length = 2.5
sampling_freq = 30
object.PeakBasedPPGCalculation(ppg_points_b,window_length,sampling_freq)
