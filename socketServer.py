import sys, traceback

from aiohttp import web
import socketio
import datetime
import logging
import json
from collections import defaultdict

import base64
from urllib import parse as urlparse

logger = logging.getLogger('socketServer')

# def Verify(username = "", token = "", by_pass_activation = False):
#     if len(token) >= 35:
#         encryption_key = config('ENCRYPTION_KEY')
#         if not encryption_key:
#             return False
#         token = TokenDecrypt(token, encryption_key)
#         if not token:
#             return False
#     p1 = User.objects.filter(username = username, token = token)
#     if not by_pass_activation:
#         p1 = p1.filter(activestatus=1)
#     if len(p1):
#         if p1[0].isdeleted:
#             return False
#         return True
#     else:
#         p1 = User.objects.filter(fullname = username, token = token)
#         if not by_pass_activation:
#             p1 = p1.filter(activestatus=1)
#         if len(p1):
#             if p1[0].isdeleted:
#                 return False
#             return True
#         return False
#
#
# def TokenDecrypt(key, encryption_key):
#     try:
#         key = urlparse.unquote(key)
#         cipher = AES.new(encryption_key.encode(), AES.MODE_ECB)
#         decoded = cipher.decrypt(base64.b64decode(key.encode())).decode()
#         decoded = decoded.split("~")
#         token = decoded[1]
#         return token
#     except Exception:
#         exc_type, exc_value, exc_traceback = sys.exc_info()
#         logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
#     return None


sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)


async def background_task():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        await sio.sleep(10)
        await sio.emit('serverMessage', 'Current Time: ' + str(datetime.datetime.now()))


async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

# @sio.on('connect')
# async def authenticateUser(sid, data):
#     authenticationStatus = verifyUser(data['username'], data['token'])
#
#     if not authenticateUser:
#         sio.disconnect(sid)


@sio.on('message')
async def print_message(sid, message):
    # print("Socket ID: " , sid)
    # print(message['profileID'])
    # logger.info('MESSAGE IS: ' + message)
    # print(app.logger())
    # await a successful emit of our reversed message
    # back to the client
    await sio.emit('clientMessage', message['msg'], room=sid)

personDict = {}

@sio.on('connect')
def connect(sid, environ):
    logger.info('connect ' + str(sid))
    print('connect ', sid)
    logger.info('connection environment: ' + str(environ))
    print('connection environment: ' + str())

@sio.on('disconnect')
def disconnect(sid):
    logger.info('disconnect ' +  str(sid))
    print('disconnect ', sid)

@sio.on('person_data')
def pushNotification(sid, data):
    room_name = str(data['personid']) + '_room'
    print('Response id: ' + str(data['responseid']))
    print('Person id: ' + str(data['personid']))
    print('creating room: ' + room_name)

    for x in personDict:
        print(x)

    print('PERSON ID: ' + str(data['personid']))

    # if personDict[data['personid']]:
    #     print('sending notification for person: {' + str(data['personid']) + '} to ' + str(len(personDict[data['personid']])) + ' sessions')
    #     print("Current person session ids list: " + str(personDict[data['personid']]))


    try:
        if str(data['personid']) in personDict:
            for x in personDict[str(data['personid' ])]:
                print('x: ' + str(x))
                sio.enter_room(x, room_name)


            sio.emit('profileready', json.dumps(data), room=room_name)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

    del personDict[str(data['personid'])]

    print('closing room: ' + room_name)
    sio.close_room(room_name)

    # print()
    # print('Response ID: ' + str(data['response_id']))
    sio.disconnect(sid)


@sio.on('testmessage')
def testFunction(sid, data):
    logger.info('Session ID: ' + str(sid))
    logger.info('Message: ' + str(data))
    print('Session ID: ' + str(sid))
    print('Message: ' + str(data))

@sio.on('searchperson')
def populateDict(sid, data):
    print('session id: {' + str(sid) + '} request for person having id: {' + str(data['personid']) + '}')

    if str(data['personid']) not in personDict:
        personDict[str(data['personid'])] = [sid]
    else:
        personDict[str(data['personid'])].append(sid)




# async def background_task():
#     """Example of how to send server generated events to clients."""
#     count = 0
#     while True:
#         await sio.sleep(10)
#         await sio.emit('serverMessage', 'Current Time: ' + str(datetime.datetime.now()))

app.router.add_get('/', index)

# We kick off our server
if __name__ == '__main__':
    # sio.start_background_task(background_task)
    web.run_app(app, port=27017)