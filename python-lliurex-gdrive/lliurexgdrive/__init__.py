#!/usr/bin/env python
import glob
import ConfigParser
import os
import json
import subprocess
import shutil
import urllib2
import datetime
import platform
import time
import tempfile


DEBUG=False
GDRIVE_CONFIG_DIR=os.path.expanduser("~/.gdfuse/")
LLIUREX_CONFIG_FILE_64='/usr/share/lliurex-gdrive/llx-data/config_64'
LLIUREX_CONFIG_FILE_32='/usr/share/lliurex-gdrive/llx-data/config_32'
GDRIVE_ENDSESSION_SERVICE='/usr/share/lliurex-gdrive/llx-data/llxgdrive-endsession.service'
FIREFOX_BROWSER_BIN='/usr/share/lliurex-gdrive/llx-data/firefox-browser'
CHROME_BROWSER_BIN='/usr/share/lliurex-gdrive/llx-data/chrome-browser'
	


class LliurexGoogleDriveManager(object):

	def __init__(self):

		super(LliurexGoogleDriveManager, self).__init__()

		self.config_dir=os.path.expanduser("~/.config/lliurex-google-drive-profiles/")
		self.config_file=self.config_dir+"configProfiles"
		self.systemd_user=os.path.expanduser("~/.config/systemd/user/")
		self.bin_dir=os.path.expanduser("~/.local/bin")
		self.chromium_path=self.bin_dir+"/chromium-browser"
		self.mount_cmd="google-drive-ocamlfuse -label %s %s"
		self.clean_cache="google-drive-ocamlfuse -cc -label %s"

		self.gdrive_path=[]
		self.read_gdrive_folder=False
		self.browser_changed=False


		self.read_conf()
		

	#def init

	def create_conf(self):

		if not os.path.exists(self.config_dir):
			os.makedirs(self.config_dir)

		var={}
		# var["default"]={}
		# var["default"]["email"]=""
		# var["default"]["mountpoint"]=""
		# var["default"]["automount"]=""

		f=open(self.config_file,"w")
		data=unicode(json.dumps(var,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")

		f.write(data)
		f.close()

		msg_log="Creating conf..."
		self.dprint(msg_log)
		

	#def create_conf
	
	def read_conf(self):
		
		if not os.path.exists(self.config_file):
			self.create_conf()
		
		log_msg="------------------------------------------\n"+"LLIUREX-GDRIVE STARTING AT: " + datetime.datetime.today().strftime("%d/%m/%y %H:%M:%S") +"\n------------------------------------------"
		self.log(log_msg)
		msg_log="Init: Reading conf..."
		self.dprint(msg_log)
		self.log(msg_log)
			
		f=open(self.config_file)
		try:
			self.profiles_config=json.load(f)
		except:
			self.profiles_config={}
		f.close()
		
	#def read_conf
	
	def check_config(self,profile):
		
		path=GDRIVE_CONFIG_DIR+profile+"/state"
		profile=profile.encode("utf-8")

		if os.path.exists(path):
			f=open(path)
			line=f.readline()
			f.close()
		
			if "1970-" in line:
				msg_log="Check config: '%s' not configured"%profile
				self.dprint(msg_log)
				self.log(msg_log)
				return False
			
			msg_log="Check config: '%s' yet configured"%profile
			self.dprint(msg_log)
			self.log(msg_log)
			return True

		else:
			msg_log="Check config: '%s' not yet create"%profile
			self.dprint(msg_log)
			self.log(msg_log)
			return False

		
	#def check_config

	def check_google_connection(self):

		try:
			req=urllib2.Request("http://google.com")
			res=urllib2.urlopen(req)
			return True
		except:
			msg_log="Check connection: Cannot connect to google.com"
			self.dprint(msg_log)
			self.log(msg_log)
			return False

	#def check_google_connection		
	
	def mount_drive(self,profile,mountpoint):
		
		#profile=profile.encode("utf-8")
		#mountpoint=mountpoint.encode("utf-8")
				
		try:
			
			if os.path.exists(GDRIVE_CONFIG_DIR+profile):
				check= self.check_config(profile)
				if check:
					#if profile in self.profiles_config:
						#mount_point=os.path.expanduser(self.profiles_config[profile]["mountpoint"])
						#if type(mount_point)==type(u""):
						if mountpoint!="":
							self.dprint("Mounting '%s'..."%profile)
							if not os.path.exists(mountpoint):
								try:
									os.makedirs(mountpoint)
								except:
									msg_log="Mount drive: Unable to create '%s' mount destination"%mountpoint.encode("utf-8")
									self.dprint(msg_log)
									self.log(msg_log)
									return {"result":False,"code":1}
								

							if os.access(mountpoint,os.W_OK):
								#os.system(self.mount_cmd%(profile,mountpoint))
								cmd=self.mount_cmd%(profile,mountpoint)
								p=subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
								poutput,perror=p.communicate()
								if len(perror)==0:
									msg_log="Mount drive: drive '%s' mounted sucessfully:"%mountpoint.encode("utf-8")
									self.dprint(msg_log)
									self.log(msg_log)
									return {"result":True,"code":0}

								else:
									msg_log="Mount drive: Error mount '%s': %s"%(mountpoint.encode("utf-8"),str(perror))
									self.code=2
									self.dprint(msg_log)
									self.log(msg_log)
																	
							else:
								msg_log="Mount drive: Mount drive: '%s' mount destination is not owned by user"%mountpoint.encode("utf-8")
								self.code=3
								self.dprint(msg_log)
								self.log(msg_log)
								
						else:
							msg_log="Mount drive: No mount point indicated"
							self.code=4
							self.dprint(msg_log)
							self.log(msg_log)
				else:
					msg_log="Mount drive: '%s' mount point not configured"%profile.encode("utf-8")
					self.code=5
					self.dprint(msg_log)
					self.log(msg_log)
			else:
				msg_log="Mount drive: '%s' GDrive profile path does not exist"%profile.encode("utf-8")
				self.code=6
				self.dprint(msg_log)
				self.log(msg_log)
				
		except Exception as e:

			raise e
			
			
		return {"result":False,"code":self.code} 

	#def mount_drive
	
	def mount_drives(self):
		
		if self.check_google_connection():
			for profile in self.profiles_config:
				automount=self.profiles_config[profile]["automount"]
				if automount:
					mountpoint=self.profiles_config[profile]["mountpoint"]
					#profile=profile.encode("utf-8")
					#mountpoint=mountpoint.encode("utf-8")
					self.mount_drive(profile,mountpoint)
						
		
	#def mount_drives

	def dprint(self,msg):
		
		if DEBUG:
			print("[LGDM] %s"%msg)
			
	#def dprint
	
	
	def save_profiles(self,info):
		
		self.profiles_config=info
		
		f=open(self.config_file,"w")
		#data=json.dumps(info,indent=4,encoding="utf-8",ensure_ascii=False)
		data=unicode(json.dumps(info,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
		f.write(data)
		f.close()

	#def save_profiles	

	def check_mountpoint_status(self,mountpoint,arg=None):

		mountpoint_size=""
		mountpoint_used=""
		mountpoint_available=""
		mountpoint_per=""
		error=False
		tmp=[]
		connect=True
		
		if arg!=None:
			connect=self.check_google_connection()
		
		if connect:
			command='df -h | grep "google-drive-ocamlfuse" | grep ' +mountpoint+'$' 
				
			p=subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			poutput,perror=p.communicate()

			if len(poutput)>0:
				status=True

				for item in poutput.split(" "):
					if len(item)>1:
						tmp.append(item)

				mountpoint_size=tmp[1]
				mountpoint_used=tmp[2]
				mountpoint_available=tmp[3]
				mountpoint_per=tmp[4]

			else:
				if len(perror)>0:
					error=True
					status=False
					self.dismount_mountpoint(mountpoint)
				else:	
					status=False
		else:
			status=None
					
		return {"status":status,"size":mountpoint_size,"used":mountpoint_used,"available":mountpoint_available,"used%":mountpoint_per,"error":error}		
		
	#def check_mountpoint_status	
		
	def check_profile_info(self,profile,mountpoint,edition,root_folder,gdrive_folder):
	
		'''
			code=0: Form OK
			code=10: Profile empty
			code=11: Profile with blanck spaces
			code=12: Profile duplicate
			
		'''	
		#profile=profile.decode("utf-8")
		###############NUEVO PUNTO ##########""
		if not edition:

			
			# type(unicode) ==> encode("utf-8")
			# type(str) ==> decode("utf-8")
			

			if profile=="":
				return {"result":False,"code":10}

			if ' ' in profile:
				return {"result":False,"code":11}
	
			else:
				for item in self.profiles_config:
					if profile==item:
						return {"result":False,"code":12}

		else:

			if root_folder:
				if len(self.gdrive_path)>1:
					if gdrive_folder=="":
						return {"result":False,"code":17}
					else:
						cont=0
						for item in self.gdrive_path:
							if type(item) is str:
								item=item.decode("utf-8")
							if item == gdrive_folder:
								cont=cont+1
						if cont==0:
							return {"result":False,"code":19}	

				else:
					if self.read_gdrive_folder==True:
						return {"result":False,"code":20}
					else:
						tmp_mountpoint=tempfile.mkdtemp('_Gdrive')
						cmd=self.clean_cache%profile.encode("utf-8")
						os.system(cmd)
						self.mount_drive(profile,tmp_mountpoint)
						status=self.check_mountpoint_status(tmp_mountpoint)

						if not status['error']:
							self.dismount_mountpoint(tmp_mountpoint,profile)
							error=False
						else:
							error=True

						try:
							shutil.rmtree(tmp_mountpoint)

						except Exception as e:
							pass

						if error:
							return {"result":False,"code":19}				

		'''
		for item in self.profiles_config:
			if profile!=item:
				if mountpoint==self.profiles_config[item]["mountpoint"]:
					return {"result":False,"code":4}


		if not os.access(mountpoint,os.W_OK):
			return {"result":False,"code":6}
			

		if os.listdir(mountpoint):
			if not edition:
				return {"result":False,"code":5}	
			else:
				if mountpoint != self.profiles_config[profile]["mountpoint"]:
					return {"result":False,"code":5}					


		return {"result":True,"code":0}				 				
			
		'''
		return self.check_mountpoint_folder(profile,mountpoint,edition)

	
	#def check_profile_info


	def check_mountpoint_folder(self,profile,mountpoint,edition):

		'''
			code=13: Mountpoint duplicate
			code=14: Mountpoint not empty
			code=15: Mountpoint not owned by user
		'''

		for item in self.profiles_config:
			if profile!=item:
				if mountpoint==self.profiles_config[item]["mountpoint"]:
					return {"result":False,"code":13}

		if not os.access(mountpoint,os.W_OK):
			return {"result":False,"code":15}
			
		if ' ' in mountpoint:
			return {"result":False,"code":16}	

		if os.listdir(mountpoint):
			if not edition:
				return {"result":False,"code":14}	
			else:
				if mountpoint != self.profiles_config[profile]["mountpoint"]:
					return {"result":False,"code":14}					

		
		return {"result":True,"code":0}		

	#def check_mountpoint_folder	
	

	def create_profile(self,profile):

		#profile=unicode(profile).encode("utf-8")
		path=GDRIVE_CONFIG_DIR+profile+"/config"

		if not self.check_config(profile):
			os.system("google-drive-ocamlfuse -label %s"%unicode(profile).encode("utf-8"))
			msg_log=("'%s' profile has been create")%profile.encode("utf-8")
			self.log(msg_log)
			self.dprint(msg_log)

			if os.path.exists(GDRIVE_CONFIG_DIR+profile):
				if platform.architecture()[0]=='64bit':
					shutil.copy(LLIUREX_CONFIG_FILE_64,path )
				else:
					shutil.copy(LLIUREX_CONFIG_FILE_32,path )
			
			self.remove_chromium_tmpbin()

		return True
				
			
	#def create_profile

	def create_mountpoint(self,info,profile):

		mountpoint=info[profile]["mountpoint"]

		result=self.mount_drive(profile,mountpoint)
		
		if result["result"]:
			self.manage_systemd_unit("create")
			self.save_profiles(info)
						
		else:
			if profile !="":
				if os.path.exists(GDRIVE_CONFIG_DIR+profile):
					shutil.rmtree(os.path.join(GDRIVE_CONFIG_DIR+profile))
					self.dprint("'%s' profile has been delete"%profile)
			
		return result

	#def create_mountpoint	

	def dismount_mountpoint(self,mountpoint,profile=None):

		if profile != None:
			cmd='fusermount -u -z ' + mountpoint + ";"+self.clean_cache%profile
		else:
			cmd='fusermount -u -z ' + mountpoint	

		p=subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		poutput,perror=p.communicate()

		mountpoint=mountpoint.encode("utf-8")
		if len(perror)>0:
			msg_log="Dismount mountpoint: Error dismounted '%s': '%s'"%(mountpoint,str(perror))
			self.dprint(msg_log)
			self.log(msg_log)
			result=False
			code=7
		else:
			msg_log="Dismount mountpoint:'%s' mountpoint has been dismounted"%mountpoint
			self.dprint(msg_log)
			self.log(msg_log)
			result=True
			code=0					

		return {"result":result,"code":code}

	#def dismount_mountpoint	

	def delete_profile(self,info,profile):

		result={}
		dismount={}
		dismount["result"]=True
		dismount["code"]=0

		connect=self.check_google_connection()
		#profile=str(profile)
		#if connect:
		mountpoint=self.profiles_config[profile]["mountpoint"]
			
		if os.path.exists(GDRIVE_CONFIG_DIR+profile):
			is_mountpoint_mounted=self.check_mountpoint_status(mountpoint,True)

			if is_mountpoint_mounted["status"]==None:
				result['result']=False
				result['code']=8
			else:
				if is_mountpoint_mounted["status"]:	
					dismount=self.dismount_mountpoint(mountpoint,profile)

				if dismount["result"]:
					if profile!="":
						shutil.rmtree(os.path.join(GDRIVE_CONFIG_DIR+profile))
						msg_log="Delete profile: '%s' profile has been delete"%profile.encode("utf-8")
						self.log(msg_log)
						self.dprint(msg_log)
					self.save_profiles(info)
				
				result=dismount	
				

		else:
			self.save_profiles(info)
			msg_log="Delete profile: '%s' GDrive profile path does not exist"%profile.encode("utf-8")
			self.log(msg_log)
			self.dprint(msg_log)
			result['result']=True
			result['code']=0
		
		self.manage_systemd_unit("delete",info)
		return result
		
			
	#def delete_profile	

	
	def edit_profile(self,info,profile):

		result={}
		result["result"]=True
		result["code"]=0

		change_config=False

		old_mountpoint=self.profiles_config[profile]["mountpoint"]
		old_automount=self.profiles_config[profile]["automount"]
		new_mountpoint=info[profile]["mountpoint"]
		new_automount=info[profile]["automount"]
		
		try:
			old_root_folder=self.profiles_config[profile]["root_folder"]
			old_gdrive_folder=self.profiles_config[profile]["gdrive_folder"]
		except Exception as e:
			old_root_folder=""
			old_gdrive_folder=""	

		new_root_folder=info[profile]["root_folder"]
		new_gdrive_folder=info[profile]["gdrive_folder"]


		if new_root_folder != old_root_folder:
			change_config=True

		else:
			if 	old_gdrive_folder !=new_gdrive_folder:
				change_config=True
		
		status=self.check_mountpoint_status(old_mountpoint)
			
		if old_mountpoint!=new_mountpoint:
					
			if status["status"]:
				result=self.dismount_mountpoint(old_mountpoint,profile)
									
				if result["result"]:
					if change_config:
						self.change_config_file(profile,new_gdrive_folder)
					result=self.mount_drive(profile,new_mountpoint)
			else:
				if change_config:
					self.change_config_file(profile,new_gdrive_folder)			

		else:
			if change_config:
				if status["status"]:
					result=self.dismount_mountpoint(old_mountpoint,profile)
					if result["result"]:
						self.change_config_file(profile,new_gdrive_folder)
						result=self.mount_drive(profile,new_mountpoint)
				else:
					self.change_config_file(profile,new_gdrive_folder)
		

				
		if result["result"]:
			self.save_profiles(info)
			msg_log="Edit profile: '%s' profile has been edited"%profile.encode("utf-8")
			self.log(msg_log)
			self.dprint(msg_log)

		return {"result":result["result"],"code":result["code"]}		

	#def edit_profile			

	def sync_profile(self,profile,mountpoint,current_status):
		
		result={}
		status=self.check_mountpoint_status(mountpoint,True)
		token_mount=profile + "__MountToken"
		token_mount_path=os.path.join(self.config_dir,token_mount)
		token_dismount=profile + "__DismountToken"
		token_dismount_path=os.path.join(self.config_dir,token_dismount)

	
		if status["status"]==None:
			result['result']=False
			result['code']=8
			
		else:
			if current_status!=None and status['status']==current_status:
				if status['status']:
					result=self.dismount_mountpoint(mountpoint,profile)
					f=open(token_dismount_path,'w')
					f.close()
					os.remove(token_dismount_path)
				else:
					if not status['error']:
						result=self.mount_drive(profile,mountpoint)
						f=open(token_mount_path,'w')
						f.close()
						os.remove(token_mount_path)
					else:
						result['result']=False
						result['code']=18
						return result,status
			
			else:
				result['result']=True
				result['code']=9
				
			status=self.check_mountpoint_status(mountpoint)	
			if status['error']:
				result['result']=False
				result['code']=18
		
		return result,status	

		#result["result"]:result["result"]
		#result["code"]:result["code"]
		#return {"result":result["result"],"code":result["code"]}	

	#def_sync_profile	

	def read_mountpoint_directory(self,profile):

		result={}
		result['result']=True
		path_orig=GDRIVE_CONFIG_DIR+profile+"/config"
		path_tmp=GDRIVE_CONFIG_DIR+profile+"/config_tmp"
		create_tmp=False
		copy_config=False
		directory=[]
		
		
		mountpoint=self.profiles_config[profile.decode("utf-8")]["mountpoint"]

			
		
		try:
			root_folder=self.profiles_config[profile.decode("utf-8")]["root_folder"]
		except Exception as e:
			root_folder=False
		

		status=self.check_mountpoint_status(mountpoint)

		if status["status"]:
			if root_folder:	
				create_tmp=True
				copy_config=True

		else:
			create_tmp=True
			if root_folder:
				copy_config=True

		
		if copy_config:
			if os.path.exists(GDRIVE_CONFIG_DIR+profile):
				if os.path.exists(path_orig):
					os.rename(path_orig,path_tmp)
				if platform.architecture()[0]=='64bit':
					shutil.copy(LLIUREX_CONFIG_FILE_64,path_orig )
				else:
					shutil.copy(LLIUREX_CONFIG_FILE_32,path_orig )

		if create_tmp:
									
			if status['status']:
				cmd=self.clean_cache%profile
				os.system(cmd)
			
			tmp_mountpoint=tempfile.mkdtemp('_Gdrive')					
			result=self.mount_drive(profile.decode("utf-8"),tmp_mountpoint)
				
			mountpoint=tmp_mountpoint

		
		if result['result']:

			self.gdrive_path=[]
			self.read_gdrive_folder=True

			for base,dirs,file in os.walk(mountpoint):
				if 'Trash' not in base:
					if 'shared' not in base:
						if base !=mountpoint:
							directory.append(base)

			directory=sorted(directory)
			
			self.gdrive_path.append('')

			for item in directory:			
				path=os.path.relpath(item,mountpoint)
				self.gdrive_path.append(path)


			if create_tmp:
			
				if copy_config:	
					os.rename(path_tmp,path_orig)
					
				result=self.dismount_mountpoint(mountpoint,profile)

				if result['result']:

					shutil.rmtree(mountpoint)
			
		else:
			if copy_config:	
				os.rename(path_tmp,path_orig)

		cmd=self.clean_cache%profile
		os.system(cmd)		
		
		return self.gdrive_path	

	#def read_mountpoint_directory	


	def change_config_file(self,profile,gdrive_folder):

			
		file=GDRIVE_CONFIG_DIR+profile+"/config"


		old_config=open(file,'r')
		params=[]
		cont=0
		for line in old_config:
			if 'root_folder' in line:
				line='root_folder='+'/'+gdrive_folder.encode("utf-8")+'\n'	
				cont=cont+1
			params.append(line)
				
		
		if cont==0:
			line='root_folder='+'\n'
			params.append(line) 		
	    	
		old_config.close()
		
		new_config=open(file,'w')

		for item in params:
			new_config.write(item)		
 
		new_config.close()

	#def change_config_file	

	def is_chromium_favourite_browser(self):

		result=False

		if os.system("xdg-mime query default x-scheme-handler/https | grep chromium 1>/dev/null")==0:
			result=True			
			msg_log="Detected chromium as favourite browser. Unable to add profile"
			self.log(msg_log)			

		return result

	#def is_chromium_favourite_browser	

	
	def can_change_browser(self):

		result=False

		if not os.path.exists(self.chromium_path):
			self.installed_browser_detect()
			if len(self.installed_browsers)>0:
				result=True

		return result		

	#def can_change_browser	

	def installed_browser_detect(self):	

		self.installed_browsers=[]

		if os.system('dpkg -l firefox | grep firefox | grep "^i[i]" 1>/dev/null')==0:
			self.installed_browsers.append("firefox")

		if os.system('dpkg -l google-chrome-stable | grep google-chrome-stable | grep "^i[i]" 1>/dev/null')==0:
			self.installed_browsers.append("google-chrome-stable")


	#def installed_browser_detec		


	def change_default_browser(self):
	

		if not os.path.exists(self.bin_dir):
			os.makedirs(self.bin_dir)		

	
		if "firefox" in self.installed_browsers:
			shutil.copy(FIREFOX_BROWSER_BIN,self.chromium_path)
		else:
			if "google-chrome-stable" in self.installed_browsers:
				shutil.copy(CHROME_BROWSER_BIN,self.chromium_path)

		self.browser_changed=True

		try:
			cmd='chmod +x '+self.chromium_path
			os.system(cmd)
		except:
			pass

	#def change_default_browser			


	def remove_chromium_tmpbin(self):


		if self.browser_changed:
			if os.path.exists(self.chromium_path):
				os.remove(self.chromium_path)
				self.browser_changed=False

		return
		
	#def remove_chromium_tmpbin		

	def manage_systemd_unit(self,action,info=None):

		if action=="create":
			if not os.path.exists(self.systemd_user):
				os.makedirs(self.systemd_user)
				shutil.copy(GDRIVE_ENDSESSION_SERVICE,self.systemd_user)
			else:	
				if not os.path.exists(os.path.join(self.systemd_user,"lxgdrive-endsession.service")):	
					shutil.copy(GDRIVE_ENDSESSION_SERVICE,self.systemd_user)
			os.system("systemctl --user enable llxgdrive-endsession.service || true")
			os.system("systemctl --user start llxgdrive-endsession.service || true")
		else:
			if os.path.exists(self.systemd_user):
				if info!=None and len(info)==0:
					os.system("systemctl --user stop llxgdrive-endsession.service || true")
					os.system("systemctl --user disable llxgdrive-endsession.service || true")


	def log(self,msg):
		
		log_file=self.config_dir+"lliurex-gdrive.log"

		f=open(log_file,"a+")
		f.write(msg + '\n')
		f.close()	

	#def log		 

if __name__=="__main__":

	llxgd=LliurexGoogleDriveManager()
	llxgd.mount_drives()
	
	
	
	#llxgd.save_profiles(llxgd.var)
	









