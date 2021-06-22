#!/usr/bin/env python3
# -*- coding: utf-8 -*


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, GdkPixbuf, Gdk, Gio, GObject,GLib

import copy
import gettext
import Core

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
DISABLE_INDICATOR="~/.config/lliurex-google-drive-profiles/disableIndicator"
PROFILE_IMAGE=RSRC+"rsrc/profile.svg"
FOLDER_IMAGE=RSRC+"rsrc/folder.svg"
MOUNT_ON_IMAGE=RSRC+"rsrc/mount_on.svg"
MOUNT_OFF_IMAGE=RSRC+"rsrc/mount_off.svg"
MANAGE_PROFILE_IMAGE=RSRC+"rsrc/manage_profile.svg"
#DELETE_IMAGE=RSRC+"rsrc/trash.svg"
MAX_RETRY_INTENTS=1200


class ProfileBox(Gtk.VBox):
	
	def __init__(self):
		
		Gtk.VBox.__init__(self)
		
		self.core=Core.Core.get_core()
		self.disable_indicator=os.path.expanduser(DISABLE_INDICATOR)
		
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-gdrive')
		ui_path=RSRC + "/rsrc/lliurex-gdrive.ui"
		builder.add_from_file(ui_path)

		self.stack = Gtk.Stack()
		self.stack.set_transition_duration(1000)
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

		self.main_box=builder.get_object("profile_data_box")
		#self.profiles_list_label=builder.get_object("profiles_list_label")
		self.profile_list_box=builder.get_object("profile_list_box")
		self.profile_list_vp=builder.get_object("profile_list_viewport")
		self.msg_box=builder.get_object("msg_box")
		self.msg_img_error=builder.get_object("msg_img_error")
		self.msg_img_ok=builder.get_object("msg_img_ok")
		self.msg_label=builder.get_object("msg_label")

		image = Gtk.Image()
		image.set_from_stock(Gtk.STOCK_ADD,Gtk.IconSize.MENU)
		
		self.add_new_profile_button=builder.get_object("add_new_profile_button")
		self.help_button=builder.get_object("help_button")
		self.global_management_button=builder.get_object("global_management_button")
		#self.add_new_profile_button.set_image(image)
		self.popover = Gtk.Popover()
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		indicator_box=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		indicator_box.set_margin_left(10)
		indicator_box.set_margin_right(10)
		indicator_eb=Gtk.EventBox()
		indicator_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
		indicator_eb.connect("button-press-event", self.manage_menu_indicator)
		indicator_eb.connect("motion-notify-event", self.mouse_over_popover)
		indicator_eb.connect("leave-notify-event", self.mouse_exit_popover)
		self.indicator_label=Gtk.Label()

		if not os.path.exists(self.disable_indicator):
			self.indicator_label.set_text(_("Hide menu indicator at login"))
		else:
			self.indicator_label.set_text(_("Show menu indicator at login"))

		indicator_eb.add(self.indicator_label)
		indicator_box.add(indicator_eb)
		vbox.pack_start(indicator_box, True, True,8)
		vbox.show_all()
		self.popover.add(vbox)
		self.popover.set_position(Gtk.PositionType.BOTTOM)
		self.popover.set_relative_to(self.global_management_button)

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

		self.profile_msg_box=builder.get_object("profile_msg_box")
		self.profile_msg_img_error=builder.get_object("profile_msg_img_error")
		self.profile_msg_img_ok=builder.get_object("profile_msg_img_ok")
		self.profile_msg=builder.get_object("profile_msg")
		self.profile_pbar=builder.get_object("profile_pbar")
		self.accept_add_profile_button=builder.get_object("accept_add_profile_button")
		self.cancel_add_profile_button=builder.get_object("cancel_add_profile_button")

		self.gdrive_combobox_box=builder.get_object("gdrive_combobox_box")
		self.gdrive_combobox_label=builder.get_object("gdrive_combobox_label")
		self.gdrive_combobox=builder.get_object("gdrive_combobox")
		self.apply_combobox_button=builder.get_object("apply_combobox_button")
		self.cancel_combobox_button=builder.get_object("cancel_combobox_button")
		
					
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
		#self.profiles_list_label.set_name("OPTION_LABEL")
		self.profile_list_vp.set_name("LIST_BOX")
		self.profile_label.set_name("OPTION_LABEL")
		self.email_label.set_name("OPTION_LABEL")
		self.mountpoint_label.set_name("OPTION_LABEL")
		self.automount_label.set_name("OPTION_LABEL")
		self.msg_label.set_name("FEEDBACK_LABEL")
		self.profile_msg.set_name("FEEDBACK_LABEL")
		self.root_folder_param_label.set_name("OPTION_LABEL")
		self.gdrive_combobox_label.set_name("OPTION_LABEL")
		self.gdrive_folder_label.set_name("OPTION_LABEL")
		self.profile_entry.set_name("CUSTOM-ENTRY")
		self.email_entry.set_name("CUSTOM-ENTRY")
		self.gdrive_folder_entry.set_name("CUSTOM-ENTRY")
			
	#def set-css_info
	
		
	def connect_signals(self):

		self.add_new_profile_button.connect("clicked",self.add_new_profile_button_clicked)
		self.help_button.connect("clicked",self.help_clicked)
		self.global_management_button.connect("clicked",self.global_management_button_clicked)
		self.accept_add_profile_button.connect("clicked",self.accept_add_profile_clicked)
		self.cancel_add_profile_button.connect("clicked",self.cancel_add_profile_clicked)
		self.new_profile_window.connect("delete_event",self.hide_window)
		self.mountpoint_entry.connect("file-set",self.check_mountpoint_folder)
		self.gdrive_combobox.connect("changed",self.on_gdrive_combobox_changed)
		self.root_folder_param_entry.connect("notify::active",self.root_folder_clicked)
		self.apply_combobox_button.connect("clicked",self.apply_combobox_button_clicked)
		self.edit_gdrive_folder_button.connect("clicked",self.edit_gdrive_folder_button_clicked)
		self.cancel_combobox_button.connect("clicked",self.cancel_combobox_button_clicked)


	#def connect_signals


	def check_initial_connection(self):
		
		self.initial_connection=self.core.LliurexGoogleDriveManager.check_google_connection()
		
		return

	#def check_initial_connection	
	
	def load_info(self,info):
		
		self.profiles_info=info
		count=len(self.profiles_info)
		for item in self.profiles_info:
			profile=item
			email=self.profiles_info[item]["email"]
			mountpoint=self.profiles_info[item]["mountpoint"]
			self.new_profile_button(profile,email,mountpoint,count)
			count-=1
	
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
		self.manage_msg_box(True)
		self.manage_profile_msg_box(True)
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
			#self.msg_label.set_name("MSG_ERROR_LABEL")
			self.manage_msg_box(False,True)
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
				#self.profile_msg.set_text("")
		

				self.init_threads()
				
				self.msg_label.set_text("")
				#self.profile_msg.hide()
				self.profile_pbar.hide()
				self.init_profile_dialog_button()
				self.new_profile_window.show()
				
			else:
				self.core.LliurexGoogleDriveManager.remove_chromium_tmpbin()		
				msg_error=self.get_msg(8)
				#self.msg_label.set_name("MSG_ERROR_LABEL")
				self.manage_msg_box(False,True)
				self.msg_label.set_text(msg_error)		
		
		return False	
		

	#def add_new_profile_button_clicked	

	def delete_profile_clicked(self,widget,event,vbox):

		popover=vbox.get_children()[0].get_children()[5].popover.hide()

		dialog = Gtk.MessageDialog(None,0,Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO, "Lliurex GDrive")
		dialog.format_secondary_text(_("Do you want delete the profile?"))
		response=dialog.run()
		dialog.destroy()
		

		if response==Gtk.ResponseType.YES:
			profile=vbox.get_children()[0].get_children()[1].get_text().split("\n")[0]
			#ENCODING TO UNICODE			
			#profile=profile.decode("utf-8")
			self.delete_profile_t=threading.Thread(target=self.delete_profile,args=(profile,))
			self.delete_profile_t.daemon=True
			GObject.threads_init()

			self.msg_label.set_text("")
			
			self.profiles_info.pop(profile)
			self.delete_profile_t.start()
			self.delete_profile_t.launched=True
			self.core.lgd.check_plabel.set_text(_("Applying changes..."))
			self.core.lgd.check_window.show()
			GLib.timeout_add(100,self.pulsate_delete_profile,profile,vbox)

	# def delete_profile_clicked
		
	def pulsate_delete_profile(self,profile,vbox):

			if self.delete_profile_t.is_alive():
				self.core.lgd.check_pbar.pulse()
				return True

			else:
				self.msg_label.show()
				self.core.lgd.check_window.hide()
				if self.delete["result"]:
					#self.msg_label.set_name("MSG_LABEL")
					self.profile_list_box.remove(vbox)
					self.draw_list_separator()
					self.manage_msg_box(False)
				else:
					self.manage_msg_box(False,True)
					#self.msg_label.set_name("MSG_ERROR_LABEL")
				
				msg_text=self.get_msg(self.delete["code"])
				self.msg_label.set_text(msg_text)
				self.profiles_info=self.core.LliurexGoogleDriveManager.profiles_config.copy()
				
			return False	

	#def pulsate_delete_profile		

	
	def delete_profile(self,profile):

		self.delete=self.core.LliurexGoogleDriveManager.delete_profile(self.profiles_info,profile)

	#def delete_profile	

	def sync_profile_clicked(self,button,hbox):

		self.manage_msg_box(True)
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
				#self.msg_label.set_name("MSG_LABEL")
				self.manage_msg_box(False)
				self.msg_label.set_text(msg_text)
				
			else:
				msg_text=self.get_msg(self.status_mod["code"])
				#self.msg_label.set_name("MSG_ERROR_LABEL")
				self.manage_msg_box(False,True)
				self.msg_label.set_text(msg_text)	
			

			info=self.item_status_info(self.status_info['status'])
			profile=hbox.get_children()[1].get_text().split("\n")[0]
			#self.current_status[profile.decode("utf-8")]=self.status_info["status"]
			self.current_status[profile]=self.status_info["status"]
			button.set_tooltip_text(info["tooltip"])
			button.set_name(info["css"])		
			hbox.get_children()[4].set_image(info["img"])	

		return False					

	#def pulsate_sync_profile	

	def sync_profile(self,hbox):
	
		profile=hbox.get_children()[1].get_text().split("\n")[0]
		mountpoint=hbox.get_children()[3].get_text()
		# ENCODING TO UNICODE		
		#profile=profile.decode("utf-8")
		#mountpoint=mountpoint.decode("utf-8")
		connect=True
		current_status=self.current_status[profile]
		self.status_mod,self.status_info=self.core.LliurexGoogleDriveManager.sync_profile(profile,mountpoint,current_status)
		
	#def sync_profile	

	def edit_profile_clicked(self,widget,event,vbox):

		self.manage_profile_msg_box(True)

		popover=vbox.get_children()[0].get_children()[5].popover.hide()
		self.edition=True
		self.read=False
		self.core.lgd.check_plabel.set_text(_("Checking connection to google..."))
		self.core.lgd.check_window.show()
		self.init_threads()
		self.check_connection_t.start()
		GLib.timeout_add(100,self.pulsate_edit_connection,vbox)

		
	#def edit_profile_clicked

	def pulsate_edit_connection(self,vbox):

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

				self.profile_to_edit=vbox.get_children()[0]		
				self.profile=self.profile_to_edit.get_children()[1].get_text().split("\n")[0]
				self.profile_entry.set_text(self.profile)
				email=self.profile_to_edit.get_children()[1].get_text().split("\n")[1]
				self.email_entry.set_text(email)
				mountpoint=self.profile_to_edit.get_children()[3].get_text()
				self.mountpoint_entry.set_filename(mountpoint)
				#automount=self.profiles_info[self.profile.decode("utf-8")]["automount"]
				automount=self.profiles_info[self.profile]["automount"]
				self.automount_entry.set_active(automount)

				try:
					#self.root_folder=self.profiles_info[self.profile.decode("utf-8")]["root_folder"]
					self.root_folder=self.profiles_info[self.profile]["root_folder"]
				except Exception as e:
					self.root_folder=False

				if self.root_folder:
					self.gdrive_folder_label.show()
					self.gdrive_folder_entry.show()
					#self.gdrive_folder_entry.set_text(self.profiles_info[self.profile.decode("utf-8")]["gdrive_folder"])
					self.gdrive_folder_entry.set_text(self.profiles_info[self.profile]["gdrive_folder"])
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

				#self.profile_msg.hide()
				self.profile_pbar.hide()
				self.msg_label.set_text("")
				self.init_profile_dialog_button()
				self.new_profile_window.show()

			else:		
				msg_text=self.get_msg(8)
				#self.msg_label.set_name("MSG_ERROR_LABEL")
				self.manage_msg_box(False,True)				
				self.msg_label.set_text(msg_text)		
		return False

	#def pulsate_edit_connection	


	def check_connection(self):
		self.connection=self.core.LliurexGoogleDriveManager.check_google_connection()

	#def check_connection	

	def new_profile_button(self,profile_name,email,mountpoint,count=1):
		
		profile_vbox=Gtk.VBox()
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
		
		manage_profile=Gtk.Button()
		manage_profile_image=Gtk.Image.new_from_file(MANAGE_PROFILE_IMAGE)
		manage_profile.add(manage_profile_image)
		manage_profile.set_halign(Gtk.Align.CENTER)
		manage_profile.set_valign(Gtk.Align.CENTER)
		manage_profile.set_name("EDIT_ITEM_BUTTON")
		manage_profile.connect("clicked",self.manage_profile_options,profile_vbox)
		manage_profile.set_tooltip_text(_("Manage profile"))

		popover = Gtk.Popover()
		manage_profile.popover=popover
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		edit_box=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		edit_box.set_margin_left(10)
		edit_box.set_margin_right(10)
		edit_eb=Gtk.EventBox()
		edit_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
		edit_eb.connect("button-press-event", self.edit_profile_clicked,profile_vbox)
		edit_eb.connect("motion-notify-event", self.mouse_over_popover)
		edit_eb.connect("leave-notify-event", self.mouse_exit_popover)
		edit_label=Gtk.Label()
		edit_label.set_text(_("Edit profile"))
		edit_eb.add(edit_label)
		edit_box.add(edit_eb)
		
		delete_box=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		delete_box.set_margin_left(10)
		delete_box.set_margin_right(10)
		delete_eb=Gtk.EventBox()
		delete_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
		delete_eb.connect("button-press-event", self.delete_profile_clicked,profile_vbox)
		delete_eb.connect("motion-notify-event", self.mouse_over_popover)
		delete_eb.connect("leave-notify-event", self.mouse_exit_popover)
		delete_label=Gtk.Label()
		delete_label.set_text(_("Delete profile"))
		delete_eb.add(delete_label)
		delete_box.add(delete_eb)

		vbox.pack_start(edit_box, True, True,8)
		vbox.pack_start(delete_box, True, True,8)
		
		vbox.show_all()
		popover.add(vbox)
		popover.set_position(Gtk.PositionType.BOTTOM)
		popover.set_relative_to(manage_profile)


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
		#hbox.pack_end(delete,False,False,10)
		hbox.pack_end(manage_profile,False,False,10)
		hbox.pack_end(mount,False,False,10)
		hbox.show_all()
		hbox.set_name("PROFILE_BOX")
		hbox.queue_draw()

		list_separator=Gtk.Separator()
		list_separator.set_margin_left(52)
		list_separator.set_margin_right(10)


		if count!=1:
			list_separator.set_name("SEPARATOR")
		else:
			list_separator.set_name("WHITE_SEPARATOR")

		profile_vbox.pack_start(hbox,False,False,0)
		profile_vbox.pack_end(list_separator,False,False,0)
		profile_vbox.show_all()
		self.profile_list_box.pack_start(profile_vbox,False,False,0)
		self.profile_list_box.queue_draw()
		self.profile_list_box.set_valign(Gtk.Align.FILL)
		profile_vbox.queue_draw()
	
	#def new_profile_button

	def draw_list_separator(self):

		count=len(self.profile_list_box)

		for item in self.profile_list_box:
			if count!=1:
				item.get_children()[1].set_name("SEPARATOR")
			else:
				item.get_children()[1].set_name("WHITE_SEPARATOR")
			count-=1	


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

		self.manage_profile_msg_box(True)
		self.disable_entry_profile_dialog()
		self.accept_add_profile_button.hide()
		self.cancel_add_profile_button.hide()
		#ENCODING TO UNICODE
		profile=self.profile_entry.get_text()

		#self.new_profile=profile.strip().decode("utf-8")
		self.new_profile=profile.strip()
		email=self.email_entry.get_text()
		self.new_email=email.strip()
		#self.new_mountpoint=self.mountpoint_entry.get_filename().decode("utf-8")
		self.new_mountpoint=self.mountpoint_entry.get_filename()

		self.new_automount=self.automount_entry.get_active()
		

		if not self.edition:
			self.new_root_folder=False
			self.new_gdrive_folder=""
		else:
			self.new_root_folder=self.root_folder_param_entry.get_state()
			if self.new_root_folder:
					try:
						#self.new_gdrive_folder=self.gdrive_folder_entry.get_text().decode("utf-8")
						self.new_gdrive_folder=self.gdrive_folder_entry.get_text()
					except Exception as e:
						print(str(e))
						self.new_gdrive_folder=""	
			else:
				self.new_gdrive_folder=""	 
		#self.profile_msg.show()
		#self.profile_msg.set_name("MSG_LABEL")
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
			
				#self.profile_msg.set_name("MSG_LABEL")
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
				#self.profile_msg.set_name("MSG_ERROR_LABEL")
				#self.profile_msg.set_text(check_form["msg"])
				self.manage_profile_msg_box(False,True)
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

		self.manage_profile_msg_box(True)
		self.disable_entry_profile_dialog()
		#ENCODING TO UNICODE
		profile=self.profile_entry.get_text()

		#new_profile=profile.strip().decode("utf-8")
		new_profile=profile.strip()
		#new_mountpoint=self.mountpoint_entry.get_filename().decode("utf-8")
		new_mountpoint=self.mountpoint_entry.get_filename()
				
		check_form=self.core.LliurexGoogleDriveManager.check_mountpoint_folder(new_profile,new_mountpoint,self.edition)
		
		if not check_form["result"]:
			#self.profile_msg.show()
			#self.profile_msg.set_name("MSG_ERROR_LABEL")
			self.manage_profile_msg_box(False,True)
			self.profile_msg.set_text(self.get_msg(check_form["code"]))
			
		
		else:
			self.manage_profile_msg_box(True)
			#self.profile_msg.set_text("")	
		
		self.enable_entry_profile_dialog()	

	#def check_mountpoint_folder	

	def pulsate_add_profile(self):

		self.retry=self.retry+1
		self.profile_pbar.pulse()
		
		if not self.create_profile_t.launched:
	
			self.create_profile_t.start()
			self.create_profile_t.launched=True

		if not self.create_profile_t.is_alive():
			if not self.create_mountpoint_t.launched:
				#self.profile_msg.set_name("MSG_LABEL")
				self.profile_msg.set_text(_("Creating profile... "))
				self.create_mountpoint_t.start()
				self.create_mountpoint_t.launched=True

			if self.create_mountpoint_t.done:
				self.profile_pbar.hide()
				if self.create_result["result"]:
						self.initial_connection=True
						self.new_profile_button(self.new_profile,self.new_email,self.new_mountpoint)
						self.draw_list_separator()
						self.profile_msg.set_text(_("Profile created successfully"))
						self.manage_profile_msg_box(False)
						self.change_cancel_button()
						
				else:
					msg_text=self.get_msg(self.create_result["code"])
					#self.profile_msg.set_name("MSG_ERROR_LABEL")
					self.manage_profile_msg_box(False,True)
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

		elif code==22:
			msg_text=_("The menu indicator has been disabled. It will hide automatically when you log in")
		elif code==23:
			msg_text=_("The menu indicator has been enabled. It will be displayed automatically when you close the application")	
				
		return msg_text		
		

	#def get_msg							

	def kill_create_profile(self):
	
		if self.retry>MAX_RETRY_INTENTS:
			parent=psutil.Process(self.create_profile_t.pid)
			for child in parent.children(recursive=True):
				child.kill()
				self.create_profile_t.terminate()
				self.core.LliurexGoogleDriveManager.remove_chromium_tmpbin()		
				#self.profile_msg.set_name("MSG_ERROR_LABEL")
				self.manage_profile_msg_box(False,True)
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
			
			self.edit_profile_t.start()
			self.edit_profile_t.launched=True

		if self.edit_profile_t.done:
			self.profile_pbar.hide()
			if self.edit_result["result"]:
				#self.profile_msg.set_name("MSG_LABEL")
				self.manage_profile_msg_box(False)
				self.profile_to_edit.get_children()[3].set_text(self.new_mountpoint)
				self.profiles_info=self.core.LliurexGoogleDriveManager.profiles_config.copy()	
				self.change_cancel_button()
			
			else:
				
				#self.profile_msg.set_name("MSG_ERROR_LABEL")
				self.manage_profile_msg_box(False,True)
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
		
		self.manage_profile_msg_box(True)
		self.core.LliurexGoogleDriveManager.remove_chromium_tmpbin()		
		self.new_profile_window.hide()
	
	#def cancel_add_profile_clicked

	
	def root_folder_clicked(self,widget,event):

		self.manage_profile_msg_box(True)
		if self.root_folder_param_entry.get_active():
			if not self.root_folder:
	
				self.init_read_mountpoint_dialog()	
			
		else:
			self.root_folder=False
			self.gdrive_folder_label.hide()
			self.gdrive_folder_entry.hide()
			self.gdrive_folder_entry.set_text("")
			self.edit_gdrive_folder_button.hide()	

		self.previous_root_folder=self.gdrive_folder_entry.get_text()	

	#def root_folder_clicked		


	def init_read_mountpoint_dialog(self):

		if not self.read:

			if not self.read_mountpoint_t.launched:
				self.disable_entry_profile_dialog()
				#self.profile_msg.set_name("MSG_LABEL")
				self.profile_msg.show()
				self.profile_msg.set_text(_("Getting folders from Google Drive profile ..."))
				self.profile_pbar.show()
				GLib.timeout_add(100,self.pulsate_read_mountpoint)	

		else:
			if len(self.syncfolders_model)>1:
				self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
				self.stack.set_visible_child_name("folder")	
				self.apply_combobox_button.set_sensitive(False)
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
			self.profile_msg.set_text("")
		
			if len(self.syncfolders_model)>1:
				self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

				self.stack.set_visible_child_name("folder")
				self.apply_combobox_button.set_sensitive(False)
				self.accept_add_profile_button.hide()
				self.cancel_add_profile_button.hide()
			else:
				#self.profile_msg.show()
				#self.profile_msg.set_name("MSG_ERROR_LABEL")
				self.manage_profile_msg_box(False,True)
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

		self.previous_root_folder=self.gdrive_folder_entry.get_text()
		self.init_threads()
		#self.profile_msg.hide()
		#self.profile_msg.set_text("")
		self.manage_profile_msg_box(True)
		self.init_read_mountpoint_dialog()
		

	#def edit_gdrive_folder_button_clicked	
	

	def apply_combobox_button_clicked(self,widget):

		
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		self.stack.set_visible_child_name("edit")	
		self.accept_add_profile_button.show()
		self.cancel_add_profile_button.show()
		
		if self.previous_root_folder =="":
			if self.gdrive_folder_entry.get_text()!="":
				self.gdrive_folder_label.show()
				self.gdrive_folder_entry.show()
				self.edit_gdrive_folder_button.show()
				self.edit_gdrive_folder_button.set_sensitive(True)	
			else:
				self.root_folder_param_entry.set_active(False)
				self.edit_gdrive_folder_button.hide()	
		else:
			self.gdrive_folder_label.show()
			self.gdrive_folder_entry.show()
			self.edit_gdrive_folder_button.show()
			self.edit_gdrive_folder_button.set_sensitive(True)			
				

	#def apply_combobox_button_clicked	

	def on_gdrive_combobox_changed (self,combo):

		tree_iter=combo.get_active_iter()

		
		if tree_iter != None:
			model = combo.get_model()

			folder = model[tree_iter][0]
			if folder != "":
				self.gdrive_folder_entry.set_text(folder)
				self.apply_combobox_button.set_sensitive(True)
			else:
				self.apply_combobox_button.set_sensitive(False)

	#def on_gdrive_combobox_changeg	

	def help_clicked(self,widget):

		lang=os.environ["LANG"]

		if 'ca_ES' in lang:
			cmd='xdg-open https://wiki.edu.gva.es/lliurex/tiki-index.php?page=LliureX-Gdrive-en-Bionic.'
		else:
			cmd='xdg-open https://wiki.edu.gva.es/lliurex/tiki-index.php?page=LliureX-Gdrive-en-Bionic'

		os.system(cmd) 

	#def help_clicked	   

	def global_management_button_clicked(self,widget,event=None):

		self.manage_msg_box(True)
		self.popover.show()

	#def global_management_button_clicked	
	
	def manage_menu_indicator(self,widget,event=None):

		self.manage_msg_box(False)

		if not os.path.exists(self.disable_indicator):
			f=open(self.disable_indicator,'w')
			f.close
			self.popover.hide()
			self.msg_label.set_text(self.get_msg(22))
			self.indicator_label.set_text(_("Show menu indicator at login"))
		else:
			os.remove(self.disable_indicator)
			self.popover.hide()
			self.msg_label.set_text(self.get_msg(23))
			self.indicator_label.set_text(_("Hide menu indicator at login"))

	#def manage_menu_indicator		


	def mouse_over_popover(self,widget,event=None):

		widget.set_name("POPOVER_ON")

	#def mouser_over_popover	

	def mouse_exit_popover(self,widget,event=None):

		widget.set_name("POPOVER_OFF")		

	#def mouse_exit_popover	

	def manage_profile_options(self,button,vbox,event=None):
	
		self.manage_msg_box(True)
		button.popover.show()

	#def manage_profile_options

	def cancel_combobox_button_clicked(self,widget,event=None):

		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		self.stack.set_visible_child_name("edit")	
		self.accept_add_profile_button.show()
		self.cancel_add_profile_button.show()
		
		self.gdrive_folder_entry.set_text(self.previous_root_folder)
		if self.previous_root_folder !="":
			self.gdrive_folder_label.show()
			self.gdrive_folder_entry.show()
			self.edit_gdrive_folder_button.set_sensitive(True)	
		
		else:
			self.root_folder_param_entry.set_active(False)
	
	def manage_msg_box(self,hide,error=False):

		if hide:
			self.msg_box.set_name("HIDE_BOX")
			self.msg_img_ok.hide()
			self.msg_img_error.hide()
			self.msg_label.set_text("")
			self.msg_label.set_halign(Gtk.Align.CENTER)

		else:
			self.msg_label.set_halign(Gtk.Align.START)
			if error:
				self.msg_box.set_name("ERROR_BOX")
				self.msg_img_ok.hide()
				self.msg_img_error.show()
			else:
				self.msg_box.set_name("SUCCESS_BOX")
				self.msg_img_ok.show()
				self.msg_img_error.hide()

	#def manage_msg_box

	def manage_profile_msg_box(self,hide,error=False):

		if hide:
			self.profile_msg_box.set_name("HIDE_BOX")
			self.profile_msg_img_ok.hide()
			self.profile_msg_img_error.hide()
			self.profile_msg.set_text("")
			self.profile_msg.set_halign(Gtk.Align.CENTER)

		else:
			self.profile_msg.set_halign(Gtk.Align.START)
			if error:
				self.profile_msg_box.set_name("ERROR_BOX")
				self.profile_msg_img_ok.hide()
				self.profile_msg_img_error.show()
			else:
				self.profile_msg_box.set_name("SUCCESS_BOX")
				self.profile_msg_img_ok.show()
				self.profile_msg_img_error.hide()

	#def manage_msg_box



#class profilebox


	
		
