from PySide2 import QtCore, QtWidgets, QtGui
from dcc.ui.dialogs import quicdialog

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QLoginDialog(quicdialog.QUicDialog):
    """
    Overload of QDialog use to renew the user's perforce login ticket.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Declare private variables
        #
        self._username = ''
        self._port = ''

        # Call parent method
        #
        super(QLoginDialog, self).__init__(*args, **kwargs)
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

        text = 'A password is required for user "{username}" on server "{port}".'.format(username=self.username, port=self.port)
        self.usernameLabel.setText(text)
    # endregion
