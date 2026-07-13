import streamlit as st
import pandas as pd
import os

# 1. 웹앱 페이지 제목 및 소개
st.title("서울-양평 기온 비교를 통한 도시 열섬현상 분석")
st.markdown("""
이 웹앱은 서울(대도시)과 양평(교외 지역)의 기온 데이터를 비교하여 **도시 열섬현상(Urban Heat Island)**을 시각적으로 분석합니다.
""")

# 데이터 불러오기 함수
@st.cache_data
def load_data():
    # 현재 main.py 파일이 있는 폴더 경로를 자동으로 인식
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 변경하신 영문 파일 이름 반영
    seoul_path = os.path.join(current_dir, "seoul.csv")
    yangpyeong_path = os.path.join(current_dir, "yang.csv")
    
    # 가장 표준적인 인코딩(cp949)으로 파일 읽기
    seoul_df = pd.read_csv(seoul_path, encoding="cp949")
    yangpyeong_df = pd.read_csv(yangpyeong_path, encoding="cp949")
    
    # 양 끝의 눈에 안 보이는 공백 제거
    seoul_df.columns = seoul_df.columns.str.strip()
    yangpyeong_df.columns = yangpyeong_df.columns.str.strip()
    
    # 데이터 속에서 '기온'이라는 글자가 포함된 컬럼을 자동으로 매칭
    seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0]
    yp_temp_col = [c for c in yangpyeong_df.columns if '기온' in c][0]
    
    # '일시' 컬럼을 datetime 형식으로 변환 (괄호 완벽 마감)
    seoul_df['일시'] = pd.to_datetime(seoul_df['일시'])
    yangpyeong_df['일시'] = pd.to_datetime(yangpyeong_df['일시'])
    
    # 필요한 컬럼만 추출하고 이름을 구별하기 쉽게 변경
    seoul_df = seoul_df[['일시', seoul_temp_col]].rename(columns={seoul_temp_col: '서울 기온'})
    yangpyeong_df = yangpyeong_df[['일시', yp_temp_col]].rename(columns={yp_temp_col: '양평 기온'})
    
    # '일시' 기준 데이터 병합
    merged_df = pd.merge(seoul_df, yangpyeong_df, on='일시', how='inner')
    
    # 기온차(서울 - 양평) 계산식 컬럼 생성
    merged_df['기온차(서울-양평)'] = merged_df['서울 기온'] - merged_df['양평 기온']
    
    return merged_df

# 메인 실행 로직
try:
    df = load_data()
    
    # 사이드바 정보 구성
    st.sidebar.header("📊 데이터 요약 정보 (2025)")
    st.sidebar.write(f"총 데이터 수: {len(df):,}개")
    st.sidebar.write(f"서울 평균 기온: {df['서울 기온'].mean().round(2)} °C")
    st.sidebar.write(f"양평 평균 기온: {df['양평 기온'].mean().round(2)} °C")
    st.sidebar.write(f"평균 기온차: {df['기온차(서울-양평)'].mean().round(2)} °C")

    # ① 1년간 두 지역의 기온 변화 (선그래프)
    st.header("① 1년간 두 지역의 기온 변화")
    st.markdown("서울과 양평의 1년간 전체 기온 추이를 선그래프로 비교합니다.")
    line_chart_data = df.set_index('일시')[['서울 기온', '양평 기온']]
    st.line_chart(line_chart_data)

    # 시간/월 분석을 위한 파생변수 생성
    df['시각'] = df['일시'].dt.hour
    df['월'] = df['일시'].dt.month

    # ② 시각별 평균 기온차 (막대그래프)
    st.header("② 시각(0~23시)별 평균 기온차 (서울 - 양평)")
    st.markdown("하루 중 어느 시간대에 도시 열섬현상(기온차)이 가장 뚜렷하게 나타나는지 확인합니다.")
    hourly_diff = df.groupby('시각')['기온차(서울-양평)'].mean()
    st.bar_chart(hourly_diff)

    # ③ 월별 평균 기온차 (막대그래프)
    st.header("③ 월(1~12월)별 평균 기온차 (서울 - 양평)")
    st.markdown("계절별(월별)로 도시 열섬현상의 세기가 어떻게 달라지는지 확인합니다.")
    monthly_diff = df.groupby('월')['기온차(서울-양평)'].mean()
    st.bar_chart(monthly_diff)

except Exception as e:
    st.error(f"⚠️ 데이터를 읽는 과정에서 에러가 발생했습니다: {e}")
    st.info("💡 파일 이름이 seoul.csv 와 yang.csv 로 정확히 수정되었는지 다시 한번 확인해 주세요.")
