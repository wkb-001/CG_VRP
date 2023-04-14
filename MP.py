# -*- coding : utf-8 -*-
# @Time      : 2023/4/14 9:57
# @Author    : wkb
from __future__ import print_function
from Data import Data
from gurobipy import *
import networkx as nx
class Mp:
    def __init__(self):
        self.data = Data()
        self.path = 'c101.txt'
        self.customerNum = 30
        self.data.readData(self.path, self.customerNum)
        self.data.vehicleNum = 30
        self.data.printData(self.customerNum)
        self.Builg_Graph()
        self.Build_mp()

    def Builg_Graph(self):
        # build graph
        self.Graph = nx.DiGraph()
        cnt = 0
        self.pos_location = {}
        self.nodes_col = {}
        self.nodeList = []

        for i in range(self.data.nodeNum):
            X_coor = self.data.cor_X[i]
            Y_coor = self.data.cor_Y[i]
            name = str(i)
            self.nodeList.append(name)
            self.nodes_col[name] = 'gray'
            node_type = 'customer'
            if (i == 0):
                node_type = 'depot'
            self.Graph.add_node(name,
                           ID=i,
                           node_type=node_type,
                           time_window=(self.data.readyTime[i], self.data.dueTime[i]),
                           arrive_time=10000,
                           demand=self.data.demand,
                           serviceTime=self.data.serverTime,
                           x_coor=X_coor,
                           y_coor=Y_coor,
                           min_dis=0,
                           previous_node=None)
            self.pos_location[name] = (X_coor, Y_coor)

        # add the edges into the graph
        for i in range(self.data.nodeNum):
            for j in range(self.data.nodeNum):
                if (i == j or (i == 0 and j == self.data.nodeNum - 1) or (j == 0 and i == self.data.nodeNum - 1)):
                    pass
                else:
                    self.Graph.add_edge(str(i), str(j), travelTime=self.data.disMatrix[i][j], length=self.data.disMatrix[i][j])

    def Build_mp(self):
        # build RMP
        self.RMP = Model()
        self.customerNum = self.data.customerNum
        self.path_set = {}

        # decision var
        self.y = {}
        for i in range(self.customerNum):
            self.y[i] = self.RMP.addVar(lb=0, ub=1, obj=round(self.data.disMatrix[0][i] + self.data.disMatrix[i][0], 1),
                              vtype=GRB.CONTINUOUS, name='y_{0}'.format(i))
            self.path_set['y_{}'.format(i)] = [0, i + 1, self.data.nodeNum - 1]
        rmp_con = []
        row_coeff = [1] * self.customerNum
        for i in range(self.customerNum):
            rmp_con.append(self.RMP.addConstr(self.y[i] == 1))

        # set obj
        print('RMP_optimal:-------------------------')
        self.RMP.write('RMP.lp')
        self.RMP.optimize()
        for var in self.RMP.getVars():
            if (var.x > 0):
                # print(var)
                print(var.VarName, '=', var.x)
                print('path:', self.path_set[var.VarName])

        rmp_pi = self.RMP.getAttr("Pi", self.RMP.getConstrs())
        rmp_pi.insert(0, 0)
        rmp_pi.append(0)
        print('rmp_pi:', rmp_pi)
        return self.RMP, rmp_pi, rmp_con,self.path_set

if __name__ == '__main__':
    t = Mp()
