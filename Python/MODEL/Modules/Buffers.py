import numpy as np
import matplotlib.pyplot as plt


class Buffer:


    def __init__(self, T_in, charge, demand, T_seg, type, resolution):


        self.T_in = T_in
        self.T_seg = T_seg
        self.demand = demand                    #kg
        self.charge = charge
        self.type  = type
        self.resolution = resolution

        n_seg = len(self.T_seg)                 #kg / resolution
        m_seg = self.resolution                               #resolution

        def charging():
            

            ndot = int(self.demand/m_seg)
            err  = self.demand - ndot

            if ndot > 0: #charging

                # print('charging')

                if self.type == 'GKW':
                    for i in range(n_seg-1, n_seg - ndot - 1, -1):
                        self.T_seg[i] = self.T_in
                
                else:
                    for i in range(ndot):
                        self.T_seg[i] = self.T_in

            elif ndot < 0: #discharging

                # print('discharging')
                
                if self.type == 'GKW':
                    for i in range(-ndot):
                        self.T_seg[i] = self.T_in + 5

                elif self.type == 'LTV':
                    for i in range(n_seg-1, n_seg + ndot - 1, -1):
                        self.T_seg[i] = self.T_in - 5

                else:
                    for i in range(n_seg-1, n_seg + ndot - 1, -1):
                        self.T_seg[i] = self.T_in - 8

            self.T_seg.sort()
            self.charge = 0

            for i in range(n_seg):

                if T_seg[i] == self.T_in:

                    self.charge = self.charge + 1/n_seg

            return(self.charge, self.T_seg)
        
        result = charging()
        [self.charge, self.T_seg] = result