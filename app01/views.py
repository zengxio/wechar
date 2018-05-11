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
    """

<error>
	<ret>0</ret>
	<message></message>
	<skey>@crypt_a7f1c18d_1dfd4206411bdea7530d503a4fc31a19</skey>
	<wxsid>v2LFhRigsWc7msxx</wxsid>
	<wxuin>2298162474</wxuin>
	<pass_ticket>0e%2FzhyWtoLJgVQR%2B6dcFhbZfXFQLIk%2BT%2Fs5SusD%2FqKMtnetBmIAl%2FA%2FPLk%2BT9D4P</pass_ticket>
	<isgrayscale>1</isgrayscale>
</error>
    :param html:
    :return:
    xml格式
    """
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
        # print(init_dict)

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

def avatar(req):
    prev=req.GET.get('prev')
    username=req.GET.get('username')
    skey=req.GET.get('skey')
    img_url = "https://wx.qq.com{0}&username={1}&skey={2}".format(prev, username, skey)
    cookies={}
    cookies.update(req.session['TICKET_COOKIE'])
    cookies.update(req.session['LOGIN_COOKIE'])
    #头像做了防盗链，所以请求获取头像的时候，需要带请求头，以及referer地址（）
    res = requests.get(img_url, headers={'Content-Type': 'image/jpeg'}, cookies=cookies)

    # with open('a.jpg','wb') as f:
    #     f.write(res.content)

    return HttpResponse(res.content)

def index(req):
    """显示最近联系人"""
    return render(req,'index.html')


def contact_list(req):
    """
       获取所有联系人
       Request URL:https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgeticon?seq=688265135&username=@1c3b3d46599f351298f34c3c9600db5f&skey=@crypt_bd4fce8d_d5d75b3402c805638a72ac15e6b59069
       :https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?lang=zh_CN&pass_ticket=9tsvk3%252Fk1lUw9g0E380a2XOp4UrtXIKr0j%252FxKG6TnhQZbBKELyPTwGhWIvmmHMNr&r=1519647210703&seq=0&skey=@crypt_bd4fce8d_cf98977df63a48ea505b711d87d16384
       Request Method:GET
       """
    cookies = {}
    cookies.update(req.session['LOGIN_COOKIE'])
    cookies.update(req.session['TICKET_DICT'])
    ctime=int(time.time()*1000)
    url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?lang=zh_CN&pass_ticket={0}&r={1}&seq=0&skey={2}".format(
        req.session['TICKET_DICT']['pass_ticket'], ctime, req.session['TICKET_DICT']['skey'])
    r1 = requests.get(url, cookies=cookies)
    r1.encoding = "utf8"
    user_list = json.loads(r1.text)
    # print(user_list)
    return render(req, 'contact_list.html',{'user_list': user_list})


def send_msg(req):
    """
        发送消息
        :param req:
        :return:
        """
    current_user = req.session["INIT_DICT"]['User']['UserName']  # session初始化,User.UserName
    ToUserName = req.POST.get('to')  # 发给谁
    Content = req.POST.get('msg')  # 发送的内容

    # print(ToUserName,Content)
    ticket_dict = req.session['TICKET_DICT']
    ctime = int(time.time() * 10000000)
    # json 数据结构
    post_data = {
        "BaseRequest": {
            'DeviceID': "e665781722037153",
            'Sid': ticket_dict['wxsid'],
            'Skey': ticket_dict['skey'],
            'Uin': ticket_dict['wxuin'],
        },
        'Msg': {
            "ClientMsgId": ctime,
            "Content": Content,
            "FromUserName": current_user,
            "LocalID": ctime,
            "ToUserName": ToUserName,
            # 文字是1 语音 图片是3 都不同
            "Type": 1,
        },
        "Scene": 0,
    }
    """
        Request URL: https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?lang=zh_CN&pass_ticket=kIjKZduslbOk%252F3vj%252FfphQ5c7UwuQjqfXRdCUM8huV6iCLDIpOyexgZDUMA3Ac2Tu
        Request Method: POST
    """

    url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?lang=zh_CN&pass_ticket={0}".format(
        req.session['TICKET_DICT']['pass_ticket'])
    res = requests.post(
        url=url,
        data=json.dumps(post_data, ensure_ascii=False).encode('utf-8'),
        headers={"Content-Type": "application/json"},
    )

    print(res.text)
    return HttpResponse('...')

def get_msg(req):
    """
    长轮询获取消息
    :param req:
    :return:
    """

    #检测是否有消息到来
    #有，获取新消息
    #  获取 cookies
    cookies = {}
    cookies.update(req.session['LOGIN_COOKIE'])
    cookies.update(req.session['TICKET_COOKIE'])

    ticket_dict = req.session['TICKET_DICT']
    ctime = int(time.time() * 10000000)
    synckey_dict = req.session['INIT_DICT']['SyncKey']

    synckey_list = []
    for item in synckey_dict['List']:
        tmp = "%s_%s" % (item['Key'], item['Val'])
        synckey_list.append(tmp)
    synckey = "|".join(synckey_list)

    check_msg_url = "https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck"


    r1=requests.get(
        url=check_msg_url,
        params={
            'r':ctime,
            'DeviceID': "e665781722037153",
            'skey': ticket_dict['skey'],
            'sid': ticket_dict['wxsid'],
            'uin': ticket_dict['wxuin'],
            '_': ctime,
            'synckey': synckey
        },
        cookies=cookies
    )
    print(r1.text)
    if 'selector:"0"' in r1.text:
        return HttpResponse("...")
    elif 'selector:"2' in r1.text:
        #有消息，获取消息
        get_msg_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid={0}&lang=zh_CN&pass_ticket={1}".format(
            ticket_dict['wxsid'], ticket_dict['pass_ticket'])

        post_data = {
            "BaseRequest": {
                'DeviceID': "e991717205648670",
                'Sid': ticket_dict['wxsid'],
                'Skey': ticket_dict['skey'],
                'Uin': ticket_dict['wxuin'],
            },
            'SyncKey': req.session['INIT_DICT']['SyncKey'],
            'rr': 694839680
        }

        r2 = requests.post(
            url=get_msg_url,
            json=post_data,
            cookies=cookies
        )
        #接收到消息，会生成新的synckey,所以要更新ynckey
        r2.encoding = 'utf8'
        msg_dict=json.loads(r2.text)

        for msg in msg_dict['AddMsgList']:
            print('您有新的消息到来',msg['Content'])

        init_dict=req.session['INIT_DICT']
        init_dict['SyncKey']=msg_dict['SyncKey']
        req.session['INIT_DICT']=init_dict

    return HttpResponse(r1.text)
