from gevent import monkey
monkey.patch_all()

from dotenv import load_dotenv
load_dotenv()
from app import create_app, db, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000, debug=False)