#!/usr/bin/env python


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, GdkPixbuf, Gdk, Gio, GObject,GLib

import copy
import gettext
import Core

import Dialog
import time
import threading
import multiprocessing
import sys
import os
import psutil

import gettext
gettext.textdomain('lliurex-gdrive')
_ = gettext.gettext



RSRC="/usr/share/lliurex-gdrive/"
CSS_FILE="/usr/share/lliurex-gdrive/lliurex-gdrive.css"
PROFILE_IMAGE=RSRC+"rsrc/profile.svg"
FOLDER_IMAGE=RSRC+"rsrc/folder.svg"
MOUNT_ON_IMAGE=RSRC+"rsrc/mount_on.svg"
MOUNT_OFF_IMAGE=RSRC+"rsrc/mount_off.svg"
EDIT_IMAGE=RSRC+"rsrc/edit.svg"
DELETE_IMAGE=RSRC+"rsrc/trash.svg"
MAX_RETRY_INTENTS=1200


class ProfileBox(Gtk.VBox):
	
	def __init__(self):
		
		Gtk.VBox.__init__(self)
		
		self.core=Core.Core.get_core()
		
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-gdrive')
		ui_path=RSRC + "/rsrc/lliurex-gdrive.ui"
		builder.add_from_file(ui_path)

		self.stack = Gtk.Stack()
		self.stack.set_transition_duration(1000)
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

		self.main_box=builder.get_object("profile_data_box")
		self.profiles_list_label=builder.get_object("profiles_list_label")
		self.profile_list_box=builder.get_object("profile_list_box")
		self.profile_list_vp=builder.get_object("profile_list_viewport")
		self.msg_label=builder.get_object("msg_label")

		image = Gtk.Image()
		image.set_from_stock(Gtk.STOCK_ADD,Gtk.IconSize.MENU)
		
		self.add_new_profile_button=builder.get_object("add_new_profile_button")
		self.add_new_profile_button.set_image(image)
		self.new_profile_window=builder.get_object("new_profile_window")
		self.data=builder.get_object("data")
		self.edit_profile_box=builder.get_object("edit_profile_box")
		self.profile_label=builder.get_object("profile_label")
		self.profile_entry=builder.get_object("profile_entry")
		self.email_label=builder.get_object("email_label")
		self.email_entry=builder.get_object("email_entry")
		self.mountpoint_label=builder.get_object("mountpoint_label")
		self.mountpoint_entry=builder.get_object("mountpoint_entry")
		self.automount_label=builder.get_object("automount_label")
		self.automount_entry=builder.get_object("automount_entry")
		self.root_folder_param_label=builder.get_object("root_folder_param_label")
		self.root_folder_param_entry=builder.get_object("root_folder_param_entry")
		self.gdrive_folder_label=builder.get_object("gdrive_folder_label")
		self.gdrive_folder_entry=builder.get_object("gdrive_folder_entry")
		self.gdrive_folder_entry.set_width_chars(30)
		self.gdrive_folder_entry.set_max_width_chars(30)
		self.gdrive_folder_entry.set_xalign(-1)
		self.gdrive_folder_entry.set_ellipsize(Pango.EllipsizeMode.START)
		self.edit_gdrive_folder_button=builder.get_object("edit_gdrive_folder_button")

		self.profile_msg=builder.get_object("profile_msg")
		self.profile_pbar=builder.get_object("profile_pbar")
		self.accept_add_profile_button=builder.get_object("accept_add_profile_button")
		self.cancel_add_profile_button=builder.get_object("cancel_add_profile_button")

		self.gdrive_combobox_box=builder.get_object("gdrive_combobox_box")
		self.gdrive_combobox_label=builder.get_object("gdrive_combobox_label")
		self.gdrive_combobox=builder.get_object("gdrive_combobox")
		self.return_combobox_button=builder.get_object("return_combobox_button")
		
					
		self.syncfolders_model=Gtk.ListStore(str)
		rende=Gtk.CellRendererText()
		rende.set_property("ellipsize-set",True)
		rende.set_property("ellipsize",Pango.EllipsizeMode.START)
		rende.set_property("width-chars",65)
		rende.set_property("max-width-chars",65)
		self.gdrive_combobox.set_model(self.syncfolders_model)
		self.gdrive_combobox.pack_start(rende,False)
		self.gdrive_combobox.add_attribute(rende,"text",0)
		
		self.gdrive_combobox.set_active(0)
			
		self.pack_start(self.main_box,True,True,0)
		self.connect_signals()
		self.set_css_info()
		self.stack.show()
		self.stack.add_titled(self.edit_profile_box,"edit","Edit")
		self.stack.add_titled(self.gdrive_combobox_box,"folder", "Folder")
		self.data.pack_start(self.stack,True,False,5)

		self.data.pack_start(self.edit_profile_box,True,True,0)


		self.current_status={}
		self.edition=False
		self.root_folder=False
		self.read=False
		self.profile_pbar.hide()

		self.init_threads()
		self.check_initial_connection()

				
	#def __init__

	def init_threads(self):

		self.create_profile_t=multiprocessing.Process(target=self.create_profile)
		self.create_mountpoint_t=threading.Thread(target=self.create_mountpoint)
		self.edit_profile_t=threading.Thread(target=self.edit_profile)
		self.check_connection_t=threading.Thread(target=self.check_connection)
		self.read_mountpoint_t=threading.Thread(target=self.read_mountpoint)
		self.check_form_t=threading.Thread(target=self.check_form)
		
		
		self.create_profile_t.daemon=True
		self.create_mountpoint_t.daemon=True
		self.edit_profile_t.daemon=True
		self.check_connection_t.daemon=True
		self.read_mountpoint_t.daemon=True
		self.check_form_t.daemon=True

		self.create_mountpoint_t.done=False
		self.edit_profile_t.done=False
		self.read_mountpoint_t.done=False
		self.check_form_t.done=False

		self.create_profile_t.launched=False
		self.create_mountpoint_t.launched=False
		self.edit_profile_t.launched=False
		self.read_mountpoint_t.launched=False
		self.check_form_t.launched=False
		
		
		GObject.threads_init()

	#def init_threads	

	def set_css_info(self):
		
		self.style_provider=Gtk.CssProvider()

		f=Gio.File.new_for_path(CSS_FILE)
		self.style_provider.load_from_file(f)

		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		self.profiles_list_label.set_name("OPTION_LABEL")
		self.profile_label.set_name("OPTION_LABEL")
		self.email_label.set_name("OPTION_LABEL")
		self.mountpoint_label.set_name("OPTION_LABEL")
		self.automount_label.set_name("OPTION_LABEL")
		self.msg_label.set_name("MSG_LABEL")
		self.profile_msg.set_name("MSG_LABEL")
		self.root_folder_param_label.set_name("OPTION_LABEL")
		self.gdrive_combobox_label.set_name("OPTION_LABEL")
		self.gdrive_folder_label.set_name("OPTION_LABEL")
		self.gdrive_folder_entry.set_name("GDRIVE_FOLDER")
		
			
	#def set-css_info
	
		
	def connect_signals(self):

		self.add_new_profile_button.connect("clicked",self.add_new_profile_button_clicked)
		self.accept_add_profile_button.connect("clicked",self.accept_add_profile_clicked)
		self.cancel_add_profile_button.connect("clicked",self.cancel_add_profile_clicked)
		self.new_profile_window.connect("delete_event",self.hide_window)
		self.mountpoint_entry.connect("file-set",self.check_mountpoint_folder)
		self.gdrive_combobox.connect("changed",self.on_gdrive_combobox_changed)
		self.root_folder_param_entry.connect("notify::active",self.root_folder_clicked)
		self.return_combobox_button.connect("clicked",self.return_combobox_button_clicked)
		self.edit_gdrive_folder_button.connect("clicked",self.edit_gdrive_folder_button_clicked)


	#def connect_signals


	def check_initial_connection(self):
		
		self.initial_connection=self.core.LliurexGoogleDriveManager.check_google_connection()
		
		return

	#def check_initial_connection	
	
	def load_info(self,info):
		
		self.profiles_info=info
		for item in self.profiles_info:
			profile=item
			email=self.profiles_info[item]["email"]
			mountpoint=self.profiles_info[item]["mountpoint"]
			self.new_profile_button(profile,email,mountpoint)
			
	
	#def load_info()		

	def hide_window(self,widget,event):
		
		widget.hide()
		return True

	#def hide_window	

	def init_profile_dialog_button(self):

		self.accept_add_profile_button.show()
		image = Gtk.Image()
		image.set_from_stock(Gtk.STOCK_CANCEL,Gtk.IconSize.MENU)
		self.cancel_add_profile_button.set_image(image)
		self.cancel_add_profile_button.set_label(_("Cancel"))
		self.cancel_add_profile_button.show()

	#def init_profile_dialog_button	

	def disable_entry_profile_dialog(self):

		self.profile_entry.set_sensitive(False)
		self.email_entry.set_sensitive(False)
		self.mountpoint_entry.set_sensitive(False)
		self.automount_entry.set_sensitive(False)
		self.root_folder_param_entry.set_sensitive(False)
		self.edit_gdrive_folder_button.set_sensitive(False)

	#def disable_entry_profile_dialog
	
	def enable_entry_profile_dialog(self):

		if not self.edition:
			
			self.new_profile_window.set_title(_("Create new profile"))
			self.profile_entry.set_sensitive(True)
			self.profile_entry.grab_focus()
			self.email_entry.set_sensitive(True)
			self.root_folder_param_entry.hide()
			self.root_folder_param_label.hide()
			self.gdrive_folder_label.hide()
			self.gdrive_folder_entry.hide()
			self.edit_gdrive_folder_button.hide()	

		else:
			self.new_profile_window	.set_title(_("Edit profile"))
			self.profile_entry.set_sensitive(False)
			self.email_entry.set_sensitive(False)
			self.root_folder_param_label.show()
			self.root_folder_param_entry.show()
			self.root_folder_param_entry.set_sensitive(True)

			if self.root_folder:
				self.edit_gdrive_folder_button.show()
				self.edit_gdrive_folder_button.set_sensitive(True)
			else:
				if self.read:
					self.edit_gdrive_folder_button.show()	
					self.edit_gdrive_folder_button.set_sensitive(True)
			
		self.mountpoint_entry.set_sensitive(True)
		self.automount_entry.set_sensitive(True)	

	#def enable_entry_profile_dialog	

	def change_cancel_button(self):
		
		image = Gtk.Image()
		image.set_from_stock(Gtk.STOCK_CLOSE,Gtk.IconSize.MENU)
		self.cancel_add_profile_button.set_image(image)
		self.cancel_add_profile_button.set_label(_("Close"))	
		self.cancel_add_profile_button.show()	

	#def change_cancel_button	

	def add_new_profile_button_clicked(self,widget):

		self.edition=False
		self.msg_label.set_text("")
		is_chromium_favourite=self.core.LliurexGoogleDriveManager.is_chromium_favourite_browser()
		changed_browser=True

		if is_chromium_favourite:
			can_change=self.core.LliurexGoogleDriveManager.can_change_browser()
			if can_change:
				dialog = Gtk.MessageDialog(None,0,Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO, "Lliurex GDrive")
				dialog.format_secondary_text(_("To add a profile it is necessary to change Chromium as default browser by another (Firefox or Chrome).\nThe change will be made automatically. Once the profile is added Chromium it will be the favorite browser again.\nDo you wish to continue?"))
				response=dialog.run()
				dialog.destroy()
				if response==Gtk.ResponseType.YES:
					self.core.LliurexGoogleDriveManager.change_default_browser()
				else:
					changed_browser=False
			else:
				changed_browser=False		

		if changed_browser:				
			self.core.lgd.check_plabel.set_text(_("Checking connection to google..."))
			self.core.lgd.check_window.show()
			self.init_threads()
			self.check_connection_t.start()
			GLib.timeout_add(100,self.pulsate_add_connection)

		else:	
			msg_error=self.get_msg(21)
			self.msg_label.set_name("MSG_ERROR_LABEL")
			self.msg_label.set_text(msg_error)

	#def add_new_profile_button_clicked	
	
	def pulsate_add_connection(self):
		
		if self.check_connection_t.is_alive():
				self.core.lgd.check_pbar.pulse()
				return True

		else:
			self.core.lgd.check_window.hide()
			self.enable_entry_profile_dialog()
			#ENCODING TO UNICODE
			if self.connection:
				self.profile_entry.set_text("")
				self.email_entry.set_text("")
				self.mountpoint_entry.set_filename(os.environ["HOME"])
				self.automount_entry.set_active(False)
				self.profile_msg.set_text("")
		

				self.init_threads()
				
				self.msg_label.set_text("")
				self.profile_msg.hide()
				self.profile_pbar.hide()
				self.init_profile_dialog_button()
				self.new_profile_window.show()
				
			else:
				self.core.LliurexGoogleDriveManager.remove_chromium_tmpbin()		
				msg_error=self.get_msg(8)
				self.msg_label.set_name("MSG_ERROR_LABEL")
				self.msg_label.set_text(msg_error)		
		
		return False	
		

	#def add_new_profile_button_clicked	

	def delete_profile_clicked(self,button,hbox):

		dialog = Gtk.MessageDialog(None,0,Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO, "Lliurex GDrive")
		dialog.format_secondary_text(_("Do you want delete the profile?"))
		response=dialog.run()
		dialog.destroy()
		

		if response==Gtk.ResponseType.YES:
			profile=hbox.get_children()[1].get_text().split("\n")[0]
			#ENCODING TO UNICODE			
			profile=profile.decode("utf-8")
			self.delete_profile_t=threading.Thread(target=self.delete_profile,args=(profile,))
			self.delete_profile_t.daemon=True
			GObject.threads_init()

			self.msg_label.set_text("")
			
			self.profiles_info.pop(profile)
			self.delete_profile_t.start()
			self.delete_profile_t.launched=True
			self.core.lgd.check_plabel.set_text(_("Applying changes..."))
			self.core.lgd.check_window.show()
			GLib.timeout_add(100,self.pulsate_delete_profile,profile,hbox)

	# def delete_profile_clicked
		
	def pulsate_delete_profile(self,profile,hbox):

			if self.delete_profile_t.is_alive():
				self.core.lgd.check_pbar.pulse()
				return True

			else:
				self.msg_label.show()
				self.core.lgd.check_window.hide()
				if self.delete["result"]:
					self.msg_label.set_name("MSG_LABEL")
					self.profile_list_box.remove(hbox)
				else:
					self.msg_label.set_name("MSG_ERROR_LABEL")
				
				msg_text=self.get_msg(self.delete["code"])
				self.msg_label.set_text(msg_text)
				self.profiles_info=self.core.LliurexGoogleDriveManager.profiles_config.copy()
				
			return False	

	#def pulsate_delete_profile		

	
	def delete_profile(self,profile):

		self.delete=self.core.LliurexGoogleDriveManager.delete_profile(self.profiles_info,profile)

	#def delete_profile	

	def sync_profile_clicked(self,button,hbox):

		self.msg_label.set_text("")
		self.sync_profile_t=threading.Thread(target=self.sync_profile,args=(hbox,))
		self.sync_profile_t.daemon=True
		GObject.threads_init()
		
		self.sync_profile_t.start()
		self.core.lgd.check_plabel.set_text(_("Applying changes..."))
		self.core.lgd.check_window.show()
		GLib.timeout_add(100,self.pulsate_sync_profile,button,hbox)

	
	#def sync_profile_cicked

	def pulsate_sync_profile(self,button,hbox):

		if self.sync_profile_t.is_alive():
			self.core.lgd.check_pbar.pulse()
			return True

		else:
			self.core.lgd.check_window.hide()
			if self.status_mod["result"]:
				msg_text=self.get_msg(self.status_mod["code"])
				self.msg_label.set_name("MSG_LABEL")
				self.msg_label.set_text(msg_text)
				
			else:
				msg_text=self.get_msg(self.status_mod["code"])
				self.msg_label.set_name("MSG_ERROR_LABEL")
				self.msg_label.set_text(msg_text)	
			

			info=self.item_status_info(self.status_info['status'])
			profile=hbox.get_children()[1].get_text().split("\n")[0]
			self.current_status[profile.decode("utf-8")]=self.status_info["status"]
			button.set_tooltip_text(info["tooltip"])
			button.set_name(info["css"])		
			hbox.get_children()[4].set_image(info["img"])	

		return False					

	#def pulsate_sync_profile	

	def sync_profile(self,hbox):
	
		profile=hbox.get_children()[1].get_text().split("\n")[0]
		mountpoint=hbox.get_children()[3].get_text()
		# ENCODING TO UNICODE		
		profile=profile.decode("utf-8")
		mountpoint=mountpoint.decode("utf-8")
		connect=True
		current_status=self.current_status[profile]
		self.status_mod,self.status_info=self.core.LliurexGoogleDriveManager.sync_profile(profile,mountpoint,current_status)
		
	#def sync_profile	

	def edit_profile_clicked(self,button,hbox):

		self.edition=True
		self.read=False
		self.core.lgd.check_plabel.set_text(_("Checking connection to google..."))
		self.core.lgd.check_window.show()
		self.init_threads()
		self.check_connection_t.start()
		GLib.timeout_add(100,self.pulsate_edit_connection,hbox)

		
	#def edit_profile_clicked

	def pulsate_edit_connection(self,hbox):

		if self.check_connection_t.is_alive():
				#self.disable_entry_profile_dialog()
				self.core.lgd.check_pbar.pulse()
				return True

		else:
			self.core.lgd.check_window.hide()
			self.enable_entry_profile_dialog()
			#ENCODING TO UNICODE
			if self.connection:
				self.stack.set_visible_child_name("edit")

				self.profile_to_edit=hbox		
				self.profile=self.profile_to_edit.get_children()[1].get_text().split("\n")[0]
				self.profile_entry.set_text(self.profile)
				email=self.profile_to_edit.get_children()[1].get_text().split("\n")[1]
				self.email_entry.set_text(email)
				mountpoint=self.profile_to_edit.get_children()[3].get_text()
				self.mountpoint_entry.set_filename(mountpoint)
				automount=self.profiles_info[self.profile.decode("utf-8")]["automount"]
				self.automount_entry.set_active(automount)

				try:
					self.root_folder=self.profiles_info[self.profile.decode("utf-8")]["root_folder"]
				except Exception as e:
					self.root_folder=False

				if self.root_folder:
					self.gdrive_folder_label.show()
					self.gdrive_folder_entry.show()
					self.gdrive_folder_entry.set_text(self.profiles_info[self.profile.decode("utf-8")]["gdrive_folder"])
					#self.gdrive_folder=self.gdrive_folder_entry.get_text()
					self.edit_gdrive_folder_button.show()
					self.edit_gdrive_folder_button.set_sensitive(True)
				else:
					self.gdrive_folder_label.hide()
					self.gdrive_folder_entry.set_text("")
					#self.gdrive_folder=self.gdrive_folder_entry.get_text()
					self.gdrive_folder_entry.hide()
					self.edit_gdrive_folder_button.hide()	

				self.root_folder_param_entry.set_active(self.root_folder)	

				self.init_threads()

				self.profile_msg.hide()
				self.profile_pbar.hide()
				self.msg_label.set_text("")
				self.init_profile_dialog_button()
				self.new_profile_window.show()

			else:		
				msg_text=self.get_msg(8)
				self.msg_label.set_name("MSG_ERROR_LABEL")
				self.msg_label.set_text(msg_text)		
		return False

	#def pulsate_edit_connection	


	def check_connection(self):
		self.connection=self.core.LliurexGoogleDriveManager.check_google_connection()

	#def check_connection	

	def new_profile_button(self,profile_name,email,mountpoint):
		
		hbox=Gtk.HBox()
		profile_image=Gtk.Image.new_from_file(PROFILE_IMAGE)
		profile_image.set_margin_left(10)
		profile_image.set_halign(Gtk.Align.CENTER)
		profile_image.set_valign(Gtk.Align.CENTER)
		profile_info="<span font='Roboto'><b>"+profile_name+"</b></span>\n"+"<span font='Roboto'>"+email+"</span>"
		profile=Gtk.Label()
		profile.set_markup(profile_info)
		profile.set_margin_left(10)
		profile.set_margin_right(15)
		profile.set_margin_top(21)
		profile.set_margin_bottom(21)
		profile.set_width_chars(25)
		profile.set_max_width_chars(25)
		profile.set_xalign(-1)
		profile.set_ellipsize(Pango.EllipsizeMode.END)
		folder_image=Gtk.Image.new_from_file(FOLDER_IMAGE)
		folder_image.set_margin_left(20)
		folder_image.set_halign(Gtk.Align.CENTER)
		folder_image.set_valign(Gtk.Align.CENTER)
		folder=Gtk.Label()
		folder.set_text(mountpoint)
		folder.set_margin_left(10)
		delete=Gtk.Button()
		delete_image=Gtk.Image.new_from_file(DELETE_IMAGE)
		delete.add(delete_image)
		delete.set_halign(Gtk.Align.CENTER)
		delete.set_valign(Gtk.Align.CENTER)
		delete.set_name("DELETE_ITEM_BUTTON")
		delete.connect("clicked",self.delete_profile_clicked,hbox)
		delete.set_tooltip_text(_("Delete profile"))
		edit=Gtk.Button()
		edit_image=Gtk.Image.new_from_file(EDIT_IMAGE)
		edit.add(edit_image)
		edit.set_halign(Gtk.Align.CENTER)
		edit.set_valign(Gtk.Align.CENTER)
		edit.set_name("EDIT_ITEM_BUTTON")
		edit.connect("clicked",self.edit_profile_clicked,hbox)
		edit.set_tooltip_text(_("Edit profile"))
		mount=Gtk.Button()
		
		if self.initial_connection:
			status_info=self.core.LliurexGoogleDriveManager.check_mountpoint_status(mountpoint)
			self.current_status[profile_name]=status_info["status"]
			info=self.item_status_info(status_info["status"])
		else:
			info=self.item_status_info(None)
			self.current_status[profile_name]=None
			
		
		mount_image=info["img"]
		mount.set_tooltip_text(info["tooltip"])
		mount.set_name(info["css"])
		mount.add(mount_image)
		mount.set_halign(Gtk.Align.CENTER)
		mount.set_valign(Gtk.Align.CENTER)
		mount.connect("clicked",self.sync_profile_clicked,hbox)
		
		hbox.pack_start(profile_image,False,False,0)
		hbox.pack_start(profile,False,False,0)
		hbox.pack_start(folder_image,False,False,0)
		hbox.pack_start(folder,False,False,0)
		hbox.pack_end(delete,False,False,10)
		hbox.pack_end(edit,False,False,10)
		hbox.pack_end(mount,False,False,10)
		hbox.show_all()
		hbox.set_name("PROFILE_BOX")
		self.profile_list_box.pack_start(hbox,False,False,5)
		self.profile_list_box.queue_draw()
		hbox.queue_draw()
		
	#def new_profile_button

	def item_status_info(self,status_info):
	
		

		if status_info==None:
			img=Gtk.Image.new_from_file(MOUNT_ON_IMAGE)
			css="WARNING_ITEM_BUTTON"
			tooltip=_("Without connection. Clicked to update")
			css="WARNING_ITEM_BUTTON"			
		elif status_info:
			img=Gtk.Image.new_from_file(MOUNT_ON_IMAGE)
			tooltip=_("Mounted. Clicked to dismount now")
			css="MOUNT_ITEM_BUTTON"
		else:
			img=Gtk.Image.new_from_file(MOUNT_ON_IMAGE)
			tooltip=_("Dismounted. Clicked to mount now")
			css="DELETE_ITEM_BUTTON"	

		return {"img":img ,"tooltip":tooltip, "css":css}	

	#def item_status_info			

	def accept_add_profile_clicked(self,widget):

		self.disable_entry_profile_dialog()
		self.accept_add_profile_button.hide()
		self.cancel_add_profile_button.hide()
		#ENCODING TO UNICODE
		profile=self.profile_entry.get_text()

		self.new_profile=profile.strip().decode("utf-8")
		email=self.email_entry.get_text()
		self.new_email=email.strip()
		self.new_mountpoint=self.mountpoint_entry.get_filename().decode("utf-8")
		self.new_automount=self.automount_entry.get_state()
		

		if not self.edition:
			self.new_root_folder=False
			self.new_gdrive_folder=""
		else:
			self.new_root_folder=self.root_folder_param_entry.get_state()
			if self.new_root_folder:
					try:
						self.new_gdrive_folder=self.gdrive_folder_entry.get_text().decode("utf-8")
					except Exception as e:
						print str(e)
						self.new_gdrive_folder=""	
			else:
				self.new_gdrive_folder=""	 
	 
	 	self.profile_msg.show()
	 	self.profile_msg.set_name("MSG_LABEL")
	 	self.profile_pbar.show()
	 	self.init_threads()
	 	if not self.check_form_t.launched:
	 		self.profile_msg.set_text(_("Validating entered data..."))
	 		GLib.timeout_add(100,self.pulsate_check_form)

	#def accept_add_profile_clicked		


	def pulsate_check_form(self):

	 	self.profile_pbar.pulse()
		
		if not self.check_form_t.launched:
			self.check_form_t.start()
			self.check_form_t.launched=True


		if self.check_form_t.done:

			if self.check_form_result['result']:
				self.profiles_info[self.new_profile]={}
				self.profiles_info[self.new_profile]["email"]=self.new_email
				self.profiles_info[self.new_profile]["mountpoint"]=self.new_mountpoint
				self.profiles_info[self.new_profile]["automount"]=self.new_automount
				self.profiles_info[self.new_profile]["root_folder"]=self.new_root_folder
				self.profiles_info[self.new_profile]["gdrive_folder"]=self.new_gdrive_folder
			
				self.profile_msg.set_name("MSG_LABEL")
				if not self.edition:
					if not self.create_profile_t.launched:
						self.profile_msg.set_text(_("Connecting with google to get account access..."))
						self.profile_pbar.show()
						self.retry=0
						GLib.timeout_add(100,self.pulsate_add_profile)
					
			
				else:
								
					if not self.edit_profile_t.launched:
						self.profile_msg.set_text(_("Applying changes..."))
						self.profile_pbar.show()
						GLib.timeout_add(100,self.pulsate_edit_profile)	
			else:
				self.profile_pbar.hide()
				self.profile_msg.set_name("MSG_ERROR_LABEL")
				#self.profile_msg.set_text(check_form["msg"])
				self.profile_msg.set_text(self.get_msg(self.check_form_result["code"]))
				self.enable_entry_profile_dialog()
				self.init_profile_dialog_button()
				return False

		if self.check_form_t.launched:
			if not self.check_form_t.done:
				return True		

	#def check_form			

	def check_form(self):			

		self.check_form_result=self.core.LliurexGoogleDriveManager.check_profile_info(self.new_profile,self.new_mountpoint,self.edition,self.new_root_folder,self.new_gdrive_folder)
		self.check_form_t.done=True
		#self.profile_msg.show()

	
	#def check_form	

	def check_mountpoint_folder(self,widget):

	
		self.disable_entry_profile_dialog()
		#ENCODING TO UNICODE
		profile=self.profile_entry.get_text()

		new_profile=profile.strip().decode("utf-8")
		new_mountpoint=self.mountpoint_entry.get_filename().decode("utf-8")
				
		check_form=self.core.LliurexGoogleDriveManager.check_mountpoint_folder(new_profile,new_mountpoint,self.edition)
		
		if not check_form["result"]:
			self.profile_msg.show()
			self.profile_msg.set_name("MSG_ERROR_LABEL")
			self.profile_msg.set_text(self.get_msg(check_form["code"]))
			
		else:
			self.profile_msg.hide()	

		self.enable_entry_profile_dialog()	

	#def check_mountpoint_folder	

	'''	
	def check_profile_info(self):

		msg_check=""

		check_form=self.core.LliurexGoogleDriveManager.check_profile_info(self.new_profile,self.new_mountpoint,self.edition)

		
		if not check_form["result"]:
			if check_form["code"]==1:
				msg_check=_("You must indicate a profile")

			elif check_form["code"]==2:
				msg_check=_("Profile can not contain blanks")

			elif check_form["code"]==3 :
				msg_check=_("Profile already exists")
			
			elif check_form["code"]==4:
				msg_check=_("Mount point already used by another profile")	

			elif check_form["code"]==5:
				msg_check=_("The mount point must be an empty folder")	

			elif check_form["code"]==6:
				msg_check=_("Mount point is not owned by user")	


		return {"result":check_form["result"],"msg":msg_check}

	#def check_profile_info	

	'''	

	def pulsate_add_profile(self):

		self.retry=self.retry+1
		self.profile_pbar.pulse()
		
		if not self.create_profile_t.launched:
			#self.accept_add_profile_button.hide()
			#self.cancel_add_profile_button.hide()
		
			self.create_profile_t.start()
			self.create_profile_t.launched=True

		if not self.create_profile_t.is_alive():
			if not self.create_mountpoint_t.launched:
				self.profile_msg.set_name("MSG_LABEL")
				self.profile_msg.set_text(_("Creating profile... "))
				self.create_mountpoint_t.start()
				self.create_mountpoint_t.launched=True

			if self.create_mountpoint_t.done:
				self.profile_pbar.hide()
				if self.create_result["result"]:
						self.initial_connection=True
						self.new_profile_button(self.new_profile,self.new_email,self.new_mountpoint)
						self.profile_msg.set_text(_("Profile created successfully"))
						self.change_cancel_button()
						
				else:
					msg_text=self.get_msg(self.create_result["code"])
					self.profile_msg.set_name("MSG_ERROR_LABEL")
					self.profile_msg.set_text(msg_text)
					self.cancel_add_profile_button.show()
					
				self.profiles_info=self.core.LliurexGoogleDriveManager.profiles_config.copy()	
				return False	
						
		if self.create_profile_t.launched:
			if self.create_profile_t.is_alive():
				self.kill_create_profile()
				return True	
				

		if self.create_mountpoint_t.launched:
			if not self.create_mountpoint_t.done:
				return True		

	#def_pulsate_add_profile	


	def get_msg(self,code):

		if 	code==0:
			msg_text=_("Changes applied successfully")
		
		elif code==1:
			msg_text=_("Error: Unable to create mount point")

		elif code==2:
			msg_text=_("Error: Unable to mount mount point")

		elif code==3:
			msg_text=_("Error: Mount point is not owned by user")	

		elif code==4:
			msg_text=_("Error: No mount point indicated")

		elif code==5:
			msg_text=_("Error: Profile is not authorized to Google Drive")

		elif code==6:
			msg_text=_("Error: Unknow profile")

		elif code==7:
			msg_text=_("Error: Unable to dismount mount point")

		elif code==8:
			msg_text=_("Error: Unable to connect with google")	
			
		elif code==9:
			msg_text=_("Status updated. Now you can change it")

		elif code==10:
			msg_text=_("You must indicate a profile")

		elif code==11:
			msg_text=_("Profile can not contain blanks")

		elif code==12:
			msg_text=_("Profile already exists")
			
		elif code==13:
			msg_text=_("Mount point already used by another profile")	

		elif code==14:
			msg_text=_("The mount point must be an empty folder")	

		elif code==15:
			msg_text=_("Mount point is not owned by user")		

		elif code==16:
			msg_text=_("Path of mount point can not contain blanks")
			
		elif code==17:
			msg_text=_("Error: You must specify a GDrive folder or disable the option")	

		elif code==18:
			msg_text=_("Error: Unable to mount mount point. The synced GDrive folder maybe not be correct")	

		elif code==19:
			msg_text=_("Error: Synced Gdrive folder no longer exists")
		
		elif code==20:
			msg_text=_("Error: No folders found in Gdrive profile. You must disable the option")

		elif code==21:
			msg_text=_("Error: To add a profile it is required that Chromium is not the default browser")		

				
		return msg_text		
		

	#def get_msg							

	def kill_create_profile(self):
	
		if self.retry>MAX_RETRY_INTENTS:
			parent=psutil.Process(self.create_profile_t.pid)
			for child in parent.children(recursive=True):
				child.kill()
				self.create_profile_t.terminate()
				self.core.LliurexGoogleDriveManager.remove_chromium_tmpbin()		
				self.profile_msg.set_name("MSG_ERROR_LABEL")
				self.profile_msg.set_text(_("Error getting authorization"))

		return True	

	#def kill_create_profile	

	def create_profile(self):

		result=self.core.LliurexGoogleDriveManager.create_profile(self.new_profile)

	#def create_profile	

	def create_mountpoint(self):

		self.create_result=self.core.LliurexGoogleDriveManager.create_mountpoint(self.profiles_info,self.new_profile)
		self.create_mountpoint_t.done=True
		
	#def create_mountpoint	

	def pulsate_edit_profile(self):

		self.profile_pbar.pulse()

		if not self.edit_profile_t.launched:
			
			#self.accept_add_profile_button.hide()
			#self.cancel_add_profile_button.hide()
			self.edit_profile_t.start()
			self.edit_profile_t.launched=True

		if self.edit_profile_t.done:
			self.profile_pbar.hide()
			if self.edit_result["result"]:
				self.profile_msg.set_name("MSG_LABEL")
				self.profile_to_edit.get_children()[3].set_text(self.new_mountpoint)
				self.profiles_info=self.core.LliurexGoogleDriveManager.profiles_config.copy()	
				self.change_cancel_button()
			
			else:
				
				self.profile_msg.set_name("MSG_ERROR_LABEL")
				self.cancel_add_profile_button.show()

			msg_text=self.get_msg(self.edit_result["code"])
			self.profile_msg.set_text(msg_text)

			return False
			

		if self.edit_profile_t.launched:
			if not self.edit_profile_t.done:
				return True

	#def pulsate_edit_profile			

	def edit_profile(self):

		self.edit_result=self.core.LliurexGoogleDriveManager.edit_profile(self.profiles_info,self.new_profile)
		self.edit_profile_t.done=True

	#def edit_profile	

	def cancel_add_profile_clicked(self,widget):
		
		self.core.LliurexGoogleDriveManager.remove_chromium_tmpbin()		
		self.new_profile_window.hide()
	
	#def cancel_add_profile_clicked

	
	def root_folder_clicked(self,widget,event):

		if self.root_folder_param_entry.get_active():
			if not self.root_folder:
	
				self.init_read_mountpoint_dialog()	
			
		else:
			self.root_folder=False
			self.gdrive_folder_label.hide()
			self.gdrive_folder_entry.hide()
			#self.gdrive_folder_entry.set_text("")
			self.edit_gdrive_folder_button.hide()	

	#def root_folder_clicked		


	def init_read_mountpoint_dialog(self):

		if not self.read:

			if not self.read_mountpoint_t.launched:
				self.disable_entry_profile_dialog()
				self.profile_msg.set_name("MSG_LABEL")
				self.profile_msg.show()
				self.profile_msg.set_text(_("Getting folders from Google Drive profile ..."))
				self.profile_pbar.show()
				GLib.timeout_add(100,self.pulsate_read_mountpoint)	

		else:
			if len(self.syncfolders_model)>1:
				self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
				self.stack.set_visible_child_name("folder")	
				self.gdrive_combobox.set_active(0)

	#def init_read_mountpoint_dialog		


	def pulsate_read_mountpoint(self):

		self.profile_pbar.pulse()

		if not self.read_mountpoint_t.launched:
			self.read_mountpoint_t.start()
			self.read_mountpoint_t.launched=True
			self.accept_add_profile_button.hide()
			self.cancel_add_profile_button.hide()

		if self.read_mountpoint_t.done:
			self.root_folder=False
			self.enable_entry_profile_dialog()
			self.profile_pbar.hide()
			self.profile_msg.hide()
		
			if len(self.syncfolders_model)>1:
				self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

				self.stack.set_visible_child_name("folder")
				self.accept_add_profile_button.hide()
				self.cancel_add_profile_button.hide()
			else:
				self.profile_msg.show()
				self.profile_msg.set_name("MSG_ERROR_LABEL")
				self.profile_msg.set_text(_("No folders detected on google drive profile"))	
				self.accept_add_profile_button.show()
				self.cancel_add_profile_button.show()
			
			return False
			

		if self.read_mountpoint_t.launched:
			if not self.read_mountpoint_t.done:
				return True

	#def pulsate_read_mountpoint	

	def read_mountpoint(self):


		folders=self.core.LliurexGoogleDriveManager.read_mountpoint_directory(self.profile)
		
		self.syncfolders_model.clear()

		if len(folders)>0:
			
			for item in folders:
				self.syncfolders_model.append([item])

								
		self.read=True			

		self.read_mountpoint_t.done=True	

	#def read_mountpoint
	
	def edit_gdrive_folder_button_clicked(self,widget):


		self.init_threads()
		self.profile_msg.hide()
		self.profile_msg.set_text("")
		self.init_read_mountpoint_dialog()

			

	#def edit_gdrive_folder_button_clicked	
	

	def return_combobox_button_clicked(self,widget):

		
		#self.gdrive_folder_entry.set_text(self.folder)
		#self.gdrive_folder=folder

		
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		self.stack.set_visible_child_name("edit")	
		self.accept_add_profile_button.show()
		self.cancel_add_profile_button.show()
		
		self.gdrive_folder_label.show()
		self.gdrive_folder_entry.show()
		self.edit_gdrive_folder_button.set_sensitive(True)	

	#def return_combobox_button_clicked	

	def on_gdrive_combobox_changed (self,combo):


		
		tree_iter=combo.get_active_iter()

		
		if tree_iter != None:
			model = combo.get_model()
			folder = model[tree_iter][0]
			self.gdrive_folder_entry.set_text(folder)


	#def on_gdrive_combobox_changeg		

        



#class profilebox


	
		
