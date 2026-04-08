from gevent import monkey
monkey.patch_all()

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.DEBUG)

try:
    from app import create_app, socketio
    app = create_app()
    print("✅ App created successfully")
except Exception as e:
    import traceback
    print("❌ App creation failed:")
    traceback.print_exc()
    raise

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000, debug=False)
