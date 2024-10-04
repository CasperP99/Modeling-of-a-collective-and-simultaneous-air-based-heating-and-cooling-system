#--------------------------------IMPORTS--------------------------------
from ModeSelection   import Mode
from EnergyPath   import BlackBox
from Buffers import Buffer
from HeatPumps import B_WW_HP

import pandas as pd
import os
import numpy  as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI as PS
from datetime import datetime



#--------------------------------INITIALIZE--------------------------------

print('---------------------START------------------------')
Season = []
Dataset = []
LTV_Buffer = []
HTV_Buffer = []
GKW_BUffer = []
C_min = []
P_elec = []
P_elec_BP = []
Q_hot = []
Q_cold = []
Q_wtw = []
LTV_gelijk = []
GKW_gelijk = []
MaxCOP = []
COP = []
COP_inc = []
C_max_LTV = []
C_max_HTV = []
C_max_GKW = []

#----------------------------------INPUTS---------------------------------------
#-----Buffer Inputs-----
m_buff_LTV = 13000    # [kg]
m_buff_GKW = 7500     # [kg]
m_buff_HTV = 1500     # [kg]
Cmin = 0.3
Cmax = 0.8
thermocline = 0.15
resolution = 1

#-----Temperature Inputs-----
dT_LTV = 5              # [C]
dT_HTV = 8              # [C]
dT_GKW = -5             # [C]
dT_DC  = 3              # [C]
T_HTV = 78              # [C]
T_GKW = 17              # [C] 

#-----Medium Propertie-----
cp_water = PS('C', 'T', 293, 'P', 101325, 'water')
cp_glycol = 3600

#-----Seasons-----
seasons = ["Winter", "Spring", "Summer", "Autumn"]

#-----Time step size-----
timestep_size = 5 * 60 #seconds

#-----Begin-----
j = 0
True_beginning = datetime.now()
while j < len(seasons):

    season = seasons[j]
    r = 1 

    while r < 11:
        print(season + str(r))
        start_time = datetime.now()

        # 1) Loading in data
        current_directory = os.getcwd()
        csv_file_path = os.path.join(current_directory, 'MODEL', season, f"{season}_{r}.csv")
        DATA   = pd.read_csv(csv_file_path, delimiter=',')
        Date   = DATA.iloc[:, 0]
        T_amb  = DATA.iloc[:, 1]
        Q_LTV  = DATA.iloc[:, 2]
        Q_GKW  = DATA.iloc[:, 3]
        Q_HTV  = DATA.iloc[:, 4]

        # 2) Setting zero arrays to store new data
        load_BM = np.zeros(len(DATA))
        load_BP = np.zeros(len(DATA))
        T_evap_in = np.zeros(len(DATA))
        charge_LTV   = np.zeros(2*len(DATA)+1)
        charge_HTV   = np.zeros(2*len(DATA)+1)
        charge_GKW   = np.zeros(2*len(DATA)+1)
        mdot_LTV_discharge = np.zeros(len(DATA))
        mdot_HTV_discharge = np.zeros(len(DATA))
        mdot_GKW_discharge = np.zeros(len(DATA))
        mdot_LTV = np.zeros(len(DATA))
        mdot_HTV = np.zeros(len(DATA))
        mdot_GKW = np.zeros(len(DATA))

        # 3) Setting temperatures
        if season == "Winter":
            T_LTV = 45
        elif season == "Summer":
            T_LTV = 35
        else:
            T_LTV = 40
        
        T_ret_LTV = T_LTV - dT_LTV
        T_ret_HTV = T_HTV - dT_HTV
        T_ret_GKW = T_GKW - dT_GKW

        # 4) Setting dimension values for Buffers
        n_cline_LTV = int((thermocline*m_buff_LTV) / resolution)   #accuracy, n = mass / resolution
        n_cline_HTV = int((thermocline*m_buff_HTV) / resolution)   #accuracy, n = mass / resolution
        n_cline_GKW = int((thermocline*m_buff_GKW) / resolution)   #accuracy, n = mass / resolution

        n_rest_LTV  = int(m_buff_LTV / resolution) - n_cline_LTV   #accuracy, n = mass / resolution  
        n_rest_HTV  = int(m_buff_HTV / resolution) - n_cline_HTV   #accuracy, n = mass / resolution
        n_rest_GKW  = int(m_buff_GKW / resolution) - n_cline_GKW   #accuracy, n = mass / resolution

        T_cline_LTV = np.zeros(n_cline_LTV)
        T_cline_HTV = np.zeros(n_cline_HTV)
        T_cline_GKW = np.zeros(n_cline_GKW)

        T_rest_LTV = np.zeros(n_rest_LTV)
        T_rest_HTV = np.zeros(n_rest_HTV)
        T_rest_GKW = np.zeros(n_rest_GKW)

        for i in range(n_cline_LTV):
            T_cline_LTV[i] = ((dT_LTV)/n_cline_LTV)*i + T_ret_LTV
        for i in range(n_cline_HTV):
            T_cline_HTV[i] = ((dT_HTV)/n_cline_HTV)*i + T_ret_HTV
        for i in range(n_cline_GKW):
            T_cline_GKW[i] = ((dT_GKW)/n_cline_GKW)*i + T_ret_GKW

        for i in range(n_rest_LTV):
            T_rest_LTV[i] = T_LTV
        for i in range(n_rest_HTV):
            T_rest_HTV[i] = T_HTV
        for i in range(n_rest_GKW):
            T_rest_GKW[i] = T_GKW

        T_sg_LTV = np.concatenate((T_rest_LTV, T_cline_LTV))
        T_sg_LTV.sort()
        T_sg_HTV = np.concatenate((T_rest_HTV, T_cline_HTV))
        T_sg_HTV.sort()
        T_sg_GKW = np.concatenate((T_rest_GKW, T_cline_GKW))
        T_sg_GKW.sort()

        max_charge = 1 - thermocline

        charge_LTV[0] = max_charge
        charge_HTV[0] = max_charge
        charge_GKW[0] = max_charge

        HP = 'On'
        BHP = 'On'
        Time_off = 0
        BTime_off = 0
        t = 0

        total_cold_produced = 0
        total_heat_produced = 0
        dc_cold = 0
        dc_hot = 0

        print("buffersizes:", m_buff_LTV, m_buff_GKW, m_buff_HTV, "Cmin =", Cmin)

        n = range(len(T_sg_LTV))


        #--------------------------------CALCULATOR--------------------------------

        for i in range(len(DATA)):
            # Setting Ambient Temperature
            T_ambient = T_amb[i]
            T_ambient = int(T_ambient)
            T_evap_in[-1] = T_GKW -10
            
            # Discharging Buffer HTV
            mdot_HTV_discharge[i] = -Q_HTV[i]/(cp_water * dT_HTV)
            Discharge_HTV = Buffer(T_HTV, charge_HTV[2*i], mdot_HTV_discharge[i], T_sg_HTV, 'HTV', resolution)
            [charge_HTV[(2*i)+1], T_sg_HTV] = [Discharge_HTV.charge, Discharge_HTV.T_seg]

            # Charging allowed?
            max_HTV = B_WW_HP(T_LTV).mdot_hot
            if BHP == 'On':
                if charge_HTV[(2*i)+1] < Cmax:
                    m_dem_HTV = (max_charge - charge_HTV[(2*i)+1]) * m_buff_HTV               
                else:
                    BHP = 'Off'                
            else:
                if BTime_off > t:
                    if charge_HTV[(2*i)+1] > Cmin:
                        BHP = 'Off' 
                    else:
                        m_dem_HTV = (max_charge - charge_HTV[(2*i)+1]) * m_buff_HTV
                        BHP = 'On'
                else:
                    BHP = 'Off'            
            if BHP == 'On' and m_dem_HTV >= max_HTV:
                BTime_off = 0

                BoosterHP = B_WW_HP(T_LTV)
                [load_BP[i], Q_BHP, mdot_HTV_to_LTV, mdot_HTV[i]] = [BoosterHP.load, BoosterHP.Q, BoosterHP.mdot_cold, BoosterHP.mdot_hot]
                ChargeHTV = Buffer(T_HTV, charge_HTV[(2*i)+1], mdot_HTV[i], T_sg_HTV, 'HTV', resolution)
                [charge_HTV[(2*i)+2], T_sg_HTV] = [ChargeHTV.charge, ChargeHTV.T_seg]            
            else:
                charge_HTV[(2*i)+2] = charge_HTV[(2*i)+1]
                mdot_HTV_to_LTV = 0
                load_BHP = 0
                Q_BHP = 0
                BTime_off = BTime_off + 1

            # Discharging Buffers
            #----------LTV----------
            mdot_LTV_discharge[i] = -Q_LTV[i]/(cp_water * dT_LTV) - mdot_HTV_to_LTV
            Discharge_LTV = Buffer(T_LTV, charge_LTV[2*i], mdot_LTV_discharge[i], T_sg_LTV, 'LTV', resolution)
            [charge_LTV[(2*i)+1], T_sg_LTV] = [Discharge_LTV.charge, Discharge_LTV.T_seg]
            #----------GKW----------
            mdot_GKW_discharge[i] = Q_GKW[i]/(cp_water * dT_GKW)
            Discharge_GKW = Buffer(T_GKW, charge_GKW[2*i], mdot_GKW_discharge[i], T_sg_GKW, 'GKW', resolution)
            [charge_GKW[(2*i)+1], T_sg_GKW] = [Discharge_GKW.charge, Discharge_GKW.T_seg]

            # Charging allowed?
            if HP == 'On':
                HP = 'Off'

                #LTV
                if charge_LTV[(2*i)+1] < Cmin:
                    HP = 'On'
                    m_dem_LTV = (max_charge-charge_LTV[(2*i)+1]) * m_buff_LTV
                else:
                    m_dem_LTV = (max_charge-charge_LTV[(2*i)+1]) * m_buff_LTV

                #GKW
                if charge_GKW[(2*i)+1] < Cmin:
                    HP = 'On'
                    m_dem_GKW = (max_charge-charge_GKW[(2*i)+1]) * m_buff_GKW
                else:
                    m_dem_GKW = (max_charge-charge_GKW[(2*i)+1]) * m_buff_GKW


            else:
                if Time_off > t:
                    #LTV
                    if charge_LTV[(2*i)+1] < Cmin:
                        HP = 'On'
                        m_dem_LTV = (max_charge-charge_LTV[(2*i)+1]) * m_buff_LTV
                    else:
                        m_dem_LTV = (max_charge-charge_LTV[(2*i)+1]) * m_buff_LTV

                    #GKW
                    if charge_GKW[(2*i)+1] < Cmin:
                        HP = 'On'
                        m_dem_GKW = (max_charge-charge_GKW[(2*i)+1]) * m_buff_GKW
                    else:
                        m_dem_GKW = (max_charge-charge_GKW[(2*i)+1]) * m_buff_GKW
                        
            m_dem_GKW = m_dem_GKW * (5/3) * (cp_water/3600)

            #Charging Buffers
            if HP == 'On':
                Mode_Value = 0     # Initiate
                Time_off = 0

                if m_dem_GKW < 1:
                    Mode_Value = "Only Heating"
                elif m_dem_LTV < 1:
                    Mode_Value = "Only Cooling"
                else:
                    Mode_Value = Mode(m_dem_LTV, m_dem_GKW, T_LTV, T_GKW, T_ambient).Mode_Value
                # print("Mode:", Mode_Value, "charges are:", charge_LTV[(2*i)+1], charge_GKW[(2*i)+1])

                # Path Execution
                if Mode_Value == "Only Heating" or Mode_Value == "More heating than cooling" or Mode_Value == "Equal heating and cooling":

                    Q_high = m_dem_LTV
                    Q_low  = m_dem_GKW

                    if Mode_Value == 'Only Heating':
                        # Determining the loads, COPs & mdots
                        BB = BlackBox(Mode_Value, Q_high, Q_low, T_LTV, T_GKW, T_ambient)
                        [load_HP, load_DC, mdot_GKW[i], mdot_LTV[i], T_evap_in[i], a, b, c, d] = [BB.load_HP, BB.load_DC, BB.mdot_dem_cold, BB.mdot_dem_hot, BB.T_evap_in, BB.a, BB.b, BB.c, BB.d]
                        ChargeLTV = Buffer(T_LTV, charge_LTV[(2*i)+1], mdot_LTV[i], T_sg_LTV, 'LTV', resolution)
                        [charge_LTV[(2*i)+2], T_sg_LTV] = [ChargeLTV.charge, ChargeLTV.T_seg]
                        charge_GKW[(2*i)+2] = charge_GKW[(2*i)+1]

                        #Load per timestep
                        load_BM[i] = load_HP + load_DC

                    else:
                        # Determining the loads, COPs & mdots
                        BB = BlackBox(Mode_Value, Q_high, Q_low, T_LTV, T_GKW, T_ambient)
                        [load_HP, load_DC, mdot_GKW[i], mdot_LTV[i], T_evap_in[i], a, b, c, d] = [BB.load_HP, BB.load_DC, BB.mdot_dem_cold, BB.mdot_dem_hot, BB.T_evap_in, BB.a, BB.b, BB.c, BB.d]
                        
                        ChargeLTV = Buffer(T_LTV, charge_LTV[(2*i)+1], mdot_LTV[i], T_sg_LTV, 'LTV', resolution)
                        [charge_LTV[(2*i)+2], T_sg_LTV] = [ChargeLTV.charge, ChargeLTV.T_seg]
                        ChargeGKW = Buffer(T_GKW, charge_GKW[(2*i)+1], mdot_GKW[i], T_sg_GKW, 'GKW', resolution)
                        [charge_GKW[(2*i)+2], T_sg_GKW] = [ChargeGKW.charge, ChargeGKW.T_seg]
                        
                        #Load per timestep
                        load_BM[i] = load_HP + load_DC
                
                elif Mode_Value == "More cooling than heating" or Mode_Value == "Only Cooling":

                    Q_high = m_dem_GKW
                    Q_low  = m_dem_LTV

                    if Mode_Value == "More cooling than heating":
                        # Determining the loads, COPs & mdots
                        BB = BlackBox(Mode_Value, Q_high, Q_low, T_LTV, T_GKW, T_ambient)
                        [load_HP, load_DC, mdot_GKW[i], mdot_LTV[i], T_evap_in[i], a, b, c, d] = [BB.load_HP, BB.load_DC, BB.mdot_dem_cold, BB.mdot_dem_hot, BB.T_evap_in, BB.a, BB.b, BB.c, BB.d]
                        
                        ChargeLTV = Buffer(T_LTV, charge_LTV[(2*i)+1], mdot_LTV[i], T_sg_LTV, 'LTV', resolution)
                        [charge_LTV[(2*i)+2], T_sg_LTV] = [ChargeLTV.charge, ChargeLTV.T_seg]
                        ChargeGKW = Buffer(T_GKW, charge_GKW[(2*i)+1], mdot_GKW[i], T_sg_GKW, 'GKW', resolution)
                        [charge_GKW[(2*i)+2], T_sg_GKW] = [ChargeGKW.charge, ChargeGKW.T_seg]
                        

                    else:
                        # Determining the loads, COPs & mdots
                        BB = BlackBox(Mode_Value, Q_high, Q_low, T_LTV, T_GKW, T_ambient)
                        [load_HP, load_DC, mdot_GKW[i], mdot_LTV[i], T_evap_in[i], a, b, c, d] = [BB.load_HP, BB.load_DC, BB.mdot_dem_cold, BB.mdot_dem_hot, BB.T_evap_in, BB.a, BB.b, BB.c, BB.d]

                        ChargeGKW = Buffer(T_GKW, charge_GKW[(2*i)+1], mdot_GKW[i], T_sg_GKW, 'GKW', resolution)
                        [charge_GKW[(2*i)+2], T_sg_GKW] = [ChargeGKW.charge, ChargeGKW.T_seg]
                        charge_LTV[(2*i)+2] = charge_LTV[(2*i)+1]               

                else:
                    print('ERROR, no Mode is chosen')

            else:
                charge_LTV[(2*i)+2] = charge_LTV[(2*i)+1]
                charge_GKW[(2*i)+2] = charge_GKW[(2*i)+1]
                Time_off = Time_off + 1
                load_HP = 0
                load_DC = 0
                a = 0
                b = 0
                c = 0
                d = 0

            #Load per timestep
            load_BM[i] = 1.1 * (load_HP + load_DC)
            load_BP[i] = 1.1 * load_BP[i]

            total_cold_produced = total_cold_produced + a
            total_heat_produced = total_heat_produced + b
            dc_cold = dc_cold + c
            dc_hot = dc_hot + d

        # Energetic Performance
        total_load_BM = sum(load_BM) / 3.6e6
        total_load_BP = sum(load_BP) / 3.6e6

        total_LTV = sum(mdot_LTV) * dT_LTV  * cp_water / 3.6e6
        total_HTV = sum(mdot_HTV) * dT_HTV * cp_water / 3.6e6
        total_cold = sum(mdot_GKW) * dT_GKW * cp_water / 3.6e6

        total_energy_produced = ((total_heat_produced * dT_LTV * cp_water) - (total_cold_produced * dT_GKW * cp_water) + (sum(mdot_HTV) * dT_HTV * cp_water))/3.6e6
        max_COP = total_energy_produced / (total_load_BM + total_load_BP)

        LTV_gelijktijdigheid = (sum(mdot_LTV) * cp_water * dT_LTV)/(total_heat_produced * cp_water * dT_LTV)
        GKW_gelijktijdigheid = (sum(mdot_GKW) * dT_GKW * cp_water)/(total_cold_produced * 3 * 3600)

        print("LTV-gelijktijdigheid:", LTV_gelijktijdigheid, "GKW-gelijktijdigheid:", GKW_gelijktijdigheid)
        print("Max COP =", max_COP)
        print("Total electric load BM:", total_load_BM, "kWh")
        print("Total useful heat produced:", total_LTV, "kWh")
        print("Total heat produced:", (total_heat_produced * cp_water * dT_LTV)/3.6e6, "kWh")        
        print("Total useful cold produced:", total_cold, "kWh")
        print("Total cold produced:", (total_cold_produced * 3600 * 3)/3.6e6, "kWh")        
        print("SCOP:", (total_LTV-total_cold)/total_load_BM)
        print("Total electric load BP:", total_load_BP, "kWh")
        print("Total useful HTV produced:", total_HTV, "kWh")
        print(' ')
        print("Total COP:", (total_LTV - total_cold + total_HTV)/(total_load_BP + total_load_BM))

        #--------------------------------VERIFICATION--------------------------------
        Ver_dis_LTV_1 = np.zeros(len(DATA))
        Ver_dis_LTV_2 = np.zeros(len(DATA))
        Ver_dis_LTV_3 = np.zeros(len(DATA))
        Ver_dis_LTV_err = np.zeros(len(DATA))
        Ver_dis_LTV_check = np.zeros(len(DATA))

        Ver_dis_HTV_1 = np.zeros(len(DATA))
        Ver_dis_HTV_2 = np.zeros(len(DATA))
        Ver_dis_HTV_3 = np.zeros(len(DATA))
        Ver_dis_HTV_err = np.zeros(len(DATA))
        Ver_dis_HTV_check = np.zeros(len(DATA))

        Ver_dis_GKW_1 = np.zeros(len(DATA))
        Ver_dis_GKW_2 = np.zeros(len(DATA))
        Ver_dis_GKW_3 = np.zeros(len(DATA))
        Ver_dis_GKW_err = np.zeros(len(DATA))
        Ver_dis_GKW_check = np.zeros(len(DATA))

        Ver_cha_LTV_1 = np.zeros(len(DATA))
        Ver_cha_LTV_2 = np.zeros(len(DATA))
        Ver_cha_LTV_3 = np.zeros(len(DATA))
        Ver_cha_LTV_err = np.zeros(len(DATA))
        Ver_cha_LTV_check = np.zeros(len(DATA))

        Ver_cha_HTV_1 = np.zeros(len(DATA))
        Ver_cha_HTV_2 = np.zeros(len(DATA))
        Ver_cha_HTV_3 = np.zeros(len(DATA))
        Ver_cha_HTV_err = np.zeros(len(DATA))
        Ver_cha_HTV_check = np.zeros(len(DATA))

        Ver_cha_GKW_1 = np.zeros(len(DATA))
        Ver_cha_GKW_2 = np.zeros(len(DATA))
        Ver_cha_GKW_3 = np.zeros(len(DATA))
        Ver_cha_GKW_err = np.zeros(len(DATA))
        Ver_cha_GKW_check = np.zeros(len(DATA))


        print("Max charges:", max(charge_LTV), max(charge_GKW), max(charge_HTV)) 

        #--------------DISCHARGE--------------

        for i in range(len(DATA)):

            #----------LTV_discharge----------

            Ver_dis_LTV_1[i] = charge_LTV[2*i]/charge_LTV[2*i]
            Ver_dis_LTV_2[i] = charge_LTV[(2*i)+1]/charge_LTV[2*i]
            Ver_dis_LTV_3[i] = -(mdot_LTV_discharge[i]/m_buff_LTV)/charge_LTV[2*i]

            if charge_LTV[2*i] == 0:
                print("ERROR, LTV-buffer was not charged @ timestep", i)

            Ver_dis_LTV_err[i] = Ver_dis_LTV_1[i] - Ver_dis_LTV_2[i] - Ver_dis_LTV_3[i]
            Ver_dis_LTV_check[i] = Ver_dis_LTV_err[i]*charge_LTV[2*i]*m_buff_LTV
            
            if abs(Ver_dis_LTV_check[i]) > resolution:
                print("ERRORR, LTV-dis-err[i] too big:", Ver_dis_LTV_check[i], "@ timestep", i)

            #----------HTV_discharge----------

            Ver_dis_HTV_1[i] = charge_HTV[2*i]/charge_HTV[2*i]
            Ver_dis_HTV_2[i] = charge_HTV[(2*i)+1]/charge_HTV[2*i]
            Ver_dis_HTV_3[i] = -(mdot_HTV_discharge[i]/m_buff_HTV)/charge_HTV[2*i]

            if charge_HTV[2*i] == 0:
                print("ERROR, HTV-buffer was not charged @ timestep", i)

            Ver_dis_HTV_err[i] = Ver_dis_HTV_1[i] - Ver_dis_HTV_2[i] - Ver_dis_HTV_3[i]
            Ver_dis_HTV_check[i] = Ver_dis_HTV_err[i]*charge_HTV[2*i]*m_buff_HTV
            
            if abs(Ver_dis_HTV_check[i]) > resolution:
                print("ERRORR, HTV-dis-err[i] too big:", Ver_dis_HTV_check[i], "@ timestep", i)
            

            #----------GKW_discharge----------

            Ver_dis_GKW_1[i] = charge_GKW[2*i]/charge_GKW[2*i]
            Ver_dis_GKW_2[i] = charge_GKW[(2*i)+1]/charge_GKW[2*i]
            Ver_dis_GKW_3[i] = -(mdot_GKW_discharge[i]/m_buff_GKW)/charge_GKW[2*i]

            if charge_GKW[2*i] == 0:
                print("ERROR, GKW-buffer was not charged @ timestep", i)

            Ver_dis_GKW_err[i] = Ver_dis_GKW_1[i] - Ver_dis_GKW_2[i] - Ver_dis_GKW_3[i]
            Ver_dis_GKW_check[i] = Ver_dis_GKW_err[i]*charge_GKW[2*i]*m_buff_GKW
            
            if abs(Ver_dis_GKW_check[i]) > resolution:
                print("ERRORR, GKW-dis-err[i] too big:", Ver_dis_GKW_check[i], "@ timestep", i)

        
        #--------------CHARGE--------------

        for i in range(len(DATA)):

            #----------LTV_charge----------

            Ver_cha_LTV_1[i] = charge_LTV[(2*i)+2]/charge_LTV[(2*i)+2]
            Ver_cha_LTV_2[i] = charge_LTV[(2*i)+1]/charge_LTV[(2*i)+2]
            Ver_cha_LTV_3[i] = (mdot_LTV[i]/m_buff_LTV)/charge_LTV[(2*i)+2]

            Ver_cha_LTV_err[i] = Ver_cha_LTV_1[i] - Ver_cha_LTV_2[i] - Ver_cha_LTV_3[i]
            Ver_cha_LTV_check[i] = Ver_cha_LTV_err[i]*charge_LTV[(2*i)+2]*m_buff_LTV
            
            if abs(Ver_cha_LTV_check[i]) > resolution:
                print("ERRORR, LTV-cha-err[i] too big:", Ver_cha_LTV_check[i], "@ timestep", i)

            #----------HTV_charge----------

            Ver_cha_HTV_1[i] = charge_HTV[(2*i)+2]/charge_HTV[(2*i)+2]
            Ver_cha_HTV_2[i] = charge_HTV[(2*i)+1]/charge_HTV[(2*i)+2]
            Ver_cha_HTV_3[i] = (mdot_HTV[i]/m_buff_HTV)/charge_HTV[(2*i)+2]

            Ver_cha_HTV_err[i] = Ver_cha_HTV_1[i] - Ver_cha_HTV_2[i] - Ver_cha_HTV_3[i]
            Ver_cha_HTV_check[i] = Ver_cha_HTV_err[i]*charge_HTV[(2*i)+2]*m_buff_HTV
            
            if abs(Ver_cha_HTV_check[i]) > resolution:
                print("ERRORR, HTV-cha-err[i] too big:", Ver_cha_HTV_check[i], "@ timestep", i)

            #----------GKW_charge----------

            Ver_cha_GKW_1[i] = charge_GKW[(2*i)+2]/charge_GKW[(2*i)+2]
            Ver_cha_GKW_2[i] = charge_GKW[(2*i)+1]/charge_GKW[(2*i)+2]
            Ver_cha_GKW_3[i] = (mdot_GKW[i]/m_buff_GKW)/charge_GKW[(2*i)+2]

            Ver_cha_GKW_err[i] = Ver_cha_GKW_1[i] - Ver_cha_GKW_2[i] - Ver_cha_GKW_3[i]
            Ver_cha_GKW_check[i] = Ver_cha_GKW_err[i]*charge_GKW[(2*i)+2]*m_buff_GKW
            
            if abs(Ver_cha_GKW_check[i]) > resolution:
                print("ERRORR, GKW-cha-err[i] too big:", Ver_cha_GKW_check[i], "@ timestep", i)    

        Season.append(season)
        Dataset.append(r)
        LTV_Buffer.append(m_buff_LTV)
        HTV_Buffer.append(m_buff_HTV)
        GKW_BUffer.append(m_buff_GKW)
        C_min.append(Cmin)
        P_elec.append(total_load_BM)
        P_elec_BP.append(total_load_BP)
        Q_hot.append(total_LTV)
        Q_cold.append(total_cold)
        Q_wtw.append(total_HTV)
        LTV_gelijk.append(LTV_gelijktijdigheid)
        GKW_gelijk.append(GKW_gelijktijdigheid)
        MaxCOP.append(max_COP)
        COP.append((total_LTV-total_cold)/total_load_BM)
        COP_inc.append((total_LTV + total_HTV - total_cold)/(total_load_BM + total_load_BP))
        C_max_LTV.append(max(charge_LTV))
        C_max_HTV.append(max(charge_HTV))
        C_max_GKW.append(max(charge_GKW))

        if max(abs(Ver_dis_LTV_check)) > resolution:
            r = 1
            if Cmin <= 0.35:
                Cmin = Cmin + 0.025
            else:
                Cmin = 0.2
                m_buff_LTV = m_buff_LTV + 500
        elif max(abs(Ver_dis_GKW_check)) > resolution:
            r = 1
            if Cmin <= 0.35:
                Cmin = Cmin + 0.025
            else:
                Cmin = 0.2
                m_buff_GKW = m_buff_GKW + 500     
        elif max(abs(Ver_dis_HTV_check)) > resolution:
            r = 1
            if Cmin <= 0.35:
                Cmin = Cmin + 0.025
            else:
                Cmin = 0.2
                m_buff_HTV = m_buff_HTV + 500
        elif max(abs(Ver_cha_LTV_check)) > resolution or round(max(charge_LTV),4) > max_charge:
            r = 1
            m_buff_LTV = m_buff_LTV + 500
        elif max(abs(Ver_cha_GKW_check)) > resolution or round(max(charge_GKW),4) > max_charge:
            r = 1
            m_buff_GKW = m_buff_GKW + 500     
        elif max(abs(Ver_cha_HTV_check)) > resolution or round(max(charge_HTV),4) > max_charge:
            r = 1
            m_buff_HTV = m_buff_HTV + 500     
        else:
            r = r + 1
        
        if r == 11:
            j = j + 1

        end_time = datetime.now()
        print(end_time - start_time)

results = pd.DataFrame(zip(Season, Dataset, LTV_Buffer, HTV_Buffer, GKW_BUffer, C_min, P_elec, P_elec_BP, Q_hot, Q_cold, Q_wtw, LTV_gelijk, GKW_gelijk, MaxCOP, COP, COP_inc, C_max_LTV, C_max_HTV, C_max_GKW), 
                columns=['Season', 'Dataset', 'LTV Buffer', 'HTV Buffer', 'GKW Buffer', 'Cmin', 'P_elec', 'P_elec_BP', 'Q_hot', 'Q_cold', 'Q_HTV', 'LTV-gelijk', 'GKW-gelijk', 'Max COP', 'COP', 'COP_inc', 'C_max_LTV', 'C_max_HTV', 'C_max_GKW'])

results.to_excel('Results.xlsx')

True_end = datetime.now()
totaltime = (True_end - True_beginning)
print(totaltime)