import string, ssl, socket, tkinter

class URL: #url example: http://example.org:80/index.html
    #http://browser.engineering:80/examples/example1-simple.html
    def __init__(self, url): # fields: protocol, domain, port, path (i.e path to object..)
        self.protocol , url =  url.split("://",1)
        assert self.protocol in ["http", "https"]
        self.domain , url= url.split(":",1)
        if "/" not in url:
            url=url + "/"
        self.port, self.path = url.split("/",1)
        self.port= int(self.port)
        self.path= "/" + self.path 
        
    def request(self): #use fields genereated in constructor to generate an HTTP request to the server running under the domain..
        #http request contains the method (POST or GET), the path, the version of http being used, all in the same lines
        #subsequent lines contain headers with "header name:value" pairs, each pair in a line.
        request= "GET "+ self.path + " HTTP/1.0" + "\r\n"
        request+= "Host: " + self.domain +"\r\n"
        request+="\r\n" #empty line to signify the end of the headers section
        
        #create a socket
        sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP) #af_inet stands for address family internet
        sock.connect((self.domain, self.port))
        if self.protocol == "https":
            ssl_context = ssl.create_default_context()
            sock= ssl_context.wrap_socket(sock, server_hostname=self.domain) #wrap in the ssl cntx to provide a secure HTTP connection
        print(request)
        sock.send(request.encode("utf8"))
        
        #The response first line holds the protocol, reponse code, response message. Example: "HTTP/1.0 200 OK"
        #Subsequent lines are response headers. After these lines there is the body that contains the HTML code.
        response= sock.makefile(mode="r", encoding="utf8", newline="\r\n") #convert the response to a string
        line= response.readline()
        resp_protocol, resp_code, resp_msg= line.split(" ", 2)
        resp_msg= resp_msg.strip()
        assert resp_msg == "OK"
        
        resp_headers= {} #dic
        while True: 
            line= response.readline()
            if line == "\r\n":
                break
            #for debug - print the resp headers:
            #print(line)
            header, val = line.split(":",1)
            resp_headers[header.casefold()]= val.strip()
        
        assert "transfer-encoding" not in resp_headers
        assert "content-encoding" not in resp_headers #we assert here that there is no compression of data from or to us
        #no what's left to read from response is the response's body
        resp_body= response.read() #read whatever data are left..
        return resp_body

WIDTH, HEIGHT, SCROLL_DELT= 800,600, 50
class Browser:
    def scrolldown_cb(self, e):
        self.scroll+= SCROLL_DELT
        if self.scroll >= HEIGHT: #scroll limit is the screen defined height!   
            self.scroll=HEIGHT
        self.draw() #this is crucial because otherwise the only rendering will be the initial one
    
    def scrollup_cb(self,e):
        self.scroll-=SCROLL_DELT
        if self.scroll >= HEIGHT: #scroll limit is the screen defined height!   
            self.scroll=HEIGHT
        self.draw()
        
    def __init__(self):
        self.window= tkinter.Tk() # get a window context from the OS
        self.canvas= tkinter.Canvas(self.window,width=WIDTH, height=HEIGHT)
        self.canvas.pack() # this line is crucial as it positions the canvas inside the window
        self.window.bind("<Down>",self.scrolldown_cb)
        self.window.bind("<Up>", self.scrollup_cb)
        self.scroll=0

    def layout(self,resp_body):
        self.rendering_list=[]
        in_tags= False
        delt_x, delt_y, pos_x,pos_y= 5,20 , 20,0
        output=""
        for c in resp_body:
                if c == '<' and not in_tags:
                    in_tags=True    
                elif c == '>' and in_tags:
                    in_tags=False
                elif not in_tags:
                    self.canvas.create_text(pos_x,pos_y,text=c)
                    pos_x+=delt_x
                    if (pos_x >= WIDTH):
                        pos_x=20
                        pos_y+= delt_y 
                    output+=c
                    self.rendering_list.append((pos_x,pos_y,c))
        print(output)
        
    def draw(self):
        self.canvas.delete("all") #remove previously rendered text that after scrolling now shouldn't appear anymore!
        for x,y,c in self.rendering_list:
            if y-self.scroll <= HEIGHT and y-self.scroll + 20 > 0:  #prevent rendering unseen chars, thereby requiring less GPU work and faster re-rendering
                self.canvas.create_text(x, y-self.scroll,text=c)
                    
    def show(self,resp_body): #display only the text within the HTML body returned by the request() method
            self.layout(resp_body) # create the positions map for letters to be rendered
            self.draw()
            
            
if __name__ == "__main__":
    import sys
    Browser().show((URL(sys.argv[1]).request()))
    tkinter.mainloop()