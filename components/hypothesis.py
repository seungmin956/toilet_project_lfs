# components/hypothesis.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

def page_function():
    # 전역 변수 사용
    global merged_df1
    
def page4_hypothesis_testing():
    """4페이지: 통계적 검증 (가설검정)"""
    
    st.info("🧪 여성 화장실 구조적 불평등에 대한 통계적 가설검정을 수행합니다.")
    
    # 사이드바에서 선택된 값들 가져오기
    selected_regions = st.session_state.get('selected_regions', [])
    
    # 데이터 필터링
    if selected_regions:
        filtered_data = merged_df1[merged_df1['행정동_동'].isin(selected_regions)]
        region_text = f" ({len(selected_regions)}개 선택 지역)"
    else:
        filtered_data = merged_df1
        region_text = " (전체 지역)"
    
    # 성별 분석 데이터 계산
    @st.cache_data
    def calculate_gender_analysis(data):
        """성별 분석 데이터 계산"""
        
        if data.empty:
            return pd.DataFrame(), {}, {}
        
        gender_analysis = data.groupby('행정동_동').agg({
            '남성인구수': 'mean',
            '여성인구수': 'mean',
            '남성_총칸수': 'sum',
            '여성_총칸수': 'sum',
            '총인구수': 'mean'
        }).reset_index()
        
        # 성별 비율 계산
        gender_analysis['남성_인구비율'] = gender_analysis['남성인구수'] / (
            gender_analysis['남성인구수'] + gender_analysis['여성인구수'])
        gender_analysis['여성_인구비율'] = gender_analysis['여성인구수'] / (
            gender_analysis['남성인구수'] + gender_analysis['여성인구수'])
        
        gender_analysis['남성_화장실비율'] = gender_analysis['남성_총칸수'] / (
            gender_analysis['남성_총칸수'] + gender_analysis['여성_총칸수'])
        gender_analysis['여성_화장실비율'] = gender_analysis['여성_총칸수'] / (
            gender_analysis['남성_총칸수'] + gender_analysis['여성_총칸수'])
        
        # 0으로 나누기 방지
        valid_mask = (gender_analysis['남성_총칸수'] + gender_analysis['여성_총칸수'] > 0) & \
                     (gender_analysis['남성인구수'] + gender_analysis['여성인구수'] > 0)
        
        # 균형 지수 계산
        gender_analysis.loc[valid_mask, '남성_균형지수'] = (
            gender_analysis.loc[valid_mask, '남성_화장실비율'] / 
            gender_analysis.loc[valid_mask, '남성_인구비율']
        )
        
        gender_analysis.loc[valid_mask, '여성_균형지수'] = (
            gender_analysis.loc[valid_mask, '여성_화장실비율'] / 
            gender_analysis.loc[valid_mask, '여성_인구비율']
        )
        
        # 전체 통계
        total_stats = {
            'total_male': data['남성인구수'].sum(),
            'total_female': data['여성인구수'].sum(),
            'total_male_toilets': data['남성_총칸수'].sum(),
            'total_female_toilets': data['여성_총칸수'].sum()
        }
        
        total_population = total_stats['total_male'] + total_stats['total_female']
        total_toilets = total_stats['total_male_toilets'] + total_stats['total_female_toilets']
        
        ratios = {
            'female_pop_ratio': total_stats['total_female'] / total_population,
            'male_pop_ratio': total_stats['total_male'] / total_population,
            'female_toilet_ratio': total_stats['total_female_toilets'] / total_toilets,
            'male_toilet_ratio': total_stats['total_male_toilets'] / total_toilets
        }
        
        return gender_analysis, total_stats, ratios
    
    # 데이터 계산
    gender_data, total_stats, ratios = calculate_gender_analysis(filtered_data)
    
    if gender_data.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        return
    
    # 균형지수 데이터 추출 (무한값과 결측값 제거)
    female_balance_scores = gender_data['여성_균형지수'].dropna()
    female_balance_scores = female_balance_scores[np.isfinite(female_balance_scores)]
    
    male_balance_scores = gender_data['남성_균형지수'].dropna()
    male_balance_scores = male_balance_scores[np.isfinite(male_balance_scores)]
    
    if len(female_balance_scores) == 0 or len(male_balance_scores) == 0:
        st.error("유효한 균형지수 데이터가 없습니다. 데이터를 확인해주세요.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "👩 여성 인구 비율",
            f"{ratios['female_pop_ratio']:.1%}",
            "기준점"
        )
    
    with col2:
        st.metric(
            "🚽 여성 화장실 비율", 
            f"{ratios['female_toilet_ratio']:.1%}",
            f"{ratios['female_toilet_ratio'] - ratios['female_pop_ratio']:+.1%}"
        )
    
    with col3:
        disadvantaged_ratio = (female_balance_scores < 1).sum() / len(female_balance_scores)
        st.metric(
            "🚨 여성 불이익 지역",
            f"{disadvantaged_ratio:.1%}",
            f"{(female_balance_scores < 1).sum()}개 지역"
        )

    
    # 효과 크기 계산 함수
    def cohens_d(x, y=None, mu=None):
        if y is not None:
            nx, ny = len(x), len(y)
            dof = nx + ny - 2
            pooled_std = np.sqrt(((nx-1)*x.std(ddof=1)**2 + (ny-1)*y.std(ddof=1)**2) / dof)
            return (x.mean() - y.mean()) / pooled_std
        elif mu is not None:
            return (x.mean() - mu) / x.std(ddof=1)
    
    def interpret_effect_size(d):
        abs_d = abs(d)
        if abs_d < 0.2:
            return "작은 효과"
        elif abs_d < 0.5:
            return "중간 효과"
        elif abs_d < 0.8:
            return "큰 효과"
        else:
            return "매우 큰 효과"
    
    # 검정 1: 일표본 t-검정
    t_stat_1, p_value_1 = stats.ttest_1samp(female_balance_scores, 1.0)
    effect_size_1 = cohens_d(female_balance_scores, mu=1.0)
    confidence_interval = stats.t.interval(0.95, len(female_balance_scores)-1, 
                                          loc=female_balance_scores.mean(), 
                                          scale=stats.sem(female_balance_scores))
    
    # 검정 2: 대응표본 t-검정
    paired_data = gender_data[['남성_균형지수', '여성_균형지수']].dropna()
    male_paired = paired_data['남성_균형지수']
    female_paired = paired_data['여성_균형지수']
    balance_diff = male_paired - female_paired
    t_stat_2, p_value_2 = stats.ttest_rel(male_paired, female_paired)
    effect_size_2 = cohens_d(male_paired, female_paired)
    
    # 검정 3: 이항검정
    female_disadvantaged = (female_balance_scores < 1).sum()
    total_regions = len(female_balance_scores)
    proportion = female_disadvantaged / total_regions
    binom_result = stats.binomtest(female_disadvantaged, total_regions, 0.5, alternative='greater')
    
    # 검정 4: 카이제곱 검정
    observed_female = total_stats['total_female_toilets']
    observed_male = total_stats['total_male_toilets']
    total_toilets = observed_female + observed_male
    expected_female = total_toilets * ratios['female_pop_ratio']
    expected_male = total_toilets * ratios['male_pop_ratio']
    chi2_stat, p_value_4 = stats.chisquare([observed_female, observed_male], 
                                           [expected_female, expected_male])
    
    # 검정 결과 카드들
    st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; margin: 10px 0;">
            <h4>🧪 검정 1: 여성 균형지수 vs 완벽한 균형</h4>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**가설**")
        st.write("• H₀: 여성 균형지수 평균 = 1 (완벽한 균형)")
        st.write("• H₁: 여성 균형지수 평균 ≠ 1 (불균형 존재)")

        if p_value_1 < 0.05:
            st.success(f"✅ **결과**: 귀무가설 기각 → 여성 화장실에 구조적 불균형 존재! (p-value:{p_value_1:.2e})")
        else:
            st.warning(f"❌ **결과**: 귀무가설 채택 → 구조적 불균형 증거 부족 (p-value:{p_value_1:.2e})")
        
        # st.write(f"**95% 신뢰구간**: ({confidence_interval[0]:.3f}, {confidence_interval[1]:.3f})")
        
    with col2:
        fig1 = go.Figure()
        fig1.add_trace(go.Histogram(
            x=female_balance_scores,
            nbinsx=30,
            name='여성 균형지수',
            marker_color='pink',
            opacity=0.7
        ))
        fig1.add_vline(x=1, line_dash="dash", line_color="red", 
                      annotation_text="완벽한 균형 (1.0)")
        fig1.add_vline(x=female_balance_scores.mean(), line_color="darkred",
                      annotation_text=f"실제 평균 ({female_balance_scores.mean():.3f})")
        fig1.update_layout(
            title=f'여성 균형지수 분포 (n={len(female_balance_scores)})',
            xaxis_title='균형지수',
            yaxis_title='지역 수'
        )
        st.plotly_chart(fig1, use_container_width=True)


    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin: 10px 0;">
        <h4>🧪 검정 2: 여성 불이익 지역 비율</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:     
        st.write("**가설**")
        st.write("• H₀: P(여성 균형지수 < 1) = 0.5 (무작위)")
        st.write("• H₁: P(여성 균형지수 < 1) > 0.5 (체계적 불이익)")
        
        if binom_result.pvalue < 0.05:
            st.success(f"✅ **결과**: 귀무가설 기각 → 여성에게 체계적 불이익 존재! (p-value:{p_value_2:.2e})")
        else:
            st.warning(f"❌ **결과**: 귀무가설 채택 → 체계적 불이익 증거 부족 (p-value:{p_value_2:.2e})")
    
    with col2:
        fig3 = go.Figure(data=[go.Pie(
            labels=[f'불이익 지역\n({female_disadvantaged}개)', 
                   f'균형/유리 지역\n({total_regions - female_disadvantaged}개)'],
            values=[female_disadvantaged, total_regions - female_disadvantaged],
            marker_colors=['lightcoral', 'lightgreen']
        )])
        fig3.update_layout(title='여성 화장실 수급 현황')
        st.plotly_chart(fig3, use_container_width=True)

    # 검정3
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107; margin: 10px 0;">
        <h4>🧪 검정 3: 인구 vs 화장실 비율</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.write("**가설**")
        st.write("• H₀: 화장실 성별 비율 = 인구 성별 비율")
        st.write("• H₁: 화장실 성별 비율 ≠ 인구 성별 비율")
        
        if p_value_4 < 0.05:
            st.success(f"✅ **결과**: 귀무가설 기각 → 화장실 배분에 구조적 불평등 존재! (p-value:{p_value_4:.2e})")
        else:
            st.warning(f"❌ **결과**: 귀무가설 채택 → 구조적 불평등 증거 부족 (p-value:{p_value_4:.2e})")

    # 시각화 섹션
    with col2:
        categories = ['인구 비율', '화장실 비율']
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            name='남성',
            x=categories,
            y=[ratios['male_pop_ratio']*100, ratios['male_toilet_ratio']*100],
            marker_color='lightblue'
        ))
        fig4.add_trace(go.Bar(
            name='여성',
            x=categories,
            y=[ratios['female_pop_ratio']*100, ratios['female_toilet_ratio']*100],
            marker_color='pink'
        ))
        fig4.update_layout(
            title='인구 vs 화장실 성별 비율',
            yaxis_title='비율 (%)',
            barmode='group'
        )
        st.plotly_chart(fig4, use_container_width=True)

    
    # 최종 결론 박스
    p_values = [p_value_1, p_value_2, binom_result.pvalue, p_value_4]
    significant_tests = sum(1 for p in p_values if p < 0.05)
    
    with st.container():
        st.markdown("""
        <style>
        .conclusion-box {
            background-color: #e8f4fd;
            padding: 25px;
            border-radius: 15px;
            border-left: 6px solid #007bff;
            margin: 20px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if significant_tests >= 3:
            conclusion_color = "#d4edda"
            conclusion_border = "#28a745"
            conclusion_text = "🎯 최종 결론: 여성 화장실 구조적 불평등이 통계적으로 강력히 입증되었습니다!"
            evidence_text = f"📊 통계적 근거: 3개 검정 중 {significant_tests}개에서 유의한 결과 도출 (p < 0.05)"
        elif significant_tests >= 2:
            conclusion_color = "#fff3cd"
            conclusion_border = "#ffc107"
            conclusion_text = "⚖️ 최종 결론: 여성 화장실 구조적 불평등의 상당한 증거가 존재합니다."
            evidence_text = f"📊 통계적 근거: 3개 검정 중 {significant_tests}개에서 유의한 결과"
        else:
            conclusion_color = "#f8d7da"
            conclusion_border = "#dc3545"
            conclusion_text = "❓ 최종 결론: 구조적 불평등의 통계적 증거가 부족합니다."
            evidence_text = f"📊 통계적 근거: 3개 검정 중 {significant_tests}개에서만 유의한 결과"
        
        st.markdown(f"""
        <div style="background-color: {conclusion_color}; padding: 25px; border-radius: 15px; border-left: 6px solid {conclusion_border}; margin: 20px 0;">
            <h3>{conclusion_text}</h3>
            <p><strong>{evidence_text}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # 정책 제안
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💪 실무적 함의**")
            shortage_percentage = (ratios['female_pop_ratio'] - ratios['female_toilet_ratio']) / ratios['female_toilet_ratio'] * 100
            st.write(f"• 여성 화장실 {shortage_percentage:.1f}% 추가 확충 필요")
            st.write(f"• 현재 {observed_female:,}칸 → 목표 {expected_female:,.0f}칸")
            st.write(f"• 부족량: {expected_female - observed_female:,.0f}칸")
            
            extreme_disadvantage = (female_balance_scores < 0.5).sum()
            st.write(f"• 극단적 불균형 지역: {extreme_disadvantage}개")
        
        with col2:
            st.markdown("**🏛️ 정책 우선순위**")
            worst_regions = gender_data.nsmallest(3, '여성_균형지수')['행정동_동'].tolist()
            if worst_regions:
                st.write(f"• 최우선 개선 지역: {', '.join(worst_regions)}")
            st.write("• 성별 비율 재조정 필요")
            st.write("• 정기적 모니터링 체계 구축")
            st.write(f"• 검정력: 매우 높음 (표본 크기 {len(female_balance_scores)}개)")