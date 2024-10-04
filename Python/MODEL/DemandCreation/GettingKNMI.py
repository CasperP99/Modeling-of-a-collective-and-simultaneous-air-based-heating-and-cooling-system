import datetime as dt
import logging
import pandas as pd
import requests
import pytz

def get_knmi_weather_data(start_time: dt.datetime, end_time: dt.datetime):
    '''
    Get hourly KNMI weather data from all the weather stations in the Netherlands. Get all hourly date between (inclusive) the given
    `start_time` and `end_time`, rounded to hours. It is allowed to get the weather data for one hour by supplying an equal start and end time.
 
    Timestamps can be tz-aware or -naive, if they are naive they are assumed to be UTC.
 
    ### Parameters
        * `start_time`, dt.datetime object with the start of the timerange for the data
        * `end_time`, dt.datetime object with the end of the timerange for the data
 
    ### Returns
    A dataframe with the weather data. Has a dt.datetime column called `ds` in UTC timezone.
    See https://www.daggegevens.knmi.nl/klimatologie/daggegevens for information on all variables.
 
 
    ### Developer Comments
    You can find an explanation of the API here: https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-een-script
    KNMI hour data can be supplied with an hour but this seems to be bugged as it is impossible to ask for hour 24 (23:00-00:00).
    If hour 24 is used instead all data of the NEXT day is supplied. So for now we just ask for the data of the entire day and then
    filter the dataframe.
 
    Also unsure of timezone is but since 23rd March 02:00 exists, I assume it is UTC.
    '''
 
    # we use these to filter for the correct start and stop time later
    orig_start_time = pytz.utc.localize(start_time) if start_time.tzinfo is None else start_time
    orig_end_time = pytz.utc.localize(end_time) if end_time.tzinfo is None else end_time
    # round to nearest hour
    orig_start_time = orig_start_time.replace(microsecond=0, second=0, minute=0)
    orig_end_time = orig_end_time.replace(microsecond=0, second=0, minute=0)
 
    # KNMI only allows getting data for 30 days, so if we ask for more data, we split the request up.
    no_split_needed = False
    df = pd.DataFrame()
    while (end_time - start_time).total_seconds() >= 0 and not no_split_needed:
        if (end_time - start_time).days < 30:
            no_split_needed = True
            temp_end_time = end_time
        else:
            temp_end_time = start_time + dt.timedelta(days=30)
        print(f"Start date: {start_time}, End date: {temp_end_time}")
        # the knmi works with hours from 1-24, pandas/python works with 0-23 so we have to add 1 to the hour value
        # moreover, using the value 24 gives all timepoints for the NEXT day and using the value 0 gives all timepoints
        api_format_start_time = start_time.strftime('%Y%m%d')
        api_format_end_time = temp_end_time.strftime('%Y%m%d')
 
        try:
            # station_codes = 'ALL'
            # url = f'https://www.daggegevens.knmi.nl/klimatologie/uurgegevens?start={api_format_start_time}&end={api_format_end_time}&stns={station_codes}&fmt=json'
            url = 'https://www.daggegevens.knmi.nl/klimatologie/uurgegevens'
            data = {
                'start': api_format_start_time,
                'end': api_format_end_time,
                'vars': 'TEMP',
                'stns': '370',
                'fmt': 'json',
            }
 
            new_info = pd.DataFrame(requests.get(url=url, data=data).json())
            print("Got response!")
            if not new_info.empty:
                new_info = new_info
                if df.empty:
                    df = new_info
                else:
                    df = pd.concat([df, new_info])
                    print("Data added to the Dataframe")
            else:
                print((f"Got an empty dataframe from KNMI for start {api_format_start_time}, {api_format_end_time}"))
 
        except Exception:
            print("Error getting KNMI Weather data")
        start_time = temp_end_time
 
    print("Done collecting KNMI data into dataframe (first and last)")
    if df.empty:
        print("Dataframe collected is empty")
    else:
        # as KNMI hours are +1 from pandas, we have to subtract 1
        df['ds'] = pd.to_datetime(df.pop('date'), utc=True) + pd.to_timedelta(df.pop('hour') - 1, unit='hour')
        df = df.drop_duplicates()
        df = df.loc[(df['ds'] >= orig_start_time) & (df['ds'] <= orig_end_time)]
        df = df.sort_values(by=['ds'])
        # df = df.rename(columns=knmi_fields_dict)
        if df.shape[0] > 1:
            print(f"Pandas Dataframe overview (first and last rows):\n{df[['ds', 'station_code', 'T']].iloc[[0, -1]]}")
            print(f"Size: {df.shape}")
        else:
            print(df.shape)
            print(f"Pandas Dataframe overview, only one row\n{df[['ds', 'station_code', 'T']].iloc[0]}")
 
    return df

x = get_knmi_weather_data(dt.datetime(2023,9,1), dt.datetime(2023,11,30))
x.to_csv('Autumn.csv')

