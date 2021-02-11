import os
import sys, traceback

from aiohttp import web
import socketio
import datetime
import logging
from logging.handlers import RotatingFileHandler
import json
import ssl
import urllib.parse


log_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')


my_handler = RotatingFileHandler('socketLog.log', mode='a', maxBytes=500*1024*1024, backupCount=2)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

logger = logging.getLogger('socketLog')
logger.setLevel(logging.INFO)

logger.addHandler(my_handler)


sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

personDict = {}
person_parse_time_log = {}

# NEW VARIABLES
# VARIABLES
user_information_object = {}
person_information_object = {}
sid_information_object = {}

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


#********************************************HTTP*******************************************

@sio.on('message')
async def print_message(sid, message):
    # print("Socket ID: " , sid)
    # print(message['profileID'])
    # logger.info('MESSAGE IS: ' + message)
    # print(app.logger())
    # await a successful emit of our reversed message
    # back to the client
    await sio.emit('clientMessage', message['msg'], room=sid)


@sio.on('connect')
async def connect(sid, environ):
    logger.info('connect ' + str(sid))
    # print('connect ', sid)
    if environ:
        username = ''
        identifier = ''

        decoded_env_data = urllib.parse.unquote(environ['QUERY_STRING'])
        env_list = str(decoded_env_data).split('&')
        for env in env_list:
            if 'username' in str(env):
                username = str(env).split('username=')[1]
            if 'identifier' in str(env):
                identifier = str(env).split('identifier=')[1]
        # username = env_list[2][9:]
        # identifier = env_list[3][11:]

        # for a in env_list:
        #     print(a)
    # logger.info('connection environment: ' + str(environ))
    # print('connection environment: ' + str())

@sio.on('disconnect')
async def disconnect(sid):
    logger.info('disconnect ' +  str(sid))
    # print('disconnect ', sid)


@sio.on('person_data')
async def pushNotification(sid, data):
    room_name = str(data['personid']) + '_room'
    # await print('CREATED ROOM [' + str(room_name) + ']')

    # await print('PERSON HAVING ID [' + str(data['personid']) + '] AND RESPONSE ID [' + str(data['responseid']) + '] HAS BEEN PARSED')

    try:
        if str(data['personid']) in personDict:
            for x in personDict[str(data['personid' ])]:
                sio.enter_room(x, room_name)

            await sio.emit('profileready', json.dumps(data), room=room_name)
            # await print('PARSED DATA HAS BEEN SENT TO THE CLIENT')

            del personDict[str(data['personid'])]

            if str(data['personid']) in personDict:
                # await print('PERSON ID NOT DELETED FROM DICTIONARY')
                logger.info('person id not deleted from dictionary')
            else:
                # await print('PERSON ID DELETED FROM DICTIONARY')
                logger.info('person id delted from dictionary')
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

    await sio.close_room(room_name)
    await sio.disconnect(sid)



@sio.on('searchperson')
def populateDict(sid, data):

    if str(data['personid']) not in personDict:
        personDict[str(data['personid'])] = [sid]
    else:
        if str(sid) not in personDict[str(data['personid'])]:
            personDict[str(data['personid'])].append(sid)


# **************************************HTTPS***************************************

sioS = socketio.AsyncServer()
appS = web.Application()
sioS.attach(appS)

@sioS.on('message')
async def print_message(sid, message):
    # print("Socket ID: " , sid)
    # print(message['profileID'])
    # logger.info('MESSAGE IS: ' + message)
    # print(app.logger())
    # await a successful emit of our reversed message
    # back to the client
    # print(message)
    await sioS.emit('clientMessage', message['msg'], room=sid)

def ExtractUsername(mixed_username):
    real_username = ''
    if 'Optional' in mixed_username:
        temp_username = str(mixed_username).split('Optional("')[1]
        real_username = temp_username.split('")')[0]

    return real_username


@sioS.on('connect')
async def connect(sid, environ):
    logger.info('STAGING-CONNECT|              SID: ' + str(sid))

    username = ''
    identifier = ''
    environment = ''

    decoded_env_data = urllib.parse.unquote(environ['QUERY_STRING'])
    env_list = str(decoded_env_data).split('&')
    logger.info('STAGING-CONNECT|              ENVIRONMENT VARIABLE: ' + str(environ['QUERY_STRING']))
    logger.info('STAGING-CONNECT|              DECODED DATA: ' + str(decoded_env_data))

    for var in env_list:
        if 'username' in str(var):
            if 'Optional' in var:
                username = ExtractUsername(var[9:])
            else:
                username = var[9:]
            logger.info('CONNECT|              USERNAME: ' + str(username))
        if 'identifier' in str(var):
            identifier = var[11:]
            logger.info('CONNECT|              IDENTIFIER: ' + str(identifier))
        if 'environment' in str(var):
            environment = var[12:]
            logger.info('CONNECT|              ENVIRONMENT: ' + str(environment))

    if environment == 'PROD':
        user_key = username + '|' + identifier
        user_key_exist = 0

        for key, val in personDict.items():
            for k, v in val.items():
                if k == user_key:
                    val[k] = sid
                    user_key_exist = 1
                    logger.info('CONNECT|              USER ALREADY EXIST IN PERSON DICT - ' + str(user_key))

        if user_key_exist == 0:
            logger.info('CONNECT|              USER DOES NOT EXIST IN PERSON DICT - ' + str(user_key))
    else:
        user_identifier_key = username + '|' + identifier
        logger.info('STAGING-CONNECT|              USERNAME: ' + str(username) + ' IDENTIFIER: ' + str(identifier))
        logger.info('STAGING-CONNECT|              USER IDENTIFIER KEY: ' + str(user_identifier_key))

        if user_identifier_key in user_information_object:
            logger.info('STAGING-CONNECT|              USER ALREADY EXISTED IN USER DICTIONARY, UPDATING SID')
            user_information_object[user_identifier_key]['sid'] = sid
        else:
            logger.info('STAGING-CONNECT|              USER NOT FOUND IN USER DICTIONARY, CREATING USER OBJECT')
            user_information_object[user_identifier_key] = {}
            user_information_object[user_identifier_key]['sid'] = sid
            user_information_object[user_identifier_key]['person'] = ''

        if 'sid_' + str(sid) not in sid_information_object:
            logger.info('STAGING-CONNECT|              SID DOES NOT EXIST IN SID DICTIONARY')
        else:
            logger.info('STAGING-CONNECT|              SID ALREADY EXIST IN SID DICTIONARY <<<>>>SID: ' + str(
                sid) + ' USER: ' + str(
                user_identifier_key))
        sid_information_object['sid_' + str(sid)] = user_identifier_key


    # logger.info('connection environment: ' + str(environ))
    # print('connection environment: ' + str())

@sioS.on('disconnect')
async def disconnect(sid):
    logger.info('STAGING-DISCONNECT|           SID: ' + str(sid))

    if 'sid_' + str(sid) in sid_information_object:
        if user_information_object[sid_information_object['sid_' + str(sid)]]['sid'] == sid:
            del user_information_object[sid_information_object['sid_' + str(sid)]]
            logger.info('STAGING-DISCONNECT|           USER HAS SAME CONNECT AND DISCONNECT SID')
        else:
            logger.info('STAGING-DISCONNECT|           USER CONNECT SID DOES NOT MATCH WITH DISCONNECT SID <<<>>>DISCONNECT SID: ' + str(
                    sid) + ' CONNECT SID: ' + str(
                    user_information_object[sid_information_object['sid_' + str(sid)]]) + ' CONNECT USER: ' + str(
                    sid_information_object['sid_' + str(sid)]))

        del sid_information_object[sid]
        logger.info('STAGING-DISCONNECT|           CONNECTED SID REMOVED FROM SID DICTIONARY <<<>>>DISCONNECT SID: ' + str(
            sid) + ' CONNECT SID: ' + str(user_information_object[sid_information_object['sid_' + str(sid)]]))
    else:
        logger.info('STAGING-DISCONNECT|           NO SID TO DISCONNECT <<<>>>SID: ' + str(sid))


@sioS.on('person_data')
async def pushNotification(sid, data):
    logger.info('STAGING-NEW_PERSON_DATA|      PERSON DICTIONARY KEYS: ' + str(person_information_object.keys()))
    if 'person_' + str(data['personid']) in person_information_object:
        room_sids_list = []
        logger.info('STAGING-NEW_PERSON_DATA|      SID: ' + str(sid))
        logger.info('STAGING-NEW_PERSON_DATA|      TIME TAKEN FOR PERSON "' + str(data['personid']) + '": ' + str(
            datetime.datetime.now() - person_information_object['person_' + str(data['personid'])]['start_time']))

        room_name = str(data['personid']) + '_room'
        for user in person_information_object['person_' + str(data['personid'])]['users']:
            if user_information_object[user]['person'] == 'person_' + str(data['personid']):
                logger.info('STAGING-NEW_PERSON_DATA|      USER: ' + str(user) + ' SID: ' + str(user_information_object[user]['sid']))
                sioS.enter_room(user_information_object[user]['sid'], room_name)
                room_sids_list.append(user_information_object[user]['sid'])
        logger.info('STAGING-NEW_PERSON_DATA|      SIDS IN ROOM <' + str(room_name) + '>: ' + str(room_sids_list))

        def CallbackFunction(data):
            logger.info('STAGING-NEW_PERSON_DATA|      MESSAGE RECIEVED BY CLIENT ' + str(data))

        await sioS.emit('profileready', json.dumps(data), room=room_name, callback=CallbackFunction)
        logger.info('STAGING-NEW_PERSON_DATA|      EVENT "profileready" EMITTED TO ROOM "' + str(room_name) + '"  ' + str(
            person_information_object['person_' + str(data['personid'])]['users']))

        del person_information_object['person_' + str(data['personid'])]
        logger.info('STAGING-NEW_PERSON_DATA|      PERSON DELETED FROM PERSON DICTIONARY')
    else:
        logger.info('NEW_PERSON_DATA|      NEW PERSON PROFILE DATA RECEIVED')
        room_name = str(data['personid']) + '_room'
        # await print('CREATED ROOM [' + str(room_name) + ']')
        logger.info('NEW_PERSON_DATA|      CREATED ROOM [' + str(room_name) + ']')

        # await print('PERSON HAVING ID [' + str(data['personid']) + '] AND RESPONSE ID [' + str(data['responseid']) + '] HAS BEEN PARSED')
        logger.info("NEW_PERSON_DATA|      PERSON'S PROFILE HAVING ID [" + str(data['personid']) + "] HAS BEEN PARSED")

        if str(data['personid']) in person_parse_time_log:
            person_parse_time_log[str(data['personid'])]['end_time'] = datetime.datetime.now()
            logger.info('NEW_PERSON_DATA|      TIME TAKEN BY NEW PERSON "' + str(data['personid']) + '" PARSE IS: ' + str(person_parse_time_log[str(data['personid'])]['end_time'] - person_parse_time_log[str(data['personid'])]['start_time']))

        try:
            if str(data['personid']) in personDict:
                for key, val in personDict[str(data['personid'])].items():
                    sioS.enter_room(val, room_name)
                    logger.info('NEW_PERSON_DATA|      SID: ' + str(val))

                await sioS.emit('profileready', json.dumps(data), room=room_name)
                # await print('PARSED DATA HAS BEEN SENT TO THE CLIENT')
                logger.info('NEW_PERSON_DATA|      PARSED DATA HAS BEEN SENT TO REGISTERED SIDS')

                del personDict[str(data['personid'])]

                if str(data['personid']) in personDict:
                    # await print('PERSON ID NOT DELETED FROM DICTIONARY')
                    logger.info('NEW_PERSON_DATA|      PERSON ID NOT DELETED FROM DICTIONARY')
                else:
                    # await print('PERSON ID DELETED FROM DICTIONARY')
                    logger.info('NEW_PERSON_DATA|      PERSON ID DELETED FROM DICTIONARY')
            else:
                logger.info('NEW_PERSON_DATA|      NEW REFRESH DATA RECIEVED FROM PARSER BUT REQUEST NOT RECIEVED FROM CLIENT')
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        await sioS.close_room(room_name)
        await sioS.disconnect(sid)


@sioS.on('searchperson')
def populateDict(sid, data):
    environment = ''
    if 'environment' in data:
        if data['environment'] == 'PROD':
            environment = 'PROD'

    if environment == 'PROD':
        logger.info('SEARCHPERSON|         DATA: ' + str(data))
        logger.info('SEARCHPERSON|         NEW PERSON PROFILE REQUEST RECEIVED')
        logger.info('SEARCHPERSON|         SESSION ID: {' + str(sid) + '} REQUEST FOR PERSON HAVING ID: {' + str(
            data['personid']) + '}')
        logger.info('SEARCHPERSON|         PERSON DICT LENGTH: ' + str(len(personDict)))
        # print('SEARCHPERSON|    SIDS FOR PERSON [' + str(data['personid']) + '] ARE: ' + str(len(personDict[str(data['personid'])])))

        if str(data['personid']) not in person_parse_time_log:
            person_parse_time_log[str(data['personid'])] = {}
            person_parse_time_log[str(data['personid'])]['start_time'] = datetime.datetime.now()

        user_key = str(data['username']) + '|' + str(data['identifier'])

        if str(data['personid']) not in personDict:
            # personDict[str(data['personid'])] = [sid]
            personDict[str(data['personid'])] = {}
            personDict[str(data['personid'])][user_key] = sid
        else:
            # if user_key not in personDict[str(data['personid'])]:
            personDict[str(data['personid'])][user_key] = sid
            # else:
            #     personDict[str(data['personid'])][user_key] = sid


            # await sioS.emit('profileready', json.dumps(testDict), room=sid)
    else:
        logger.info('STAGING-SEARCHPERSON|         SID: ' + str(sid))
        logger.info('STAGING-SEARCHPERSON|         PERSON ID: ' + str(data['personid']))

        if 'Optional' in data['username']:
            data['username'] = ExtractUsername(data['username'])

        user_identifier_key = str(data['username']) + '|' + str(data['identifier'])
        logger.info('STAGING-SEARCHPERSON|         USER ID: ' + str(user_identifier_key))
        if 'person_' + str(data['personid']) in person_information_object:
            logger.info('STAGING-SEARCHPERSON|         UPDATING PERSON OBJECT ALREADY EXIST IN PERSON DICTIONARY')
            person_information_object['person_' + str(data['personid'])]['users'].append(user_identifier_key)
        else:
            logger.info('STAGING-SEARCHPERSON|         CREATING NEW PERSON OBJECT IN PERSON DICTIONARY')
            person_information_object['person_' + str(data['personid'])] = {}
            person_information_object['person_' + str(data['personid'])]['users'] = [user_identifier_key]
            person_information_object['person_' + str(data['personid'])]['start_time'] = datetime.datetime.now()
            person_information_object['person_' + str(data['personid'])]['type'] = 'SEARCH'

        if user_identifier_key in user_information_object:
            logger.info('STAGING-SEARCHPERSON|         UPDATING PERSON IN USER DICTIONARY')
            user_information_object[user_identifier_key]['person'] = 'person_' + str(data['personid'])
        else:
            logger.info('STAGING-SEARCHPERSON|         USER "' + str(
                user_identifier_key) + '" OBJECT NOT CREATED IN USER DICTIONARY <<<>>>')







@sioS.on('refresh_data')
async def pushNotification(sid, data):
    logger.info('STAGING-REFRESH_PERSON_DATA|  PERSON DICTIONARY KEYS: ' + str(person_information_object.keys()))
    if 'person_' + str(data['personid']) in person_information_object:
        room_sids_list = []
        logger.info('STAGING-REFRESH_PERSON_DATA|  SID: ' + str(sid))
        logger.info('STAGING-REFRESH_PERSON_DATA|  TIME TAKEN FOR PERSON "' + str(data['personid']) + '": ' + str(
            datetime.datetime.now() - person_information_object['person_' + str(data['personid'])]['start_time']))

        room_name = str(data['personid']) + '_room'
        for user in person_information_object['person_' + str(data['personid'])]['users']:
            if user_information_object[user]['person'] == 'person_' + str(data['personid']):
                logger.info('STAGING-REFRESH_PERSON_DATA|  USER: ' + str(user) + ' SID: ' + str(user_information_object[user]['sid']))
                sioS.enter_room(user_information_object[user]['sid'], room_name)
                room_sids_list.append(user_information_object[user]['sid'])
        logger.info('STAGING-REFRESH_PERSON_DATA|  SIDS IN ROOM <' + str(room_name) + '>: ' + str(room_sids_list))

        def CallbackFunction(data):
            logger.info('STAGING-REFRESH_PERSON_DATA|  MESSAGE RECIEVED BY CLIENT ' + str(data))

        await sioS.emit('refreshprofileready', json.dumps(data), room=room_name, callback=CallbackFunction)
        logger.info('STAGING-REFRESH_PERSON_DATA|  EVENT "refreshprofileready" EMITTED TO ROOM "' + str(room_name) + '"  ' + str(
                person_information_object['person_' + str(data['personid'])]['users']))

        del person_information_object['person_' + str(data['personid'])]
        logger.info('STAGING-REFRESH_PERSON_DATA|  PERSON DELETED FROM PERSON DICTIONARY')
    else:
        logger.info('REFRESH_PERSON_DATA|    PERSON REFRESH DATA RECEIVED')
        room_name = str(data['personid']) + '_room'
        # await print('CREATED ROOM [' + str(room_name) + ']')
        logger.info('REFRESH_PERSON_DATA|    CREATED ROOM [' + str(room_name) + ']')

        # await print('PERSON HAVING ID [' + str(data['personid']) + '] AND RESPONSE ID [' + str(data['responseid']) + '] HAS BEEN PARSED')
        logger.info("REFRESH_PERSON_DATA|    PERSON HAVING ID [" + str(data['personid']) + "] HAS BEEN PARSED")

        if str(data['personid']) in person_parse_time_log:
            person_parse_time_log[str(data['personid'])]['end_time'] = datetime.datetime.now()
            logger.info('REFRESH_PERSON_DATA|    TIME TAKEN BY REFRESH PERSON "' + str(data['personid']) + '" IS: ' + str(
                person_parse_time_log[str(data['personid'])]['end_time'] - person_parse_time_log[str(data['personid'])][
                    'start_time']))

        try:
            if str(data['personid']) in personDict:
                for key, val in personDict[str(data['personid'])].items():
                    sioS.enter_room(val, room_name)
                    logger.info('REFRESH_PERSON_DATA|    SID: ' + str(val))

                await sioS.emit('refreshprofileready', json.dumps(data), room=room_name)
                # await print('PARSED DATA HAS BEEN SENT TO THE CLIENT')
                logger.info('REFRESH_PERSON_DATA|    PARSED DATA HAS BEEN SENT TO THE CLIENTS')

                del personDict[str(data['personid'])]

                if str(data['personid']) in personDict:
                    # await print('PERSON ID NOT DELETED FROM DICTIONARY')
                    logger.info('REFRESH_PERSON_DATA|    PERSON ID NOT DELETED FROM DICTIONARY')
                else:
                    # await print('PERSON ID DELETED FROM DICTIONARY')
                    logger.info('REFRESH_PERSON_DATA|    PERSON ID DELETED FROM DICTIONARY')
            else:
                logger.info('REFRESH_PERSON_DATA|    PERSON REFRESH DATA RECIEVED FROM PARSER BUT REQUEST NOT RECIEVED FROM CLIENT')
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        await sioS.close_room(room_name)
        await sioS.disconnect(sid)


@sioS.on('refreshperson')
def populateDict(sid, data):
    environment = ''
    if 'environment' in data:
        if data['environment'] == 'PROD':
            environment = 'PROD'

    if environment == 'PROD':
        logger.info('REFRESHPERSON|        DATA: ' + str(data))
        logger.info('REFRESHPERSON|        PERSON REFRESH REQUEST RECEIVED')
        logger.info('REFRESHPERSON|        SESSION ID: {' + str(sid) + '} REQUEST FOR PERSON HAVING ID: {' + str(
            data['personid']) + '}')
        logger.info('REFRESHPERSON|        PERSON DICT LENGTH: ' + str(len(personDict)))

        if str(data['personid']) not in person_parse_time_log:
            person_parse_time_log[str(data['personid'])] = {}
            person_parse_time_log[str(data['personid'])]['start_time'] = datetime.datetime.now()

        user_key = str(data['username']) + '|' + str(data['identifier'])

        if str(data['personid']) not in personDict:
            # personDict[str(data['personid'])] = [sid]
            personDict[str(data['personid'])] = {}
            personDict[str(data['personid'])][user_key] = sid
        else:
            # if str(sid) not in personDict[str(data['personid'])]:
            # personDict[str(data['personid'])].append(sid)
            personDict[str(data['personid'])][user_key] = sid
    else:
        logger.info('STAGING-REFRESHPERSON|        SID: ' + str(sid))
        logger.info('STAGING-REFRESHPERSON|        PERSON ID: ' + str(data['personid']))

        if 'Optional' in data['username']:
            data['username'] = ExtractUsername(data['username'])

        user_identifier_key = str(data['username']) + '|' + str(data['identifier'])
        logger.info('STAGING-REFRESHPERSON|        USER ID: ' + str(user_identifier_key))
        if 'person_' + str(data['personid']) in person_information_object:
            logger.info('STAGING-REFRESHPERSON|        UPDATING PERSON OBJECT ALREADY EXIST IN PERSON DICTIONARY')
            person_information_object['person_' + str(data['personid'])]['users'].append(user_identifier_key)
        else:
            logger.info('STAGING-REFRESHPERSON|        CREATING NEW PERSON OBJECT IN PERSON DICTIONARY')
            person_information_object['person_' + str(data['personid'])] = {}
            person_information_object['person_' + str(data['personid'])]['users'] = [user_identifier_key]
            person_information_object['person_' + str(data['personid'])]['start_time'] = datetime.datetime.now()
            person_information_object['person_' + str(data['personid'])]['type'] = 'REFRESH'

        if user_identifier_key in user_information_object:
            logger.info('STAGING-REFRESHPERSON|        UPDATING PERSON IN USER DICTIONARY')
            user_information_object[user_identifier_key]['person'] = 'person_' + str(data['personid'])
        else:
            logger.info('STAGING-REFRESHPERSON|        USER "' + str(
                user_identifier_key) + '" OBJECT NOT CREATED IN USER DICTIONARY <<<>>>')


def http_socket_server():
    app.router.add_get('/', index)
    web.run_app(app, port=27017)



def https_socket_server():
    # appS.router.add_get('/', index)
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('star_xiq_io.crt', 'xiq_io.key')

    web.run_app(appS, port=27018, ssl_context=ssl_context)

def start_socket():
    try:
        if is_process_running(__file__):
            logger.info('SOCKET IS ALREADY RUNNING')
        else:
            # print('STARTING HTTP SOCKET SERVER')
            # http_socket_server()
            logger.info('STARTING HTTPS SOCKET SERVER')
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