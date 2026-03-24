import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
