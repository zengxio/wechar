from django.shortcuts import render,redirect,HttpResponse
import requests
# Create your views here.
import time
import re
import json
from bs4 import BeautifulSoup
def login(req):
    if req.method=="GET":
        uuid_time=int(time.time()*1000)
        base_uuid_url="https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&redirect_uri=https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage&fun=new&lang=zh_CN&_={0}"
        uuid_url=base_uuid_url.format(uuid_time)
        r1=requests.get(uuid_url)
        # print(r1.text)
        result=re.findall('= "(.*)";',r1.text)
        uuid=result[0]
        req.session['UUID_TIME']=uuid_time
        req.session['UUID']=uuid
        print(uuid)
        return render(req,'login.html',{'uuid':uuid})

def ticket(html):
    ret={}
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find(name='error').find_all():
        ret[tag.name]=tag.text
    return ret


def check_login(req):
    response={}
    ctime=int(time.time()*1000)
    base_login_url="https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid={0}&tip=1&r=-1142458658&_={1}"
    login_url=base_login_url.format(req.session['UUID'],ctime)
    r1=requests.get(login_url)
    # print(r1.text)
    if 'window.code=408' in r1.text:
        #无人扫码
        response['code']=408

    elif 'window.code=201' in r1.text:
        #扫码成功，返回头像
        response['code'] = 201
        response['data']=re.findall("window.userAvatar = '(.*)';",r1.text)[0]

    elif 'window.code=200' in r1.text:
        #扫码并确认登陆
        #跳转到一个url
        req.session['LOGIN_COOKIE']=r1.cookies.get_dict()
        base_redirect_url=re.findall('window.redirect_uri="(.*)";',r1.text)[0]
        redirect_url = base_redirect_url + "&fun=new&version=v2"

        # window.code=200;window.redirect_uri="https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=Ac7UdZpGiJ7ImeACbVHjtZQx@qrticket_0&uuid=wbLyAoJJkQ==&lang=zh_CN&scan=1525920952";""

        # 获取凭证
        r2=requests.get(redirect_url)

        ticket_dict=ticket(r2.text)
        req.session['TICKET_DICT']=ticket_dict
        req.session['TICKET_COOKIE']=r2.cookies.get_dict()
        #初始化获取最近联系人信息，工作号
        post_data={
            'BaseRequest':{
            'DeviceID':"e665781722037153",
            'Sid':ticket_dict['wxsid'],
            'Skey':ticket_dict['skey'],
            'Uin':ticket_dict['wxuin'],
                }
            }
        #用户初始化，获取最近联系人、个人信息放在session中
        init_url="https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=792831246&lang=zh_CN&pass_ticket={0}".format(ticket_dict['pass_ticket'])
        r3=requests.post(
            url=init_url,
            json=post_data
        )
        r3.encoding = 'utf8'
        init_dict=json.loads(r3.text)
        response['code']=200
        print(init_dict)

        # # 个人info
        # print(init_dict['User'])
        # # 最近联系人信息
        # print(init_dict['ContactList'])
        # # 订阅号
        # print(init_dict['MPSubscribeMsgList'])
        #SyncKey发送消息的唯一标识

        # 将初始化信息放入 Session
        req.session['INIT_DICT'] = init_dict
    return HttpResponse(json.dumps(response))



def index(req):
    """显示最近联系人"""
    img_url="h"
    return render(req,'index.html')