import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import random
import os
from scipy.stats import multivariate_normal

# ----- Weather Data
current_directory = os.getcwd()
print(current_directory)
csv_file_path = os.path.join(current_directory, 'MODEL', 'Modules', 'DemandCreation', 'Winter.csv')
df = pd.read_csv(csv_file_path, delimiter=',')
df = df.drop(columns=['Unnamed: 0', 'station_code', 'T10N', 'TD', 'ds'])
df['T'] = df['T'] * 0.1
df['dT'] = (17.4 - df['T'])
begin = '2023-09-01' #'2023-12-23'
end = '2023-11-30' #'2024-03-10'

# ----- Creating interpolated datapoints for the weather
interpolated_knmi = []

for i in range(len(df['T'])-1):
    start = df['T'].iloc[i]
    end = df['T'].iloc[i + 1]
    points = np.linspace(start, end, num=12, endpoint=False)  # 12 includes both start and end
    interpolated_knmi.extend(points)

interpolated_knmi.append(df['T'].iloc[-1])
interpolated = pd.DataFrame(interpolated_knmi, columns=['T'])
interpolated['rolling_KNMI'] = interpolated['T'].rolling(2 * 12, center=True).mean()
interpolated.index = pd.date_range(begin, periods=len(interpolated_knmi), freq='5min')

for i in range(24):
    interpolated['rolling_KNMI'].iloc[i]  = interpolated_knmi[i]
    interpolated['rolling_KNMI'].iloc[-i] = interpolated_knmi[-i]

# ----- Creating new data using a Gaussian distribution
std = 11149.347400905994
demand = []

for i in range(len(interpolated_knmi)):

    if interpolated_knmi[i] <= 15.9:
        mean = 8822.5 * (17.4 - interpolated_knmi[i]) + 70.664
        value = abs(np.random.normal(mean, std))
    elif interpolated_knmi[i] >= 18.9:
        mean = 8822.5 * (17.4 - interpolated_knmi[i]) + 70.664
        value = -abs(np.random.normal(mean, std))
    else:
        value = 0

    demand.append(value)

interpolated['Demand'] = demand

# ----- Seperation of LTV and GKW
LTV = []
GKW = []

for i in range(len(interpolated_knmi)):

    if interpolated['Demand'].iloc[i] > 0:
        hot = interpolated['Demand'].iloc[i]
        cold = 0
    elif interpolated['Demand'].iloc[i] < 0:
        hot = 0
        cold = interpolated['Demand'].iloc[i]
    else:
        hot = 0
        cold = 0
    
    LTV.append(hot)
    GKW.append(cold)

interpolated['LTV'] = LTV
interpolated['GKW'] = GKW


# ----- Hot tapwater demand
ratio = 2/3
total_demand = sum(interpolated['LTV']) * ratio
n_timesteps = len(interpolated['LTV'])
# av_demand = total_demand/n_timesteps
# print('av_demand =', av_demand)
av_demand = 36850
mean_dif = av_demand * 0.15

std_wtw = mean_dif
HTV = []

for i in range(len(interpolated_knmi)):
    if (interpolated.index[i].hour > 6 and interpolated.index[i].hour < 10) or (interpolated.index[i].hour > 16 and interpolated.index[i].hour < 20):
        value = np.random.normal(2 * av_demand, std_wtw)
    else:
        value = np.random.normal((2/3) * av_demand, std_wtw)
    
    HTV.append(value)

interpolated['HTV'] = HTV
check = (sum(interpolated['HTV'])/len(interpolated_knmi) / av_demand)

# ----- Size of the Project
n_households = 179  # number of houses
n_commercial = 4000 # m2 of commercial floorspace

interpolated['LTV'] = interpolated['LTV'] * n_households
interpolated['HTV'] = interpolated['HTV'] * n_households
interpolated['GKW'] = interpolated['GKW'] * n_households

# ----- Commercial cooling
average_demand_commercial_cooling = n_commercial * 41.7 * 3.6e6 / (365*24*12) # average Joule per timestep
mean_dif = average_demand_commercial_cooling * 0.15

std_commercial_cooling = mean_dif
GKW_commercial = []

for i in range(len(interpolated_knmi)):
    if interpolated.index[i].hour < 8 or interpolated.index[i].hour > 17:
        value = -abs(np.random.normal(11/24 * average_demand_commercial_cooling, std_commercial_cooling))
    else:
        value = -abs(np.random.normal(24/13 * average_demand_commercial_cooling, std_commercial_cooling))

    GKW_commercial.append(value)

interpolated['GKW_commercial'] = GKW_commercial

# ----- Formatting for final use
interpolated['GKW'] = abs(interpolated['GKW'])#+ interpolated['GKW_commercial'])
# interpolated = interpolated.drop(['GKW_commercial', 'rolling_KNMI', 'Demand'], axis=1)

# ----- Prints
print(interpolated)

# ----- Showing results
plt.figure(1)
interpolated['LTV'].plot(style='orange')
interpolated['HTV'].plot(style='red')
interpolated['GKW'].plot(style='blue')
# interpolated['GKW_commercial'].plot(style='green')

plt.figure(2)
interpolated['T'].plot()

# plt.show()

# ----- Saving results
interpolated.to_csv('Winter_extra.csv')