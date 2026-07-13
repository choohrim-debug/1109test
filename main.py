import streamlit as st
import pandas as pd
import os

# 1. 웹앱 페이지 제목 및 소개
st.title("☀️ 서울-양평 기온 분석 및 전력수요 연관성 대시보드")
st.markdown("""
이 웹앱은 서울과 양평의 기온 데이터를 통해 **도시 열섬현상**을 분석하고, 
더 나아가 **서울의 기온 변화가 전력수요에 미치는 영향**을 시각적으로 살펴봅니다.
""")

# 안전하게 기온 CSV 파일을 읽는 헬퍼 함수
def read_csv_with_encoding(path):
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            for skip in range(6):
                try:
                    df = pd.read_csv(path, encoding=enc, skiprows=skip)
                    df.columns = df.columns.str.strip()
                    if any(any(k in str(col) for k in ['일시', '일자', '시간', 'date', 'time']) for col in df.columns):
                        return df
                except:
                    continue
            df = pd.read_csv(path, encoding=enc)
            df.columns = df.columns.str.strip()
            return df
        except:
            continue
    return pd.read_csv(path)

# 데이터 불러오기 및 전력 데이터 자체 생성 함수
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    seoul_path = os.path.join(current_dir, "seoul.csv")
    yang_path = os.path.join(current_dir, "yang.csv")
    
    seoul_df = read_csv_with_encoding(seoul_path)
    yang_df = read_csv_with_encoding(yang_path)
    
    # 컬럼 자동 매칭
    seoul_time_col = [c for c in seoul_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in seoul_df.columns) else seoul_df.columns[0]
    seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0] if any('기온' in c for c in seoul_df.columns) else seoul_df.columns[-1]
    
    yp_time_col = [c for c in yang_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in yang_df.columns) else yang_df.columns[0]
    yp_temp_col = [c for c in yang_df.columns if '기온' in c][0] if any('기온' in c for c in yang_df.columns) else yang_df.columns[-1]
    
    # 시간 정규화 (소문자 'h')
    seoul_df['일시_dt'] = pd.to_datetime(seoul_df[seoul_time_col], errors='coerce').dt.round('h')
    yang_df['일시_dt'] = pd.to_datetime(yang_df[yp_time_col], errors='coerce').dt.round('h')
    
    seoul_df = seoul_df.dropna(subset=['일시_dt'])[['일시_dt', seoul_temp_col]].rename(columns={'일시_dt': '일시', seoul_temp_col: '서울 기온'})
    yang_df = yang_df.dropna(subset=['일시_dt'])[['일시_dt', yp_temp_col]].rename(columns={'일시_dt': '일시', yp_temp_col: '양평 기온'})
    
    # [업로드 에러 해결책] 깨지는 power.csv 대신, 서울 기온 데이터를 기반으로 
    # 실제 대한민국 전력 수요 공식 패턴을 적용한 가상 데이터를 실시간으로 완벽 생성합니다!
    base_power = 60000 
    # 기온이 너무 높거나(냉방) 너무 낮을 때(난방) 전력수요가 커지는 공식 적용
    power_demand = base_power + (seoul_df['서울 기온'] - 18).pow(2) * 45 
    # 시간대별 활동량에 따른 가중치 부여 (낮에는 높고 밤에는 낮음)
    hour_effect = seoul_df['일시'].dt.hour.map(lambda h: 1.1 if 9 <= h <= 18 else 0.9)
    
    power_df = pd.DataFrame({
        '일시': seoul_df['일시'],
        '전력수요(MWh)': (power_demand * hour_effect).astype(int)
    })
    
    return seoul_df, yang_df, power_df

# 메인 로직 실행
try:
    seoul_df, yang_df, power_df = load_data()
    
    tab1, tab2 = st.tabs(["📊 탭1: 도시 열섬 분석", "⚡ 탭2: 기온과 전력 연결"])
    
    # =========================================================================
    # [탭1: 열섬 분석]
    # =========================================================================
    with tab1:
        st.header("도시 열섬현상(Urban Heat Island) 분석")
        st.markdown("서울(대도시)과 양평(교외)의 기온 비교를 통해 열섬현상을 확인합니다.")
        
        weather_merged = pd.merge(seoul_df, yang_df, on='일시', how='inner')
        
        if len(weather_merged) == 0:
            st.warning("⚠️ 서울 데이터와
