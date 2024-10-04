import pandas as pd
import os
from CoolProp.CoolProp import PropsSI as PS

class WW_HP:


    def __init__(self, x, y):

        self.x = x
        self.y = y

        # Data imports
        current_directory = os.getcwd()
        csv_file_path = os.path.join(current_directory, 'DATA', 'Carrier_2nd_order.xlsx')
        self.data_P_compressor =  pd.read_excel(csv_file_path, sheet_name="P_COMP")
        self.data_Q       =  pd.read_excel(csv_file_path, sheet_name="Q_MAX")
        cp_water = PS('C', 'T', 293, 'P', 101325, 'water')
        cp_glycol = 3600

        def calc():

            load = self.data_P_compressor.iloc[self.y,self.x] * 3e5      # from kW to J in 5 minutes
            Q            = self.data_Q.iloc[self.y,self.x] * 3e5         # from kW to J in 5 minutes

            mdot_cold = (Q-load)/(cp_glycol * 3)
            mdot_hot  = Q/(cp_water * 5)

            return(load, Q, mdot_cold, mdot_hot)
        
        [self.load, self.Q, self.mdot_cold, self.mdot_hot] = calc()


class B_WW_HP:


    def __init__(self, T_LTV):

        self.T_LTV = T_LTV

        # Data imports
        self.data_P_compressor = [16.3, 16.5, 16.7]
        self.data_Q            = [56.7, 63.5, 70.3]
        self.T_in              = [35, 40, 45]

        cp_water = PS('C', 'T', 293, 'P', 101325, 'water')

        def calc():
            
            for i in range(len(self.T_in)):

                if self.T_in[i] == self.T_LTV:
                    x = i

            load = self.data_P_compressor[x] * 3e5      # from kW to J in 5 minutes
            Q = self.data_Q[x] * 3e5                 # from kW to J in 5 minutes

            mdot_cold = (Q-load)/(cp_water * 5)
            mdot_hot  = Q/(cp_water * 8)

            return(load, Q, mdot_cold, mdot_hot)

        [self.load, self.Q, self.mdot_cold, self.mdot_hot] = calc()