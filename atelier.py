import time
import json
import base64
import html
import uuid
import streamlit as st

PATHS = {
 'home':'<path d="m3 10 9-7 9 7v11H3Z M9 21v-8h6v8"/>',
 'menus':'<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 8h8M8 12h8M8 16h5"/>',
 'account':'<circle cx="9" cy="8" r="4"/><path d="M2 21v-3a7 7 0 0 1 14 0v3M19 9v8M15 13h8"/>',
 'logout':'<path d="M10 3H3v18h7M9 12h13m-5-5 5 5-5 5"/>',
}
def style():
    css='''<style>
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:#f8f7f4;color:#202020;}
    .block-container{max-width:1260px;padding-top:2rem;}
    h1,h2,h3{font-weight:450!important;letter-spacing:-.045em;color:#202020!important;}
    p,label,input,textarea,[data-testid="stMetricValue"],[data-testid="stMetricLabel"]{color:#202020!important;}
    input,textarea,[data-baseweb="select"]>div{background:#fff!important;color:#202020!important;}
    input::placeholder{color:#747474!important;}
    .brand{font-family:Georgia,serif;font-size:42px;letter-spacing:.14em;border-bottom:1px solid #c9c7c2;padding:0 0 22px;margin-bottom:20px;}
    .brand span{font-family:sans-serif;font-size:10px;letter-spacing:.3em;margin-left:22px;}
    .stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:0!important;background:#faf9f6!important;color:#202020!important;border:1px solid #bcbab5!important;min-height:42px;box-shadow:none!important;}
    .stButton>button:hover{background:#eae8e2!important;border-color:#202020!important;}
    .stButton>button[kind="primary"],.stFormSubmitButton>button{background:#202020!important;color:white!important;}
    .stButton>button[kind="primary"] p,.stFormSubmitButton>button p{color:white!important;}
    [data-testid="stForm"],[data-testid="stMetric"],[data-testid="stExpander"]{border-radius:0!important;box-shadow:none!important;border-color:#d5d2ca!important;}
    [data-testid="stMetric"]{padding:20px;background:#efede7;}
    .auth-hero{border-top:1px solid #202020;border-bottom:1px solid #bcbab5;padding:32px 0;margin-bottom:24px;}
    .auth-hero small{letter-spacing:.2em;color:#555;}
    .auth-hero h2{font-size:36px;line-height:1.5;}
    .st-key-drawer{border-right:1px solid #ccc;padding-right:20px;animation:enter .24s ease-out;}
    @keyframes enter{from{opacity:0;transform:translateX(-18px)}to{opacity:1;transform:translateX(0)}}
    [data-testid="stSidebar"]{background:#efede7;border-right:1px solid #d5d2ca;}
    [data-testid="stSidebar"] .block-container{padding:16px;}
    [data-testid="stSidebar"] .stButton>button{width:100%;text-align:left;}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.6rem;}
    @media(max-width:700px){.brand{font-size:30px}.brand span{display:block;margin:8px 0}.block-container{padding:1rem;}}
    '''
    css+='''
'''
    css+='\n    .st-key-menu_tab button,.st-key-account_tab button{min-height:40px!important;font-size:13px!important;border-radius:2px!important;}\n    [data-testid="stSidebar"] button[kind="primary"]{background:#202020!important;color:#fff!important;}\n    [data-testid="stSidebar"] button[kind="primary"] p{color:#fff!important;}\n    '
    css+='[data-testid="stSidebar"] hr{display:none!important;} [data-testid="stSidebar"] .brand{border-bottom:0!important;} .st-key-nav_manage button{text-align:left!important;}'
    for name,path in PATHS.items():
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#202020" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'
        data=base64.b64encode(svg.encode()).decode()
        css+=f'.st-key-nav_{name} button{{background-image:url("data:image/svg+xml;base64,{data}")!important;background-repeat:no-repeat!important;background-position:12px center!important;background-size:19px!important;padding-left:42px!important;}}'
    css += """
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:#fff!important;}
    h1,h2,h3{font-family:Arial,sans-serif!important;font-weight:850!important;letter-spacing:-.055em!important;}
    .brand{font-family:Arial,sans-serif!important;font-weight:900;font-size:52px;letter-spacing:-.07em;border:0!important;padding-bottom:8px;margin-bottom:8px;}
    .brand span{font-weight:600;letter-spacing:.2em;color:#666;}
    [data-testid="stSidebar"]{background:#f5f5f5!important;border-right:0!important;}
    .stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:28px!important;background:#fff!important;border:1px solid #d6d6d6!important;min-height:46px;transition:background .18s,color .18s;}
    .stButton>button:hover{background:#eee!important;border-color:#aaa!important;}
    .stButton>button[kind="primary"],.stFormSubmitButton>button{background:#111!important;border-color:#111!important;color:#fff!important;}
    .stButton>button[kind="primary"] p,.stFormSubmitButton>button p{color:#fff!important;}
    [data-testid="stMetric"]{background:#f5f5f5!important;border:0!important;padding:24px!important;}
    [data-testid="stMetricValue"]{font-weight:800!important;letter-spacing:-.05em;font-size:38px!important;}
    [data-testid="stForm"]{background:#fafafa;padding:22px;border:0!important;}
    [data-testid="stExpander"]{border:1px solid #e5e5e5!important;background:white;}
    .auth-hero{background:#111;color:white;padding:38px 28px;border:0!important;}
    .auth-hero h2{color:#fff!important;font-size:42px;line-height:1.2;}
    .auth-hero small,.auth-hero p{color:#ddd!important;}
    .st-key-nav_home button,.st-key-nav_manage button,.st-key-nav_logout button{background-color:transparent!important;border:0!important;border-radius:8px!important;justify-content:flex-start;font-weight:700!important;}
    .st-key-nav_home button:hover,.st-key-nav_manage button:hover,.st-key-nav_logout button:hover{background-color:#e8e8e8!important;}
    @media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;}}
    """
    css += """
    [data-testid="stSidebar"] .st-key-nav_home button,
    [data-testid="stSidebar"] .st-key-nav_manage button,
    [data-testid="stSidebar"] .st-key-nav_logout button{
      background-image:none!important;justify-content:flex-start!important;
      padding:14px 20px!important;min-height:54px!important;border-radius:14px!important;
      border:1px solid #e3e3e3!important;background-color:#fff!important;
      box-shadow:0 2px 6px #00000004!important;text-align:left!important;
    }
    [data-testid="stSidebar"] .st-key-nav_home button p,
    [data-testid="stSidebar"] .st-key-nav_manage button p,
    [data-testid="stSidebar"] .st-key-nav_logout button p{
      font-size:14px!important;font-weight:650!important;letter-spacing:-.03em!important;
    }
    [data-testid="stSidebar"] .st-key-nav_home button:hover,
    [data-testid="stSidebar"] .st-key-nav_manage button:hover{
      background-color:#e9e9e9!important;border-color:#bbb!important;
    }
    [data-testid="stSidebar"] .st-key-nav_logout button{
      background-color:#eee!important;border-color:transparent!important;
    }
    [data-testid="stSidebar"] .brand{margin:4px 0 24px!important;font-size:34px!important;}
    """
    css += """
    [data-testid="stSidebar"] [data-testid="stExpander"]{animation:accountReveal .28s ease-out;}
    @keyframes accountReveal{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
    @media(prefers-reduced-motion:reduce){[data-testid="stSidebar"] [data-testid="stExpander"]{animation:none;}}
    """
    css += """
    [data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important;}
    .block-container{max-width:1060px!important;margin-inline:auto!important;}
    """
    css += """
    .st-key-nav_logout button{background:#d92d20!important;color:white!important;border:1px solid #d92d20!important;}
    .st-key-nav_logout button p,.st-key-nav_logout button span{color:white!important;}
    .st-key-nav_logout button:hover{background:#b42318!important;border-color:#b42318!important;}
    """
    css += """
    .brand{font-family: 'Gungsuh','궁서','GungsuhChe','궁서체','Batang','바탕',serif!important;
    font-weight:400!important;font-style:normal!important;letter-spacing:.015em!important;}
    """
    st.markdown(css+'</style>',unsafe_allow_html=True)

def clear_workspace():
    for key in list(st.session_state):
        if key in ('menus','active_menu') or key.startswith(('name_','price_','target_','extra_','ingredients_','confirm_delete_')):
            del st.session_state[key]
    st.session_state.page='home'

def accounts(cloud):
    bank=st.session_state.setdefault('account_bank',{})
    bank[st.session_state.auth['uid']]=dict(st.session_state.auth)
    st.caption('ACCOUNTS / 현재 접속 중 빠른 전환')
    for uid,a in list(bank.items()):
        c1,c2=st.columns([4,1])
        if c1.button(a['email'],key='switch_'+uid,disabled=uid==st.session_state.auth['uid'],use_container_width=True):
            try:
                key,_=cloud.config()
                d=cloud.call('POST','https://securetoken.googleapis.com/v1/token',params={'key':key},data={'grant_type':'refresh_token','refresh_token':a['refresh']})
                updated={'uid':d['user_id'],'token':d['id_token'],'refresh':d['refresh_token'],'expires':time.time()+int(d['expires_in']),'email':a['email']}
                cloud.forget(cloud.cookie_store())
                clear_workspace()
                st.session_state.auth=updated
                st.rerun()
            except cloud.CloudError as e:st.error(str(e))
        if c2.button('제거',key='remove_'+uid,disabled=uid==st.session_state.auth['uid']):
            del bank[uid];st.rerun()
    with st.form('add_account',clear_on_submit=True):
        st.caption('다른 계정으로 로그인하여 추가')
        email=st.text_input('이메일',key='account_email')
        password=st.text_input('비밀번호',type='password',key='account_password')
        submit=st.form_submit_button('계정 추가 및 전환')
    if submit:
        previous=dict(st.session_state.auth)
        try:
            cloud.login(email.strip(),password)
            bank[st.session_state.auth['uid']]=dict(st.session_state.auth)
            cloud.forget(cloud.cookie_store())
            clear_workspace();st.rerun()
        except cloud.CloudError as e:
            st.session_state.auth=previous;st.error(str(e))
    st.caption('자동 저장 완료를 확인한 후 전환하세요. 추가 계정은 새로고침 시 목록에서 사라집니다. 비밀번호는 저장하지 않습니다. 계정 전환 시 이전 자동 로그인 쿠키를 해제합니다.')

def navigation(cloud,delete_menu):
    page=st.session_state.get('page','home')
    if page=='home':
        with st.container():
            for label, page, icon in [('메뉴 관리','menus_hub','restaurant_menu'), ('계정 관리','accounts_hub','person')]:
                if st.button(label,icon=':material/'+icon+':',key='route_'+page,use_container_width=True,
                             type='primary' if st.session_state.get('page','home')==page else 'secondary'):
                    st.session_state.page=page
                    st.rerun()
            if st.button('로그아웃',icon=':material/logout:',key='nav_logout',use_container_width=True):
                cloud.forget(cloud.cookie_store())
                clear_workspace()
                st.session_state.pop('auth',None)
                st.session_state.pop('account_bank',None)
                st.session_state['_logged_out']=True
                st.rerun()
        st.stop()
    parent = 'menus_hub' if page in ('menu_list','menu_add','menu_delete','edit') else 'accounts_hub' if page in ('my_account','account_switch') else 'home'
    if st.button('돌아가기', icon=':material/arrow_back:', key='page_back'):
        st.session_state.page=parent
        st.rerun()
    hubs = {
        'menus_hub': ('메뉴 관리', [('메뉴 목록','menu_list','restaurant_menu'), ('메뉴 추가','menu_add','add'), ('메뉴 삭제','menu_delete','delete')]),
        'accounts_hub': ('계정 관리', [('내 계정','my_account','person'), ('계정 추가·전환','account_switch','switch_account')])
    }
    if page in hubs:
        title, actions = hubs[page]
        st.subheader(title)
        for label, destination, icon in actions:
            if st.button(label, icon=':material/'+icon+':', key='hub_'+destination, use_container_width=True):
                st.session_state.page=destination
                st.rerun()
        st.stop()
    titles={'menu_list':'메뉴 목록','menu_add':'새 메뉴 추가','menu_delete':'메뉴 삭제','my_account':'내 계정','account_switch':'계정 추가·전환'}
    if page in ('save_help','formula_help'):
        st.subheader('저장 안내' if page=='save_help' else '계산식·입력 기준')
        if page=='save_help':
            st.write('Enter 또는 다른 칸 클릭으로 입력을 확정하면 자동 저장됩니다. 저장 완료 메시지를 확인하세요.')
        else:
            st.write('1인분 원가 = 재료별 구매 가격 ÷ 구매량 ÷ (수율/100) × 사용량의 합계. 원가율 = 1인분 원가 ÷ 판매가 × 100. 구매량과 사용량은 같은 단위를 사용하세요. 원가는 식재료비이며 인건비·임대료는 포함하지 않습니다.')
        if st.button('메뉴로 돌아가기'):
            st.session_state.page='edit';st.rerun()
        st.stop()
    if page not in titles:
        return
    st.subheader(titles[page])
    if page=='my_account':
        st.caption(st.session_state.auth['email'])
        with st.form('change_password', clear_on_submit=True):
            old = st.text_input('현재 비밀번호', type='password')
            new = st.text_input('새 비밀번호', type='password')
            confirm = st.text_input('새 비밀번호 확인', type='password')
            submitted = st.form_submit_button('비밀번호 변경')
        if submitted:
            if len(new) < 6 or new != confirm or not old:
                st.error('현재 비밀번호와 일치하는 새 비밀번호 확인을 입력하세요. 새 비밀번호는 6자 이상이어야 합니다.')
            else:
                try:
                    cloud.change_password(old, new)
                    cloud.forget(cloud.cookie_store())
                    st.session_state.account_bank = {}
                    st.success('변경 완료. 이 기기의 로그인 유지를 해제했습니다.')
                except cloud.CloudError as e:
                    st.error(str(e))

    elif page=='account_switch':
        accounts(cloud)
    elif page=='menu_list':
        for name in ('cloud_error','delete_notice'):
            if name in st.session_state:st.info(st.session_state.pop(name))
        for mid,m in list(st.session_state.menus.items()):
            c1,c2=st.columns([4,1])
            if c1.button(m['name'],key='view_'+mid,use_container_width=True):
                st.session_state.active_menu=mid
                st.session_state.page='edit'
                st.rerun()
            cost=0.0
            valid=True
            for row in m.get('rows',[]):
                if not str(row.get('재료명','')).strip():
                    continue
                try:
                    purchase=float(row['구매 가격(원)']);amount=float(row['구매량'])
                    used=float(row['1인분 사용량']);yield_pct=float(row['수율(%)'])
                    if amount<=0 or not 0<yield_pct<=100 or purchase<0 or used<0:
                        raise ValueError()
                    cost+=purchase/amount*used/(yield_pct/100)
                except (KeyError,TypeError,ValueError):
                    valid=False
            price=float(m.get('price',0))
            if valid and price>0:
                with c1:
                    metrics=st.columns(3)
                    metrics[0].metric('원가율',f'{cost/price*100:.2f}%')
                    metrics[1].metric('원가 (1인분 재료비)',f'{cost:,.0f}원')
                    metrics[2].metric('판매가',f'{price:,.0f}원')
            else:
                c1.caption('원가율 계산 불가 · 재료 입력 및 판매가를 확인하세요')
            if c2.button('',icon=':material/edit:',key='edit_'+mid,help='메뉴 수정',use_container_width=True):
                st.session_state.active_menu=mid;st.session_state.page='edit';st.session_state.drawer_open=False;st.rerun()
    elif page=='menu_add':
        with st.form('new_menu',clear_on_submit=True):
            name=st.text_input('새 메뉴 이름')
            add=st.form_submit_button('추가')
        if add and name.strip():
            mid=uuid.uuid4().hex
            st.session_state.menus[mid]={'name':name.strip(),'price':8000,'target':30.0,'extra':0,'rows':[]}
            st.session_state.active_menu=mid;st.session_state.page='edit';st.session_state.drawer_open=False;st.rerun()
    elif page=='menu_delete':
        if st.session_state.menus:
            st.selectbox('삭제할 메뉴',list(st.session_state.menus),key='active_menu',format_func=lambda k:st.session_state.menus[k]['name'])
            mid=st.session_state.active_menu
            confirmed=st.checkbox('복구할 수 없음을 확인했습니다',key=f'confirm_delete_{mid}')
            st.button('삭제',on_click=delete_menu,disabled=not confirmed)
    st.stop()
