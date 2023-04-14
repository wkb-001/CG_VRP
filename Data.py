# -*- coding : utf-8 -*-
# @Time      : 2022/10/2 15:33
# @Author    : wkb
from __future__ import print_function
import re
import math

class Data:

    def __init__(self):
        self.customerNum = 0
        self.nodeNum = 0
        self.vehicleNum = 0
        self.capacity = 0
        self.cor_X = []
        self.cor_Y = []
        self.demand = []
        self.serverTime = []
        self.readyTime = []
        self.dueTime = []
        self.disMatrix = [[]]


    # read data
    def readData(data, path, customerNum):
        data.customerNum = customerNum
        data.nodeNum = customerNum+ 2
        f = open(path, 'r')
        lines = f.readlines()
        count = 0
        # read file
        for line in lines:
            count = count+1
            if(count == 5):
                line = line[:-1].strip()
                str = re.split(r" +", line)
                data.vehicleNum = int(str[0])
                data.capacity = float(str[1])
            elif(count >= 10 and count <= 10 + customerNum):
                line = line[:-1]
                str = re.split(r" +",line)
                data.cor_X.append(float(str[2]))
                data.cor_Y.append(float(str[3]))
                data.demand.append(float(str[4]))
                data.readyTime.append(float(str[5]))
                data.dueTime.append(float(str[6]))
                data.serverTime.append(float(str[7]))
        data.cor_X.append(data.cor_X[0])
        data.cor_Y.append(data.cor_Y[0])
        data.demand.append(data.demand[0])
        data.readyTime.append(data.readyTime[0])
        data.dueTime.append(data.dueTime[0])
        data.serverTime.append(data.serverTime[0])

        # compute the distance matrix
        data.disMatrix = [([0] * data.nodeNum) for p in range(data.nodeNum)]
        for i in range(data.nodeNum):
            for j in range(data.nodeNum):
                temp = (data.cor_X[i] - data.cor_X[j])**2 + (data.cor_Y[i] - data.cor_Y[j])**2
                data.disMatrix[i][j] = round(math.sqrt(temp), 1)
                temp = 0
        return data


    def printData(data, customerNum):
        print("下面打印数据\n")
        print('vehicle number = %4d'% data.vehicleNum)
        print('vehicle capacity = %4d'% data.capacity)
        for i in range(len(data.demand)):
            print('{0}\t{1}\t{2}\t{3}'.format(data.demand[i], data.readyTime[i], data.dueTime[i], data.serverTime[i]))

        print('---------距离矩阵------------')
        for i in range(data.nodeNum):
            for j in range(data.nodeNum):
                print('%6.2f' % (data.disMatrix[i][j]), end = ' ')
            print()



