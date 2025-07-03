#components/desert.py

import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
    try:
        url = 'https://github.com/seungmin956/toilet_project_lfs/raw/master/data/data.csv'
        df = pd.read_csv(url, encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {str(e)}")
        return pd.DataFrame()

merged_df1 = load_data()
    
def page2_desert_analysis():
    """2페이지: 화장실 사막 지역 발굴 분석"""
    
    st.info("🗺️ 지역별 화장실 수급 현황 및 사막 지역을 분석합니다.")
    
    # 사이드바에서 선택된 값들 가져오기
    selected_regions = st.session_state.get('selected_regions', [])
    
    # 데이터 필터링
    if selected_regions:
        filtered_data = merged_df1[merged_df1['행정동_동'].isin(selected_regions)]
        region_text = f" ({len(selected_regions)}개 선택 지역)"
    else:
        filtered_data = merged_df1
        region_text = " (전체 지역)"
    
    # 지역별 집계 계산
    @st.cache_data
    def calculate_region_summary(data):
        """지역별 요약 통계 계산"""
        
        if data.empty:
            return pd.DataFrame()
        
        region_summary = data.groupby('행정동_동').agg({
            '총인구수': 'mean',        # 평균 인구수 (시간대별 평균)
            '남성인구수': 'mean',
            '여성인구수': 'mean', 
            '전체_총칸수': 'sum',      # 총 화장실 칸수
            '남성_총칸수': 'sum',
            '여성_총칸수': 'sum',
            '번호': 'count',           # 화장실 개수
            '화장실명': 'nunique'      # 고유 화장실 수
        }).reset_index()
        
        # 핵심 지표들 계산
        region_summary['평균인구수'] = region_summary['총인구수'].round(0)
        region_summary['화장실_수급비율'] = (region_summary['전체_총칸수'] / region_summary['총인구수'] * 1000).round(3)
        region_summary['화장실당_인구수'] = (region_summary['총인구수'] / region_summary['번호'].replace(0, 1)).round(0)
        region_summary['인구밀도당_화장실수'] = (region_summary['화장실명'] / (region_summary['총인구수'] / 1000)).round(3)
        
        # 성별 지표
        region_summary['남성_화장실_수급'] = (region_summary['남성_총칸수'] / region_summary['남성인구수'] * 1000).round(3)
        region_summary['여성_화장실_수급'] = (region_summary['여성_총칸수'] / region_summary['여성인구수'] * 1000).round(3)
        region_summary['성별_수급_격차'] = (region_summary['남성_화장실_수급'] - region_summary['여성_화장실_수급']).round(3)
        
        # 인구 규모 분류
        def classify_population(pop):
            if pop >= 50000:
                return "대규모 (5만+)"
            elif pop >= 30000:
                return "중규모 (3-5만)"
            elif pop >= 15000:
                return "소규모 (1.5-3만)"
            else:
                return "소형 (1.5만 미만)"
        
        region_summary['인구규모'] = region_summary['총인구수'].apply(classify_population)
        
        # 복합 위기 지수 계산
        region_summary['위기지수'] = (
            (1 / (region_summary['화장실_수급비율'] + 0.001)) * 0.4 +  # 수급 비율 (가중치 40%)
            (region_summary['화장실당_인구수'] / 1000) * 0.3 +  # 부담도 (가중치 30%)
            (region_summary['성별_수급_격차'].abs()) * 0.3      # 성별 격차 (가중치 30%)
        ).round(3)
        
        return region_summary
    
    # 데이터 계산
    region_data = calculate_region_summary(filtered_data)
    
    if region_data.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        return
    
    # 상단 지표 카드들
    # st.subheader(f"📊 핵심 지표{region_text}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        worst_region = region_data.loc[region_data['화장실_수급비율'].idxmin()]
        st.metric(
            "🏜️ 최악 사막 지역",
            worst_region['행정동_동'],
            f"{worst_region['화장실_수급비율']:.3f}칸/1000명"
        )
    
    with col2:
        best_region = region_data.loc[region_data['화장실_수급비율'].idxmax()]
        st.metric(
            "🏞️ 최고 오아시스",
            best_region['행정동_동'],
            f"{best_region['화장실_수급비율']:.3f}칸/1000명"
        )

    with col3:
        avg_supply = region_data['화장실_수급비율'].mean()
        supply_gap = region_data['화장실_수급비율'].max() - region_data['화장실_수급비율'].min()
        st.metric(
            "📊 평균 수급 비율",
            f"{avg_supply:.3f}",
            f"격차: {supply_gap:.3f}"
        )


    # 전체 요약 박스
    st.markdown(f"""
    <div class="insight-container">
        <h4>📈 분석 요약</h4>
        <p><strong>분석 대상:</strong> {len(region_data)}개 행정동</p>
        <p><strong>평균 수급 비율:</strong> {region_data['화장실_수급비율'].mean():.3f}칸/1000명</p>
        <p><strong>수급 격차:</strong> {region_data['화장실_수급비율'].max() - region_data['화장실_수급비율'].min():.3f}</p>
        <p><strong>정책 제안:</strong> 화장실 사막 지역 우선 개선 및 성별 균형 화장실 확충이 필요합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    
    # 메인 콘텐츠 영역
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # 인구 vs 수급 비율 산점도
        # st.subheader("🔍 인구 규모와 화장실 수급 관계")
        
        fig_scatter = px.scatter(
            region_data,
            x='총인구수',
            y='화장실_수급비율',
            color='인구규모',
            size='화장실명',
            hover_data=['행정동_동', '화장실당_인구수'],
            title='인구 규모 vs 화장실 수급 비율',
            labels={'총인구수': '평균 인구수', '화장실_수급비율': '화장실 수급 비율'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 성별 수급 비교 산점도
    
    with col_right:
        fig_gender = px.scatter(
        region_data,
        x='남성_화장실_수급',
        y='여성_화장실_수급',
        hover_data=['행정동_동', '성별_수급_격차'],
        title='성별 화장실 수급 비교',
        labels={'남성_화장실_수급': '남성 수급 비율', '여성_화장실_수급': '여성 수급 비율'}
        )
        # 균형선 추가
        max_val = max(region_data['남성_화장실_수급'].max(), region_data['여성_화장실_수급'].max())
        fig_gender.add_shape(
            type="line", x0=0, y0=0, x1=max_val, y1=max_val,
            line=dict(color="red", width=2, dash="dash")
        )
        fig_gender.add_annotation(x=max_val*0.7, y=max_val*0.8, text="균형선", showarrow=False)
        st.plotly_chart(fig_gender, use_container_width=True)
    
    # 인구 규모별 분석 섹션
    st.subheader("👥 인구 규모별 화장실 수급 분석")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 인구 규모별 박스플롯
        fig_box = px.box(
            region_data,
            x='인구규모',
            y='화장실_수급비율',
            title='인구 규모별 화장실 수급 분포',
            labels={'인구규모': '인구 규모', '화장실_수급비율': '화장실 수급 비율'}
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    with col2:
        # 인구 규모별 통계표
        # pop_stats = region_data.groupby('인구규모').agg({
        #     '화장실_수급비율': ['mean', 'min', 'max', 'count'],
        #     '위기지수': 'mean'
        # }).round(3)
        
        # # 컬럼 이름 정리
        # pop_stats.columns = ['평균_수급', '최소_수급', '최대_수급', '지역수', '평균_위기지수']
        # pop_stats = pop_stats.reset_index()
        
        # st.write("**인구 규모별 통계**")
        # st.dataframe(pop_stats, use_container_width=True, hide_index=True)
        
        # 대규모 지역 중 사막 지역
        large_regions = region_data[region_data['인구규모'] == "대규모 (5만+)"]
        if not large_regions.empty:
            st.write("**대규모 지역 중 화장실 사막 TOP 5**")
            large_desert = large_regions.nsmallest(5, '화장실_수급비율')
            for idx, row in large_desert.iterrows():
                dong = row['행정동_동']
                ratio = row['화장실_수급비율']
                population = int(row['평균인구수'])
                st.write(f"• {dong}: {ratio:.3f}칸/1000명 (인구 {population:,}명)")
    
    
    # 인사이트 요약 (박스 디자인 적용)
    st.subheader("💡 주요 인사이트")
    
    with st.container():
        # CSS 스타일 적용
        st.markdown("""
        <style>
        .insight-container {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #17a2b8;
            margin: 10px 0;
        }
        .pattern-box {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin-bottom: 15px;
        }
        .suggestion-box {
            background-color: #d1ecf1;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #17a2b8;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 발견된 패턴 박스
            st.markdown('<div class="pattern-box">', unsafe_allow_html=True)
            st.markdown("**🔍 발견된 패턴**")
            
            insights = []
            
            # 사막 지역 분석
            severe_desert = len(region_data[region_data['화장실_수급비율'] < 0.5])
            if severe_desert > 0:
                insights.append(f" {severe_desert}개 지역이 극심한 화장실 사막 상태")
            
            # 인구 규모별 패턴
            large_desert_count = len(region_data[(region_data['인구규모'] == "대규모 (5만+)") & 
                                                (region_data['화장실_수급비율'] < 1.0)])
            if large_desert_count > 0:
                insights.append(f" 대규모 지역 중 {large_desert_count}개가 화장실 부족")
            
            # 성별 격차
            gender_gap_severe = len(region_data[region_data['성별_수급_격차'].abs() > 1.0])
            if gender_gap_severe > 0:
                insights.append(f" {gender_gap_severe}개 지역에서 심각한 성별 격차")
            
            # 위기 지역
            high_crisis = len(region_data[region_data['위기지수'] > region_data['위기지수'].quantile(0.8)])
            insights.append(f" 상위 20% 위기 지역: {high_crisis}개")
            
            if not insights:
                insights.append(" 전반적으로 안정적인 화장실 수급 상태")
            
            for insight in insights:
                st.markdown(f"• {insight}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # 개선 제안 박스
            st.markdown('<div class="suggestion-box">', unsafe_allow_html=True)
            st.markdown("**🎯 개선 제안**")
            
            suggestions = []
            
            # 최우선 개선 지역
            worst_regions = region_data.nsmallest(3, '화장실_수급비율')['행정동_동'].tolist()
            suggestions.append(f" 최우선 개선: {', '.join(worst_regions)}")
            
            # 대규모 지역 우선
            if large_desert_count > 0:
                suggestions.append(" 대규모 지역 화장실 확충 우선")
            
            # 성별 균형 개선
            if gender_gap_severe > 0:
                suggestions.append(" 여성 화장실 비율 증대 필요")
            
            # 인구 규모별 차등 지원
            suggestions.append(" 인구 규모별 차등 화장실 배치 기준 수립")
            
            # 정기 모니터링
            suggestions.append(" 화장실 수급 현황 정기 모니터링 체계 구축")
            
            for suggestion in suggestions:
                st.markdown(f"• {suggestion}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        

    #상세 테이블 표시
    # 표시 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_detail = st.checkbox("상세 데이터 표시", value=False)
    
    with col2:
        sort_by = st.selectbox(
            "정렬 기준",
            options=['화장실_수급비율', '위기지수', '성별_수급_격차', '평균인구수'],
            format_func=lambda x: {
                '화장실_수급비율': '수급 비율',
                '위기지수': '위기 지수',
                '성별_수급_격차': '성별 격차',
                '평균인구수': '인구수'
            }.get(x, x)
        )
    
    with col3:
        ascending = st.checkbox("오름차순 정렬", value=True)
    
    if show_detail:
        # 표시할 컬럼 선택
        display_columns = [
            '행정동_동', '평균인구수', '화장실명', '화장실_수급비율',
            '화장실당_인구수', '성별_수급_격차', '위기지수', '인구규모'
        ]
        
        # 컬럼명 한글화
        column_names = {
            '행정동_동': '지역명',
            '평균인구수': '평균 인구수',
            '화장실명': '화장실 수',
            '화장실_수급비율': '수급 비율',
            '화장실당_인구수': '화장실당 인구',
            '성별_수급_격차': '성별 격차',
            '위기지수': '위기 지수',
            '인구규모': '인구 규모'
        }
        
        sorted_data = region_data.sort_values(sort_by, ascending=ascending)
        display_data = sorted_data[display_columns].rename(columns=column_names)
        
        st.dataframe(display_data, use_container_width=True, hide_index=True)
