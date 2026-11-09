import json
import time
import streamlit as st


def theme():
    st.markdown('''<style>
    .stApp {background:#f5f7fb;color:#172539;}
    [data-testid="stSidebar"] {background:#edf3ef;}
    h1,h2,h3 {letter-spacing:-.045em;color:#183b32;}
    [data-testid="stForm"] {background:white;border:1px solid #dce6e1;border-radius:20px;padding:26px;box-shadow:0 12px 35px #153d2910;}
    .stButton>button[kind="primary"], .stFormSubmitButton>button {background:#176b50;color:white;border:0;border-radius:12px;min-height:44px;}
    [data-testid="stMetric"] {background:white;border:1px solid #dce6e1;border-radius:16px;padding:20px;}
    .auth-hero {background:#153e32;border-radius:22px;padding:30px;color:white;margin:10px 0 26px;}
    .auth-hero h2 {color:white;margin:8px 0;}
    .auth-hero p {color:#dcece4;margin-bottom:0;}
    input {border-radius:10px!important;}
    </style>''',unsafe_allow_html=True)


def remember_login(cloud, jar, remember, email):
    if remember:
        jar['session']=json.dumps({'refresh':st.session_state.auth['refresh'],
                                  'email':email,'until':time.time()+7*86400})
        jar.save()
    else:
        cloud.forget(jar)


def screen(cloud, jar):
    _, main, _ = st.columns([1,5,1])
    with main:
        st.markdown('''<div class="auth-hero"><small>MENU COST · 나의 가게 관리실</small>
        <h2>한 접시의 가치를,<br>숫자로 정확하게.</h2>
        <p>재료비 계산부터 메뉴 관리까지 한곳에서 시작하세요.</p></div>''',unsafe_allow_html=True)
        mode=st.radio('계정 메뉴',['로그인','회원가입','비밀번호 찾기','아이디 찾기'],horizontal=True,label_visibility='collapsed')
        if mode=='로그인':
            with st.form('sign_in',clear_on_submit=True):
                st.subheader('다시 만나 반가워요')
                email=st.text_input('이메일 아이디',placeholder='you@example.com')
                password=st.text_input('비밀번호',type='password')
                remember=st.checkbox('이 기기에서 7일 동안 로그인 유지')
                submit=st.form_submit_button('로그인',use_container_width=True)
            if submit:
                if not email.strip() or not password:
                    st.error('이메일과 비밀번호를 입력하세요.')
                else:
                    try:
                        cloud.login(email.strip(),password)
                        remember_login(cloud,jar,remember,email.strip())
                        st.rerun()
                    except cloud.CloudError as e:st.error(str(e))
        elif mode=='회원가입':
            with st.form('sign_up',clear_on_submit=True):
                st.subheader('우리 가게의 첫 시작')
                email=st.text_input('이메일 아이디',placeholder='실제로 사용하는 이메일')
                password=st.text_input('비밀번호',type='password',help='6자 이상. 프로젝트의 비밀번호 정책이 추가로 적용됩니다.')
                repeat=st.text_input('비밀번호 확인',type='password')
                remember=st.checkbox('이 기기에서 7일 동안 로그인 유지')
                st.caption('입력한 이메일이 로그인 아이디입니다. 공용 기기에서는 로그인 유지를 선택하지 마세요.')
                submit=st.form_submit_button('회원가입하고 시작하기',use_container_width=True)
            if submit:
                if '@' not in email.strip() or len(password)<6:
                    st.error('올바른 이메일과 6자 이상의 비밀번호를 입력하세요.')
                elif password!=repeat:st.error('비밀번호 확인이 일치하지 않습니다.')
                else:
                    try:
                        cloud.login(email.strip(),password,signup=True)
                        remember_login(cloud,jar,remember,email.strip())
                        st.rerun()
                    except cloud.CloudError as e:st.error(str(e))
        elif mode=='비밀번호 찾기':
            with st.form('reset_password',clear_on_submit=True):
                st.subheader('비밀번호를 잊으셨나요?')
                st.caption('기존 비밀번호를 보여주는 대신, 이메일로 재설정 링크를 보내드립니다.')
                email=st.text_input('가입한 이메일',placeholder='you@example.com')
                submit=st.form_submit_button('재설정 메일 요청',use_container_width=True)
            if submit:
                if '@' not in email.strip():st.error('올바른 이메일 주소를 입력하세요.')
                else:
                    try:
                        key,_=cloud.config()
                        cloud.call('POST','https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode',
                                   params={'key':key},json={'requestType':'PASSWORD_RESET','email':email.strip()})
                        st.success('해당 이메일이 등록되어 있고 발송 가능한 경우 재설정 메일이 전송됩니다. 받은편지함과 스팸함을 확인하세요.')
                    except cloud.CloudError:
                        st.info('메일을 요청할 수 없습니다. 잠시 후 재시도하거나 Firebase 이메일 인증 설정을 확인하세요. 계정 존재 여부는 안내하지 않습니다.')
        else:
            with st.container(border=True):
                st.subheader('아이디는 가입한 이메일이에요')
                st.write('현재 앱은 별도의 숫자·문자 아이디 없이 이메일로 로그인합니다.')
                st.info('이름이나 전화번호로 이메일을 자동 조회하는 기능은 제공하지 않습니다. 본인 확인 수단이 등록되어 있지 않아 안전하게 계정을 찾아드릴 수 없어요.')
                st.markdown('1. 자주 쓰는 이메일 주소를 확인하세요.\n2. 브라우저의 비밀번호 관리자에서 이 앱 주소를 검색하세요.\n3. 이메일 주소가 기억나면 **비밀번호 찾기**에서 재설정을 요청하세요.')
                st.caption('새 계정을 만들면 기존 계정의 메뉴는 자동으로 이전되지 않습니다.')
        st.caption('계정별 메뉴 분리 보관 · 비밀번호 원문 저장 안 함 · 공용 기기 사용 후 로그아웃')
