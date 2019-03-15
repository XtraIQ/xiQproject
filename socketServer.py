from aiohttp import web
import socketio
import datetime

# creates a new Async Socket IO Server
sio = socketio.AsyncServer()
# Creates a new Aiohttp Web Application
app = web.Application()
# print(app)
# Binds our Socket.IO server to our Web App
# instance
sio.attach(app)

async def background_task():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        await sio.sleep(10)
        await sio.emit('serverMessage', 'Current Time: ' + str(datetime.datetime.now()))

# we can define aiohttp endpoints just as we normally
# would with no change
async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

# If we wanted to create a new websocket endpoint,
# use this decorator, passing in the name of the
# event we wish to listen out for
@sio.on('message')
async def print_message(sid, message):
    # print("Socket ID: " , sid)
    # print(message['profileID'])
    # logger.info('MESSAGE IS: ' + message)
    # print(app.logger())
    # await a successful emit of our reversed message
    # back to the client
    await sio.emit('clientMessage', message['msg'], room=sid)

# @sio.on('connect')
# def serverMessage():
#     print('connected')

    # while True:
    #     time.sleep(5)
    #     await sio.emit('serverMessage', 'Current Time: ' + str(datetime.datetime.now()))


# We bind our aiohttp endpoint to our app
# router
app.router.add_get('/', index)

# We kick off our server
if __name__ == '__main__':
    sio.start_background_task(background_task)
    web.run_app(app, port=8983)