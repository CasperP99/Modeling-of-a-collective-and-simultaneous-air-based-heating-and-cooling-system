import pandas as pd
import math
from CoolProp.CoolProp import PropsSI

#-------------------------------------------------------------------------------------------------------------

class DC_simple:


    def __init__(self, T_out, mdot):
        
        self.T_out      = T_out
        self.mdot       = mdot

        self.cp        = 3600           # J/kgK
        self.Q_max     = 180 * 3e5    # from kW to J
        self.P_max     = 7 * 3e5      # from kW to J

        def calc():
            dT    = 3 #K
            max_RPM = 1000 
            Q     = self.mdot * self.cp * dT
            ratio = Q/self.Q_max
            fanspeed = ratio * max_RPM
            load = (fanspeed**3)/(max_RPM**3) * self.P_max
            # load  = ratio * self.P_max
            n_drycoolers = math.ceil(ratio)

            # print("Number of DryCoolers activated:", n_drycoolers) 

            return(Q, load)
        

        # Running the script
        [self.Q, self.load] = calc()        

            

class TSA_1:


    def __init__(self, mdot):

        self.mdot_HP = mdot
        self.cp      = PropsSI('C', 'T', 293, 'P', 101325, 'water')

        def calc():

            dT_HP  = 3
            dT_GKW = 5

            mdot_GKW = self.mdot_HP * (dT_HP/dT_GKW) * (3600/self.cp)
        
            return(mdot_GKW)
        

        # Running the script
        self.mdot_GKW = calc()

class TSA_2:

    
    def __init__(self, mdot):

        self.mdot_HP = mdot
        self.cp      = PropsSI('C', 'T', 293, 'P', 101325, 'water')

        def calc():

            dT_DC  = 3
            dT_HP  = 5

            mdot_DC = self.mdot_HP * (dT_HP/dT_DC) * (self.cp/3600)
        
            return(mdot_DC)
        

        # Running the script
        self.mdot_DC = calc()
