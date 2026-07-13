import streamlit as st
import pandas as pd
import os
import re

# 1. 웹앱 페이지 제목 및 소개
st.title("☀️ 서울-양평 기온 분석 및 전력수요 연관성 대시보드")
st.markdown("""
이 웹앱은 서울과 양평의 기온 데이터를 통해 **도시 열섬현상**을 분석하고, 
더 나아가 **서울의 기온 변화가 전력수요(MWh)에 미치는 영향**을 시각적으로 살펴봅니다.
""")

# 깨진 power.csv 파일을 강제로 정상화하는 특수 함수
def repair_power_data(path):
    try:
        # 파일을 바이너리로 읽어서 텍스트 추출
        with open(path, 'rb') as f:
            content = f.read().decode('utf-8-sig', errors='ignore')
        
        # 쉼표나 줄바꿈 없이 한 줄로 뭉친 데이터에서 날짜와 숫자 패턴 추출
        # 패턴 예시: 2025-01-01 01:00,62256
        pairs = re.findall(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*,\s*(\d+)', content)
        
        if pairs:
            df = pd.DataFrame(pairs, columns=['일시', '전력수요(MWh)'])
            df['전력수요(MWh)'] = pd.to_numeric(df['전력수요(MWh)'])
            return df
    except:
        pass
    
    # 만약 일반적인 형태로 읽기 성공하면 그대로 반환
    try:
        df = pd.read_csv(path, encoding='utf-8-sig')
        return df
    except:
        return pd.read_csv(path, encoding='cp949')

# 안전하게 기온 CSV 파일을 읽는 헬퍼 함수
def read_weather_csv(path):
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            df.columns = df.columns.str.strip()
            if any('기온' in c for c in df.columns):
                return df
        except:
            continue
    return pd.read_csv(path)

# 데이터 불러오기 및 결합 함수
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    seoul_path = os.path.join(current_dir, "seoul.csv")
    yang_path = os.path.join(current_dir, "yang.csv")
    power_path = os.path.join(current_dir, "power.csv")
    
    seoul_df = read_weather_csv(seoul_path)
    yang_df = read_weather_csv(yang_path)
    # 전력 데이터는 특수 복구 함수로 로드
    power_df = repair_power_data(power_path)
    
    # 기온 컬럼 자동 찾기
    seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0]
    yp_temp_col = [c for c in yang_df.columns if '기온' in c][0]
    
    # 시간 포맷 정규화 (정각 단위 'h'로 반올림)
    seoul_df['일시_dt'] = pd.to_datetime(seoul_df['일시'], errors='coerce').dt.round('h')
    yang_df['일시_dt'] = pd.to_datetime(yang_df['일시'], errors='coerce').dt.round('h')
    power_df['일시_dt'] = pd.to_datetime(power_df['일시'], errors='coerce').dt.round('h')
    
    # 결측치 제거 및 정제
    seoul_df = seoul_df.dropna(subset=['일시_dt'])[['일시_dt', seoul_temp_col]].rename(columns={'일시_dt': '일시', seoul_temp_col: '서울 기온'})
    yang_df = yang_df.dropna(subset=['일시_dt'])[['일시_dt', yp_temp_col]].rename(columns={'일시_dt': '일시', yp_temp_col: '양평 기온'})
    power_df = power_df.dropna(subset=['일시_dt'])[['일시_dt', '전력수요(MWh)']].rename(columns={'일시_dt': '일시'})
    
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
            st.warning("⚠️ 기온 데이터의 시간대 정보가 일치하지 않습니다.")
        else:
            weather_merged['기온차(서울-양평)'] = weather_merged['서울 기온'] - weather_merged['양평 기온']
            weather_merged['시각'] = weather_merged['일시'].dt.hour
            weather_merged['월'] = weather_merged['일시'].dt.month
            
            st.subheader("① 1년간 두 지역 기온 변화")
            st.line_chart(weather_merged.set_index('일시')[['서울 기온', '양평 기온']])
            
            st.subheader("② 시각(0~23시)별 평균 기온차 (서울 - 양평)")
            st.bar_chart(weather_merged.groupby('시각')['기온차(서울-양평)'].mean())
            
            st.subheader("③ 월(1~12월)별 평균 기온차 (서울 - 양평)")
            st.bar_chart(weather_merged.groupby('월')['기온차(서울-양평)'].mean())

    # =========================================================================
    # [탭2: 전력 연결]
    # =========================================================================
    with tab2:
        st.header("서울 기온과 전력수요의 연관성 분석")
        st.markdown("대도시 서울의 기온 변화가 실제 전력에 어떤 부하를 주는지 분석합니다.")
        
        power_merged = pd.merge(seoul_df, power_df, on='일시', how='inner')
        
        if len(power_merged) == 0:
            st.error("⚠️ 서울 기온 파일과 전력수요 파일의 매칭되는 시간대가 없습니다.")
        else:
            power_merged['월'] = power_merged['일시'].dt.month
            
            st.subheader("① 기온별 전력수요 분포 (산점도)")
            st.scatter_chart(data=power_merged, x='서울 기온', y='전력수요(MWh)')
            
            st.subheader("② 기온 구간별 평균 전력수요")
            power_merged['기온 구간'] = (power_merged['서울 기온'] // 5) * 5
            st.bar_chart(power_merged.groupby('기온 구간')['전력수요(MWh)'].mean())
            
            st.subheader("③ 월(1~12월)별 평균 전력수요")
            st.bar_chart(power_merged.groupby('월')['전력수요(MWh)'].mean())

except Exception as e:
    st.error(f"⚠️ 시스템 오류가 발생했습니다: {e}")
