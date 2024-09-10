import pandas as pd
import numpy as np

# 为了复现结果，设置随机种子
np.random.seed(42)

# 生成日期范围
dates = pd.date_range(start='2021-01-01', periods=90, freq='D')

# 生成 fake 数据
data = {
    'Date': dates,
    'Module': np.random.choice(['Authentication', 'Dashboard', 'Reporting', 'User Management'], size=90),
    'Test_Cases': np.random.randint(10, 100, size=90),
    'Pass_Rate': np.random.uniform(80, 100, size=90),
    'Fail_Rate': lambda x: 100 - x['Pass_Rate'],
    'Bugs_Found': np.random.poisson(5, size=90),
    'Tester': np.random.choice(['Alice', 'Bob', 'Charlie', 'David'], size=90)
}

df = pd.DataFrame(data)
df['Fail_Rate'] = 100 - df['Pass_Rate']
if __name__ == "__main__":
    print(df.head())
    print(list(df.columns))
    print(df.iloc[:2,:].to_string())