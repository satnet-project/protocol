# coding=utf-8
import sys
import os

from PyQt4 import QtGui, QtCore
from Queue import Queue


"""
     Copyright 2015 Samuel Góngora García

     Licensed under the Apache License, Version 2.0 (the "License");
     you may not use this file except in compliance with the License.
     You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.

:Author:
    Samuel Góngora García (s.gongoragarcia@gmail.com)
"""
__author__ = 's.gongoragarcia@gmail.com'


# QDialog, QWidget or QMainWindow, which is better in this situation? TO-DO
class LogViewer(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 18))

        # enviromentDesktop = os.environ.get('DESKTOP_SESSION')

        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.read(".settings")
        name = config.get('Server', 'name')

        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        self.setFixedSize(1300, 800)
        self.setWindowTitle("SATNet protocol console - %s" % (name))

        filesAvailable = []
        filesAvailable = self.searchForLogs()
        self.initButtons(filesAvailable)
        self.initLogo()
        self.initConsole()

    def initUI(self):
        pass

    def initButtons(self, filesAvailable):
        # Control buttons.
        buttons = QtGui.QGroupBox(self)
        grid = QtGui.QGridLayout(buttons)
        buttons.setLayout(grid)

        # File selector
        self.LabelFile = QtGui.QComboBox()
        self.LabelFile.setFixedWidth(300)
        self.LabelFile.addItems(filesAvailable)
        self.LabelFile.activated.connect(self.openFile)
        # Configuration
        ButtonConfiguration = QtGui.QPushButton("Configuration")
        ButtonConfiguration.setToolTip("Open configuration window")
        ButtonConfiguration.setFixedWidth(145)
        # Help.
        ButtonHelp = QtGui.QPushButton("Help")
        ButtonHelp.setToolTip("Click for help")
        ButtonHelp.setFixedWidth(145)
        ButtonHelp.clicked.connect(self.usage)
        # Clear window
        ButtonClearWindow = QtGui.QPushButton("Clear Window")
        ButtonClearWindow.setToolTip("Click for clear the actual window")
        ButtonClearWindow.setFixedWidth(145)
        ButtonClearWindow.clicked.connect(self.clearWindow)
        # Clear file
        ButtonClearLog = QtGui.QPushButton("Clear Log")
        ButtonClearLog.setToolTip("Click for remove the actual log")
        ButtonClearLog.setFixedWidth(145)
        ButtonClearLog.clicked.connect(self.clearLog)

        grid.addWidget(self.LabelFile, 0, 0, 1, 2)
        grid.addWidget(ButtonConfiguration, 1, 0, 1, 1)
        grid.addWidget(ButtonHelp, 1, 1, 1, 1)
        grid.addWidget(ButtonClearWindow, 2, 0, 1, 1)
        grid.addWidget(ButtonClearLog, 2, 1, 1, 1)
        buttons.setTitle("Connection")
        buttons.move(10, 10)

    def initLogo(self):
        # Logo.
        LabelLogo = QtGui.QLabel(self)
        LabelLogo.move(1110, 10)
        pic = QtGui.QPixmap(os.getcwd() + "/logo.png")
        LabelLogo.setPixmap(pic)
        LabelLogo.show()

    def initConsole(self):
        self.console = QtGui.QTextBrowser(self)
        self.console.move(10, 200)
        self.console.resize(1280, 580)
        self.console.setFont(QtGui.QFont('SansSerif', 11))

    def usage(self):
        print "Log viewer for protocol logs of SATNet server and protocol."

    def searchForLogs(self):
        from os import listdir
        from os import path
        home = str(path.expanduser('~'))
        filesAvailable = listdir(home + '/.satnet/logs/')
        filesNeeded = []
        for i in range(len(filesAvailable)):
            if filesAvailable[i].startswith('satnet'):
                filesNeeded.append(filesAvailable[i])
        return filesNeeded

    def openFile(self):
        from os import path
        home = str(path.expanduser('~'))
        fileNeeded = str(self.LabelFile.currentText())
        fileNeeded = home + '/.satnet/logs/' + fileNeeded
        file = open(fileNeeded, 'r')
        print file.read()
        # Needs a new thread
        # timefile_old = os.stat(fileNeeded).st_mtime
        # while 1:
        #     timefile_new = os.stat(fileNeeded).st_mtime
        #     if timefile_new > timefile_old:
        #         timefile_old = timefile_new
        #         print file.read()

    def center(self):
        frameGm = self.frameGeometry()
        screen_pos = QtGui.QApplication.desktop().cursor().pos()
        screen = QtGui.QApplication.desktop().screenNumber(screen_pos)
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen
                                                                  ).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    # Functions designed to output information
    @QtCore.pyqtSlot(str)
    def append_text(self, text):
        self.console.moveCursor(QtGui.QTextCursor.End)
        self.console.insertPlainText(text)

    def clearWindow(self):
        self.console.clear()

    def clearLog(self):
        from os import path
        from os import remove
        home = str(path.expanduser('~'))
        log = str(self.LabelFile.currentText())
        filename = home + '/.satnet/logs/' + log
        open(filename, 'w').close()
        print "Log located at %s has been cleared." % (filename)
        # timefile = os.stat(filename).st_mtime
        # print timefile


# Objects designed for output the information
class WriteStream(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass

#  A QObject (to be run in a QThread) which sits waiting
#  for data to come  through a Queue.Queue().
#  It blocks until data is available, and one it has got something from
#  the queue, it sends it to the "MainThread" by emitting a Qt Signal


class MyReceiver(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, queue, *args, **kwargs):
        QtCore.QThread.__init__(self, *args, **kwargs)
        self.queue = queue

    @QtCore.pyqtSlot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)


class ResultObj(QtCore.QObject):
    def __init__(self, val):
        self.val = val


if __name__ == '__main__':
    queue = Queue()
    sys.stdout = WriteStream(queue)

    print('------------------------------------------------- ' +
          'SATNet - Protocol log viewer' +
          ' -------------------------------------------------')

    qapp = QtGui.QApplication(sys.argv)
    app = LogViewer()
    app.setWindowIcon(QtGui.QIcon('icono.png'))
    app.show()

    # Create thread that will listen on the other end of the
    # queue, and send the text to the textedit in our application
    my_receiver = MyReceiver(queue)
    my_receiver.mysignal.connect(app.append_text)
    my_receiver.start()

    sys.exit(qapp.exec_())
