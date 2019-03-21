from socketIO_client import SocketIO

def on_bbb_response(*args):
    print('on_bbb_response', args)

with SocketIO('http://34.212.33.247', 27017) as socketIO:
    socketIO.emit('pushMessage', {'data': 'I am socketIO_Client'})