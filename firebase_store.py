import json
import time
from urllib.parse import quote
import requests
import streamlit as st

class CloudError(Exception):
    pass

def config():
    try:
        c = st.secrets['firebase']
        return c['api_key'], c['project_id']
    except Exception:
        raise CloudError('Firebase 설정이 없습니다. 설정안내.md에 따라 Secrets를 등록하세요.') from None

def call(method, url, **kwargs):
    try:
        r = requests.request(method, url, timeout=20, **kwargs)
    except requests.RequestException:
        raise CloudError('네트워크 연결 실패. 입력을 유지한 채 다시 시도하세요.') from None
    if not r.ok:
        raise CloudError(f'Firebase 요청 실패 (HTTP {r.status_code}). 계정 정보, Firestore 규칙, 프로젝트 설정을 확인하세요.')
    return r.json() if r.content else {}

def login(email, password, signup=False):
    key, _ = config()
    action = 'signUp' if signup else 'signInWithPassword'
    d = call('POST', f'https://identitytoolkit.googleapis.com/v1/accounts:{action}',
             params={'key':key}, json={'email':email, 'password':password, 'returnSecureToken':True})
    st.session_state.auth = {'uid':d['localId'], 'token':d['idToken'], 'refresh':d['refreshToken'], 'expires':time.time()+int(d['expiresIn']), 'email':email}

def headers():
    a = st.session_state.auth
    if time.time() > a['expires']-60:
        key, _ = config()
        d = call('POST', 'https://securetoken.googleapis.com/v1/token', params={'key':key},
                 data={'grant_type':'refresh_token', 'refresh_token':a['refresh']})
        a.update(token=d['id_token'], refresh=d['refresh_token'], expires=time.time()+int(d['expires_in']))
    return {'Authorization':'Bearer '+a['token']}

def base():
    _, project = config()
    return f'https://firestore.googleapis.com/v1/projects/{quote(project, safe="")}/databases/(default)/documents/users/{quote(st.session_state.auth["uid"], safe="")}/menus'

def load():
    menus, page = {}, None
    while True:
        params = {'pageSize':100}
        if page: params['pageToken'] = page
        data = call('GET', base(), headers=headers(), params=params)
        for doc in data.get('documents', []):
            menus[doc['name'].rsplit('/',1)[-1]] = json.loads(doc['fields']['payload']['stringValue'])
        page = data.get('nextPageToken')
        if not page: return menus

def save(ident, menu):
    # Persist only the current menu; no whole-account overwrite or cross-user cache.
    clean = {k:menu[k] for k in ('name','price','target','extra')}
    clean['rows'] = menu.get('latest_rows',menu['rows'])
    # Pandas missing values are normalized before Firestore JSON serialization.
    for row in clean['rows']:
        for k,v in list(row.items()):
            if isinstance(v,float) and not __import__('math').isfinite(v): row[k]=None
    text=json.dumps(clean,ensure_ascii=False,allow_nan=False)
    call('PATCH',base()+'/'+quote(ident,safe=''),headers=headers(),json={'fields':{'payload':{'stringValue':text}}})

def delete(ident):
    call('DELETE',base()+'/'+quote(ident,safe=''),headers=headers())

def gate():
    if 'auth' not in st.session_state:
        st.subheader('🔐 로그인 / 회원가입')
        st.caption('같은 계정으로 로그인하면 저장한 메뉴를 다시 불러옵니다.')
        with st.form('login_form',clear_on_submit=True):
            email=st.text_input('이메일')
            password=st.text_input('비밀번호',type='password')
            signup=st.checkbox('새 계정 만들기')
            submit=st.form_submit_button('계속')
        if submit:
            try:
                login(email.strip(),password,signup)
                st.rerun()
            except CloudError as e: st.error(str(e))
        st.stop()
    with st.sidebar:
        st.caption(st.session_state.auth['email'])
        if st.button('로그아웃 (저장하지 않은 변경은 사라짐)'):
            st.session_state.clear()
            st.rerun()
    if 'menus' not in st.session_state:
        try:
            menus=load()
        except (CloudError,ValueError,KeyError) as e:
            st.error(str(e) if isinstance(e,CloudError) else '저장 데이터 형식을 확인할 수 없습니다. 관리자에게 문의하세요.')
            st.button('불러오기 다시 시도')
            st.stop()
        st.session_state.menus=menus
        if menus: st.session_state.active_menu=next(iter(menus))
