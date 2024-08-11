import socketio

sio = socketio.AsyncServer(async_mode='asgi')


@sio.event
def connect(sid, environ, auth):
    print('connect ', sid)
    sio.emit("hello world")


@sio.event
def disconnect(sid):
    print('disconnect ', sid)


@sio.event(namespace='/')
async def queue(sid, data):
    print('message ', data)


app = socketio.ASGIApp(sio)
