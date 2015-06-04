from enigma import *
from Screens.Screen import Screen
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap

class AboutTeam(Screen):
    skin = """
    <screen name="AboutTeam" position="0,0" size="1280,720" title="About Team" flags="wfNoBorder" >
        <panel name="GenericLayoutLiteTemplate" /> 
        <widget name="about" font="Regular;24" position="65,80" size="680,490" halign="center" transparent="1" backgroundColor="background" />
    </screen>"""

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        abouttxt = '\nAtemio4you OpenGl Xbmc Image :\n\n- SODO (Developer)\n- mmark (Graphics and Skin) \n\n- Further credits goes to:\n SODO...\n\n- Project for This Image\n\n- Oe-Alliance OE CORE 3.0 \n\n>>>>>>>>>>READ PLEASE<<<<<<<<<<\n\n- This Image Based On VIX-enigma2 Source code Included last Driver for GLS And XBMC and New Feed For Plugins And Softcam\n\n'
        self['about'] = Label(abouttxt)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'cancel': self.quit}, -2)

    def quit(self):
        self.close()

####### Utils For Extra #####
from os import system, statvfs, remove

class AtemioUtils:

	def readExtraUrl(self):
		try:
			#os.system("dos2unix /var/etc/extra.url");
			f = open("/var/etc/atemio_extra.url", "r")
			line = f.readline() [:-1]
			f.close()
			return line
		except:
			return None

	def getVarSpace(self):
		free = -1
		try:
			s = statvfs("/")
		except OSError:
			return free
		free = s.f_bfree/1024 * s.f_bsize/1024
		return s.f_bfree/1024 * (s.f_bsize / 1024)	

	def getVarSpaceKb(self):
		try:
			s = statvfs("/")
		except OSError:
			return 0,0
		return float(s.f_bfree * (s.f_bsize / 1024)), float(s.f_blocks * (s.f_bsize / 1024))
