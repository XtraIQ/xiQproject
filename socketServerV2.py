import os
import sys, traceback

from aiohttp import web
import socketio
import datetime
import logging
import json
import ssl
import urllib.parse
import time

# VARIABLES
user_information_object = {}
person_information_object = {}
sid_information_object = {}

logging.basicConfig(filename='socketLogV2.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Socket server initialization
sioS = socketio.AsyncServer()
appS = web.Application()
sioS.attach(appS)

# Test Event
@sioS.on('message')
async def print_message(sid, message):
    logging.info(message)
    await sioS.emit('clientMessage', message['msg'], room=sid)


@sioS.on('connect')
async def connect(sid, environ):
    logging.info('CONNECT|              SID: ' + str(sid))

    username = ''
    identifier = ''
    decoded_env_data = urllib.parse.unquote(environ['QUERY_STRING'])
    env_list = str(decoded_env_data).split('&')
    logging.info('CONNECT|              ENVIRONMENT VARIABLE: ' + str(environ['QUERY_STRING']))
    logging.info('CONNECT|              DECODED DATA: ' + str(decoded_env_data))

    for var in env_list:
        if 'username' in str(var):
            username = var[9:]
        if 'identifier' in str(var):
            identifier = var[11:]

    user_identifier_key = username + '|' + identifier
    logging.info('CONNECT|              USERNAME: ' + str(username) + ' IDENTIFIER: ' + str(identifier))
    logging.info('CONNECT|              USER IDENTIFIER KEY: ' + str(user_identifier_key))


    if user_identifier_key in user_information_object:
        logging.info('CONNECT|              USER ALREADY EXISTED IN USER DICTIONARY, UPDATING SID')
        user_information_object[user_identifier_key]['sid'] = sid
    else:
        logging.info('CONNECT|              USER NOT FOUND IN USER DICTIONARY, CREATING USER OBJECT')
        user_information_object[user_identifier_key] = {}
        user_information_object[user_identifier_key]['sid'] = sid
        user_information_object[user_identifier_key]['person'] = ''


    if 'sid_' + str(sid) not in sid_information_object:
        logging.info('CONNECT|              SID DOES NOT EXIST IN SID DICTIONARY')
    else:
        logging.info('CONNECT|              SID ALREADY EXIST IN SID DICTIONARY <<<>>>SID: ' + str(sid) + ' USER: ' + str(user_identifier_key))
    sid_information_object['sid_' + str(sid)] = user_identifier_key


@sioS.on('disconnect')
async def disconnect(sid):
    logging.info('DISCONNECT|           SID: ' + str(sid))

    if 'sid_' + str(sid) in sid_information_object:
        if user_information_object[sid_information_object['sid_' + str(sid)]]['sid'] == sid:
            del user_information_object[sid_information_object['sid_' + str(sid)]]
            logging.info('DISCONNECT|           USER HAS SAME CONNECT AND DISCONNECT SID')
        else:
            logging.info('DISCONNECT|           USER CONNECT SID DOES NOT MATCH WITH DISCONNECT SID <<<>>>DISCONNECT SID: ' + str(sid) + ' CONNECT SID: ' + str(user_information_object[sid_information_object['sid_' + str(sid)]]) + ' CONNECT USER: ' + str(sid_information_object['sid_' + str(sid)]))

        del sid_information_object[sid]
        logging.info('DISCONNECT|           CONNECTED SID REMOVED FROM SID DICTIONARY <<<>>>DISCONNECT SID: ' + str(sid) + ' CONNECT SID: ' + str(user_information_object[sid_information_object['sid_' + str(sid)]]))
    else:
        logging.info('DISCONNECT|           NO SID TO DISCONNECT <<<>>>SID: ' + str(sid))


@sioS.on('searchperson')
def populateDict(sid, data):
    logging.info('SEARCHPERSON|         SID: ' + str(sid))

    user_identifier_key = str(data['username']) + '|' + str(data['identifier'])
    if data['personid'] in person_information_object:
        logging.info('SEARCHPERSON|         UPDATING PERSON OBJECT ALREADY EXIST IN PERSON DICTIONARY')
        person_information_object[data['personid']]['users'].append(user_identifier_key)
    else:
        logging.info('SEARCHPERSON|         CREATING NEW PERSON OBJECT IN PERSON DICTIONARY')
        person_information_object[data['personid']] = {}
        person_information_object[data['personid']]['users'] = [user_identifier_key]
        person_information_object[data['personid']]['start_time'] = datetime.datetime.now()
        person_information_object[data['personid']]['type'] = 'SEARCH'

    if user_identifier_key in user_information_object:
        logging.info('SEARCHPERSON|         UPDATING PERSON IN USER DICTIONARY')
        user_information_object[user_identifier_key]['person'] = data['personid']
    else:
        logging.info('SEARCHPERSON|         USER "' + str(user_identifier_key) + '" OBJECT NOT CREATED IN USER DICTIONARY <<<>>>')


@sioS.on('person_data')
async def pushNotification(sid, data):
    logging.info('NEW_PERSON_DATA|      SID: ' + str(sid))
    logging.info('NEW_PERSON_DATA|      TIME TAKEN FOR PERSON "' + str(data['personid']) + '": ' + str(datetime.datetime.now() - person_information_object[data['personid']]['start_time']))

    room_name = str(data['personid']) + '_room'
    for user in person_information_object[data['personid']]['users']:
        sioS.enter_room(user, room_name)

    await sioS.emit('profileready', json.dumps(data), room=room_name)
    logging.info('NEW_PERSON_DATA|      EVENT "profileready" EMITTED TO ROOM "' + str(room_name) + '"  ' + str(person_information_object[data['personid']]['users']))

    del person_information_object[data['personid']]
    logging.info('NEW_PERSON_DATA|      PERSON DELETED FROM PERSON DICTIONARY')


@sioS.on('refreshperson')
def populateDict(sid, data):
    logging.info('REFRESHPERSON|        SID: ' + str(sid))

    user_identifier_key = str(data['username']) + '|' + str(data['identifier'])
    if data['personid'] in person_information_object:
        logging.info('REFRESHPERSON|        UPDATING PERSON OBJECT ALREADY EXIST IN PERSON DICTIONARY')
        person_information_object[data['personid']]['users'].append(user_identifier_key)
    else:
        logging.info('REFRESHPERSON|        CREATING NEW PERSON OBJECT IN PERSON DICTIONARY')
        person_information_object[data['personid']] = {}
        person_information_object[data['personid']]['users'] = [user_identifier_key]
        person_information_object[data['personid']]['start_time'] = datetime.datetime.now()
        person_information_object[data['personid']]['type'] = 'REFRESH'

    if user_identifier_key in user_information_object:
        logging.info('REFRESHPERSON|        UPDATING PERSON IN USER DICTIONARY')
        user_information_object[user_identifier_key]['person'] = data['personid']
    else:
        logging.info('REFRESHPERSON|        USER "' + str(user_identifier_key) + '" OBJECT NOT CREATED IN USER DICTIONARY <<<>>>')


@sioS.on('refresh_data')
async def pushNotification(sid, data):
    logging.info('REFRESH_PERSON_DATA|  SID: ' + str(sid))
    logging.info('REFRESH_PERSON_DATA|  TIME TAKEN FOR PERSON "' + str(data['personid']) + '": ' + str(datetime.datetime.now() - person_information_object[data['personid']]['start_time']))

    room_name = str(data['personid']) + '_room'
    for user in person_information_object[data['personid']]['users']:
        sioS.enter_room(user, room_name)

    await sioS.emit('refreshprofileready', json.dumps(data), room=room_name)
    logging.info('REFRESH_PERSON_DATA|  EVENT "refreshprofileready" EMITTED TO ROOM "' + str(room_name) + '"  ' + str(person_information_object[data['personid']]['users']))

    del person_information_object[data['personid']]
    logging.info('REFRESH_PERSON_DATA|  PERSON DELETED FROM PERSON DICTIONARY')

# --------------------------------------------------------------------------------------------------------------------

def is_process_running(file_name):
    is_running = False
    count = 0
    for line in os.popen("ps -aux"):
        if '/bin/sh' not in line and 'sudo' in line and file_name in line:
            count += 1
    if count > 1:
        is_running = True
    return is_running


def https_socket_server():
    # appS.router.add_get('/', index)
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('star_xiq_io.crt', 'xiq_io.key')

    web.run_app(appS, port=27020, ssl_context=ssl_context)

def start_socket():
    try:
        if is_process_running(__file__):
            logging.info('SOCKET IS ALREADY RUNNING')
        else:
            logging.info('STARTING HTTPS SOCKET SERVER')
            https_socket_server()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))


start_socket()