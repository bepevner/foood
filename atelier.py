import json
import math
import uuid
import streamlit as st

def style():
    st.markdown('''<style>
    .stApp,[data-testid="stHeader"]{background:#fff;color:#202020}
    .block-container{max-width:1060px;padding-top:2rem;margin:auto}
    .brand{font-family:'Gungsuh','궁서','GungsuhChe','Batang',serif;font-size:46px;margin-bottom:12px}
    h1,h2,h3{color:#202020!important;letter-spacing:-.04em}
    .stButton>button,.stDownloadButton>button{border-radius:24px;min-height:46px}
    [data-testid="stMetric"]{background:#f5f5f5;padding:20px}
    [data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none}
    </style>''', unsafe_allow_html=True)

def go(page):
    st.session_state.page=page
    st.rerun()

def navigation(store, delete_menu):
    page=st.session_state.get('page','home')
    if page != 'home':
        if st.button('돌아가기'):
            go('home')
    if page=='home':
        st.subheader('우리 가게 메뉴')
        a,b,c=st.columns(3)
        if a.button('메뉴 추가',use_container_width=True):go('menu_add')
        if b.button('메뉴 삭제',use_container_width=True):go('menu_delete')
        if c.button('백업·불러오기',use_container_width=True):go('backup')
        for mid,m in st.session_state.menus.items():
            if st.button(m['name'],key='view_'+mid,use_container_width=True):
                st.session_state.active_menu=mid
                go('edit')
            cost=0.;valid=True
            for row in m.get('latest_rows',m.get('rows',[])):
                try:
                    p,q,u,y=[float(row[k]) for k in ('구매 가격(원)','구매량','1인분 사용량','수율(%)')]
                    if not all(math.isfinite(v) for v in (p,q,u,y)) or p<0 or q<=0 or u<0 or not 0<y<=100:raise ValueError()
                    cost+=p/q*u/(y/100)
                except (KeyError,TypeError,ValueError):valid=False
            price=m.get('price',0)
            a,b,c=st.columns(3)
            a.metric('원가율',f'{cost/price*100:.2f}%' if valid and price else '계산 불가')
            b.metric('1인분 재료비',f'{cost:,.0f}원' if valid else '확인 필요')
            c.metric('판매가',f'{price:,.0f}원')
        if not st.session_state.menus:st.info('메뉴 추가를 눌러 첫 메뉴를 등록하세요.')
        st.stop()
    if page=='menu_add':
        with st.form('new_menu'):
            name=st.text_input('새 메뉴 이름')
            submit=st.form_submit_button('추가')
        if submit:
            if not name.strip():st.warning('메뉴 이름을 입력하세요.')
            else:
                mid=uuid.uuid4().hex
                menu={'name':name.strip(),'price':8000,'target':30.0,'extra':0,'rows':[]}
                proposed=dict(st.session_state.menus);proposed[mid]=menu
                try:store.write_all(proposed)
                except store.CloudError as e:st.error(str(e))
                else:
                    st.session_state.menus=proposed
                    st.session_state.active_menu=mid
                    go('edit')
        st.stop()
    if page=='menu_delete':
        if st.session_state.menus:
            mid=st.selectbox('삭제할 메뉴',list(st.session_state.menus),format_func=lambda k:st.session_state.menus[k]['name'])
            st.session_state.active_menu=mid
            confirmed=st.checkbox('삭제하면 복구할 수 없음을 확인했습니다',key=f'confirm_delete_{mid}')
            st.button('삭제',on_click=delete_menu,disabled=not confirmed)
            if 'delete_notice' in st.session_state:st.success(st.session_state.pop('delete_notice'))
        else:st.info('삭제할 메뉴가 없습니다.')
        st.stop()
    if page=='backup':
        st.subheader('백업·불러오기')
        st.warning('메뉴는 실행 중인 서버의 파일에 저장됩니다. Streamlit Cloud에서는 재배포·서버 초기화 시 사라질 수 있으니 백업 파일을 내려받으세요. 로그인 없이 공개한 주소는 누구나 메뉴를 보고 수정할 수 있습니다.')
        payload=json.dumps({k:store.clean_menu(v) for k,v in st.session_state.menus.items()},ensure_ascii=False,indent=2)
        st.download_button('전체 메뉴 백업',payload.encode('utf-8'),'menus_backup.json','application/json')
        upload=st.file_uploader('메뉴 백업 파일',type=['json'])
        confirmed=st.checkbox('현재 메뉴를 백업 파일 내용으로 교체합니다')
        if st.button('불러오기',disabled=not upload or not confirmed):
            try:
                data=json.loads(upload.getvalue())
                if not isinstance(data,dict):raise ValueError('잘못된 백업 형식')
                for mid,m in data.items():
                    if not isinstance(mid,str) or not isinstance(m,dict):raise ValueError('잘못된 메뉴 형식')
                    if not isinstance(m.get('name'),str) or not isinstance(m.get('rows'),list):raise ValueError('이름 또는 재료 형식 오류')
                    for key in ('price','extra'):
                        if not isinstance(m.get(key),int) or m[key]<0:raise ValueError('금액 형식 오류')
                    if not isinstance(m.get('target'),(int,float)) or not 0<m['target']<=100:raise ValueError('목표 원가율 오류')
                    if not all(isinstance(row,dict) for row in m['rows']):raise ValueError('재료 형식 오류')
                store.write_all(data)
            except (ValueError,TypeError,KeyError,store.CloudError) as e:st.error(str(e))
            else:
                for key in list(st.session_state):
                    if key.startswith(('name_','price_','target_','extra_','ingredients_','confirm_delete_')):del st.session_state[key]
                st.session_state.menus=data
                if data:st.session_state.active_menu=next(iter(data))
                go('home')
        st.stop()
    if page in ('save_help','formula_help'):
        if page=='save_help':st.write('입력을 Enter 또는 다른 칸 클릭으로 확정하면 서버 파일에 저장됩니다. Cloud에서는 영구 보관이 보장되지 않으므로 홈의 백업 기능을 이용하세요.')
        else:st.write('재료비 = 구매 가격 ÷ 구매량 ÷ (수율/100) × 사용량. 원가율 = 재료비 합계 ÷ 판매가 × 100. 구매량과 사용량은 같은 단위로 입력하세요.')
        st.stop()
