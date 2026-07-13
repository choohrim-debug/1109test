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
            # 기상청 주석(Header) 회피를 위해 0줄부터 5줄까지 스킵해보며 정상 데이터 탐색
            for skip in range(6):
                try:
                    df = pd.read_csv(path, encoding=enc, skiprows=skip)
                    df.columns = df.columns.str.strip()
                    # 필수 데이터인 '일시' 혹은 '시간' 관련 컬럼이 헤더에 보이면 성공으로 간주
                    if any(any(k in str(col) for k in ['일시', '일자', '시간', 'date', 'time']) for col in df.columns):
                        return df
                except:
                    continue
            
            # 실패 시 기본으로 읽기
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
    
    # 파일 경로 설정
    seoul_path = os.path.join(current_dir, "seoul.csv")
    yang_path = os.path.join(current_dir, "yang.csv")
    power_path = os.path.join(current_dir, "power.csv")
    
    # 데이터 로드
    seoul_df = read_csv_with_encoding(seoul_path)
    yang_df = read_csv_with_encoding(yang_path)
    power_df = read_csv_with_encoding(power_path)
    
    # --- 서울 컬럼 찾기 ---
    seoul_time_col = [c for c in seoul_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in seoul_df.columns) else seoul_df.columns[0]
    seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0] if any('기온' in c for c in seoul_df.columns) else seoul_df.columns[-1]
    
    # --- 양평 컬럼 찾기 ---
    yp_time_col = [c for c in yang_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in yang_df.columns) else yang_df.columns[0]
    yp_temp_col = [c for c in yang_df.columns if '기온' in c][0] if any('기온' in c for c in yang_df.columns) else yang_df.columns[-1]
    
    # --- 전력 컬럼 찾기 ---
    power_time_col = [c for c in power_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in power_df.columns) else power_df.columns[0]
    power_val_col = [c for c in power_df.columns if '전력' in c][0] if any('전력' in c for c in power_df.columns) else power_df.columns[-1]
    
    # '일시' 컬럼을 datetime 형식으로 변환
    seoul_df['일시'] = pd.to_datetime(seoul_df[seoul_time_col])
    yang_df['일시'] = pd.to_datetime(yang_df[yp_time_col])
    power_df['일시'] = pd.to_datetime(power_df[power_time_col])
    
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
        st.markdown("서울(대도시)과 양평(교외)의 기온 비교를 통해 열섬현상을 확인합니다.")
        
        # 기온 데이터 병합
        weather_merged = pd.merge(seoul_df, yang_df, on='일시', how='inner')
        weather_merged['기온차(서울-양평)'] = weather_merged['서울 기온'] - weather_merged['양평 기온']
        
        # 시간/월 파생변수 생성
        weather_merged['시각'] = weather_merged['일시'].dt.hour
        weather_merged['월'] = weather_merged['일시'].dt.month
        
        # ① 1년간 두 지역 기온 변화 (선그래프)
        st.subheader("① 1년간 두 지역 기온 변화")
        line_data = weather_merged.set_index('일시')[['서울 기온', '양평 기온']]
        st.line_chart(line_data)
        
        # ② 시각(0~23시)별 평균 기온차 (막대그래프)
        st.subheader("② 시각(0~23시)별 평균 기온차 (서울 - 양평)")
        hourly_diff = weather_merged.groupby('시각')['기온차(서울-양평)'].mean()
        st.bar_chart(hourly_diff)
        
        # ③ 월(1~12월)별 평균 기온차 (막대그래프)
        st.subheader("③ 월(1~12월)별 평균 기온차 (서울 - 양평)")
        monthly_diff = weather_merged.groupby('월')['기온차(서울-양평)'].mean()
        st.bar_chart(monthly_diff)

    # =========================================================================
    # [탭2: 전력 연결]
    # =========================================================================
    with tab2:
        st.header("서울 기온과 전력수요의 연관성 분석")
        st.markdown("대도시 서울의 기온 변화가 실제 전력에 어떤 부하를 주는지 분석합니다.")
        
        # 서울 기온과 전력 데이터 병합
        power_merged = pd.merge(seoul_df, power_df, on='일시', how='inner')
        power_merged['월'] = power_merged['일시'].dt.month
        
        # ① 기온(가로)과 전력수요(세로)의 산점도
        st.subheader("① 기온별 전력수요 분포 (산점도)")
        st.scatter_chart(data=power_merged, x='서울 기온', y='전력수요(MWh)')
        
        # ② 기온 구간별 평균 전력수요 (막대그래프)
        st.subheader("② 기온 구간별 평균 전력수요")
        power_merged['기온 구간'] = (power_merged['서울 기온'] // 5) * 5
        temp_bin_power = power_merged.groupby('기온 구간')['전력수요(MWh)'].mean()
        st.bar_chart(temp_bin_power)
        
        # ③ 월(1~12월)별 평균 전력수요 (막대그래프)
        st.subheader("③ 월(1~12월)별 평균 전력수요")
        monthly_power = power_merged.groupby('월')['전력수요(MWh)'].mean()
        st.bar_chart(monthly_power)

except Exception as e:
    st.error(f"⚠️ 에러가 발생했습니다: {e}")
