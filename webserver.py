import _socket
import http.server
import socketserver
from http import HTTPStatus
import time
from multiprocessing import Process


class Handler(http.server.SimpleHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        print('get request')
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        print(self.sentence)
        self.wfile.write(self.sentence[0].encode('utf-8'))
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        print("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        
        print(post_data.decode())
        self.sentence[0] = post_data.decode()

        print(self.sentence)
        self._set_response()
        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

h = Handler
h.sentence = ['no sentence']
httpd = socketserver.TCPServer(('', 8000), h)
httpd.serve_forever()

time.sleep(10)
sentence = 'world'
print('changed sentence')