from ...ui.dialogs import qmaindialog
from ...vendor.Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QLoginDialog(qmaindialog.QMainDialog):
    """
    Overload of `QMainDialog` that renew the user's perforce login ticket.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QLoginDialog, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._username = ''
        self._port = ''

        # Declare public variables
        #
        self.usernameLabel = None
        self.passwordLabel = None

        self.passwordLayout = None
        self.passwordWidget = None
        self.passwordLineEdit = None
        self.rememberPasswordCheckBox = None

        self.buttonsLayout = None
        self.buttonsWidget = None
        self.horizontalSpacer = None
        self.okayPushButton = None
        self.cancelPushButton = None

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QLoginDialog, self).__setup_ui__(*args, **kwargs)

        # Initialize dialog
        #
        self.setWindowTitle("|| Perforce Password Required")
        self.setMinimumSize(QtCore.QSize(600, 150))

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)

        # Initialize labels
        #
        self.usernameLabel = QtWidgets.QLabel('')
        self.usernameLabel.setObjectName('usernameLabel')
        self.usernameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.usernameLabel.setFixedHeight(24)

        self.passwordLabel = QtWidgets.QLabel('Please enter the password:')
        self.passwordLabel.setObjectName('passwordLabel')
        self.passwordLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.passwordLabel.setFixedHeight(24)

        centralLayout.addWidget(self.usernameLabel)
        centralLayout.addWidget(self.passwordLabel)

        # Initialize password widget
        #
        self.passwordLayout = QtWidgets.QHBoxLayout()
        self.passwordLayout.setObjectName('passwordLayout')
        self.passwordLayout.setContentsMargins(0, 0, 0, 0)

        self.passwordWidget = QtWidgets.QWidget()
        self.passwordWidget.setObjectName('passwordWidget')
        self.passwordWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.passwordWidget.setFixedHeight(24)
        self.passwordWidget.setLayout(self.passwordLayout)

        self.passwordLineEdit = QtWidgets.QLineEdit('')
        self.passwordLineEdit.setObjectName('passwordWidget')
        self.passwordLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.passwordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)

        self.rememberPasswordCheckBox = QtWidgets.QCheckBox('Remember Password')
        self.rememberPasswordCheckBox.setObjectName('passwordWidget')
        self.rememberPasswordCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred))

        self.passwordLayout.addWidget(self.passwordLineEdit)
        self.passwordLayout.addWidget(self.rememberPasswordCheckBox)

        centralLayout.addWidget(self.passwordWidget)

        # Initialize button widget
        #
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName('buttonsLayout')
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)

        self.buttonsWidget = QtWidgets.QWidget()
        self.buttonsWidget.setObjectName('buttonsWidget')
        self.buttonsWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.buttonsWidget.setFixedHeight(24)
        self.buttonsWidget.setLayout(self.buttonsLayout)

        self.horizontalSpacer = QtWidgets.QSpacerItem(50, 24, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.okayPushButton = QtWidgets.QPushButton('OK')
        self.okayPushButton.setObjectName('okayPushButton')
        self.okayPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.okayPushButton.clicked.connect(self.accept)

        self.cancelPushButton = QtWidgets.QPushButton('Cancel')
        self.cancelPushButton.setObjectName('cancelPushButton')
        self.cancelPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.cancelPushButton.clicked.connect(self.reject)

        self.buttonsLayout.addItem(self.horizontalSpacer)
        self.buttonsLayout.addWidget(self.okayPushButton)
        self.buttonsLayout.addWidget(self.cancelPushButton)

        centralLayout.addWidget(self.buttonsWidget)
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
        Getter method that returns the current password.

        :rtype: str
        """

        return self.passwordLineEdit.text()

    @password.setter
    def password(self, password):
        """
        Setter method that updates the current password.

        :type password: str
        :rtype: None
        """

        self.passwordLineEdit.setText(password)

    @property
    def rememberPassword(self):
        """
        Getter method that returns the remember-password flag.

        :rtype: bool
        """

        return self.rememberPasswordCheckBox.isChecked()

    @rememberPassword.setter
    def rememberPassword(self, rememberPassword):
        """
        Setter method that updates the remember-password flag.

        :type rememberPassword: bool
        :rtype: None
        """

        self.rememberPasswordCheckBox.setChecked(rememberPassword)
    # endregion

    # region Methods
    def invalidate(self):
        """
        Forces the dialog to re-concatenate its display text.

        :rtype: None
        """

        text = 'A password is required for user "{username}" on server "{port}".'.format(
            username=self.username,
            port=self.port
        )

        self.usernameLabel.setText(text)
    # endregion
