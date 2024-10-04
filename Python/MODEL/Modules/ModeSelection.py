from HeatPumps import WW_HP
from CoolProp.CoolProp import PropsSI as PS

class Mode:


    def __init__(self, Q_LTV, Q_GKW, T_LTV, T_GKW, T_amb):
        
        self.Q_LTV = Q_LTV #kg/s
        self.Q_GKW = Q_GKW #kg/s
        self.T_LTV = T_LTV #kg/s
        self.T_GKW = T_GKW #kg/s
        self.T_amb = T_amb

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

        HeatPump = WW_HP(x,y)
        mdot_cold = HeatPump.mdot_cold
        mdot_hot  = HeatPump.mdot_hot

        hot = self.Q_LTV - mdot_hot
        cold = self.Q_GKW - mdot_cold

        if hot >= 0 and cold >= 0:
            self.Mode_Value = "Equal heating and cooling"
        elif hot >= 0 and cold < 0: 
            self.Mode_Value = "More heating than cooling"
        elif hot < 0 and cold >= 0:
            self.Mode_Value = "More cooling than heating"
        else:
            print('ERROR: BUFFERS TOO SMALL')
            print("hot:", self.Q_LTV, mdot_hot)
            print("cold:", self.Q_GKW, mdot_cold)

