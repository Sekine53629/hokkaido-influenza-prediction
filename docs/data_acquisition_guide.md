# Data Acquisition Guide

This guide provides step-by-step instructions to download the required data for the Hokkaido Influenza Prediction project.

## 1. Influenza Data

### Source
**Hokkaido Infectious Disease Surveillance Center**
https://www.iph.pref.hokkaido.jp/kansen/501/data.html

### Steps

1. Visit the above URL
2. Navigate to the data section showing weekly reports ("週報データ")
3. Download CSV files for the following years:
   - 2015年 (2015.csv)
   - 2016年 (2016.csv)
   - 2017年 (2017.csv)
   - 2018年 (2018.csv)
   - 2019年 (2019.csv)
   - 2020年 (2020.csv)
   - 2021年 (2021.csv)
   - 2022年 (2022.csv)
   - 2023年 (2023.csv)
   - 2024年 (2024.csv)

4. Save all files to `data/raw/influenza/` directory

### Expected Data Structure

```
週 (Week)
年 (Year)
報告数 (Reported cases)
定点当たり (Cases per sentinel)
```

**Note**: The CSV files are likely in Shift-JIS encoding. Make sure to specify encoding when reading:
```python
pd.read_csv('file.csv', encoding='shift-jis')
```

## 2. Weather Data

### Source
**Japan Meteorological Agency - Past Weather Data Download**
https://www.data.jma.go.jp/risk/obsdl/index.php

### Steps

1. Visit the above URL
2. Select the following options:
   - **地点選択 (Location)**: 札幌 (Sapporo)
   - **項目選択 (Items)**:
     - 気温 (Temperature) - 日平均 (Daily average)
     - 湿度 (Humidity) - 日平均 (Daily average)
     - 降水量 (Precipitation) - 日合計 (Daily total) [optional]
   - **期間選択 (Period)**:
     - Start: 2015年1月1日
     - End: 2024年12月31日
   - **データ形式 (Format)**: CSV

3. Click "CSVファイルをダウンロード" (Download CSV file)

4. Save the downloaded file to `data/raw/weather/sapporo_weather_2015-2024.csv`

### Expected Columns

```
年月日 (Date)
平均気温(℃) (Average Temperature)
平均湿度(%) (Average Humidity)
降水量の合計(mm) (Total Precipitation) [if selected]
```

## 3. Additional Data (Optional)

### School Calendar Data

For the school holiday feature, create a simple CSV file manually:

**File**: `data/raw/school_holidays.csv`

```csv
start_date,end_date,holiday_type
2015-07-25,2015-08-20,summer
2015-12-24,2016-01-18,winter
2016-03-25,2016-04-05,spring
2016-07-25,2016-08-20,summer
2016-12-24,2017-01-18,winter
2017-03-25,2017-04-05,spring
...
```

**Note**: Hokkaido school holidays typically are:
- Summer: Late July - Mid August (~25 days)
- Winter: Late December - Mid January (~25 days)
- Spring: Late March - Early April (~2 weeks)

## 4. Data Verification

After downloading all files, your directory structure should look like:

```
data/
├── raw/
│   ├── influenza/
│   │   ├── 2015.csv
│   │   ├── 2016.csv
│   │   ├── ...
│   │   └── 2024.csv
│   ├── weather/
│   │   └── sapporo_weather_2015-2024.csv
│   └── school_holidays.csv (optional)
└── processed/
    └── (empty for now)
```

Run the following Python code to verify:

```python
import os
import pandas as pd

# Check influenza data
influenza_files = os.listdir('data/raw/influenza/')
print(f"Influenza files found: {len(influenza_files)}")
print(influenza_files)

# Check weather data
weather_file = 'data/raw/weather/sapporo_weather_2015-2024.csv'
if os.path.exists(weather_file):
    print("Weather data found")
    df_weather = pd.read_csv(weather_file)
    print(f"Weather data shape: {df_weather.shape}")
else:
    print("Weather data NOT found")

# Test reading an influenza file
df_flu = pd.read_csv('data/raw/influenza/2019.csv', encoding='shift-jis')
print(f"\nSample influenza data (2019):")
print(df_flu.head())
```

## Troubleshooting

### Encoding Issues
If you encounter garbled text when reading CSV files:
```python
# Try different encodings
pd.read_csv('file.csv', encoding='shift-jis')
pd.read_csv('file.csv', encoding='cp932')
pd.read_csv('file.csv', encoding='utf-8')
```

### Missing Data
- Some weeks may have missing or zero values
- Handle these during preprocessing (imputation or exclusion)

### File Format Variations
- Column names may vary by year
- Check column names for each year and standardize during preprocessing

## Next Steps

Once data is acquired, proceed to:
1. **EDA** - `notebooks/01_data_exploration.ipynb`
2. **Data Merging** - Combine influenza and weather data by week
3. **Feature Engineering** - Create lag features, seasonal indicators, etc.
