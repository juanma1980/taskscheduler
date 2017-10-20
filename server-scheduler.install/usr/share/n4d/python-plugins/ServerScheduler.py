#!/usr/bin/env python
######
#Scheduler library for Lliurex
#Add to N4D the scheduled tasks
#This class reads the json file with the scheduled tasks and
#distributes the info among the clients

import os
import json

class ServerScheduler():
	def __init__(self):
		self.dbg=1
		self.taskDir="/etc/scheduler/tasks.d"
		self.schedTasksDir=self.taskDir+"/scheduled"
		self.remote_tasks_dir=self.schedTasksDir+"/remote"
		self.crondir="/etc/cron.d"
		self.cronPrefix="scheduler-"
		self.status=0
		self.errormsg=''
		sw_readErr=False
	#def __init__

	def _debug(self,msg):
		if (self.dbg):
			print("Scheduler: %s" % msg)
	#def _debug

	def get_tasks(self):
		scheduled_tasks=[]
		wrkfiles=self._get_wrkfiles()
		for wrkfile in wrkfiles:
			content=self._read_tasks_file(wrkfile)
			if not self.readErr:
				scheduled_tasks.append(content)
		self._debug("Tasks loaded")
		self._debug(str(scheduled_tasks))
		return(scheduled_tasks)
	#def get_tasks

	def _get_wrkfiles(self):
		if not os.path.isdir(self.remote_tasks_dir):
			os.makedirs(self.remote_tasks_dir)

		wrkfiles=[]
		for f in os.listdir(self.remote_tasks_dir):
			wrkfiles.append(self.remote_tasks_dir+'/'+f)
		return wrkfiles

	def _read_tasks_file(self,wrkfile):
		self._debug("Opening %s" % wrkfile)
		self.readErr=0
		tasks={}
		if os.path.isfile(wrkfile):
			try:
				tasks=json.loads(open(wrkfile).read())
			except :
				self.errormsg=(("unable to open %s") % wrkfile)
				self._debug(self.errormsg)
				self.readErr=1
		return(tasks)
	#def _read_tasks_file
	
	def remove_task(self,task_name,task_serial,task_cmd):
		self._debug("Removing task from system")
		sw_del=False
		wrkfile=self.remote_tasks_dir+'/'+task_name
		wrkfile=wrkfile.replace(' ','_')
		task=self._read_tasks_file(wrkfile)
		if task_name in task.keys():
			if task_serial in task[task_name].keys():
				del task[task_name][task_serial]
				self._debug("Task deleted")
				sw_del=True

		if sw_del:
			task=self._serialize_task(task)
			with open(wrkfile,'w') as json_data:
				json.dump(task,json_data,indent=4)
			self._register_cron_update()
		return True

	def _serialize_task(self,task):
		serial_task={}
		for name,task_data in task.items():
			cont=0
			serial_task[name]={}
			for serial,data in task_data.items():
				serial_task[name].update({cont+1:data})
				cont+=1
		return(serial_task)

	def write_tasks(self,tasks):
		self._debug("Writing remote task info")
		task_name=list(tasks.keys())[0]
		task_serial=list(tasks[task_name].keys())[0]
		self._debug(tasks)
		serialized_task={}
		sched_tasks={}
		if not os.path.isdir(self.remote_tasks_dir):
			os.makedirs(self.remote_tasks_dir)

		wrkfile=self.remote_tasks_dir+'/'+task_name
		wrkfile=wrkfile.replace(' ','_')
		if os.path.isfile(wrkfile):
			sched_tasks=json.loads(open(wrkfile).read())
			serial=len(sched_tasks[task_name])
			if task_serial in sched_tasks[task_name].keys():
				self._debug("Modify item %s" % serial)
				sched_tasks[task_name][task_serial]=tasks[task_name][task_serial]
				#Modify
			else:
				#Add
				self._debug("Add item %s" % serial)
				serialized_data={}
				serialized_data[serial+1]=tasks[task_name][task_serial]
				sched_tasks[task_name].update(serialized_data)
		else:
			self._debug("Add new item 1 to %s"%wrkfile)
			tasks[task_name]={"1":tasks[task_name]["0"]}
			sched_tasks=tasks.copy()

		try:
			with open(wrkfile,'w') as json_data:
				json.dump(sched_tasks,json_data,indent=4)
		except Exception as e:
			print(e)
		self._register_cron_update()
		self._debug("%s updated" % task_name)
	#def write_tasks

	def _register_cron_update(self):
		objects["VariableManager"].set_variable("SCHEDULED_TASK",1)
