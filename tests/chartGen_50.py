

import matplotlib
from matplotlib.font_manager import FontProperties
from matplotlib import font_manager
font_path = 'font/SourceHanSansSC-Normal-2.otf'
font_manager.fontManager.addfont(font_path)
font_prop = FontProperties(fname=font_path)
matplotlib.rcParams['font.sans-serif'] = [font_prop.get_name()]
matplotlib.rcParams['axes.unicode_minus'] = False

import pandas as pd
import matplotlib.pyplot as plt
# 读取 CSV 文件
data = pd.read_csv('/tmp/report/1725526996-id97d2d3b9.csv')
# 提取列数据
x = data['bug_create_date月']
y = data['bug_count计数']
# 设置颜色
colors = plt.get_cmap('tab20c')
# 绘制折线图
plt.plot(x, y, color=colors(0))
# 设置坐标轴标签
plt.xlabel('月份')
plt.ylabel('Bug 数量')
# 设置标题
plt.title('Bug 数量随月份变化')
# 自动调整 x 轴刻度标签的旋转角度
plt.xticks(rotation=45)
# 根据数据范围设置坐标轴范围
plt.xlim(min(x), max(x))
plt.ylim(0, max(y) + 5)
plt.show()