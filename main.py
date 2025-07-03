# main.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# desert.py import 전에 전역변수로 설정
import builtins
builtins.px = px
builtins.go = go

from components.desert import page2_desert_analysis
from components.time_check import page1_hourly_analysis 
from components.hypothesis import page4_hypothesis_testing

st.set_page_config(page_title="서울시 화장실 수급 현황", page_icon="🚻",layout='wide')

# CSS 스타일
st.markdown("""
<style>
@keyframes glitterSweep {
  0% {background-position: -200% 0;}
  100% {background-position: 200% 0;}
}
            
/* 탭 내부 글자 크기 설정 */
[data-baseweb="tab-list"] button p {
    font-size: 20px !important;
}
            
/* 탭 여백 조절 */
[data-baseweb="tab"] {
    padding: 1rem 2rem !important;
}
            
/* 활성화된 탭 제목 강조 (선택사항) */
[data-baseweb="tab"][aria-selected="true"] p {
    font-size: 24px !important;
    font-weight: bold !important;
}

/* 기본 텍스트 크기 설정 */
html, body, [class*="css"] {
  font-size: 22px !important;
}

/* 제목 태그 (h1 ~ h4) 크기/굵기 설정 */
h1, h2, h3, h4 {a
  font-size: 20px !important;
  font-weight: bold !important;
}

/* 입력/버튼/라디오 글자 크기 설정 */
.stTextInput > div > input,
.stChatInput > div > textarea,
.stButton > button,
.stRadio > div {
  font-size: 14px !important;
}
            
/* st.alert 계열의 스타일을 커스터마이징 */
.stAlert > div {
    background-color: #E5E5E5;  /* 배경색 */
    color: #1F1F1F;  /* 텍스트 색상 */
}            

.main-header {
  text-align: center;
  padding: 2rem 0;
  border-radius: 10px;
  margin-bottom: 2rem;
  background: linear-gradient(60deg,
    transparent 0%,
    rgba(255,255,255,0.3) 20%,
    transparent 40%),
    #764ba2;
  background-size: 200% 100%;
#   animation: glitterSweep 8s linear infinite;
  color: #FFFFFF;
}
.main-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}
            
/* 선택된 탭 스타일 */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    border-bottom: 3px solid #845AC0 !important;
    color: #845AC0 !important;
    font-weight: bold;
}
""", unsafe_allow_html=True)

# 헤더 표시
st.markdown("""
<div class="main-header">
    <div class="main-title">서울시 화장실 수급 현황</div>
</div>
""", unsafe_allow_html=True)


tab1, tab2, tab3= st.tabs(["⏰시간대별 화장실 대란 분석", "화장실 사막 지역 발굴", "통계적 검증(가설검정)"])


@st.cache_data
def load_data():
    """GitHub LFS에서 데이터 로드"""
    try:
        url = 'https://github.com/seungmin956/toilet_project_lfs/raw/master/data/data.csv'
        df = pd.read_csv(url, encoding='utf-8')
        st.success(f"✅ 데이터 로드 성공! 행 수: {len(df):,}개")
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {str(e)}")
        return pd.DataFrame()

# 전역 데이터 로드
merged_df1 = load_data()

with st.sidebar:
    st.subheader("🗺️ 지역 선택")
    
    # 1. 지역 리스트 캐싱
    @st.cache_data
    def get_region_list():
        return sorted(merged_df1['행정동_동'].unique())
    
    region_list = get_region_list()
    
    # 2. 빠른 선택 옵션
    quick_options = st.selectbox(
        "빠른 선택",
        ["직접 선택", "전체 지역", "화장실 사막 TOP 5", "화장실 오아시스 TOP 5"]
    )
    
    if quick_options == "전체 지역":
        default_selection = region_list
    elif quick_options == "화장실 사막 TOP 5":
        # 사막 지역 TOP 10 계산 (실제 데이터 기반)
        default_selection = ["둔촌1동", "난곡동", "이문1동","도림동","구로1동"] 
    elif quick_options== "화장실 오아시스 TOP 5":
        default_selection=["신정6동","신당5동","공릉2동","신월7동","홍은2동"] # 예시
    else:
        default_selection = []
    
    # 3. 멀티셀렉트
    selected_regions = st.multiselect(
        "관심 지역 선택",
        options=region_list,
        default=default_selection,
        help="분석하고 싶은 행정동을 선택하세요"
    )
    
    # 4. 결과 표시
    if selected_regions:
        st.success(f"✅ {len(selected_regions)}개 지역 선택")
    else:
        st.error("❌ 지역을 선택해주세요")


with tab1:
    if 'selected_regions' not in st.session_state:
        st.session_state.selected_regions = []
    if 'use_weights' not in st.session_state:
        st.session_state.use_weights = True
    
    page1_hourly_analysis()

with tab2:
  page2_desert_analysis()


with tab3:
  page4_hypothesis_testing()
