import os
import getpass
import base64

from PySide2 import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QLoginDialog(QtWidgets.QDialog):
    """
    Overload of QDialog use to renew the user's perforce login ticket.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :keyword parent: QtWidgets.QWidget
        :keyword f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.get('parent', QtWidgets.QApplication.activeWindow())
        f = kwargs.get('f', QtCore.Qt.WindowFlags())

        super(QLoginDialog, self).__init__(parent=parent, f=f)

        # Declare private variables
        #
        self._username = kwargs.get('username', '')
        self._port = kwargs.get('port', 'localhost:1666')
        self._password = ''

        # Build user interface
        #
        self.__build__(*args, **kwargs)

        # Check if any arguments were supplied
        #
        numArgs = len(args)

        if numArgs == 0:

            self.username = os.environ.get('P4USER', getpass.getuser())
            self.port = os.environ.get('P4PORT', 'localhost:1666')

        elif numArgs == 1:

            self.username = args[0]
            self.port = os.environ.get('P4PORT', 'localhost:1666')

        else:

            self.username = args[0]
            self.port = args[1]

    def __build__(self, *args, **kwargs):
        """
        Private method that builds the user interface.

        :rtype: None
        """

        # Edit dialog properties
        #
        self.setObjectName('loginDialog')
        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setMinimumSize(QtCore.QSize(600, 150))
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('Perforce Password Required')

        # Create password widgets
        #
        self.usernameLabel = QtWidgets.QLabel('')
        self.usernameLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.usernameLabel.setFixedHeight(24)

        self.passwordLabel = QtWidgets.QLabel('Please enter the password:')
        self.passwordLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.passwordLabel.setFixedHeight(24)

        self.passwordLineEdit = QtWidgets.QLineEdit('')
        self.passwordLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.passwordLineEdit.setFixedHeight(24)
        self.passwordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)

        # Create buttons
        #
        self.buttonSpacerItem = QtWidgets.QSpacerItem(0, 24, hData=QtWidgets.QSizePolicy.Expanding, vData=QtWidgets.QSizePolicy.Fixed)

        self.okayPushButton = QtWidgets.QPushButton('Okay')
        self.okayPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.okayPushButton.setFixedHeight(24)
        self.okayPushButton.pressed.connect(self.accept)

        self.cancelPushButton = QtWidgets.QPushButton('Cancel')
        self.cancelPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.cancelPushButton.setFixedHeight(24)
        self.cancelPushButton.pressed.connect(self.reject)

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addSpacerItem(self.buttonSpacerItem)
        self.buttonLayout.addWidget(self.okayPushButton)
        self.buttonLayout.addWidget(self.cancelPushButton)

        # Assign central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.addWidget(self.usernameLabel)
        centralLayout.addWidget(self.passwordLabel)
        centralLayout.addWidget(self.passwordLineEdit)
        centralLayout.addLayout(self.buttonLayout)

        self.setLayout(centralLayout)
    # endregion

    # region Properties
    @property
    def username(self):
        """
        Getter method that returns the current username.

        :rtype: str
        """

        return self._username

    @username.setter
    def username(self, username):
        """
        Setter method that updates the current username.

        :type username: str
        :rtype: None
        """

        self._username = username
        self.invalidate()

    @property
    def port(self):
        """
        Getter method that returns the current server address.

        :rtype: str
        """

        return self._port

    @port.setter
    def port(self, port):
        """
        Setter method that updates the current address.

        :type port: str
        :rtype: None
        """

        self._port = port
        self.invalidate()

    @property
    def password(self):
        """
        Returns the entered password.

        :rtype: str
        """

        return base64.b64decode(self._password).decode('utf-8')
    # endregion

    # region Methods
    def invalidate(self):
        """
        Forces the dialog to re-concatenate its display text.

        :rtype: None
        """

        text = 'A password is required for user "{username}" on server "{port}".'.format(username=self.username, port=self.port)
        self.usernameLabel.setText(text)
    # endregion

    # region Slots
    def accept(self):
        """
        Hides the modal dialog and sets the result code to QDialogCode.Accepted.

        :rtype: None
        """

        # Store encoded password
        #
        print(self.size())
        self._password = base64.b64encode(self.passwordLineEdit.text().encode('utf-8'))

        # Call parent method
        #
        super(QLoginDialog, self).accept()
    # endregion
