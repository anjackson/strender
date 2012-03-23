#!/usr/bin/env python

import re
import sys
import os
import mimetools
from StringIO import StringIO

linere = re.compile(r'^(\d+)\s+(\w+)\((.+)\)\s+\=\s*([^\n]*)\n$')
send_re = re.compile(r'^(\d+), "(.+)", (\d+), (\w+)$')
#linere = re.compile(r'^(\S+)\s+(\w+)\(.+)\)\s+\=\s*(.*)$')
#
# Does not cope file-descriptor switches:
#fcntl(3, F_DUPFD, 10)             = 10
#close(3)                          = 0
#fcntl(10, F_SETFD, FD_CLOEXEC)    = 0
# but this is not a Killar.


def main():
  openfiles = dict()
  filesread = list()
  with open(sys.argv[1]) as f:
    for line in f:
      mo = linere.match(line)
      #print line,
      if mo is None:
        print "WARN: Unmatched line %r" % line
        continue
      pid, command, args, results = mo.groups()
      if command == 'open':
        fn = args.split(',', 1)[0].strip('"').rstrip('0').rstrip('\\')
	mode = args.split(',', 1)[1].strip()
        fd = int(results.split(' ', 1)[0])
        # Only remember successfully opened files
        if fd != -1:
          openfiles[fd] = fn
        else:
          print "INFO: Failed to open",fn,mode
        #print "OPEN:",fn,":",mode,":",fd
      elif command == 'pipe':
        print "PIPE:",args
      elif command == 'read' or command == 'write':
        #if results != '0':
        fd = int(args.split(',', 1)[0],0) #.lstrip('0').lstrip('x')
        if fd in openfiles:
          if not openfiles[fd] in filesread:
            filesread.append(openfiles[fd])
        else:
	  print "WARN: fd",fd,"not found!"
      elif command == 'mmap2':
        fds = args.split(', ')[4]
        if fds != 'NULL' and fds != '-1':
          fd = int(fds,0)
          if fd in openfiles:
            if not openfiles[fd] in filesread:
              filesread.append(openfiles[fd])
          else:
	    print "WARN: fd",fd,"not found! (mmap2)"
      elif command == 'close':
        #print "CLOSE:",args
        fd = int(args.strip(),0)
        if fd in openfiles:
          del openfiles[fd]
        else:
          print "WARN: Closed unmonitored handle",fd
      elif command == 'connect':
        print "CONNECT:",args
        # sockfd, sockaddr, addrlen
        # sockaddr = {sa_family=AF_FILE, path="/var/run/nscd/socket"}
        # sockaddr = {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("192.168.239.2")}
      elif command == 'send':
        #print "SEND:",args
        if args.find('\\r\\n') > 0:
          hm = send_re.match(args)
          if hm is None:
            print "WARN: Unmatched send command %r" % args
            continue
          sockfd, buf, length, flags = hm.groups()
          buf = buf.replace('\\r\\n','\r\n')
          request_line, headers_alone = buf.split('\r\n', 1)
          m = mimetools.Message(StringIO(headers_alone))
          m.dict['method'], m.dict['path'], m.dict['http-version'] = request_line.split()
          print "----"
          print m['method'], m['path'], m['http-version']
          print m.headers
          print m['Host']+m['path']
          print m.dict
          print "----"
      elif command == 'recv':
        #print "RECV:",args
        pass
      elif command == 'execve':
        print "EXECVE:",args,results
        #pass


      else:
        print "INFO: Unmonitored command: %r" % command

  for item in filesread:
        sha1 = os.popen("sha1sum -b '"+item+"'",'r').read().rstrip().replace(" *"+item,"")
	type = os.popen("file -b --mime-type '"+item+"'",'r').read().rstrip()
	print "<file mode=\"?\" type=\""+type+"\" sha1=\""+sha1+"\">"+item+"</file>"
	#print "SORTED, ",item, ", ",

main()

