#!/usr/bin/env python2

import os
import os.path
import sys
sys.path.append( os.path.join(os.path.dirname(__file__), '..') )

import ublog.handler
import ublog.initialize

import SocketServer



class MyTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def __init__(self, *args, **kwargs):
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)

    def handle(self):
        # self.request is the TCP socket connected to the client
        data = self.request.recv(65536)

        print "Handling Request from " + str(self.client_address) + " [length=" + str(len(data)) + "]"

        global handler
        response = handler.handle(data, self.request.sendall)

        if (response != None):
            print "Finished Request from " + str(self.client_address) + " [length=" + str(len(response)) + "]"
        else:
            print "Finished Request from " + str(self.client_address)

if __name__ == "__main__":
    HOST, PORT = "", 12696

    # Create the server, binding to (HOST, PORT)
    server = MyTCPServer((HOST, PORT), MyTCPHandler)

    ublog.initialize.initialize()

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        handler = ublog.handler.Handler()
        server.serve_forever()
    except:
        handler.join()
        
