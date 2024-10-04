from HeatExchangers import DC_simple, TSA_1, TSA_2
from HeatPumps import WW_HP

import pandas as pd
from CoolProp.CoolProp import PropsSI

class BlackBox:

    def __init__(self, Mode_Value, Q_high, Q_low, T_LTV, T_GKW, T_amb):

        self.Mode_Value = Mode_Value
        self.Q_high     = Q_high
        self.Q_low      = Q_low
        self.T_LTV      = T_LTV
        self.T_GKW      = T_GKW
        self.T_amb      = T_amb
        self.cp         = PropsSI('C', 'T', 293, 'P', 101325, 'water')


        def Mode1():

            T_DC_out = self.T_amb
            T_LTV_table = list(range( 30, 51))
            T_DC_out_table = list(range( -15, 21))
        
            for i in range(len(T_LTV_table)):    
                            if T_LTV_table[i] == self.T_LTV:
                                x = i
                                break
            for i in range(len(T_DC_out_table)):    
                            if T_DC_out_table[i] == T_DC_out:
                                y = i
                                break

            # HEATPUMP
            T_evap_in   = T_DC_out
            HeatPump    = WW_HP(x,y)
            load_HP     = HeatPump.load
            Q           = HeatPump.Q
            mdot_cold   = HeatPump.mdot_cold
            mdot_hot    = HeatPump.mdot_hot

            mdot_rest = mdot_cold - self.Q_low

            # COLD SIDE
            DryCooler   = DC_simple(T_DC_out, mdot_rest)
            Q_DC        = DryCooler.Q
            load_DC     = DryCooler.load
            mdot_dem_cold = mdot_cold - mdot_rest

            # HOT SIDE
            mdot_dem_hot    = mdot_hot

            # CHECK
            cold_check = Q - load_HP - Q_DC - (mdot_dem_cold * self.cp * 5)
            hot_check =  Q - (mdot_dem_hot * self.cp * 5)

            if cold_check >= 1:
                print("ERROR, Mode 1 cold check failed:", cold_check, mdot_cold, self.Q_low, mdot_rest)
            elif hot_check >= 1:
                print("ERROR, hot check failed:", hot_check)

            a = mdot_cold
            b = mdot_hot
            c = mdot_rest
            d = 0

            return(load_HP, load_DC, mdot_dem_cold, mdot_dem_hot, T_evap_in, a, b, c, d)
        
        
        
        def Mode2():
               
            
            if self.T_amb < self.T_GKW + 3:      
                T_DC_out = self.T_amb
            else:
                T_DC_out = self.T_GKW + 3

            T_LTV_table = list(range( 30, 51))
            T_DC_out_table = list(range( -15, 21))
        
            for i in range(len(T_LTV_table)):    
                            if T_LTV_table[i] == self.T_LTV:
                                x = i
                                break
            for i in range(len(T_DC_out_table)):    
                            if T_DC_out_table[i] == T_DC_out:
                                y = i
                                break
            
            # HEATPUMP
            # print(x,y)
            T_evap_in   = T_DC_out
            HeatPump    = WW_HP(x,y)
            load_HP     = HeatPump.load
            Q         = HeatPump.Q
            mdot_cold = HeatPump.mdot_cold
            mdot_hot  = HeatPump.mdot_hot

            mdot_rest = mdot_cold - self.Q_low

            # COLD SIDE
            DryCooler   = DC_simple(T_DC_out, mdot_rest)
            Q_DC        = DryCooler.Q
            load_DC     = DryCooler.load
            mdot_TSA_cold = mdot_cold - mdot_rest

            # TSA @ COLD SIDE
            HeatExchanger   = TSA_1(mdot_TSA_cold)
            mdot_dem_cold   = HeatExchanger.mdot_GKW

            # HOT SIDE
            mdot_dem_hot    = mdot_hot

            # CHECK
            cold_check = Q - load_HP - Q_DC - (mdot_dem_cold * self.cp * 5)
            hot_check =  Q - (mdot_dem_hot * self.cp * 5)

            if cold_check >= 1:
                print("ERROR, Mode 2 cold check failed:", cold_check)
            elif hot_check >= 1:
                print("ERROR, hot check failed:", hot_check)

            a = mdot_cold
            b = mdot_hot
            c = mdot_rest
            d = 0

            return(load_HP, load_DC, mdot_dem_cold, mdot_dem_hot, T_evap_in, a, b, c, d)
        


        def Mode3():
                
            T_evap_in_table = list(range( -15, 21))
            T_LTV_table = list(range( 30, 51))
            T_evap_in = self.T_GKW - 10

            for i in range(len(T_LTV_table)):    
                            if T_LTV_table[i] == self.T_LTV:
                                x = i
                                break
            for i in range(len(T_evap_in_table)):    
                            if T_evap_in_table[i] == T_evap_in:
                                y = i
                                break

            # HEATPUMP
            HeatPump    = WW_HP(x,y)
            load_HP     = HeatPump.load
            Q         = HeatPump.Q
            mdot_cold = HeatPump.mdot_cold
            mdot_hot  = HeatPump.mdot_hot

            # TSA @ COLD SIDE
            HeatExchanger   = TSA_1(mdot_cold)
            mdot_dem_cold   = HeatExchanger.mdot_GKW

            # HOT SIDE   
            mdot_dem_hot    = mdot_hot

            # DC == OFF
            load_DC = 0

            # CHECK
            cold_check = Q - load_HP - (mdot_dem_cold * self.cp * 5)
            hot_check =  Q - (mdot_dem_hot * self.cp * 5)

            if cold_check >= 1:
                print("ERROR, Mode 3 cold check failed:", cold_check)
            elif hot_check >= 1:
                print("ERROR, hot check failed:", hot_check)

            a = mdot_cold
            b = mdot_hot
            c = 0
            d = 0

            return(load_HP, load_DC, mdot_dem_cold, mdot_dem_hot, T_evap_in, a, b, c, d)
        


        def Mode4():
                
            T_DC_out = self.T_amb
            T_evap_in = self.T_GKW - 10
            T_LTV_table = list(range( 30, 51))
            T_evap_in_table = list(range( -15, 21))
            
            for i in range(len(T_LTV_table)):    
                            if T_LTV_table[i] == self.T_LTV:
                                x = i
                                break
            for i in range(len(T_evap_in_table)):    
                            if T_evap_in_table[i] == T_evap_in:
                                y = i
                                break

            # HEATPUMP
            HeatPump    = WW_HP(x,y)
            load_HP     = HeatPump.load
            Q         = HeatPump.Q
            mdot_cold = HeatPump.mdot_cold
            mdot_hot  = HeatPump.mdot_hot

            mdot_rest = mdot_hot - self.Q_low

            # TSA @ COLD SIDE
            HeatExchanger   = TSA_1(mdot_cold)
            mdot_dem_cold   = HeatExchanger.mdot_GKW

            # TSA @ HOT SIDE
            HeatExchanger   = TSA_2(mdot_rest)
            mdot_DC   = HeatExchanger.mdot_DC
            mdot_dem_hot = mdot_hot - mdot_rest

            # DRY COOLER @ HOT SIDE
            DryCooler   = DC_simple(T_DC_out, mdot_DC)
            Q_DC        = DryCooler.Q
            load_DC     = DryCooler.load

            # CHECK
            cold_check = Q - load_HP - (mdot_dem_cold * self.cp * 5)
            hot_check =  Q - Q_DC - (mdot_dem_hot * self.cp * 5)
            
            if cold_check >= 1:
                print("ERROR, Mode 4 cold check failed:", cold_check)
            elif hot_check >= 1:
                print("ERROR, hot check failed:", hot_check)

            a = mdot_cold
            b = mdot_hot
            c = 0
            d = mdot_DC

            return(load_HP, load_DC, mdot_dem_cold, mdot_dem_hot, T_evap_in, a, b, c, d)


        def Mode5():
                
            T_DC_out = self.T_amb
            T_evap_in = self.T_GKW - 10
            T_LTV_table = list(range( 30, 51))
            T_evap_in_table = list(range( -15, 21))
            
            for i in range(len(T_LTV_table)):    
                            if T_LTV_table[i] == self.T_LTV:
                                x = i
                                break
            for i in range(len(T_evap_in_table)):    
                            if T_evap_in_table[i] == T_evap_in:
                                y = i
                                break

           # HEATPUMP
            HeatPump    = WW_HP(x,y)
            load_HP     = HeatPump.load
            Q         = HeatPump.Q
            mdot_cold = HeatPump.mdot_cold
            mdot_hot  = HeatPump.mdot_hot

            mdot_rest = mdot_hot # - self.Q_low

            # TSA @ COLD SIDE
            HeatExchanger   = TSA_1(mdot_cold)
            mdot_dem_cold   = HeatExchanger.mdot_GKW

            # TSA @ HOT SIDE
            HeatExchanger   = TSA_2(mdot_rest)
            mdot_DC   = HeatExchanger.mdot_DC
            mdot_dem_hot = mdot_hot - mdot_rest

            # DRY COOLER @ HOT SIDE
            DryCooler   = DC_simple(T_DC_out, mdot_DC)
            Q_DC        = DryCooler.Q
            load_DC     = DryCooler.load

            # CHECK
            cold_check = Q - load_HP - (mdot_dem_cold * self.cp * 5)
            hot_check =  Q - Q_DC - (mdot_dem_hot * self.cp * 5)

            if cold_check >= 1:
                print("ERROR, Mode 5 cold check failed:", cold_check)
            elif hot_check >= 1:
                print("ERROR, hot check failed:", hot_check)

            a = mdot_cold
            b = mdot_hot
            c = 0
            d = mdot_DC

            return(load_HP, load_DC, mdot_dem_cold, mdot_dem_hot, T_evap_in, a, b, c, d)
        



        #----------------------RESULTS----------------------


        if self.Mode_Value == "Only Heating":
                
            [self.load_HP, self.load_DC, self.mdot_dem_cold, self.mdot_dem_hot, self.T_evap_in, self.a, self.b, self.c, self.d] = Mode1()
                
        if Mode_Value == "More heating than cooling":
                
            [self.load_HP, self.load_DC, self.mdot_dem_cold, self.mdot_dem_hot, self.T_evap_in, self.a, self.b, self.c, self.d] = Mode2()

        if Mode_Value == "Equal heating and cooling":
                
            [self.load_HP, self.load_DC, self.mdot_dem_cold, self.mdot_dem_hot, self.T_evap_in, self.a, self.b, self.c, self.d] = Mode3()

        if Mode_Value == "More cooling than heating":

            [self.load_HP, self.load_DC, self.mdot_dem_cold, self.mdot_dem_hot, self.T_evap_in, self.a, self.b, self.c, self.d] = Mode4()    

        elif Mode_Value == "Only Cooling":
                
            [self.load_HP, self.load_DC, self.mdot_dem_cold, self.mdot_dem_hot, self.T_evap_in, self.a, self.b, self.c, self.d] = Mode5()