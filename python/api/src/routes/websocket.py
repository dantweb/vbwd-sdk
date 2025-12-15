from flask_socketio import join_room, leave_room


def register_socket_handlers(socketio):
    """Register WebSocket event handlers."""

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('subscribe')
    def handle_subscribe(data):
        """Subscribe to updates for a specific email."""
        email = data.get('email')
        if email:
            room = f'user_{email}'
            join_room(room)
            print(f'Client joined room: {room}')

    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """Unsubscribe from updates."""
        email = data.get('email')
        if email:
            room = f'user_{email}'
            leave_room(room)
            print(f'Client left room: {room}')
