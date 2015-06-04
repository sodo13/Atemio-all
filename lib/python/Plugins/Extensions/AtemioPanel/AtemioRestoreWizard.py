from Components.About import about
from Components.Console import Console
from Components.config import config, configfile
from Components.Pixmap import Pixmap, MovingPixmap, MultiPixmap
from Components.Harddisk import harddiskmanager
from Screens.Wizard import wizardManager, WizardSummary
from Screens.WizardLanguage import WizardLanguage
from Screens.Rc import Rc
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists, pathExists, resolveFilename, SCOPE_PLUGINS
from os import mkdir, listdir, path, walk
from boxbranding import getMachineBrand, getMachineName

class AtemioRestoreWizard(WizardLanguage, Rc):
	def __init__(self, session):
		self.xmlfile = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/AtemioCore/restorewizard.xml")
		WizardLanguage.__init__(self, session, showSteps = False, showStepSlider = False)
		Rc.__init__(self)
		self.session = session
		self.skinName = "StartWizard"
#		self.skin = "StartWizard.skin"
		self["wizard"] = Pixmap()
		self.selectedAction = None
		self.NextStep = None
		self.Text = None
		self.buildListRef = None
		self.didSettingsRestore = False
		self.didPluginRestore = False
		self.PluginsRestore = False
		self.fullbackupfilename = None
		self.delaymess = None
		self.Console = Console()

	def getTranslation(self, text):
		return _(text).replace("%s %s","%s %s" % (getMachineBrand(), getMachineName()))

	def listDevices(self):
		devices = [(r.description, r.mountpoint) for r in harddiskmanager.getMountedPartitions(onlyhotplug = False)]
		list = []
		files = []
		for x in devices:
			if x[1] == '/':
				devices.remove(x)
		if len(devices):
			for x in devices:
				devpath = path.join(x[1],'backup')
				if path.exists(devpath):
					try:
						files = listdir(devpath)
					except:
						files = []
				else:
					files = []
				if len(files):
					for file in files:
						if file.endswith('.tar.gz'):
							list.append((path.join(devpath,file),path.join(devpath,file)))
		if len(list):
			list.sort()
			list.reverse()
		return list

	def settingsdeviceSelectionMade(self, index):
		self.selectedAction = index
		self.settingsdeviceSelect(index)

	def settingsdeviceSelect(self, index):
		self.selectedDevice = index
		self.fullbackupfilename = index
 		self.NextStep = 'settingrestorestarted'

	def settingsdeviceSelectionMoved(self):
		self.settingsdeviceSelect(self.selection)

	def pluginsdeviceSelectionMade(self, index):
		self.selectedAction = index
		self.pluginsdeviceSelect(index)

	def pluginsdeviceSelect(self, index):
		self.selectedDevice = index
		self.fullbackupfilename = index
 		self.NextStep = 'plugindetection'

	def pluginsdeviceSelectionMoved(self):
		self.pluginsdeviceSelect(self.selection)

	def markDone(self):
		pass

	def listAction(self):
		list = []
		list.append((_("OK, to perform a restore"), "settingsquestion"))
		list.append((_("Exit the restore wizard"), "end"))
		return list

	def listAction2(self):
		list = []
		list.append((_("YES, to restore settings"), "settingsrestore"))
		list.append((_("NO, do not restore settings"), "pluginsquestion"))
		return list

	def listAction3(self):
		list = []
		if self.didSettingsRestore:
			list.append((_("YES, to restore plugins"), "pluginrestore"))
			list.append((_("NO, do not restore plugins"), "reboot"))
		else:
			list.append((_("YES, to restore plugins"), "pluginsrestoredevice"))
			list.append((_("NO, do not restore plugins"), "end"))
		return list

	def rebootAction(self):
		list = []
		list.append((_("OK"), "reboot"))
		return list

	def ActionSelectionMade(self, index):
		self.selectedAction = index
		self.ActionSelect(index)

	def ActionSelect(self, index):
		self.NextStep = index

	def ActionSelectionMoved(self):
		self.ActionSelect(self.selection)

	def buildList(self,action):
		if self.NextStep is 'reboot':
			self.Console.ePopen("init 4 && reboot")
		elif self.NextStep is 'settingsquestion' or self.NextStep is 'settingsrestore' or self.NextStep is 'pluginsquestion' or self.NextStep is 'pluginsrestoredevice' or self.NextStep is 'end' or self.NextStep is 'noplugins':
			self.buildListfinishedCB(False)
		elif self.NextStep is 'settingrestorestarted':
			self.Console.ePopen("tar -xzvf " + self.fullbackupfilename + " tmp/ExtraInstalledPlugins tmp/backupkernelversion tmp/backupimageversion -C /", self.settingsRestore_Started)
			self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("Please wait while gathers information..."), type = MessageBox.TYPE_INFO, enable_input = False, wizard = True)
			self.buildListRef.setTitle(_("Restore Wizard"))
		elif self.NextStep is 'plugindetection':
			print '[RestoreWizard] Stage 2: Restoring plugins'
			self.Console.ePopen("tar -xzvf " + self.fullbackupfilename + " tmp/ExtraInstalledPlugins tmp/backupkernelversion tmp/backupimageversion -C /", self.pluginsRestore_Started)
			self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("Please wait while gathers information..."), type = MessageBox.TYPE_INFO, enable_input = False, wizard = True)
			self.buildListRef.setTitle(_("Restore Wizard"))
		elif self.NextStep is 'pluginrestore':
			if self.feeds == 'OK':
				print '[RestoreWizard] Stage 6: Feeds OK, Restoring Plugins'
				self.Console.ePopen("opkg install " + self.pluginslist + ' ' + self.pluginslist2, self.pluginsRestore_Finished)
				self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("Please wait while plugins restore completes..."), type = MessageBox.TYPE_INFO, enable_input = False, wizard = True)
				self.buildListRef.setTitle(_("Restore Wizard"))
			elif self.feeds == 'DOWN':
				print '[RestoreWizard] Stage 6: Feeds Down'
				config.misc.restorewizardrun.setValue(True)
				config.misc.restorewizardrun.save()
				configfile.save()
				self.didPluginRestore = True
				self.NextStep = 'reboot'
				self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("Sorry feeds are down for maintenance, Please try using Backup Manager to restore plugins later."), type = MessageBox.TYPE_INFO, timeout = 30, wizard = True)
				self.buildListRef.setTitle(_("Restore Wizard"))
			elif self.feeds == 'BAD':
				print '[RestoreWizard] Stage 6: No Network'
				config.misc.restorewizardrun.setValue(True)
				config.misc.restorewizardrun.save()
				configfile.save()
				self.didPluginRestore = True
				self.NextStep = 'reboot'
				self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("Your %s %s is not connected to the internet, Please try using Backup Manager to restore plugins later.") % (getMachineBrand(), getMachineName()), type = MessageBox.TYPE_INFO, timeout = 30, wizard = True)
				self.buildListRef.setTitle(_("Restore Wizard"))
			elif self.feeds == 'ERROR':
				self.NextStep = 'pluginrestore'
				self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("A background update check is is progress, please wait for retry."), type = MessageBox.TYPE_INFO, timeout = 10, wizard = True)
				self.buildListRef.setTitle(_("Restore Wizard"))

	def buildListfinishedCB(self,data):
		# self.buildListRef = None
		if data is True:
			self.currStep = self.getStepWithID(self.NextStep)
			self.afterAsyncCode()
		else:
			self.currStep = self.getStepWithID(self.NextStep)
			self.afterAsyncCode()

	def settingsRestore_Started(self, result, retval, extra_args = None):
		self.doRestoreSettings1()

	def doRestoreSettings1(self):
		print '[RestoreWizard] Stage 1: Check Version'
		if fileExists('/tmp/backupimageversion'):
			imageversion = file('/tmp/backupimageversion').read()
			print 'Backup Image:',imageversion
			print 'Current Image:',about.getVersionString()
			if imageversion == about.getVersionString():
				print '[RestoreWizard] Stage 1: Image ver OK'
				self.doRestoreSettings2()
			else:
				print '[RestoreWizard] Stage 1: Image ver Differant'
				self.noVersion = self.session.openWithCallback(self.doNoVersion, MessageBox, _("Sorry, but the file is not compatible with this image version."), type = MessageBox.TYPE_INFO, timeout = 30, wizard = True)
				self.noVersion.setTitle(_("Restore Wizard"))
		else:
			print '[RestoreWizard] Stage 1: No Image ver to check'
			self.noVersion = self.session.openWithCallback(self.doNoVersion, MessageBox, _("Sorry, but the file is not compatible with this image version."), type = MessageBox.TYPE_INFO, timeout = 30, wizard = True)
			self.noVersion.setTitle(_("Restore Wizard"))

	def doNoVersion(self, result = None, retval = None, extra_args = None):
		self.buildListRef.close(True)

	def doRestoreSettings2(self):
		print '[RestoreWizard] Stage 2: Restoring settings'
		self.Console.ePopen("tar -xzvf " + self.fullbackupfilename + " -C /", self.settingRestore_Finished)
		self.pleaseWait = self.session.open(MessageBox, _("Please wait while settings restore completes..."), type = MessageBox.TYPE_INFO, enable_input = False, wizard = True)
		self.pleaseWait.setTitle(_("Restore Wizard"))

	def settingRestore_Finished(self, result, retval, extra_args = None):
		self.didSettingsRestore = True
		configfile.load()
		# self.NextStep = 'plugindetection'
		self.pleaseWait.close()
		self.doRestorePlugins1()

	def pluginsRestore_Started(self, result, retval, extra_args = None):
		self.doRestorePlugins1()

	def pluginsRestore_Finished(self, result, retval, extra_args = None):
		config.misc.restorewizardrun.setValue(True)
		config.misc.restorewizardrun.save()
		configfile.save()
		self.didPluginRestore = True
		self.NextStep = 'reboot'
		self.buildListRef.close(True)

	def doRestorePlugins1(self):
		print '[RestoreWizard] Stage 3: Check Kernel'
		if fileExists('/tmp/backupkernelversion') and fileExists('/tmp/backupimageversion'):
			imageversion = file('/tmp/backupimageversion').read()
			kernelversion = file('/tmp/backupkernelversion').read()
			print 'Backup Image:',imageversion
			print 'Current Image:',about.getVersionString()
			print 'Backup Kernel:',kernelversion
			print 'Current Kernel:',about.getKernelVersionString()
			if kernelversion == about.getKernelVersionString() and imageversion == about.getVersionString():
				print '[RestoreWizard] Stage 3: Kernel and image ver OK'
				self.doRestorePluginsTest()
			else:
				print '[RestoreWizard] Stage 3: Kernel or image ver Differant'
				if self.didSettingsRestore:
					self.NextStep = 'reboot'
				else:
					self.NextStep = 'noplugins'
				self.buildListRef.close(True)
		else:
			print '[RestoreWizard] Stage 3: No Kernel to check'
			if self.didSettingsRestore:
				self.NextStep = 'reboot'
			else:
				self.NextStep = 'noplugins'
			self.buildListRef.close(True)

	def doRestorePluginsTest(self, result = None, retval = None, extra_args = None):
		if self.delaymess:
			self.delaymess.close()
		print '[RestoreWizard] Stage 4: Feeds Test'
		self.Console.ePopen('opkg update', self.doRestorePluginsTestComplete)

	def doRestorePluginsTestComplete(self, result = None, retval = None, extra_args = None):
		print '[RestoreWizard] Stage 4: Feeds Test Result',result
		if result.find('bad address') != -1:
			self.NextStep = 'reboot'
			self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("Your %s %s is not connected to the internet, Please try using Backup Manager to restore plugins later.") % (getMachineBrand(), getMachineName()), type = MessageBox.TYPE_INFO, timeout = 30, wizard = True)
			self.buildListRef.setTitle(_("Restore Wizard"))
		elif result.find('wget returned 1') != -1 or result.find('wget returned 255') != -1 or result.find('404 Not Found') != -1:
			self.NextStep = 'reboot'
			self.buildListRef = self.session.openWithCallback(self.buildListfinishedCB, MessageBox, _("Sorry feeds are down for maintenance, Please try using Backup Manager to restore plugins later."), type = MessageBox.TYPE_INFO, timeout = 30, wizard = True)
			self.buildListRef.setTitle(_("Restore Wizard"))
		elif result.find('Collected errors') != -1:
			print '[RestoreWizard] Stage 4: Update is in progress, delaying'
			self.delaymess = self.session.openWithCallback(self.doRestorePluginsTest, MessageBox, _("A background update check is is progress, please wait for retry."), type = MessageBox.TYPE_INFO, timeout = 10, wizard = True)
			self.delaymess.setTitle(_("Restore Wizard"))
		else:
			print '[RestoreWizard] Stage 4: Feeds OK'
			self.feeds = 'OK'
			self.doListPlugins()

	def doListPlugins(self):
		print '[RestoreWizard] Stage 4: Feeds Test'
		self.Console.ePopen('opkg list-installed', self.doRestorePlugins2)

	def doRestorePlugins2(self, result, retval, extra_args):
		print '[RestoreWizard] Stage 5: Build list of plugins to restore'
		self.pluginslist = ""
		self.pluginslist2 = ""
		if path.exists('/tmp/ExtraInstalledPlugins'):
			self.pluginslist = []
			plugins = []
			for line in result.split('\n'):
				if line:
					parts = line.strip().split()
					plugins.append(parts[0])
			tmppluginslist = open('/tmp/ExtraInstalledPlugins', 'r').readlines()
			for line in tmppluginslist:
				if line:
					parts = line.strip().split()
					if parts[0] not in plugins:
						self.pluginslist.append(parts[0])

		if path.exists('/tmp/3rdPartyPlugins'):
			self.pluginslist2 = []
			if path.exists('/tmp/3rdPartyPluginsLocation'):
				self.thirdpartyPluginsLocation = open('/tmp/3rdPartyPluginsLocation', 'r').readlines()
				self.thirdpartyPluginsLocation = "".join(self.thirdpartyPluginsLocation)
				self.thirdpartyPluginsLocation = self.thirdpartyPluginsLocation.replace('\n','')
				self.thirdpartyPluginsLocation = self.thirdpartyPluginsLocation.replace(' ', '%20')
			else:
				self.thirdpartyPluginsLocation = " "

			tmppluginslist2 = open('/tmp/3rdPartyPlugins', 'r').readlines()
			available = None
			for line in tmppluginslist2:
				if line:
					parts = line.strip().split('_')
					if parts[0] not in plugins:
						ipk = parts[0]
						if path.exists(self.thirdpartyPluginsLocation):
							available = listdir(self.thirdpartyPluginsLocation)
						else:
							for root, subFolders, files in walk('/media'):
								for folder in subFolders:
									if folder and folder == path.split(self.thirdpartyPluginsLocation[:-1])[-1]:
										self.thirdpartyPluginsLocation = path.join(root,folder)
										self.thirdpartyPluginsLocation = self.thirdpartyPluginsLocation.replace(' ', '%20')
										available = listdir(self.thirdpartyPluginsLocation)
										break
						if available:
							for file in available:
								if file:
									fileparts = file.strip().split('_')
									if fileparts[0] == ipk:
										self.thirdpartyPluginsLocation = self.thirdpartyPluginsLocation.replace(' ', '%20')
										ipk = path.join(self.thirdpartyPluginsLocation, file)
										if path.exists(ipk):
											self.pluginslist2.append(ipk)

		if len(self.pluginslist) or len(self.pluginslist2):
			self.doRestorePluginsQuestion()
		else:
			if self.didSettingsRestore:
				self.NextStep = 'reboot'
			else:
				self.NextStep = 'noplugins'
			self.buildListRef.close(True)

	def doRestorePluginsQuestion(self):
		if len(self.pluginslist) or len(self.pluginslist2):
			if len(self.pluginslist):
				self.pluginslist = " ".join(self.pluginslist)
			else:
				self.pluginslist = ""
			if len(self.pluginslist2):
				self.pluginslist2 = " ".join(self.pluginslist2)
			else:
				self.pluginslist2 = ""
			print '[RestoreWizard] Stage 6: Plugins to restore in feeds',self.pluginslist
			print '[RestoreWizard] Stage 6: Plugins to restore in extra location',self.pluginslist2
			if self.didSettingsRestore:
				print '[RestoreWizard] Stage 6: proceed to question'
				self.NextStep = 'pluginsquestion'
				self.buildListRef.close(True)
			else:
				print '[RestoreWizard] Stage 6: proceed to restore'
				self.NextStep = 'pluginrestore'
				self.buildListRef.close(True)
		else:
			print '[RestoreWizard] Stage 6: NO Plugins to restore'
			if self.didSettingsRestore:
				self.NextStep = 'reboot'
			else:
				self.NextStep = 'noplugins'
		self.buildListRef.close(True)