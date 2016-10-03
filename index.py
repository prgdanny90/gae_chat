#-*- coding: utf-8-*-
import os
# 실제 데이터 Path를 얻기 위해 OS 모듈을 임포트 한다.
import logging
# 로그를 남기기위한 모듈을 임포트 한다.
import wsgiref.handlers
# wsgi를 이용한 핸들러를 사용하며, 이를 상속하여 child 핸들러를 만들어 처리한다.
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
# 구글 앱엔진에서의 Template은 장고에서 쓰는 Template과 동일하다. 모듈을 로드
from util.sessions import Session
# 구글 앱엔진에서는 User관리를 Google Account를 통해서도 가능하지만
# Google Account 사용시 Email과 Nickname만 알 수 있기 때문에 그 밖에 다른 정보들을
# 다루고자 할때는 로그인 Account를 따로 만들어야 한다.
# 이 Account를 다루고자 Session을 이용하고자 Session 모듈을 만들어 임포트 한다.
from google.appengine.ext import db         # 구글 앱엔진에서 지원하는 BigTable 모듈 로드
# SQL대신 GQL을 사용 (GQL을 SQL의 Subset이며, 몇가지 기능이 빠졌다.)
# BigTable에서는 로우키, 컬럼키, 타임스탬프로 데이터를 관리하고 byte배열에 저장 
# Row키는 전체 시스템에서 유일
# Read/Write는 Row단위로 이루어진다.
# Row단위 잠금은 Table 단위 잠금과 달리 다른 연산과 상호 영향을 최소화하여 데이터를 변경하는 유리함이 있다.
# Row여러개는 Tablet이라는 단위로 관리되고 이 Tablet 단위로 물리적인 서버에 할당된다.
# 즉, Row를 제어하지 않을 경우 각 Row가 다른 Tablet 혹은 다른 물리적 서버에 위치할 수 있음.
from google.appengine.api import memcache
# 구글 앱엔진에서 지원하는 범용캐시 모듈 로드
# 범용캐시란 자주 사용되는 리소스를 캐싱하여 부하를 줄여준다.

# A Model for a User
# User에 관한 모델을 설정한다.
# db.Model을 사용하여 확장 하고 있다.
# 테이블을 설계 하는데 밑줄을 두개 사용하는 속성은 만들수 없다.
class User(db.Model):
  account = db.StringProperty()
  # StringProperty는 순수 파이썬 문자열 혹은 유니코드 문자열을 저장하는 속성
  # 이 속성을 이용하여 인덱싱이 되므로 정렬이나 쿼리 필터의 속성으로 사용 할 수 있다.
  password = db.StringProperty()
  name = db.StringProperty()
  created = db.DateTimeProperty(auto_now=True)
  # 시간과 날짜를 저장하는 속성 auto_now=True면 생성될때 자동으로 현재 시간과 날짜가 기록된다.

  
# A Model for a ChatMessage
class ChatMessage(db.Model):
  user = db.ReferenceProperty()
  # 데이터스토어는 엔티티끼리 관계 연산을 제공하지 않는다고 설명했습니다.
  # 하지만 엔티티 간 참조 속성을 이용하면 객체의 상속 연산자(.)로
  # 다른 엔티티 그룹에 있는 엔티티에 접근 가능
  text = db.StringProperty()
  created = db.DateTimeProperty(auto_now=True)
  # 메시지가 언제 생성됬는지를 저장한다.

# A helper to do the rendering and to add the necessary
# variables for the _base.htm template
def doRender(handler, tname = 'index.htm', values = { }):
  temp = os.path.join(
      os.path.dirname(__file__),
      'templates/' + tname)
  # 랜더링을 진행하기 위한 템플릿의 Path를 __file__의 디렉토리를 구하여
  # templates/ 폴더에서 정적 html로 가져온다.
  # 만약 tname이 입력이 되지 않는다면 자동으로 index.htm 파일을 default로 가져온다.
  if not os.path.isfile(temp):
    return False
  # 없으면 false를 반환한다.

  # Make a copy of the dictionary and add the path and session
  newval = dict(values)
  # newval에 values (dictionary type)를 copy한다.
  
  newval['path'] = handler.request.path
  # dictionary에 path를 추가 한다. 

  handler.session = Session()
  if 'username' in handler.session:
     newval['username'] = handler.session['username']
     # 만약 로그인 중이라면 유저의 이름을 추가한다.

  outstr = template.render(temp, newval)
  # template에 newval을 넘겨줘 필요한 것들을 사용하여 html코드를 생성하게 한다.
  # 이때 출력결과는 unicode로 변환하여 출력한다.
  handler.response.out.write(unicode(outstr))
  # 최종적으로 완성된 html코드를 랜더링 한다.
  return True

class LoginHandler(webapp.RequestHandler):

  def get(self):
    doRender(self, 'loginscreen.htm')
    # request get이라면 loginscreen을 랜더링한다.

  def post(self):
    self.session = Session()
    acct = self.request.get('account')
    pw = self.request.get('password')
    print acct
    print pw
    # request post이라면 세션을 만들고 accout, pw를 가져온다. 
    logging.info('Checking account='+acct+' pw='+pw)

    self.session.delete_item('username')
    self.session.delete_item('userkey')
    # 만약 로그인 중이라서 session이 존재한다면 삭제한다.

    # 예외처리 pw 나 accout가 빈칸이면 에러 html 반환
    if pw == '' or acct == '':
      doRender(
          self,
          'loginscreen.htm',
          {'error' : 'Please specify Account and Password'} )
      return

    que = db.Query(User)
    que = que.filter('account =',acct)
    que = que.filter('password = ',pw)

    results = que.fetch(limit=1)
    # db에서 accout와 pw와 같은 게 있다면 1개만 가져온다.

    if len(results) > 0 :
      user = results[0]
      self.session['userkey'] = user.key()
      self.session['username'] = acct
      doRender(self,'index.htm',{ } )
    else:
      doRender(
          self,
          'loginscreen.htm',
          {'error' : 'Incorrect password'} )
    # db에서 가져온 개수가 1개 이상이면 세션에 기록하고 index.html을 render한다.
    # 없다면 암호가 틀렸습니다. 라고 loginscreen.htm을 다시 render한다.

# 회원가입 핸들러
class ApplyHandler(webapp.RequestHandler):

  def get(self):
    doRender(self, 'applyscreen.htm')
    # request get이라면 applyscreen.htm을 랜더링한다.
  def post(self):
    self.session = Session()
    name = self.request.get('name')
    acct = self.request.get('account')
    pw = self.request.get('password')
    # request post라면 세션을 만들고 request에서 name, account, pw를 가져온다.
    logging.info('Adding account='+acct)


    # 예외처리 pw, acct, name이 빈칸일 경우 에러 메시지를 출력한다.
    if pw == '' or acct == '' or name == '':
      doRender(
          self,
          'applyscreen.htm',
          {'error' : 'Please fill in all fields'} )
      return

    # Check if the user already exists
    que = db.Query(User).filter('account =',acct)
    results = que.fetch(limit=1)

    # DB에서 account가 같은 Row가 1개이상 있다면 이미 있다라고 출력한다.
    if len(results) > 0 :
      doRender(
          self,
          'applyscreen.htm',
          {'error' : 'Account Already Exists'} )
      return

    # Create the User object and log the user in
    # 없다면 새로운 유저를 만들어 db에 추가한다.
    newuser = User(name=name, account=acct, password=pw);
    pkey = newuser.put();
    self.session['username'] = acct
    self.session['userkey'] = pkey
    doRender(self,'index.htm',{ })

# 채팅 페이지 핸들러
class ChatHandler(webapp.RequestHandler):

  def get(self):
    doRender(self,'chatscreen.htm')
  # get으로 온건 render

  def post(self):
    self.session = Session()
    # 예외처리 session이 존재 하지 않는다면, 로그인을 하라고 출력한다.
    if not 'userkey' in self.session:
      doRender(
          self,
          'chatscreen.htm',
          {'error' : 'Must be logged in'} )
      return

    msg = self.request.get('message')
    # post일 경우에 message가 비어있다면, 비어있는 메시지는 무시된다고 Render 한다.
    if msg == '':
      doRender(
          self,
          'chatscreen.htm',
          {'error' : 'Blank message ignored'} )
      return

    newchat = ChatMessage(user = self.session['userkey'], text=msg)
    newchat.put();
    # chat메시지를 db에 추가한다.
    doRender(self,'chatscreen.htm')

# Messages를 열개 출력하는 Message 핸들러
class MessagesHandler(webapp.RequestHandler):

  def get(self):
    que = db.Query(ChatMessage).order('created');
    chat_list = que.fetch(limit=10)
    # order에 - 는 created col을 기준으로 최신순 내림차순으로 정렬한다.
    # fetch limit=10은 10개를 가져온다.
    # list로 반환된 chat메시지를 messagelist.htm에 넘겨 render 한다.
    doRender(self, 'messagelist.htm', {'chat_list': chat_list})

# Logout 핸들러
class LogoutHandler(webapp.RequestHandler):

  def get(self):
    self.session = Session()
    self.session.delete_item('username')
    self.session.delete_item('userkey')
    # session에서 현재 로그인 되어있는 user를 삭제하고
    # index.htm 을 Render한다.
    doRender(self, 'index.htm')
    
# A quick way to clean up the data models and log out all users
# app.yaml insures that only the app owner can call this
# 리셋 Handler
class ResetHandler(webapp.RequestHandler):
  def get(self):
    memcache.flush_all()
    # 공용 캐시에 있는 내용을 모두 삭제한다.
    
    while True:
        q = db.GqlQuery("SELECT __key__ FROM User")
        results = q.fetch(1000)
        if ( len(results) < 1 ) : break
        db.delete(results)
        # DB에 있는 모든 유저정보 record를 1000개 씩 가져와서 삭제하고
        # 1개 이하 일때 삭제 하고 끝낸다.

    while True :
        q = db.GqlQuery("SELECT __key__ FROM ChatMessage")
        results = q.fetch(1000)
        if ( len(results) < 1 ) : break
        db.delete(results)
        # DB에 있는 모든 채팅 record를 1000개 씩 가져와서 삭제하고
        # 1개 이하 일때 삭제 하고 끝낸다.
        
    self.response.out.write('Reset Complete. <a href="/">Go Back</a>.')
    # 모두 reset이 되었음을 출력한다.


# 메인 핸들러 는 설정되지 않은 URI 에 따른 핸들러 설정이 안된 모든 것들을 처리한다.
# index.htm을 랜더한다.
class MainHandler(webapp.RequestHandler):

  def get(self):
    # title로 Path를 출력한다.
    if doRender(self,self.request.path) :
      try:
        print "Title"
        print self.requeust.path
      except:
        pass
      return
    doRender(self,'index.htm')

# main함수 정의
def main():
  application = webapp.WSGIApplication([
     ('/login', LoginHandler),
     ('/apply', ApplyHandler),
     ('/chat', ChatHandler),
     ('/messages', MessagesHandler),
     ('/reset', ResetHandler),
     ('/logout', LogoutHandler),
     ('/.*', MainHandler)],
     debug=True)
  # uri와 handler를 연결하고, 실행한다.
  wsgiref.handlers.CGIHandler().run(application)

# 직접 실행시켰을때만 main함수를 실행하며, 모듈로 불려 실행되면 main을 실행하지 않는다.
if __name__ == '__main__':
  main()
