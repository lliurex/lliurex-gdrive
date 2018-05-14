
#!/usr/bin/env python

#import LliurexGoogleDriveManager
import lliurexgdrive
import LliurexGdrive
import ProfileBox




class Core:
	
	singleton=None
	DEBUG=True
	
	@classmethod
	def get_core(self):
		
		if Core.singleton==None:
			Core.singleton=Core()
			Core.singleton.init()

		return Core.singleton
		
	
	def __init__(self,args=None):
		
		self.dprint("Init...")
		
	#def __init__
	
	def init(self):
		
		self.dprint("Creating Config...")
		self.LliurexGoogleDriveManager=lliurexgdrive.LliurexGoogleDriveManager()
		self.dprint("Creating ProfileBox...")
		self.profile_box=ProfileBox.ProfileBox()
			
		
		
		# Main window must be the last one
		self.dprint("Creating LliurexGdrive...")
		self.lgd=LliurexGdrive.LliurexGdrive()
		
		self.lgd.load_gui()
		self.lgd.start_gui()
		
		
	#def init
	
	
	
	def dprint(self,msg):
		
		if Core.DEBUG:
			
			print("[CORE] %s"%msg)
	
	#def  dprint
