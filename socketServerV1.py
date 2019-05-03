import os
import sys, traceback

from aiohttp import web
import socketio
import datetime
import logging
import json
import ssl


logger = logging.getLogger('socketServer')

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

sioS = socketio.AsyncServer()
appS = web.Application()
sioS.attach(appS)

personDict = {}

def is_process_running(file_name):
    is_running = False
    count = 0
    for line in os.popen("ps -aux"):
        if '/bin/sh' not in line and 'sudo' in line and file_name in line:
            count += 1
    if count > 1:
        is_running = True
    return is_running

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')




@sio.on('message')
async def print_message(sid, message):
    # print("Socket ID: " , sid)
    # print(message['profileID'])
    # logger.info('MESSAGE IS: ' + message)
    # print(app.logger())
    # await a successful emit of our reversed message
    # back to the client
    await sio.emit('clientMessage', message['msg'], room=sid)

@sioS.on('message')
async def print_message(sid, message):
    # print("Socket ID: " , sid)
    # print(message['profileID'])
    # logger.info('MESSAGE IS: ' + message)
    # print(app.logger())
    # await a successful emit of our reversed message
    # back to the client
    print(message)
    await sioS.emit('clientMessage', message['msg'], room=sid)



@sio.on('connect')
async def connect(sid, environ):
    logger.info('connect ' + str(sid))
    print('connect ', sid)
    # logger.info('connection environment: ' + str(environ))
    # print('connection environment: ' + str())

@sio.on('disconnect')
async def disconnect(sid):
    logger.info('disconnect ' +  str(sid))
    print('disconnect ', sid)

@sio.on('person_data')
async def pushNotification(sid, data):
    room_name = str(data['personid']) + '_room'
    # await print('CREATED ROOM [' + str(room_name) + ']')
    print('created room [' + str(room_name) + ']')

    # await print('PERSON HAVING ID [' + str(data['personid']) + '] AND RESPONSE ID [' + str(data['responseid']) + '] HAS BEEN PARSED')
    print('person having id [' + str(data['personid']) + '] and response id [' + str(data['responseid']) + '] has been parsed')

    try:
        if str(data['personid']) in personDict:
            for x in personDict[str(data['personid' ])]:
                sio.enter_room(x, room_name)

            await sio.emit('profileready', json.dumps(data), room=room_name)
            # await print('PARSED DATA HAS BEEN SENT TO THE CLIENT')
            print('parsed data has been sent to the client')

            del personDict[str(data['personid'])]

            if str(data['personid']) in personDict:
                # await print('PERSON ID NOT DELETED FROM DICTIONARY')
                print('person id not deleted from dictionary')
            else:
                # await print('PERSON ID DELETED FROM DICTIONARY')
                print('person id delted from dictionary')
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

    await sio.close_room(room_name)
    await sio.disconnect(sid)


@sio.on('searchperson')
def populateDict(sid, data):
    print('session id: {' + str(sid) + '} request for person having id: {' + str(data['personid']) + '} and response id: {' +  '}')
    print('Person dict length: ' + str(len(personDict)))

    if str(data['personid']) not in personDict:
        personDict[str(data['personid'])] = [sid]
    else:
        if str(sid) not in personDict[str(data['personid'])]:
            personDict[str(data['personid'])].append(sid)

testDict = {
            'personid': 456235,
            'image': 'abc.png',
            'action': 'Executive Profile',
            'name': 'UNIT TEST',
            'type': 'profile',
            'responseid': 875965
                                                    }

@sioS.on('searchperson')
def populateDict(sid, data):
    print('session id: {' + str(sid) + '} request for person having id: {' + str(data['personid']) + '} and response id: {' +  '}')
    print('Person dict length: ' + str(len(personDict)))

    if str(data['personid']) not in personDict:
        personDict[str(data['personid'])] = [sid]
    else:
        if str(sid) not in personDict[str(data['personid'])]:
            personDict[str(data['personid'])].append(sid)

    sioS.emit('profileready', json.dumps(testDict), room=sid)


def http_socket_server():
    # app.router.add_get('/', index)
    web.run_app(app, port=27017)



def https_socket_server():
    appS.router.add_get('/', index)
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('star_xiq_io.crt', 'xiq_io.key')

    web.run_app(appS, port=27018, ssl_context=ssl_context)

def start_socket():
    try:
        if is_process_running(__file__):
            print('SOCKET IS ALREADY RUNNING')
        else:
            # print('STARTING HTTP SOCKET SERVER')
            # http_socket_server()
            print('STARTING HTTPS SOCKET SERVER')
            https_socket_server()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))


start_socket()



























async def background_task():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        await sio.sleep(10)
        await sio.emit('serverMessage', 'Current Time: ' + str(datetime.datetime.now()))




# @sio.on('connect')
# async def authenticateUser(sid, data):
#     authenticationStatus = verifyUser(data['username'], data['token'])
#
#     if not authenticateUser:
#         sio.disconnect(sid)





# @sio.on('testmessage')
# def testFunction(sid, data):
#     logger.info('Session ID: ' + str(sid))
#     logger.info('Message: ' + str(data))
#     print('Session ID: ' + str(sid))
#     print('Message: ' + str(data))

# async def background_task():
#     """Example of how to send server generated events to clients."""
#     count = 0
#     while True:
#         await sio.sleep(10)
#         await sio.emit('serverMessage', 'Current Time: ' + str(datetime.datetime.now()))