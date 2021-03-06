# -*-coding:utf-8 -*-
import json
import random
import threading
import time
import uuid
from collections import defaultdict
import dwebsocket
from django.http import HttpResponse
from django.shortcuts import render
from dwebsocket import accept_websocket, require_websocket
from rec.tankgame.room import Room
from rec.tankgame.settings import Settings
from rec.tankgame.tank import Tank

# Create your views here.
usr_dict = defaultdict(list)
tank_settings = Settings()
room = defaultdict(list)
channelid = str(uuid.uuid1())
room[channelid] = Room()
room[channelid].channelid = channelid

def index(request):
    return HttpResponse("Hello, world. You're at the rec index.哈哈")

@require_websocket  #只接受websocket请求，不接受http请求，这是调用了dwebsocket的装饰器
def websocket_test(request):
    message = request.websocket.wait()
    request.websocket.send("reply:" + message)

@accept_websocket  #既能接受http也能接受websocket请求
def echo(request):
    if not request.is_websocket():
        try:
            message = request.GET['message']
            return HttpResponse(message)
        except:
            return render(request, 'app02/user2.html')
    else:
        u = request.session['u']
        u = request.GET.get('user')
        usr_dict[u] = request.websocket
        print(usr_dict)
        for message in request.websocket:
            try:
                if len(message) <= 140 and '*' in message:
                    print(u)
                    msg_info = str(message, 'utf-8').split('*#*#*')
                    sendby = msg_info[0]
                    msg = msg_info[1]
                    sendto = msg_info[2]
                    print(sendby, msg, sendto)
                    usr_dict[sendto].send(message + ''.encode('utf-8'))
                else:
                    if 'replay' in usr_dict:
                        #print('replay', len(message))
                        usr_dict['replay'].send(message)
            except Exception as e:
                print(e)

@accept_websocket  #既能接受http也能接受websocket请求
def snake(request):
    clientid = request.GET.get('clientid')
    last_roomid = -1
    userinfo = {'clientid': clientid, 'channelid': channelid}
    request.session['userinfo'] = userinfo
    request.websocket.send(json.dumps(userinfo).encode('utf8'))
    print(clientid, ':连接成功')
    for message in request.websocket:
        try:
            jmsg = json.loads(message.decode('utf8'))
            code = jmsg['code']
            if code:
                if code == 1000:
                    print(jmsg)
            else:
                pass
        except Exception as e:
            print(e)

@accept_websocket  #既能接受http也能接受websocket请求
def tank(request):
    clientid = request.GET.get('clientid')
    last_roomid = -1
    userinfo = {'clientid': clientid, 'channelid': channelid}
    request.session['userinfo'] = userinfo
    request.websocket.send(json.dumps(userinfo).encode('utf8'))
    print(clientid, ':连接成功')
    for message in request.websocket:
        try:
            jmsg = json.loads(message.decode('utf8'))
            code = jmsg['code']
            if code:
                # print(message)
                if code == 3333:  #ResetAI
                    room[channelid].add_ai(random.randint(3, 8))
                elif code == 5000:  #ping 
                    request.websocket.send(json.dumps({"code": 5000}))
                elif code == 1111:  #game_status
                    t = Tank(channelid, clientid, random.randint(140, 1300),
                             random.randint(140, 700), random.randint(0, 3),
                             tank_settings)
                    color = [tank_settings.random_color(), '#00FFFF']
                    t.tank_color = color
                    user = {"id": clientid, "roomid": channelid, 'tank': t}
                    room[channelid].add_user_requests(clientid, request)
                    room[channelid].add_user(user)
                    room[channelid].add_battling_user(user)
                    room[channelid].run()
                elif code == 1000:  #
                    request.websocket.send(json.dumps().encode('utf8'))
                    pass
                elif code == 1001:  #get_players
                    pass
                elif code == 1002:  #in_room
                    roomid = int(jmsg['data'])
                    if roomid in room:
                        room[roomid][clientid] = {}
                        if last_roomid == -1:
                            last_roomid = roomid
                        else:
                            room[last_roomid].pop(clientid)
                        request.websocket.send(
                            json.dumps({
                                'roomid': roomid
                            }).encode('utf8'))
                    else:
                        request.websocket.send(
                            json.dumps({
                                'roomid': '-1'
                            }).encode('utf8'))
                elif code == 1003:  #get_rooms
                    request.websocket.send(
                        json.dumps({
                            'rooms': room
                        }).encode('utf8'))
                elif code == 2222:  #game_cmd
                    """
                    {"code":2222,"type":"getrooms","message":"","data":{clientid:1,cmd:0,1,2,3}}
                    """
                    cmd_data = jmsg['data']
                    rcid = cmd_data['clientid']
                    rcmd = cmd_data['cmd']
                    battle_ing = room[channelid].battling[clientid]['tank']
                    if rcmd == 87:
                        battle_ing.move(0)
                    elif rcmd == 68:
                        battle_ing.move(1)
                    elif rcmd == 83:
                        battle_ing.move(2)
                    elif rcmd == 65:
                        battle_ing.move(3)
                    elif rcmd == 69:
                        battle_ing.biu()
                    elif rcmd in [16, 32, 37, 38, 39, 40]:
                        # check shoting frequency
                        # LAST_SHOT_TIME_STAMP
                        user = room[channelid].battling[clientid]
                        shotable = False
                        now = int(time.time() * 1000)
                        if 'LAST_SHOT_TIME_STAMP' in user:
                            last = user['LAST_SHOT_TIME_STAMP']
                            if now - last > 100:
                                user['LAST_SHOT_TIME_STAMP'] = now
                                shotable = True
                        else:
                            shotable = True
                            user['LAST_SHOT_TIME_STAMP'] = now
                        if shotable:
                            battle_ing.shot(rcmd)
                    request.websocket.send(
                        json.dumps({
                            "code":
                            1111,
                            "status":
                            1,
                            "type":
                            "game_status",
                            "message":
                            "normal",
                            "data":
                            json.loads(
                                json.dumps(
                                    room[channelid].battling,
                                    default=lambda o: o.__dict__,
                                    sort_keys=True))
                        }).encode('utf8'))
                else:
                    pass
            else:
                pass
        except Exception as e:
            print(e)
