import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform
import re
import streamlit as st


# =========================================================
# 한글 폰트 설정
# =========================================================
try:
    if platform.system() == 'Windows':
        font_name = font_manager.FontProperties(
            fname="c:/Windows/Fonts/malgun.ttf"
        ).get_name()
        rc('font', family=font_name)
    else:
        rc('font', family='AppleGothic')
except:
    pass

matplotlib.rcParams['axes.unicode_minus'] = False


# =========================================================
# 국민연금 데이터 클래스
# =========================================================
class pensionData:

    def __init__(self, filepath):

        warnings.simplefilter(
            action='ignore',
            category=pd.errors.DtypeWarning
        )

        self.df = pd.read_csv(
            filepath,
            encoding='cp949'
        )

        self.pattern1 = r'(\([^)]+\))'
        self.pattern2 = r'(\[[^\]]+\])'
        self.pattern3 = r'[^A-Za-z0-9가-힣]'

        self.preprocess()


    # =====================================================
    # 데이터 전처리
    # =====================================================
    def preprocess(self):

        # 사업장업종코드가 비어있는 데이터 제거
        mask = (
            self.df['사업장업종코드']
            .replace({r'^\s*$': pd.NA}, regex=True)
            .isna()
        )

        self.df = self.df.loc[~mask].copy()


        # 사업장업종코드 숫자형 변환
        self.df['사업장업종코드'] = pd.to_numeric(
            self.df['사업장업종코드'],
            errors='coerce'
        )

        self.df = self.df.dropna(
            subset=['사업장업종코드']
        ).copy()

        self.df['사업장업종코드'] = (
            self.df['사업장업종코드']
            .astype('int32')
        )


        # 컬럼명 변경
        self.df.columns = [
            '자료생성년월',
            '사업장명',
            '사업자등록번호',
            '가입상태',
            '우편번호',
            '사업장지번상세주소',
            '주소',
            '고객법정동주소코드',
            '고객행정동주소코드',
            '시도코드',
            '시군구코드',
            '읍면동코드',
            '사업장형태구분코드 1 법인 2 개인',
            '업종코드',
            '업종코드명',
            '적용일자',
            '재등록일자',
            '탈퇴일자',
            '가입자수',
            '금액',
            '신규',
            '상실'
        ]


        # 불필요 컬럼 삭제
        df = self.df.drop(
            [
                '자료생성년월',
                '우편번호',
                '사업장지번상세주소',
                '고객법정동주소코드',
                '고객행정동주소코드',
                '사업장형태구분코드 1 법인 2 개인',
                '적용일자',
                '재등록일자'
            ],
            axis=1
        ).copy()


        # 사업장명 정제
        df['사업장명'] = (
            df['사업장명']
            .fillna('')
            .apply(self.preprocessing)
        )


        # 탈퇴일자 날짜형 변환
        탈퇴일자 = pd.to_datetime(
            df['탈퇴일자'],
            errors='coerce'
        )

        df['탈퇴일자_연도'] = 탈퇴일자.dt.year
        df['탈퇴일자_월'] = 탈퇴일자.dt.month


        # 주소에서 시도 추출
        df['시도'] = (
            df['주소']
            .fillna('')
            .str.split()
            .str[0]
        )


        # 현재 가입중인 회사만 남기기
        df = (
            df.loc[df['가입상태'] == 1]
            .drop(
                ['가입상태', '탈퇴일자'],
                axis=1
            )
            .reset_index(drop=True)
        )


        # 숫자형 변환
        df['가입자수'] = pd.to_numeric(
            df['가입자수'],
            errors='coerce'
        ).fillna(0)

        df['금액'] = pd.to_numeric(
            df['금액'],
            errors='coerce'
        ).fillna(0)

        df['신규'] = pd.to_numeric(
            df['신규'],
            errors='coerce'
        ).fillna(0)

        df['상실'] = pd.to_numeric(
            df['상실'],
            errors='coerce'
        ).fillna(0)


        # 1인당 금액
        df['인당금액'] = np.where(
            df['가입자수'] > 0,
            df['금액'] / df['가입자수'],
            np.nan
        )


        # 월급여 추정
        df['월급여추정'] = (
            df['인당금액'] / 9 * 100
        )


        # 연간급여 추정
        df['연간급여추정'] = (
            df['월급여추정'] * 12
        )


        self.df = df


    # =====================================================
    # 사업장명 정제
    # =====================================================
    def preprocessing(self, x):

        x = str(x)

        x = re.sub(
            self.pattern1,
            '',
            x
        )

        x = re.sub(
            self.pattern2,
            '',
            x
        )

        x = re.sub(
            self.pattern3,
            ' ',
            x
        )

        x = re.sub(
            r' +',
            ' ',
            x
        )

        return x.strip()


    # =====================================================
    # 회사 검색
    # =====================================================
    def find_company(self, company_name):

        result = self.df.loc[
            self.df['사업장명'].str.contains(
                company_name,
                case=False,
                na=False,
                regex=False
            ),
            [
                '사업장명',
                '월급여추정',
                '연간급여추정',
                '업종코드',
                '가입자수'
            ]
        ]

        return result.sort_values(
            '가입자수',
            ascending=False
        )


    # =====================================================
    # 회사 상세 정보
    # =====================================================
    def company_info(self, company_name):

        result = self.df.loc[
            self.df['사업장명'].str.contains(
                company_name,
                case=False,
                na=False,
                regex=False
            )
        ].sort_values(
            '가입자수',
            ascending=False
        )

        if result.empty:
            return None

        return result.iloc[0]


    # =====================================================
    # 전체 데이터 가져오기
    # =====================================================
    def get_data(self):

        return self.df


    # =====================================================
    # 동종 업계 비교
    # =====================================================
    def compare_company(self, company_name):

        company = self.find_company(
            company_name
        )

        if company.empty:
            return None

        code = company['업종코드'].iloc[0]

        df1 = self.df.loc[
            self.df['업종코드'] == code,
            [
                '월급여추정',
                '연간급여추정'
            ]
        ].agg(
            [
                'mean',
                'count',
                'min',
                'max'
            ]
        )

        df1.columns = [
            '업종_월급여추정',
            '업종_연간급여추정'
        ]

        df1 = df1.T

        df1.columns = [
            '평균',
            '개수',
            '최소',
            '최대'
        ]

        df1.loc[
            '업종_월급여추정',
            company_name
        ] = company['월급여추정'].iloc[0]

        df1.loc[
            '업종_연간급여추정',
            company_name
        ] = company['연간급여추정'].iloc[0]

        return df1


# =========================================================
# CSV 파일 주소
# =========================================================
file_path = r'https://www.dropbox.com/scl/fi/q05nabk8r0822dy8q1kew/_-_20251124.csv?rlkey=x3z852i71fwm60kc69rijiwno&st=cxcnw7rz&dl=1'


# =========================================================
# 데이터 불러오기
# =========================================================
@st.cache_resource
def read_pensionData():

    return pensionData(file_path)


data = read_pensionData()


# =========================================================
# Streamlit 화면
# =========================================================
st.title("국민연금 데이터 분석")

st.write(
    "회사명을 검색하면 국민연금 데이터를 기반으로 "
    "추정 급여와 사업장 정보를 확인할 수 있습니다."
)


company_name = st.text_input(
    "회사명을 입력해 주세요",
    placeholder="예: 삼성전자"
)


# =========================================================
# 회사 검색
# =========================================================
if company_name:

    output = data.find_company(
        company_name=company_name
    )


    # =====================================================
    # 검색 결과가 없는 경우
    # =====================================================
    if output.empty:

        st.subheader(
            "검색결과가 없습니다"
        )


    # =====================================================
    # 검색 결과가 있는 경우
    # =====================================================
    else:

        selected = output.iloc[0]


        # 회사명
        st.subheader(
            selected['사업장명']
        )


        # 회사 상세정보
        info = data.company_info(
            company_name=company_name
        )


        st.markdown(
            f"""
            - 주소 : `{info['주소']}`
            - 업종코드명 : `{info['업종코드명']}`
            - 총 근무자 : `{int(info['가입자수']):,}` 명
            - 신규 입사자 : `{int(info['신규']):,}` 명
            - 퇴사자 : `{int(info['상실']):,}` 명
            """
        )


        # =================================================
        # 주요 지표
        # =================================================
        col1, col2, col3 = st.columns(3)


        col1.metric(
            "월급여 추정",
            f"{int(selected['월급여추정']):,} 원"
        )


        col2.metric(
            "연봉 추정",
            f"{int(selected['연간급여추정']):,} 원"
        )


        col3.metric(
            "가입자수",
            f"{int(selected['가입자수']):,} 명"
        )


        # =================================================
        # 검색 결과 전체
        # =================================================
        st.subheader(
            "검색 결과"
        )

        display_output = output.copy()

        display_output['월급여추정'] = (
            display_output['월급여추정']
            .round(0)
        )

        display_output['연간급여추정'] = (
            display_output['연간급여추정']
            .round(0)
        )

        st.dataframe(
            display_output,
            use_container_width=True
        )


        # =================================================
        # 동종업계 비교
        # =================================================
        st.subheader(
            "동종업계 급여 비교"
        )

        comp_output = data.compare_company(
            company_name=company_name
        )


        if comp_output is not None:

            st.dataframe(
                comp_output.round(0),
                use_container_width=True
            )


            # =============================================
            # 업종 평균 VS 회사 비교
            # =============================================
            st.markdown(
                f"### 업종 평균 VS {company_name} 비교"
            )


            # 업종 평균 월급
            average_month = comp_output.loc[
                '업종_월급여추정',
                '평균'
            ]


            # 업종 평균 연봉
            average_year = comp_output.loc[
                '업종_연간급여추정',
                '평균'
            ]


            # 회사 월급
            company_month = info[
                '월급여추정'
            ]


            # 회사 연봉
            company_year = info[
                '연간급여추정'
            ]


            # 업종 평균 대비 %
            if average_month != 0:

                percent_value = (
                    company_month
                    / average_month
                    * 100
                    - 100
                )

            else:

                percent_value = 0


            # 월급 차이
            diff_month = abs(
                average_month
                - company_month
            )


            # 연봉 차이
            diff_year = abs(
                average_year
                - company_year
            )


            # 높은지 낮은지
            if percent_value > 0:

                upordown = '높은'

            elif percent_value < 0:

                upordown = '낮은'

            else:

                upordown = '같은'


            st.markdown(
                f"""
                - 업종 **평균 월급여**는 `{int(average_month):,}` 원,
                  **평균 연봉**은 `{int(average_year):,}` 원 입니다.

                - `{company_name}`의 월급여 추정액은
                  업종 평균보다 `{int(diff_month):,}` 원,
                  약 `{abs(percent_value):.2f}%` `{upordown}` 수준으로
                  `{int(company_month):,}` 원입니다.

                - `{company_name}`의 연봉 추정액은
                  업종 평균보다 `{int(diff_year):,}` 원 `{upordown}` 수준으로
                  `{int(company_year):,}` 원입니다.
                """
            )


            # =============================================
            # 월급 / 연봉 그래프
            # =============================================
            fig, ax = plt.subplots(
                1,
                2,
                figsize=(10, 4)
            )


            # 월급 그래프
            p1 = ax[0].bar(
                x=[
                    "Average",
                    "Your Company"
                ],
                height=[
                    average_month,
                    company_month
                ],
                width=0.7
            )

            ax[0].bar_label(
                p1,
                fmt='%.0f'
            )

            ax[0].set_title(
                'Monthly Salary'
            )


            # 연봉 그래프
            p2 = ax[1].bar(
                x=[
                    "Average",
                    "Your Company"
                ],
                height=[
                    average_year,
                    company_year
                ],
                width=0.7
            )

            ax[1].bar_label(
                p2,
                fmt='%.0f'
            )

            ax[1].set_title(
                'Yearly Salary'
            )


            ax[0].tick_params(
                axis='both',
                which='major',
                labelsize=8
            )

            ax[1].tick_params(
                axis='both',
                which='major',
                labelsize=8
            )


            plt.tight_layout()

            st.pyplot(fig)

            plt.close(fig)


            # =============================================
            # 동종업계 TOP 10
            # =============================================
            st.markdown(
                '### 동종업계'
            )

            df = data.get_data()


            same_industry = df.loc[
                df['업종코드'] == info['업종코드'],
                [
                    '사업장명',
                    '월급여추정',
                    '연간급여추정',
                    '가입자수'
                ]
            ]


            same_industry = (
                same_industry
                .sort_values(
                    '연간급여추정',
                    ascending=False
                )
                .head(10)
                .round(0)
            )


            st.dataframe(
                same_industry,
                use_container_width=True
            )
        










