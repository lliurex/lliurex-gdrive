#!/usr/bin/env python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, GdkPixbuf, Gdk, Gio, GObject,GLib



import signal
import os
import json
import sys
import Core


signal.signal(signal.SIGINT, signal.SIG_DFL)

import gettext
gettext.textdomain('lliurex-gdrive')
_ = gettext.gettext

RSRC="/usr/share/lliurex-gdrive/"
#CONFIG_DIR=os.path.expanduser("~/.config/lliurex-google-drive-profiles/config")
CSS_FILE="/usr/share/lliurex-gdrive/lliurex-gdrive.css"
LOCK_INDICATOR="~/.config/lliurex-google-drive-profiles/lgdIndicator.lock"
LOCK_GUI="~/.config/lliurex-google-drive-profiles/lgdGUI.lock"
DISABLE_INDICATOR="~/.config/lliurex-google-drive-profiles/disableIndicator"


class LliurexGdrive:
	
	def __init__(self):

		self.islgd_running()
		self.core=Core.Core.get_core()
		self.disable_indicator=os.path.expanduser(DISABLE_INDICATOR)
		self.lock_gui=os.path.expanduser(LOCK_GUI)
		self.lock_indicator=os.path.expanduser(LOCK_INDICATOR)
		
		self.createLockToken()

	#def init

	
	def islgd_running(self):

		if os.path.exists(LOCK_GUI):
			dialog = Gtk.MessageDialog(None,0,Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Lliurex GDrive")
			dialog.format_secondary_text(_("Lliurex GDrive is now running."))
			dialog.run()
			sys.exit(1)

	#def islgd_running		
	

	def createLockToken(self):

		if not os.path.exists(self.lock_gui):
			f=open(self.lock_gui,'w')
			f.close

	#def createLockToken	
	
	def load_gui(self):
		
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-gdrive')
		ui_path=RSRC + "rsrc/lliurex-gdrive.ui"
		builder.add_from_file(ui_path)
		
		
		self.main_window=builder.get_object("main_window")
		self.main_window.set_title("Lliurex GDrive")
		self.main_box=builder.get_object("main_box")
		self.help_button=builder.get_object("help_button")
		self.check_window=builder.get_object("check_window")
		self.check_pbar=builder.get_object("check_pbar")
		self.check_plabel=builder.get_object("check_plabel")
		self.check_window.set_transient_for(self.main_window)


		self.indicator_label=builder.get_object("indicator_label")
		self.indicator_switch=builder.get_object("indicator_switch")
		if os.path.exists(self.disable_indicator):
			self.indicator_switch.set_active(False)
				

		self.profile_box=self.core.profile_box
		self.main_box.add(self.profile_box)
		
		
		# Add components
			
		self.set_css_info()
		self.connect_signals()
		self.load_info()
		
		self.main_window.show_all()
		
	#def load_gui


		
	def load_info(self):

		self.load_profiles=self.core.LliurexGoogleDriveManager.profiles_config.copy()
				
		self.profile_box.load_info(self.load_profiles)

	#def load_info	
		
	def set_css_info(self):
		
		
		self.style_provider=Gtk.CssProvider()
		f=Gio.File.new_for_path(CSS_FILE)
		self.style_provider.load_from_file(f)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		self.main_window.set_name("WINDOW")
		self.indicator_label.set_name("OPTION_LABEL")
		self.check_plabel.set_name("MSG_LABEL")

	#def remove_chromium_tmpbin			
			
	def connect_signals(self):
		
		self.main_window.connect("destroy",self.quit)
		self.help_button.connect("clicked",self.help_clicked)
	
		
	#def connect_signals

	def launch_indicator(self):


		#self.lockpath=R=os.path(LOCK_INDICATOR)
		if len(self.load_profiles):
			if not os.path.exists(self.lock_indicator):
				cmd="/usr/bin/lliurexGdriveIndicator" + "&"
				os.system(cmd)

	#def launch_indicator
	
	def config_indicator(self):

		if self.show_indicator:
			if os.path.exists(self.disable_indicator):
				os.remove(self.disable_indicator)	
		else:
			if not os.path.exists(self.disable_indicator):
				f=open(self.disable_indicator,'w')
				f.close

	#def config_indicator			

	def cleanLockToken(self):

		if os.path.exists(self.lock_gui):
			os.remove(self.lock_gui)

	#def cleanIndicatorLock  		

	def quit(self,widget):

		self.show_indicator=self.indicator_switch.get_state()
		self.config_indicator()

		if self.show_indicator:
			self.launch_indicator()

		self.core.LliurexGoogleDriveManager.remove_chromium_tmpbin()
		self.cleanLockToken()
		Gtk.main_quit()	
	
	#def quit


	def help_clicked(self,widget):

		lang=os.environ["LANG"]

		if 'ca_ES' in lang:
			cmd='xdg-open http://wiki.lliurex.net/tiki-index.php?page=LliureX%2BGDrive_va'
		else:
			cmd='xdg-open http://wiki.lliurex.net/tiki-index.php?page=LliureX+Gdrive'

		os.system(cmd)

	#def help_clicked
		
	
	def start_gui(self):
		
		GObject.threads_init()
		Gtk.main()
		
	#def start_gui

	
	

	
#class LliurexRemoteInstaller


if __name__=="__main__":
	
	lgd=LliurexGdrive()
	lgd.start_gui()
	
