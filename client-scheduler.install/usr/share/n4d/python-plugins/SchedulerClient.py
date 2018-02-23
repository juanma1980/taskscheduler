#!/usr/bin/env python
###
#
###

# -*- coding: utf-8 -*-
import os,socket
import threading
import time
from  datetime import date
import xmlrpclib as xmlrpc

class SchedulerClient():
	def __init__(self):
		self.cron_dir='/etc/cron.d'
		self.task_prefix='remote-' #Temp workaround->Must be declared on a n4d var
		self.cron_dir='/etc/cron.d'
		self.count=0
		self.dbg=0

	def startup(self,options):
		t=threading.Thread(target=self._main_thread)
		t.daemon=True
		t.start()

	def _debug(self,msg):
		if self.dbg:
			print(str(msg))

	def _main_thread(self):
		objects["VariablesManager"].register_trigger("SCHEDULED_TASKS","SchedulerClient",self.process_tasks)
		tries=10
		for x in range (0,tries):
			self.scheduler_var=objects["VariablesManager"].get_variable("SCHEDULED_TASKS")
			if self.scheduler_var!=self.count:
				self.count=self.scheduler_var
				self.process_tasks()
				break
			else:
				time.sleep(1)

	def process_tasks(self,data=None):
		self._debug("Scheduling tasks")
		today=date.today()
		prefixes={'remote':True,'local':False}
		tasks={}
		try:
			socket.gethostbyname('server')
		except:
				prefixes={'local':False}
		for prefix,sw_remote in prefixes.iteritems():
			if prefix=='remote':
				n4d=xmlrpc.ServerProxy("https://server:9779")
				tasks=n4d.get_remote_tasks("","SchedulerServer")['data'].copy()
			else:
				n4d=xmlrpc.ServerProxy("https://localhost:9779")
				tasks=n4d.get_local_tasks("","SchedulerServer")['data'].copy()

			#Delete files
			for f in os.listdir(self.cron_dir):
				if f.startswith(prefix):
					os.remove(self.cron_dir+'/'+f)
			#Create the cron files
			task_names={}
			for name in tasks.keys():
				for serial in tasks[name].keys():
					sw_pass=False
					if 'autoremove' in tasks[name][serial]:
						if type(tasks[name][serial]['m'])==type(int):
							if tasks[name][serial]['m']<today.month:
								sw_pass=True
						if sw_pass==False:
							if type(tasks[name][serial]['d'])==type(int):
								if tasks[name][serial]['d']<today.day:
									sw_pass=True
					if sw_pass:
						continue
					self._debug("Scheduling %s"%name)
					fname=name.replace(' ','_')
					task_names[fname]=tasks[name][serial].copy()
					self._write_crontab_for_task(task_names,prefix)

	#def process_tasks

	def _write_crontab_for_task(self,ftask,prefix):
		cron_array=[]
		for task_name,task_data in ftask.iteritems():
			self._debug("Writing data %s"%task_name)
			fname=self.cron_dir+'/'+prefix+task_name.replace(' ','_')
			cron_task=("%s %s %s %s %s root %s"%(task_data['m'],task_data['h'],task_data['dom'],\
							task_data['mon'],task_data['dow'],u""+task_data['cmd']))
			cron_array.append(cron_task)
			if task_data:
				if os.path.isfile(fname):
					mode='a'
				else:
					mode='w'
				with open(fname,mode) as data:
					if mode=='w':
						data.write('#Scheduler tasks\n')
						data.write('SHELL=/bin/bash\n')
						data.write('PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n')
						data.write('DISPLAY=:0\n')
						data.write('XAUTHORITY=/var/run/lightdm/root/:0\n')
						if 'https_proxy' in os.environ.keys():
							https_proxy=os.environ['https_proxy']
							data.write('https_proxy=%s\n'%https_proxy)
						if 'http_proxy' in os.environ.keys():
							http_proxy=os.environ['http_proxy']
							data.write('http_proxy=%s\n'%http_proxy)
					for cron_line in cron_array:
						data.write(cron_line.encode('utf8')+"\n")
	#def _write_crontab_for_task

