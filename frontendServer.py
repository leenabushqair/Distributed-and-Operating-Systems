from flask import Flask
import requests
import datetime
import threading
from flask_caching import Cache
import time
import socket

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

catalog_urls = {'A': 'http://localhost:5001', 'B': 'http://localhost:5002'}
order_urls = {'A': 'http://localhost:5003', 'B': 'http://localhost:5004'}


log_lock = threading.Lock()  # lock for calculating performance metrics
shared_flag_lock = threading.Lock()  # lock for shared data structure for heartbeat messages (replicas_alive)
shared_buffer_lock = threading.Lock()  # lock for shared data structure for heartbeat messages (buffer)

catalog_replicas_alive = {'A': True, 'B': True}
order_replicas_alive = {'A': True, 'B': True}

last_order_server = 'A'
last_catalog_server = 'A'


@app.route('/searchh/<args>', methods=["GET"])
@cache.memoize()
def search(args):

    global last_catalog_server
    # note the starting time of the request
    request_start = datetime.datetime.now()
    #request_id = request.values['request_id']
    request_success = False
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    while not request_success:
        # form the query url using load balancing (round robin)
        shared_flag_lock.acquire()
        if catalog_replicas_alive[last_catalog_server]:
            query_url = catalog_urls[last_catalog_server] + '/search/' + str(args)
        else:
            # global last_catalog_server
            last_catalog_server = 'A' if last_catalog_server == 'B' else 'B'
            query_url = catalog_urls[last_catalog_server] + '/search/' + str(args)
        last_catalog_server = 'A' if last_catalog_server == 'B' else 'B'
        shared_flag_lock.release()

        # get the results
        try:
            query_result = requests.get(url=query_url, data={})

            # note the request end time and calculate the difference
            request_end = datetime.datetime.now()
            request_time = request_end - request_start

            # acquire a lock on the file and write the time
            log_lock.acquire()
            #file = open(log_file, "a+")


            #file.write("{} \t\t\t {}\n".format(request_id, (request_time.microseconds / 1000)))

            #file.close()
            log_lock.release()

            # return the results
            request_success = True
            result = query_result.json()
            result['front_end_host/ip'] = hostname + '/' + ip
            return result
        except Exception:
            time.sleep(3)
            pass


@app.route('/lookupp/<args>', methods=["GET"])
@cache.memoize()
def lookup(args):

    global last_catalog_server
    # note the starting time of the request
    request_start = datetime.datetime.now()
    #request_id = request.values['request_id']
    request_success = False
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    while not request_success:
        # form the query url using load balancing (round robin)
        shared_flag_lock.acquire()
        if catalog_replicas_alive[last_catalog_server]:
            query_url = catalog_urls[last_catalog_server] + '/lookup/' + str(args)
        else:
            # global last_catalog_server
            last_catalog_server = 'A' if last_catalog_server == 'B' else 'B'
            query_url = catalog_urls[last_catalog_server] + '/lookup/' + str(args)
        last_catalog_server = 'A' if last_catalog_server == 'B' else 'B'
        shared_flag_lock.release()

        # get the result
        try:
            query_result = requests.get(url=query_url, data={})

            # note the request end time and calculate the difference
            request_end = datetime.datetime.now()
            request_time = request_end - request_start

            # acquire a lock on the file and write the time
            log_lock.acquire()
            log_lock.release()

            # return the results
            request_success = True
            result = query_result.json()
            result['front_end_host/ip'] = hostname + '/' + ip
            return result
        except Exception:
            time.sleep(3)
            pass


@app.route('/buy/<args>', methods=["GET"])
def buy(args):

    global last_order_server
    # note the starting time of the request
    request_start = datetime.datetime.now()
    #request_id = request.values['request_id']
    request_success = False
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    # invalidate cache
    cache.delete_memoized(lookup, args)

    while not request_success:
        # form the query url using load balancing (round robin)
        shared_flag_lock.acquire()
        if order_replicas_alive[last_order_server]:
            query_url = order_urls[last_order_server] + '/buy/' + str(args)
        else:
            # global last_order_server
            last_order_server = 'A' if last_order_server == 'B' else 'B'
            query_url = order_urls[last_order_server] + '/buy/' + str(args)
        last_order_server = 'A' if last_order_server == 'B' else 'B'
        shared_flag_lock.release()

        # get the result
        try:
            query_result = requests.get(url=query_url, data={})
            if query_result.json()['result'] == 'Server Error':
                pass
            else:
                # note the request end time and calculate the difference
                request_end = datetime.datetime.now()
                request_time = request_end - request_start

                # acquire a lock on the file and write the time
                log_lock.acquire()

                log_lock.release()

                # return the results
                request_success = True
                result = query_result.json()
                result['front_end_host/ip'] = hostname + '/' + ip
                return result
        except Exception:
            time.sleep(3)
            pass


@app.route('/', methods=['GET'])
def start():
    return "it's working!"


if __name__ == '__main__':

    app.run(host='localhost', port=34600)