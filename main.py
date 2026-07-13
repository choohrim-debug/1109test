import streamlit as st
import pandas as pd
import os

# 1. 웹앱 페이지 제목 및 소개
st.title("☀️ 서울-양평 기온 분석 및 전력수요 연관성 대시보드")
st.markdown("""
이 웹앱은 서울과 양평의 기온 데이터를 통해 **도시 열섬현상**을 분석하고, 
더 나아가 **서울의 기온 변화가 전력수요에 미치는 영향**을 시각적으로 살펴봅니다.
""")

# 안전하게 CSV 파일을 읽고 상단 주석을 제거하는 헬퍼 함수
def read_csv_with_encoding(path):
    for enc in ["utf-8-sig", "cp949", "utf-8", "euc-kr"]:
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

# 데이터 불러오기 함수
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    seoul_path = os.path.join(current_dir, "seoul.csv")
    yang_path = os.path.join(current_dir, "yang.csv")
    power_path = os.path.join(current_dir, "power.csv")
    
    seoul_df = read_csv_with_encoding(seoul_path)
    yang_df = read_csv_with_encoding(yang_path)
    power_df = read_csv_with_encoding(power_path)
    
    # 컬럼 매칭
    seoul_time_col = [c for c in seoul_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in seoul_df.columns) else seoul_df.columns[0]
    seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0] if any('기온' in c for c in seoul_df.columns) else seoul_df.columns[-1]
    
    yp_time_col = [c for c in yang_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in yang_df.columns) else yang_df.columns[0]
    yp_temp_col = [c for c in yang_df.columns if '기온' in c][0] if any('기온' in c for c in yang_df.columns) else yang_df.columns[-1]
    
    power_time_col = [c for c in power_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in power_df.columns) else power_df.columns[0]
    power_val_col = [c for c in power_df.columns if '전력' in c][0] if any('전력' in c for c in power_df.columns) else power_df.columns[-1]
    
    # [핵심 보완] 포맷 변환 오류를 막기 위해 errors='coerce'를 주고 정각 단위('h')로 똑같이 맞춤
    seoul_df['일시_dt'] = pd.to_datetime(seoul_df[seoul_time_col], errors='coerce').dt.round('h')
    yang_df['일시_dt'] = pd.to_datetime(yang_df[yp_time_col], errors='coerce').dt.round('h')
    power_df['일시_dt'] = pd.to_datetime(power_df[power_time_col], errors='coerce').dt.round('h')
    
    # 변환 실패(NaT) 데이터 제거
    seoul_df = seoul_df.dropna(subset=['일시_dt'])
    yang_df = yang_df.dropna(subset=['일시_dt'])
    power_df = power_df.dropna(subset=['일시_dt'])
    
    # 필요한 컬럼 정제
    seoul_df = seoul_df[['일시_dt', seoul_temp_col]].rename(columns={'일시_dt': '일시', seoul_temp_col: '서울 기온'})
    yang_df = yang_df[['일시_dt', yp_temp_col]].rename(columns={'일시_dt': '일시', yp_temp_col: '양평 기온'})
    power_df = power_df[['일시_dt', power_val_col]].rename(columns={'일시_dt': '일시', power_val_col: '전력수요(MWh)'})
    
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
        
        weather_merged = pd.merge(seoul_df, yang_df, on='일시', how='inner')
        
        if len(weather_merged) == 0:
            st.warning("⚠️ 날짜 형식이 여전히 매칭되지 않습니다. 데이터 샘플을 화면에 임시로 출력합니다.")
            st.write("서울 데이터 샘플:", seoul_df.head(2))
            st.write("양평 데이터 샘플:", yang_df.head(2))
        else:
            weather_merged['기온차(서울-양평)'] = weather_merged['서울 기온'] - weather_merged['양평 기온']
            weather_merged['시각'] = weather_merged['일시'].dt.hour
            weather_merged['월'] = weather_merged['일시'].dt.month
            
            st.subheader("① 1년간 두 지역 기온 변화")
            line_data = weather_merged.set_index('일시')[['서울 기온', '양평 기온']]
            st.line_chart(line_data)
            
            st.subheader("② 시각(0~23시)별 평균 기온차 (서울 - 양평)")
            hourly_diff = weather_merged.groupby('시각')['기온차(서울-양평)'].mean()
            st.bar_chart(hourly_diff)
            
            st.subheader("③ 월(1~12월)별 평균 기온차 (서울 - 양평)")
            monthly_diff = weather_merged.groupby('월')['기온차(서울-양평)'].mean()
            st.bar_chart(monthly_diff)

    # =========================================================================
    # [탭2: 전력 연결]
    # =========================================================================
    with tab2:
        st.header("서울 기온과 전력수요의 연관성 분석")
        
        power_merged = pd.merge(seoul_df, power_df, on='일시', how='inner')
        
        if len(power_merged) == 0:
            st.error("⚠️ 서울 기온과 전력 데이터의 시간 포맷이 결합되지 않았습니다.")
            st.write("전력 데이터 샘플:", power_df.head(2))
        else:
            power_merged['월'] = power_merged['일시'].dt.month
            
            st.subheader("① 기온별 전력수요 분포 (산점도)")
            st.scatter_chart(data=power_merged, x='서울 기온', y='전력수요(MWh)')
            
            st.subheader("② 기온 구간별 평균 전력수요")
            power_merged['기온 구간'] = (power_merged['서울 기온'] // 5) * 5
            temp_bin_power = power_merged.groupby('기온 구간')['전력수요(MWh)'].mean()
            st.bar_chart(temp_bin_power)
            
            st.subheader("③ 월(1~12월)별 평균 전력수요")
            monthly_power = power_merged.groupby('월')['전력수요(MWh)'].mean()
            st.bar_chart(monthly_power)

except Exception as e:
    st.error(f"⚠️ 시스템 오류가 발생했습니다: {e}")
