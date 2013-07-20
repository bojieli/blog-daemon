
# -*- coding:utf-8 -*-

import ublog.request
import ublog.params
import ublog.action

import traceback
import threading
import Queue
import urllib
import urllib2

class Worker(threading.Thread):

    def __init__(self, queue, *args, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)

        if not queue:
            queue = Queue.Queue()
        self.queue = queue
        self.joining = threading.Event()

        self.daemon = False
        self.start()

    def put(self, task):
        self.queue.put(task)

    def run(self):
        while not self.joining.is_set():
            try:
                task = self.queue.get(True, 1)
                try:
                    task()
                except:
                    # should not run to here
                    traceback.print_exc()
            except Queue.Empty:
                continue

            self.queue.task_done()

    def join(self, *args, **kwargs):
        self.joining.set()
        super(Worker, self).join(*args, **kwargs)

class WorkerPool(object):

    def __init__(self, size):
        self.workers = [];
        self.size = size;

        self.queue = Queue.Queue()

        for x in range(size):
            self.workers.append(Worker(self.queue))

    def put(self, task):
        self.queue.put(task)

    def join(self, *args, **kwargs):
        for x in range(self.size):
            self.workers[x].joining.set()
        for x in range(self.size):
            self.workers[x].join()


class Handler(object):

    def __init__(self):
        self._worker_pool_async = WorkerPool(ublog.params.get_param('handler.worker-pool-async.size'))

    def join(self, *args, **kwargs):
        self._worker_pool_async.join(*args, **kwargs)

    def handle(self, data, callback):
        try:
            sd = ublog.request.StructedRequest(data)
            h = ublog.action.get_action(sd.action) # h() won't raise any exception

            if sd.method == 'sync':
                result = h(sd)
                callback(result)
                return result
            elif sd.method == 'async':
                def t():
                    h(sd)
                self._worker_pool_async.put(t)
            elif sd.method == 'async-callback':
                def t():
                    result = h(sd)
                    try:
                        data = urllib.urlencode( {'request':sd.request_data, 'response':result} )
                        req = urllib2.urlopen( ublog.params.get_param('async.post.url'), data )
                        req.close()
                    except:
                        traceback.print_exc()
                self._worker_pool_async.put(t)
        except:
            traceback.print_exc()

