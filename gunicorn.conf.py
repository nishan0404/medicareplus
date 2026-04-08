from gevent import monkey
monkey.patch_all()

workers = 1
worker_class = "gevent"
bind = "0.0.0.0:10000"
