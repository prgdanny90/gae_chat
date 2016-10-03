#-*- coding: utf-8-*-
import os
# ���� ������ Path�� ��� ���� OS ����� ����Ʈ �Ѵ�.
import logging
# �α׸� ��������� ����� ����Ʈ �Ѵ�.
import wsgiref.handlers
# wsgi�� �̿��� �ڵ鷯�� ����ϸ�, �̸� ����Ͽ� child �ڵ鷯�� ����� ó���Ѵ�.
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
# ���� �ۿ��������� Template�� ����� ���� Template�� �����ϴ�. ����� �ε�
from util.sessions import Session
# ���� �ۿ��������� User������ Google Account�� ���ؼ��� ����������
# Google Account ���� Email�� Nickname�� �� �� �ֱ� ������ �� �ۿ� �ٸ� ��������
# �ٷ���� �Ҷ��� �α��� Account�� ���� ������ �Ѵ�.
# �� Account�� �ٷ���� Session�� �̿��ϰ��� Session ����� ����� ����Ʈ �Ѵ�.
from google.appengine.ext import db         # ���� �ۿ������� �����ϴ� BigTable ��� �ε�
# SQL��� GQL�� ��� (GQL�� SQL�� Subset�̸�, ��� ����� ������.)
# BigTable������ �ο�Ű, �÷�Ű, Ÿ�ӽ������� �����͸� �����ϰ� byte�迭�� ���� 
# RowŰ�� ��ü �ý��ۿ��� ����
# Read/Write�� Row������ �̷������.
# Row���� ����� Table ���� ��ݰ� �޸� �ٸ� ����� ��ȣ ������ �ּ�ȭ�Ͽ� �����͸� �����ϴ� �������� �ִ�.
# Row�������� Tablet�̶�� ������ �����ǰ� �� Tablet ������ �������� ������ �Ҵ�ȴ�.
# ��, Row�� �������� ���� ��� �� Row�� �ٸ� Tablet Ȥ�� �ٸ� ������ ������ ��ġ�� �� ����.
from google.appengine.api import memcache
# ���� �ۿ������� �����ϴ� ����ĳ�� ��� �ε�
# ����ĳ�ö� ���� ���Ǵ� ���ҽ��� ĳ���Ͽ� ���ϸ� �ٿ��ش�.

# A Model for a User
# User�� ���� ���� �����Ѵ�.
# db.Model�� ����Ͽ� Ȯ�� �ϰ� �ִ�.
# ���̺��� ���� �ϴµ� ������ �ΰ� ����ϴ� �Ӽ��� ����� ����.
class User(db.Model):
  account = db.StringProperty()
  # StringProperty�� ���� ���̽� ���ڿ� Ȥ�� �����ڵ� ���ڿ��� �����ϴ� �Ӽ�
  # �� �Ӽ��� �̿��Ͽ� �ε����� �ǹǷ� �����̳� ���� ������ �Ӽ����� ��� �� �� �ִ�.
  password = db.StringProperty()
  name = db.StringProperty()
  created = db.DateTimeProperty(auto_now=True)
  # �ð��� ��¥�� �����ϴ� �Ӽ� auto_now=True�� �����ɶ� �ڵ����� ���� �ð��� ��¥�� ��ϵȴ�.

  
# A Model for a ChatMessage
class ChatMessage(db.Model):
  user = db.ReferenceProperty()
  # �����ͽ����� ��ƼƼ���� ���� ������ �������� �ʴ´ٰ� �����߽��ϴ�.
  # ������ ��ƼƼ �� ���� �Ӽ��� �̿��ϸ� ��ü�� ��� ������(.)��
  # �ٸ� ��ƼƼ �׷쿡 �ִ� ��ƼƼ�� ���� ����
  text = db.StringProperty()
  created = db.DateTimeProperty(auto_now=True)
  # �޽����� ���� ����������� �����Ѵ�.

# A helper to do the rendering and to add the necessary
# variables for the _base.htm template
def doRender(handler, tname = 'index.htm', values = { }):
  temp = os.path.join(
      os.path.dirname(__file__),
      'templates/' + tname)
  # �������� �����ϱ� ���� ���ø��� Path�� __file__�� ���丮�� ���Ͽ�
  # templates/ �������� ���� html�� �����´�.
  # ���� tname�� �Է��� ���� �ʴ´ٸ� �ڵ����� index.htm ������ default�� �����´�.
  if not os.path.isfile(temp):
    return False
  # ������ false�� ��ȯ�Ѵ�.

  # Make a copy of the dictionary and add the path and session
  newval = dict(values)
  # newval�� values (dictionary type)�� copy�Ѵ�.
  
  newval['path'] = handler.request.path
  # dictionary�� path�� �߰� �Ѵ�. 

  handler.session = Session()
  if 'username' in handler.session:
     newval['username'] = handler.session['username']
     # ���� �α��� ���̶�� ������ �̸��� �߰��Ѵ�.

  outstr = template.render(temp, newval)
  # template�� newval�� �Ѱ��� �ʿ��� �͵��� ����Ͽ� html�ڵ带 �����ϰ� �Ѵ�.
  # �̶� ��°���� unicode�� ��ȯ�Ͽ� ����Ѵ�.
  handler.response.out.write(unicode(outstr))
  # ���������� �ϼ��� html�ڵ带 ������ �Ѵ�.
  return True

class LoginHandler(webapp.RequestHandler):

  def get(self):
    doRender(self, 'loginscreen.htm')
    # request get�̶�� loginscreen�� �������Ѵ�.

  def post(self):
    self.session = Session()
    acct = self.request.get('account')
    pw = self.request.get('password')
    print acct
    print pw
    # request post�̶�� ������ ����� accout, pw�� �����´�. 
    logging.info('Checking account='+acct+' pw='+pw)

    self.session.delete_item('username')
    self.session.delete_item('userkey')
    # ���� �α��� ���̶� session�� �����Ѵٸ� �����Ѵ�.

    # ����ó�� pw �� accout�� ��ĭ�̸� ���� html ��ȯ
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
    # db���� accout�� pw�� ���� �� �ִٸ� 1���� �����´�.

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
    # db���� ������ ������ 1�� �̻��̸� ���ǿ� ����ϰ� index.html�� render�Ѵ�.
    # ���ٸ� ��ȣ�� Ʋ�Ƚ��ϴ�. ��� loginscreen.htm�� �ٽ� render�Ѵ�.

# ȸ������ �ڵ鷯
class ApplyHandler(webapp.RequestHandler):

  def get(self):
    doRender(self, 'applyscreen.htm')
    # request get�̶�� applyscreen.htm�� �������Ѵ�.
  def post(self):
    self.session = Session()
    name = self.request.get('name')
    acct = self.request.get('account')
    pw = self.request.get('password')
    # request post��� ������ ����� request���� name, account, pw�� �����´�.
    logging.info('Adding account='+acct)


    # ����ó�� pw, acct, name�� ��ĭ�� ��� ���� �޽����� ����Ѵ�.
    if pw == '' or acct == '' or name == '':
      doRender(
          self,
          'applyscreen.htm',
          {'error' : 'Please fill in all fields'} )
      return

    # Check if the user already exists
    que = db.Query(User).filter('account =',acct)
    results = que.fetch(limit=1)

    # DB���� account�� ���� Row�� 1���̻� �ִٸ� �̹� �ִٶ�� ����Ѵ�.
    if len(results) > 0 :
      doRender(
          self,
          'applyscreen.htm',
          {'error' : 'Account Already Exists'} )
      return

    # Create the User object and log the user in
    # ���ٸ� ���ο� ������ ����� db�� �߰��Ѵ�.
    newuser = User(name=name, account=acct, password=pw);
    pkey = newuser.put();
    self.session['username'] = acct
    self.session['userkey'] = pkey
    doRender(self,'index.htm',{ })

# ä�� ������ �ڵ鷯
class ChatHandler(webapp.RequestHandler):

  def get(self):
    doRender(self,'chatscreen.htm')
  # get���� �°� render

  def post(self):
    self.session = Session()
    # ����ó�� session�� ���� ���� �ʴ´ٸ�, �α����� �϶�� ����Ѵ�.
    if not 'userkey' in self.session:
      doRender(
          self,
          'chatscreen.htm',
          {'error' : 'Must be logged in'} )
      return

    msg = self.request.get('message')
    # post�� ��쿡 message�� ����ִٸ�, ����ִ� �޽����� ���õȴٰ� Render �Ѵ�.
    if msg == '':
      doRender(
          self,
          'chatscreen.htm',
          {'error' : 'Blank message ignored'} )
      return

    newchat = ChatMessage(user = self.session['userkey'], text=msg)
    newchat.put();
    # chat�޽����� db�� �߰��Ѵ�.
    doRender(self,'chatscreen.htm')

# Messages�� ���� ����ϴ� Message �ڵ鷯
class MessagesHandler(webapp.RequestHandler):

  def get(self):
    que = db.Query(ChatMessage).order('created');
    chat_list = que.fetch(limit=10)
    # order�� - �� created col�� �������� �ֽż� ������������ �����Ѵ�.
    # fetch limit=10�� 10���� �����´�.
    # list�� ��ȯ�� chat�޽����� messagelist.htm�� �Ѱ� render �Ѵ�.
    doRender(self, 'messagelist.htm', {'chat_list': chat_list})

# Logout �ڵ鷯
class LogoutHandler(webapp.RequestHandler):

  def get(self):
    self.session = Session()
    self.session.delete_item('username')
    self.session.delete_item('userkey')
    # session���� ���� �α��� �Ǿ��ִ� user�� �����ϰ�
    # index.htm �� Render�Ѵ�.
    doRender(self, 'index.htm')
    
# A quick way to clean up the data models and log out all users
# app.yaml insures that only the app owner can call this
# ���� Handler
class ResetHandler(webapp.RequestHandler):
  def get(self):
    memcache.flush_all()
    # ���� ĳ�ÿ� �ִ� ������ ��� �����Ѵ�.
    
    while True:
        q = db.GqlQuery("SELECT __key__ FROM User")
        results = q.fetch(1000)
        if ( len(results) < 1 ) : break
        db.delete(results)
        # DB�� �ִ� ��� �������� record�� 1000�� �� �����ͼ� �����ϰ�
        # 1�� ���� �϶� ���� �ϰ� ������.

    while True :
        q = db.GqlQuery("SELECT __key__ FROM ChatMessage")
        results = q.fetch(1000)
        if ( len(results) < 1 ) : break
        db.delete(results)
        # DB�� �ִ� ��� ä�� record�� 1000�� �� �����ͼ� �����ϰ�
        # 1�� ���� �϶� ���� �ϰ� ������.
        
    self.response.out.write('Reset Complete. <a href="/">Go Back</a>.')
    # ��� reset�� �Ǿ����� ����Ѵ�.


# ���� �ڵ鷯 �� �������� ���� URI �� ���� �ڵ鷯 ������ �ȵ� ��� �͵��� ó���Ѵ�.
# index.htm�� �����Ѵ�.
class MainHandler(webapp.RequestHandler):

  def get(self):
    # title�� Path�� ����Ѵ�.
    if doRender(self,self.request.path) :
      try:
        print "Title"
        print self.requeust.path
      except:
        pass
      return
    doRender(self,'index.htm')

# main�Լ� ����
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
  # uri�� handler�� �����ϰ�, �����Ѵ�.
  wsgiref.handlers.CGIHandler().run(application)

# ���� ������������� main�Լ��� �����ϸ�, ���� �ҷ� ����Ǹ� main�� �������� �ʴ´�.
if __name__ == '__main__':
  main()
