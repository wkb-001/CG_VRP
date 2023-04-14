# -*- coding : utf-8 -*-
# @Time      : 2023/4/14 10:04
# @Author    : wkb
from __future__ import print_function
from Data import Data
from gurobipy import *
from MP import Mp
import time

class Sp:
    def __init__(self):
        self.start_time = time.time()
        self.data = Data()
        path = 'c101.txt'
        self.customerNum = 30
        self.data.readData(path, self.customerNum)
        self.data.vehicleNum = 10
        self.data.printData(self.customerNum)

        # print(self.data.nodeNum)
        self.mp  = Mp(self.customerNum, self.data.vehicleNum)
        self.RMP, self.rmp_pi, self.rmp_con,self.path_set = self.mp.Build_mp()
        self.SP = Model('sp')
        self.RMP.setParam('OutputFlag', 0)
        self.SP.setParam('OutputFlag', 0)
        self.Build_sp()
        self.run()


    def Build_sp(self):
        # decision var
        self.x = {}
        self.s = {}
        big_m = 1e5
        for i in range(self.data.nodeNum):
            self.s[i] = self.SP.addVar(lb=self.data.readyTime[i], ub=self.data.dueTime[i], vtype=GRB.CONTINUOUS, name='s_{0}'.format(i))
            for j in range(self.data.nodeNum):
                if (i != j):
                    self.x[i, j] = self.SP.addVar(lb=0, ub=1, vtype=GRB.BINARY, name='x_{0}_{1}'.format(i, j))
        # set sp obj
        sub_obj = LinExpr()
        for key in self.x.keys():
            node_i = key[0]
            node_j = key[1]
            sub_obj.addTerms(self.data.disMatrix[node_i][node_j], self.x[key])
            sub_obj.addTerms(-self.rmp_pi[node_i], self.x[key])

        self.SP.setObjective(sub_obj, sense=GRB.MINIMIZE)

        # cons_1
        lhs = LinExpr()
        for key in self.x.keys():
            node_i = key[0]
            node_j = key[1]
            lhs.addTerms(self.data.demand[node_i], self.x[key])
        self.SP.addConstr(lhs <= self.data.capacity, name='c1')

        # cons_2
        lhs = LinExpr()
        for key in self.x.keys():
            if (key[0] == 0):
                lhs.addTerms(1, self.x[key])
        self.SP.addConstr(lhs == 1, name='c_2')

        # cons_3:
        for h in range(1, self.data.nodeNum - 1):
            lhs = LinExpr()
            for i in range(self.data.nodeNum):
                temp_k = (i, h)
                if (temp_k in self.x.keys()):
                    lhs.addTerms(1, self.x[temp_k])
            for j in range(self.data.nodeNum):
                temp_k = (h, j)
                if (temp_k in self.x.keys()):
                    lhs.addTerms(-1, self.x[temp_k])
            self.SP.addConstr(lhs == 0, name='c_3_{}'.format(h))

        # cons_4:
        lhs = LinExpr()
        for key in self.x.keys():
            if (key[1] == self.data.nodeNum - 1):
                lhs.addTerms(1, self.x[key])
        self.SP.addConstr(lhs == 1, name='c_4')

        # cons_5:
        for key in self.x.keys():
            node_i = key[0]
            node_j = key[1]
            self.SP.addConstr(self.s[node_i] + self.data.disMatrix[node_i][node_j] - self.s[node_j] - big_m + big_m * self.x[key] <= 0,
                         name='c_5')
        self.SP.write('sp.lp')
        # slove SP
        # print('sp_optimal:-----------------')
        self.SP.optimize()



    def run(self):
        self.eps = -0.01
        self.cnt = 0
        # print('sb_obj',SP.ObjVal)
        while (self.SP.ObjVal < self.eps):
            # print('reduce cost:', self.SP.ObjVal)
            self.cnt += 1
            # print('-----------cnt=', self.cnt, '----------')
            '''add new column'''
            path_length = 0
            for key in self.x.keys():
                node_i = key[0]
                node_j = key[1]
                path_length += self.x[key].x * self.data.disMatrix[node_i][node_j]
            path_length = round(path_length, 2)

            # creat new column
            col_coef = [0] * (self.data.nodeNum - 2)
            for key in self.x.keys():
                if (self.x[key].x > 0):
                    node_i = key[0]
                    if (node_i > 0 and node_i < self.data.nodeNum - 1):
                        col_coef[node_i - 1] = 1
            # print('new path length:', path_length)
            # print('new column:', col_coef)

            rmp_col = Column(col_coef, self.rmp_con)
            # print(col_coef, self.rmp_con)
            new_path = []
            current_node = 0
            new_path.append(current_node)
            while (current_node != self.data.nodeNum - 1):
                for key in self.x.keys():
                    if (self.x[key].x > 0 and key[0] == current_node):
                        current_node = key[1]
                        new_path.append(current_node)
            # print('new path:', new_path)

            # update the RMP
            var_name = 'cg_' + str(self.cnt)
            self.RMP.addVar(lb=0, ub=1, obj=path_length, vtype=GRB.CONTINUOUS, name=var_name, column=rmp_col)
            self.RMP.update()
            self.path_set[var_name] = new_path
            # print('current column number:', self.RMP.Numvars)
            self.RMP.optimize()

            # get dual var
            rmp_pi = self.RMP.getAttr("Pi", self.RMP.getConstrs())
            rmp_pi.insert(0, 0)
            rmp_pi.append(0)
            # print('rmp_pi:', rmp_pi)

            # update the SP obj
            sub_obj = LinExpr()
            for key in self.x.keys():
                node_i = key[0]
                node_j = key[1]
                sub_obj.addTerms(self.data.disMatrix[node_i][node_j], self.x[key])
                sub_obj.addTerms(-rmp_pi[node_i], self.x[key])

            self.SP.setObjective(sub_obj, sense=GRB.MINIMIZE)
            self.SP.optimize()

        self.end_time = time.time()
        self.RMP.write('RMP_final.lp')
        # change Rmp to IP
        mip_var = self.RMP.getVars()
        for i in range(self.RMP.numVars):
            mip_var[i].setAttr('VType', GRB.INTEGER)
        self.RMP.optimize()
        for var in self.RMP.getVars():
            if (var.x > 0):
                # print(var)
                print(var.VarName, '=', var.x)
                print('path:', self.path_set[var.VarName])
        print('obj:',self.RMP.ObjVal)
        print('cpu_time:',round(self.end_time - self.start_time,3))
if __name__ == '__main__':
    t = Sp()


