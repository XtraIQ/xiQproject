from aiohttp import web
import socketio
import datetime
import json
from collections import defaultdict

import base64
from urllib import parse as urlparse


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

# @sio.on('connect')
# async def authenticateUser(sid, data):
#     authenticationStatus = verifyUser(data['username'], data['token'])
#
#     if not authenticateUser:
#         sio.disconnect(sid)

personDict = defaultdict(list)


@sio.on('personData')
async def pushNotification(sid, personData, personid):
    for sid in personDict[personid]:
        sio.enter_room(sid, 'chat_users')

    await sio.emit('profileready', json.dumps(personData), room='chat_users')
    del personDict[personid]


@sio.on('searchperson')
async def populateDict(sid, profileid):
    personDict[profileid].append(sid)



# async def background_task():
#     """Example of how to send server generated events to clients."""
#     count = 0
#     while True:
#         await sio.sleep(10)
#         await sio.emit('serverMessage', 'Current Time: ' + str(datetime.datetime.now()))


# We kick off our server
if __name__ == '__main__':
    # sio.start_background_task(background_task)
    web.run_app(app, port=27017)