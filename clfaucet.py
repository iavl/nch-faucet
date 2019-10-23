import tornado.ioloop
import tornado.web
import tornado.httpserver

import json
import requests

import os
import re
import ratelimit
import subprocess


FROM_ACCOUNT = "nch1f94fzxp6hthrx3gzy4dmj6ccwh2xljuyzlwj8t"

PASSWD = "11111111"

# ------------------------------------------------------------------------------------------
# ------ token transfer limiter

def token_limit_exceed(handler):
    write_json_response(handler, {'msg': 'reach 24 hours max token amount'}, 403)

def account_limit_exceed(handler):
    write_json_response(handler, {'msg': 'reach 24 hours max account amount'}, 403)

single_get_token_call_amount = 200

ip_24h_token_amount_limiter = ratelimit.RateLimitType(
  name = "ip_24h_token_amount",
  amount = 6000,         # 24 hours amount
  expire = 3600*24,      # 24 hours
  identity = lambda h: h.request.remote_ip,
  on_exceed = token_limit_exceed)


account_24h_token_amount_limiter = ratelimit.RateLimitType(
  name = "account_24h_token_amount",
  amount = 5,         # 24 hours amount
  expire = 3600*24,      # 24 hours
  identity = lambda h: h.request.arguments.keys()[0] if len(h.request.arguments.keys()) == 1 else '',
  on_exceed = account_limit_exceed)

# ------------------------------------------------------------------------------------------
# ------ common functions

def write_json_response(handler, msg, code=200):
  handler.set_status(code)
  handler.set_header('Content-Type', 'application/json; charset=UTF-8')
  handler.write(msg)

def get_first_arg_name_from_request(request):
  args = request.arguments.keys()
  if len(args) == 1:
    return args[0]
  else:
    return ''

# ------------------------------------------------------------------------------------------
# ------ Get Token Handler

class GetTokenHandler(tornado.web.RequestHandler):

  def __init__(self, application, request, **kwargs):
    tornado.web.RequestHandler.__init__(self, application, request, **kwargs)

  def _assembly_args(self, data):
    if data.has_key('account') and is_valid_account_name(data['account']):
      p = {}
      p['to']       = data['account']
      p['quantity'] = single_get_token_call_amount
      return p
    else:
      return None

  def _os_cmd_transfer(self, param):
    cmd = 'echo "%s" |  nchcli send --from %s --to %s --amount %dunch --gas-prices 0.001unch --memo "for test" -y' % (PASSWD, FROM_ACCOUNT, p['to'], p['quantity']])
    a = subprocess.Popen('./a.out', stdin = subprocess.PIPE, stdout =subprocess.PIPE)
    output = a.stdout.read()
    print output
    # js = json.loads(response.text)
    # return js['result']

  def _make_transfer(self, p):
    return self._os_cmd_transfer(p)

  def _handle(self, data):
    param = self._assembly_args(data)
    if param:
      if self._make_transfer(param):
        ip_24h_token_amount_limiter.increase_amount(param['quantity'], self)
        account_24h_token_amount_limiter.increase_amount(1, self)
        print ip_24h_token_amount_limiter.server_name(self)
        print account_24h_token_amount_limiter.server_name(self)
        write_json_response(self, {'msg': 'succeeded'})
      else:
        failmsg = {'msg': 'transaction failed, possible reason: account does not exist'}
        write_json_response(self, failmsg, 400)
    else:
      fmtmsg = {'msg':'please use request with URL of format: http://xxxx.org/get_token?valid_account_address'}
      write_json_response(self, fmtmsg, 400)

  @ratelimit.limit_by(ip_24h_token_amount_limiter)
  @ratelimit.limit_by(account_24h_token_amount_limiter)
  def get(self):
    data = {'account': get_first_arg_name_from_request(self.request)}
    self._handle(data)

# --------------------------l---------------------------------------------------------------
# ------ service app

def make_app():
  return tornado.web.Application([
    (r"/get_token", GetTokenHandler),
  ])

if __name__ == "__main__":
  app = make_app()
  server = tornado.httpserver.HTTPServer(app)
  server.bind(8088)
  server.start(0)
  tornado.ioloop.IOLoop.current().start()
