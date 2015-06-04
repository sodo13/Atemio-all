from enigma import eTimer, eConsoleAppContainer
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Tools.Directories import fileExists
from os import remove
from Tools.BoundFunction import boundFunction
from Components.ScrollLabel import ScrollLabel
from Components.config import config

class AtemioDownloader(Screen):

	EVENT_DONE = 10
	EVENT_KILLED = 5
	EVENT_CURR = 0

	def __init__(self, session, url, folder, filename):
		screen = """
		  <screen  flags="wfNoBorder" position="0,0" size="1280,720" backgroundColor="transparent">
		  <widget source="fname" render="Label" position="610,147" size="580,75" font="Regular;18" halign="center" valign="center"  transparent="1" />
		  <widget source="progressbar" render="Progress" pixmap="icons/bar_downloader.png" position="610,233" size="580,12" zPosition="2" transparent="1" />
		  <widget source="status" render="Label" position="610,258" zPosition="3" size="580,71" font="Regular;22" halign="center" transparent="1" />
		</screen>"""
		Screen.__init__(self, session)
		self.url = url
		self.filename = filename
		self.dstfilename = folder + filename
		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["fname"] = StaticText('')
		self["status"] = StaticText('')
		self["progressbar"] = Progress()
		self["progressbar"].range = 1000
		self["progressbar"].value = 0
		self["actions"] = ActionMap(["WizardActions", "DirectionActions",'ColorActions'], 
		{
			"ok": self.cancel,
			"back": self.cancel,
			"red": self.stop,
			"green": self.cancel
		}, -1)
		self.autoCloseTimer = eTimer()
		self.autoCloseTimer.timeout.get().append(self.cancel)
		self.startDownloadTimer = eTimer()
		self.startDownloadTimer.timeout.get().append(self.fileDownload)
		self.download = None
		self.downloading(False)
		self.onShown.append(self.setWindowTitle)
		self.onLayoutFinish.append(self.startDownload)

	def setWindowTitle(self):
		self.setTitle(_("Downloading..."))

	def startDownload(self):
		self["progressbar"].value = 0
		self.startDownloadTimer.start(250,True)

	def downloading(self, state=True):
		if state:	
			self["canceltext"].show()
			self["oktext"].hide()
		else:
			self.download = None
			self["canceltext"].hide()
			self["oktext"].show()

	def fileDownload(self):
		from Tools.Downloader import downloadWithProgress
		#print "[download] downloading %s to %s" % (self.url, self.dstfilename)
		self.download = downloadWithProgress(self.url, self.dstfilename)
		self.download.addProgress(self.progress)
		self.download.start().addCallback(self.finished).addErrback(self.failed)
		self.downloading(True)
		self["fname"].text = _("Downloading file: %s ...") % (self.filename)

	def progress(self, recvbytes, totalbytes):
		if self.download:
			self["progressbar"].value = int(1000*recvbytes/float(totalbytes))
			self["status"].text = "%d of %d kBytes (%.2f%%)" % (recvbytes/1024, totalbytes/1024, 100*recvbytes/float(totalbytes))

	def failed(self, failure_instance=None, error_message=""):
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
		#print "[Download_failed] " + error_message
		if fileExists(self.dstfilename):
			remove(self.dstfilename)
		self["fname"].text = _("Download file %s failed!") % (self.filename)
		self["status"].text = error_message
		self.EVENT_CURR = self.EVENT_KILLED
		self.downloading(False)

	def finished(self, string = ""):
		if self.download:
			#print "[Download_finished] " + str(string)
			self.EVENT_CURR = self.EVENT_DONE
			self.downloading(False)
			self["oktext"].hide()
			self["fname"].text = _("Download file %s finished!") % (self.filename)
			self["status"].text = ''
			self.autoCloseTimer.start(200)

	def stop(self):
		if self.download:
			self.download.stop()
			self.downloading(False)
			if fileExists(self.dstfilename):
				remove(self.dstfilename)
			self.EVENT_CURR = self.EVENT_KILLED
			self["fname"].text = _("Downloading killed by user!")
			self["status"].text = _("Press OK to close window.")

	def cancel(self):
		if self.download == None:
			self.close(self.EVENT_CURR)


class AtemioConsole(Screen):

	EVENT_DONE = 10
	EVENT_KILLED = 5
	EVENT_CURR = 0

	def __init__(self, session, cmd, Wtitle, large = False):
		Screen.__init__(self, session)
		if large:
			self.skinName = 'AtemioConsoleL'
		lang = config.osd.language.getText()
		self.cmd = cmd
		self.Wtitle = Wtitle
		self.callbackList = []
		self["text"] = ScrollLabel("")
		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["actions"] = ActionMap(["WizardActions", "DirectionActions",'ColorActions'], 
		{
			"ok": self.cancel,
			"back": self.cancel,
			"up": self["text"].pageUp,
			"down": self["text"].pageDown,
			"red": self.stop,
			"green": self.cancel
		}, -1)
		self["oktext"].hide()
		self.autoCloseTimer = eTimer()
		self.autoCloseTimer.timeout.get().append(self.cancel)
		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.runFinished)
		self.container.dataAvail.append(self.dataAvail)
		self.onLayoutFinish.append(self.startRun)
		self.onShown.append(self.setWindowTitle)

	def setWindowTitle(self):
		self.setTitle(self.Wtitle)

	def startRun(self):
		#print "Console: executing in run the command:", self.cmd
		if self.container.execute(self.cmd):
			self.runFinished(-1)

	def runFinished(self, retval):
		self.EVENT_CURR = self.EVENT_DONE
		self["text"].setText(self["text"].getText() + _('Done') + '\n')
		self["canceltext"].hide()
		if config.atemio.autocloseconsole.value:
			if int(config.atemio.autocloseconsoledelay.value) != 0:
				self.autoCloseTimer.startLongTimer(int(config.atemio.autocloseconsoledelay.value))
			else:
				self.cancel()
		else:
			self["text"].setText(self["text"].getText() + _('Please Press OK Button to close windows!') + '\n')
			self["oktext"].show()

	def stop(self):
		if self.isRunning():
			self.EVENT_CURR = self.EVENT_KILLED
			self["text"].setText(self["text"].getText() + _('Action killed by user') + '\n')
			self.container.kill()
			self["canceltext"].hide()
			if config.atemio.autocloseconsole.value:
				if int(config.atemio.autocloseconsoledelay.value) != 0:
					self.autoCloseTimer.startLongTimer(int(config.atemio.autocloseconsoledelay.value))
				else:
					self.cancel()
			else:
				self["text"].setText(self["text"].getText() + _('Please Press OK Button to close windows!') + '\n')
				self["oktext"].show()

	def cancel(self):
		if not self.isRunning():
			if self.autoCloseTimer.isActive():
				self.autoCloseTimer.stop()
			del self.autoCloseTimer
			self.container.appClosed.remove(self.runFinished)
			self.container.dataAvail.remove(self.dataAvail)
			del self.container.dataAvail[:]
			del self.container.appClosed[:]
			del self.container
			self.close(self.EVENT_CURR)

	def dataAvail(self, str):
		self["text"].setText(self["text"].getText() + str)

	def isRunning(self):
		return self.container.running()
