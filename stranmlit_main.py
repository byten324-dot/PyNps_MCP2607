import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform
import seaborn as sns
import re
import streamlit as st

# 한글폰트 설정
try :
    if platform.system() == 'Windows':
    # 윈도우인 경우
        font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
        rc('font', family=font_name)
    else:    
    # Mac 인 경우
        rc('font', family='AppleGothic')
except :
    pass
matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지


st.title("국민연금 데이터 분석")


