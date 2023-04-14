# -*- coding : utf-8 -*-
# @Time      : 2023/4/14 10:41
# @Author    : wkb

from __future__ import print_function
from gurobipy import *
import re
import math
import matplotlib.pyplot  as plt
import numpy as np
import pandas as pd
import networkx as nx
import copy
import random

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

#read data
data = Data()
path = 'c101.txt'
customerNum = 30
data.readData(path,customerNum)
data.vehicleNum = 30
data.printData(customerNum)

#build graph
Graph = nx.DiGraph()
cnt = 0
pos_location = {}
nodes_col = {}
nodeList = []

for i in range(data.nodeNum):
    X_coor = data.cor_X[i]
    Y_coor = data.cor_Y[i]
    name = str(i)
    nodeList.append(name)
    nodes_col[name] = 'gray'
    node_type = 'customer'
    if(i == 0):
        node_type = 'depot'
    Graph.add_node(name,
                   ID=i,
                   node_type = node_type,
                   time_window = (data.readyTime[i],data.dueTime[i]),
                   arrive_time = 10000,
                   demand = data.demand,
                   serviceTime = data.serverTime,
                   x_coor = X_coor,
                   y_coor = Y_coor,
                   min_dis = 0,
                   previous_node = None)
    pos_location[name] = (X_coor, Y_coor)

# add the edges into the graph
for i in range(data.nodeNum):
    for j in range(data.nodeNum):
        if(i == j or (i == 0 and j == data.nodeNum - 1) or ( j == 0 and i == data.nodeNum - 1 )):
            pass
        else:
            Graph.add_edge(str(i), str(j), travelTime = data.disMatrix[i][j], length = data.disMatrix[i][j])

# build RMP
RMP = Model()
customerNum = data.customerNum
path_set = {}

# decision var
y = {}
for i in range(customerNum):
    y[i] = RMP.addVar(lb=0, ub=1, obj=round(data.disMatrix[0][i] + data.disMatrix[i][0], 1), vtype=GRB.CONTINUOUS, name='y_{0}'.format(i))
    path_set['y_{}'.format(i)] = [0,i+1,data.nodeNum-1]
rmp_con = []
row_coeff = [1]*customerNum
for i in range(customerNum):
    rmp_con.append(RMP.addConstr(y[i] == 1))

# set obj
print('RMP_optimal:-------------------------')
RMP.write('RMP.lp')
RMP.optimize()
for var in RMP.getVars():
    if(var.x > 0):
        # print(var)
        print(var.VarName,'=', var.x)
        print('path:', path_set[var.VarName])


rmp_pi = RMP.getAttr("Pi", RMP.getConstrs())
rmp_pi.insert(0, 0)
rmp_pi.append(0)
print('rmp_pi:', rmp_pi)





# build sp
SP = Model('sp')
# decision var
x = {}
s = {}
big_m = 1e5
for i in range(data.nodeNum):
    s[i] = SP.addVar(lb=data.readyTime[i], ub=data.dueTime[i], vtype=GRB.CONTINUOUS, name = 's_{0}'.format(i))
    for j in range(data.nodeNum):
        if(i != j):
            x[i,j] = SP.addVar(lb=0, ub=1, vtype=GRB.BINARY, name='x_{0}_{1}'.format(i,j))

# set sp obj
sub_obj = LinExpr()
for key in x.keys():
    node_i = key[0]
    node_j = key[1]
    sub_obj.addTerms(data.disMatrix[node_i][node_j], x[key])
    sub_obj.addTerms(-rmp_pi[node_i], x[key])

SP.setObjective(sub_obj, sense=GRB.MINIMIZE)

# cons_1
lhs = LinExpr()
for key in x.keys():
    node_i = key[0]
    node_j = key[1]
    lhs.addTerms(data.demand[node_i], x[key])
SP.addConstr(lhs <= data.capacity, name='c1')

# cons_2
lhs = LinExpr()
for key in x.keys():
    if(key[0]==0):
        lhs.addTerms(1,x[key])
SP.addConstr(lhs == 1, name='c_2')

# cons_3:
for h in range(1, data.nodeNum-1):
    lhs = LinExpr()
    for i in range(data.nodeNum):
        temp_k = (i,h)
        if(temp_k in x.keys()):
            lhs.addTerms(1, x[temp_k])
    for j in range(data.nodeNum):
        temp_k = (h,j)
        if(temp_k in x.keys()):
            lhs.addTerms(-1, x[temp_k])
    SP.addConstr(lhs == 0, name='c_3_{}'.format(h))

# cons_4:
lhs = LinExpr()
for key in x.keys():
    if(key[1] == data.nodeNum-1):
        lhs.addTerms(1, x[key])
SP.addConstr(lhs==1, name='c_4')

# cons_5:
for key in x.keys():
    node_i = key[0]
    node_j = key[1]
    SP.addConstr(s[node_i] + data.disMatrix[node_i][node_j] - s[node_j] - big_m + big_m*x[key] <= 0, name='c_5')
SP.write('sp.lp')

RMP.setParam('OutputFlag',0)
SP.setParam('OutputFlag',0)

# slove SP
print('sp_optimal:-----------------')
SP.optimize()
eps = -0.01
cnt = 0
# print('sb_obj',SP.ObjVal)
while(SP.ObjVal < eps):
    print('reduce cost:', SP.ObjVal)
    cnt += 1
    print('-----------cnt=',cnt,'----------')
    '''add new column'''
    path_length = 0
    for key in x.keys():
        node_i = key[0]
        node_j = key[1]
        path_length += x[key].x * data.disMatrix[node_i][node_j]
    path_length = round(path_length,2)

    # creat new column
    col_coef = [0]*(data.nodeNum-2)
    for key in x.keys():
        if(x[key].x > 0):
            node_i = key[0]
            if(node_i > 0 and node_i < data.nodeNum-1):
                col_coef[node_i - 1] = 1
    print('new path length:', path_length)
    print('new column:', col_coef)

    rmp_col = Column(col_coef, rmp_con)
    print(col_coef,rmp_con)
    new_path = []
    current_node = 0
    new_path.append(current_node)
    while(current_node != data.nodeNum-1):
        for key in x.keys():
            if(x[key].x > 0 and key[0] == current_node):
                current_node = key[1]
                new_path.append(current_node)
    print('new path:', new_path)

    #update the RMP
    var_name = 'cg_'+str(cnt)
    RMP.addVar(lb=0, ub=1, obj=path_length, vtype=GRB.CONTINUOUS, name=var_name, column=rmp_col)
    RMP.update()
    path_set[var_name] = new_path
    print('current column number:', RMP.Numvars)
    RMP.optimize()

    # get dual var
    rmp_pi = RMP.getAttr("Pi", RMP.getConstrs())
    rmp_pi.insert(0, 0)
    rmp_pi.append(0)
    print('rmp_pi:', rmp_pi)

    # update the SP obj
    sub_obj = LinExpr()
    for key in x.keys():
        node_i = key[0]
        node_j = key[1]
        sub_obj.addTerms(data.disMatrix[node_i][node_j], x[key])
        sub_obj.addTerms(-rmp_pi[node_i], x[key])

    SP.setObjective(sub_obj, sense=GRB.MINIMIZE)
    SP.optimize()

RMP.write('RMP_final.lp')
# change Rmp to IP
mip_var = RMP.getVars()
for i in range(RMP.numVars):
    mip_var[i].setAttr('VType',GRB.INTEGER)
RMP.optimize()
for var in RMP.getVars():
    if(var.x > 0):
        # print(var)
        print(var.VarName,'=', var.x)
        print('path:', path_set[var.VarName])




