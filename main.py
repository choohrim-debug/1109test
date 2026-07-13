import streamlit as st
import pandas as pd
import os

# 1. 웹앱 페이지 제목 및 소개
st.title("☀️ 서울-양평 기온 분석 및 전력수요 연관성 대시보드")
st.markdown("""
이 웹앱은 서울과 양평의 기온 데이터를 통해 **도시 열섬현상**을 분석하고, 
더 나아가 **서울의 기온 변화가 전력수요(MWh)에 미치는 영향**을 시각적으로 살펴봅니다.
""")

# 데이터 불러오기 함수 (맥 환경 및 인코딩 방어 적용)
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 파일 경로 설정
    seoul_path = os.path.join(current_dir, "seoul.csv")
    yang_path = os.path.join(current_dir, "yang.csv")
    power_path = os.path.join(current_dir, "power.csv")
    
    # 맥(Mac) 환경과 기상청/전력 데이터 특성을 고려하여 utf-8-sig와 cp949 모두 대응하도록 설계
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
    
    # 기온 컬럼 자동 찾기 및 이름 변경
    seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0]
    yp_temp_col = [c for c in yang_df.columns if '기온' in c][0]
    
    # '일시' 컬럼을 datetime 형식으로 변환
    seoul_df['일시'] = pd.to_datetime(seoul_df['일시'])
    yang_df['일시'] = pd.to_datetime(yang_df['일시'])
    power_df['일시'] = pd.to_datetime(power_df['일시'])
    
    # 필요한 컬럼만 추출 및 이름 변경
    seoul_df = seoul_df[['일시', seoul_temp_col]].rename(columns={seoul_temp_col: '서울 기온'})
    yang_df = yang_df[['일시', yp_temp_col]].rename(columns={yp_temp_col: '양평 기온'})
    power_df = power_df[['일시', '전력수요(MWh)']]
    
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
        st.markdown("일반적으로 해가 진 후 야간 시간에 도시의 열 방출이 늦어져 기온차가 벌어집니다.")
        hourly_diff = weather_merged.groupby('시각')['기온차(서울-양평)'].mean()
        st.bar_chart(hourly_diff)
        
        # ③ 월(1~12월)별 평균 기온차 (막대그래프)
        st.subheader("③ 월(1~12월)별 평균 기온차 (서울 - 양평)")
        st.markdown("계절별로 대도시 환경이 주변 지역에 미치는 기온 변화를 확인할 수 있습니다.")
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
        st.markdown("여름철 폭염(고온)과 겨울철 한파(저온) 때 전력수요가 급증하는 V자형 곡선 흐름을 관찰할 수 있습니다.")
        # Streamlit 내장 scatter_chart 사용 (x=가로축, y=세로축 지정)
        st.scatter_chart(data=power_merged, x='서울 기온', y='전력수요(MWh)')
        
        # ② 기온 구간별 평균 전력수요 (막대그래프)
        st.subheader("② 기온 구간별 평균 전력수요")
        # 기온을 5도 단위 구간으로 나눔 (예: -10~-5도, 20~25도 등)
        power_merged['기온 구간'] = (power_merged['서울 기온'] // 5) * 5
        temp_bin_power = power_merged.groupby('기온 구간')['전력수요(MWh)'].mean()
        st.bar_chart(temp_bin_power)
        
        # ③ 월(1~12월)별 평균 전력수요 (막대그래프)
        st.subheader("③ 월(1~12월)별 평균 전력수요")
        st.markdown("냉난방 가동률이 높은 달과 온화한 봄/가을철의 전력 수요 차이를 비교합니다.")
        monthly_power = power_merged.groupby('월')['전력수요(MWh)'].mean()
        st.bar_chart(monthly_power)

except Exception as e:
    st.error(f"⚠️ 데이터를 읽는 과정에서 에러가 발생했습니다: {e}")
    st.info("💡 파일 목록에 `seoul.csv`, `yang.csv`, `power.csv`가 정확한 이름으로 들어가 있는지 다시 한 번 확인해 주세요.")
