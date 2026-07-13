import streamlit as st
import pandas as pd
import os

# 1. 웹앱 페이지 제목 및 소개
st.title("☀️ 서울-양평 기온 분석 및 전력수요 연관성 대시보드")
st.markdown("""
이 웹앱은 서울과 양평의 기온 데이터를 통해 **도시 열섬현상**을 분석하고, 
더 나아가 **서울의 기온 변화가 전력수요에 미치는 영향**을 시각적으로 살펴봅니다.
""")

# 데이터 불러오기 함수
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 파일 경로 설정
    seoul_path = os.path.join(current_dir, "seoul.csv")
    yang_path = os.path.join(current_dir, "yang.csv")
    power_path = os.path.join(current_dir, "power.csv")
    
    # 안전하게 파일 읽기 함수
    def read_csv_safe(path):
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
            if len(df.columns) > 1: return df
        except:
            pass
        return pd.read_csv(path, encoding="cp949")

    seoul_df = read_csv_safe(seoul_path)
    yang_df = read_csv_safe(yang_path)
    power_df = read_csv_safe(power_path)
    
    # 컬럼명의 미세한 공백 제거
    seoul_df.columns = seoul_df.columns.str.strip()
    yang_df.columns = yang_df.columns.str.strip()
    power_df.columns = power_df.columns.str.strip()
    
    # 각 파일별 필요한 컬럼 자동 매칭 ('기온' 혹은 '전력' 글자가 포함된 컬럼 찾기)
    seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0]
    yp_temp_col = [c for c in yang_df.columns if '기온' in c][0]
    power_val_col = [c for c in power_df.columns if '전력' in c][0]
    
    # '일시' 컬럼을 datetime 형식으로 변환
    seoul_df['일시'] = pd.to_datetime(seoul_df['일시'])
    yang_df['일시'] = pd.to_datetime(yang_df['일시'])
    power_df['일시'] = pd.to_datetime(power_df['일시'])
    
    # 필요한 컬럼만 추출 및 이름 통일
    seoul_df = seoul_df[['일시', seoul_temp_col]].rename(columns={seoul_temp_col: '서울 기온'})
    yang_df = yang_df[['일시', yp_temp_col]].rename(columns={yp_temp_col: '양평 기온'})
    power_df = power_df[['일시', power_val_col]].rename(columns={power_val_col: '전력수요(MWh)'})
    
    return seoul_df, yang_df, power_df

# 메인 로직 실행
try:
    seoul_df, yang_df, power_df = load_data()
    
    # 탭 2개 생성
    tab1, tab2 = st.tabs(["📊 탭1: 도시 열섬 분석", "⚡ 탭2: 기온과 전력 연결"])
    
    # =========================================================================
    # [탭1: 열섬 분석]
    # =========================================================================
    with tab1:
        st.header("도시 열섬현상(Urban Heat Island) 분석")
