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
    st.caption('전환 전 메뉴를 저장하세요. 추가 계정은 새로고침 시 목록에서 사라집니다. 비밀번호는 저장하지 않습니다. 계정 전환 시 이전 자동 로그인 쿠키를 해제합니다.')

def navigation(cloud,delete_menu):
    with st.sidebar:
        st.markdown('<div class="brand" style="font-size:28px">MISE</div>',unsafe_allow_html=True)
        st.caption(st.session_state.auth['email'])
        if st.button('홈',key='nav_home',use_container_width=True):
            st.session_state.page='home'
            st.session_state.drawer_tab='menus'
            st.session_state.sidebar_view='메뉴 관리'
        if st.button('관리',key='nav_manage',use_container_width=True):
            st.session_state.sidebar_view='관리'
        section=st.session_state.get('sidebar_view','메뉴 관리')
        if st.button('로그아웃',key='nav_logout',use_container_width=True):
            jar=cloud.cookie_store();cloud.forget(jar)
            clear_workspace()
            st.session_state.pop('auth',None)
            st.session_state.pop('account_bank',None)
            st.session_state['_logged_out']=True
            st.rerun()
        if section=='관리':
            with st.expander('계정 추가 · 전환',expanded=False):
                accounts(cloud)
        st.subheader('메뉴 목록')
        for name in ('cloud_error','delete_notice'):
            if name in st.session_state:st.info(st.session_state.pop(name))
        for mid,m in list(st.session_state.menus.items()):
            c1,c2=st.columns([4,1])
            c1.write(m['name'])
            if c2.button('',icon=':material/edit:',key='edit_'+mid,help='메뉴 수정',use_container_width=True):
                st.session_state.active_menu=mid;st.session_state.page='edit';st.session_state.drawer_open=False;st.rerun()
        with st.expander('메뉴 추가'):
            with st.form('new_menu',clear_on_submit=True):
                name=st.text_input('새 메뉴 이름')
                add=st.form_submit_button('추가')
            if add and name.strip():
                mid=uuid.uuid4().hex
                st.session_state.menus[mid]={'name':name.strip(),'price':8000,'target':30.0,'extra':0,'rows':[]}
                st.session_state.active_menu=mid;st.session_state.page='edit';st.session_state.drawer_open=False;st.rerun()
        if st.session_state.menus:
            with st.expander('메뉴 삭제'):
                st.selectbox('삭제할 메뉴',list(st.session_state.menus),key='active_menu',format_func=lambda k:st.session_state.menus[k]['name'])
                mid=st.session_state.active_menu
                confirmed=st.checkbox('복구할 수 없음을 확인했습니다',key=f'confirm_delete_{mid}')
                st.button('삭제',on_click=delete_menu,disabled=not confirmed)
        st.caption('새 메뉴와 수정 사항은 편집 화면에서 저장해야 합니다.')
