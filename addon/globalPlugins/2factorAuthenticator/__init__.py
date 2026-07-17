import os
import time
import hmac
import hashlib
import base64
import struct
import wx
import gui
import ui
import globalPluginHandler
from configobj import ConfigObj

# कॉन्फ़िगरेशन पाथ
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "tools", "two_fa_config.ini")

def get_totp_code(secret):
	"""गिटहब और गूगल से शत-प्रतिशत मैच होने वाला सटीक TOTP गणित"""
	try:
		# सारे स्पेस हटाएं और अक्षरों को अपरकेस करें
		secret = str(secret).replace(" ", "").strip().upper()
		
		# बेस32 के लिए पैडिंग एकदम सटीक 8 के मल्टीपल में सेट करें
		secret = secret.rstrip('=')
		missing_padding = len(secret) % 8
		if missing_padding != 0:
			secret += '=' * (8 - missing_padding)
			
		key = base64.b32decode(secret, casefold=True)
		
		# वर्तमान यूनिक्स टाइमस्टैम्प (30 सेकंड विंडो)
		intervals_no = int(time.time() // 30)
		msg = struct.pack(">Q", intervals_no)
		
		# HMAC-SHA1 जनरेशन
		hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
		
		# डायनामिक ट्रंकेशन
		offset = hmac_hash[-1] & 0x0f
		binary = struct.unpack(">I", hmac_hash[offset:offset+4])[0] & 0x7fffffff
		
		code = binary % 1000000
		return str(code).zfill(6)
	except Exception:
		return None

def copy_to_windows_clipboard(text):
	"""विंडोज ओएस क्लिपबोर्ड डायरेक्ट एक्सेस"""
	if wx.TheClipboard.Open():
		wx.TheClipboard.SetData(wx.TextDataObject(text))
		wx.TheClipboard.Close()
		return True
	return False

class AddAccountDialog(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent, title="Add New 2FA Account")
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		wx.StaticText(self, label="Account Name (e.g., GitHub):")
		self.nameCtrl = wx.TextCtrl(self)
		sizer.Add(self.nameCtrl, 0, wx.ALL | wx.EXPAND, 5)
		
		wx.StaticText(self, label="Secret Key:")
		self.keyCtrl = wx.TextCtrl(self, style=wx.TE_PASSWORD)
		sizer.Add(self.keyCtrl, 0, wx.ALL | wx.EXPAND, 5)
		
		btnSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		sizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
		
		self.SetSizer(sizer)
		sizer.Fit(self)

class Master2FAManager(wx.Dialog):
	def __init__(self, parent, plugin):
		super().__init__(parent, title="2Factor Authenticator Manager")
		self.plugin = plugin
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		wx.StaticText(self, label="Saved Accounts List:")
		
		self.accountsList = wx.ListBox(self, style=wx.LB_SINGLE)
		mainSizer.Add(self.accountsList, 1, wx.ALL | wx.EXPAND, 5)
		
		btnRowSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.addBtn = wx.Button(self, label="&Add Account")
		self.addBtn.Bind(wx.EVT_BUTTON, self.on_add_account)
		btnRowSizer.Add(self.addBtn, 0, wx.ALL, 5)
		
		self.deleteBtn = wx.Button(self, label="&Delete Account")
		self.deleteBtn.Bind(wx.EVT_BUTTON, self.on_delete_account)
		btnRowSizer.Add(self.deleteBtn, 0, wx.ALL, 5)
		
		self.copyBtn = wx.Button(self, label="&Copy OTP Code")
		self.copyBtn.Bind(wx.EVT_BUTTON, self.on_copy_otp)
		btnRowSizer.Add(self.copyBtn, 0, wx.ALL, 5)
		
		mainSizer.Add(btnRowSizer, 0, wx.ALIGN_CENTER, 5)
		
		closeBtnSizer = self.CreateButtonSizer(wx.CLOSE)
		mainSizer.Add(closeBtnSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
		
		self.SetSizer(mainSizer)
		self.refresh_list()
		self.SetMinSize((400, 300))
		mainSizer.Fit(self)
		
	def refresh_list(self):
		self.accountsList.Clear()
		self.plugin.config.reload()
		for account in sorted(self.plugin.config.keys()):
			self.accountsList.Append(account)
		if self.accountsList.GetCount() > 0:
			self.accountsList.SetSelection(0)

	def on_add_account(self, event):
		dlg = AddAccountDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			name = dlg.nameCtrl.GetValue().strip()
			secret = dlg.keyCtrl.GetValue().strip()
			if name and secret:
				self.plugin.config[name] = secret
				self.plugin.config.write()
				self.refresh_list()
				ui.message(f"{name} account saved.")
			else:
				ui.message("Error: Name and Secret required.")
		dlg.Destroy()

	def on_delete_account(self, event):
		selection = self.accountsList.GetStringSelection()
		if not selection:
			ui.message("No account selected.")
			return
		
		if wx.MessageBox(f"Are you sure you want to delete {selection}?", "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			del self.plugin.config[selection]
			self.plugin.config.write()
			self.refresh_list()
			ui.message(f"{selection} deleted.")

	def on_copy_otp(self, event):
		selection = self.accountsList.GetStringSelection()
		if not selection:
			ui.message("No account selected.")
			return
		self.plugin.copy_otp(selection)

# NVDA प्लगइन हैंडलर के लिए क्लास का नाम एकदम परफेक्ट होना अनिवार्य है
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		
		tools_dir = os.path.dirname(CONFIG_PATH)
		if not os.path.exists(tools_dir):
			os.makedirs(tools_dir)
			
		self.config = ConfigObj(CONFIG_PATH)
		
		self.menuItem = gui.mainFrame.sysTrayIcon.toolsMenu.Append(
			wx.ID_ANY, "2FA Manager..."
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.on_2fa_manager, self.menuItem)

	def on_2fa_manager(self, evt):
		wx.CallAfter(self._show_manager_gui)

	def _show_manager_gui(self):
		parent = gui.mainFrame
		dlg = Master2FAManager(parent, self)
		dlg.ShowModal()
		dlg.Destroy()

	def script_generateOTP(self, gesture):
		self.config.reload()
		accounts = list(self.config.keys())
		
		if not accounts:
			ui.message("No 2FA accounts found. Open 2FA Manager to add one.")
			return
			
		if len(accounts) == 1:
			self.copy_otp(accounts[0])
			return
			
		wx.CallAfter(self._show_selection_gui, accounts)

	def _show_selection_gui(self, accounts):
		parent = gui.mainFrame
		dlg = wx.SingleChoiceDialog(parent, "Select account for OTP:", "2Factor Authenticator", accounts)
		if dlg.ShowModal() == wx.ID_OK:
			selected_account = dlg.GetStringSelection()
			self.copy_otp(selected_account)
		dlg.Destroy()

	def copy_otp(self, account_name):
		try:
			secret = self.config.get(account_name)
			if not secret:
				ui.message("Secret not found.")
				return
				
			otp = get_totp_code(secret)
			if otp:
				if copy_to_windows_clipboard(otp):
					ui.message(f"OTP for {account_name} copied: {otp}")
				else:
					ui.message("Clipboard error.")
			else:
				ui.message("Invalid secret key format.")
		except Exception:
			ui.message("Error generating OTP.")

	__gestures = {
		"kb:NVDA+control+2": "generateOTP",
	}

	def terminate(self):
		try:
			gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self.menuItem)
		except Exception:
			pass