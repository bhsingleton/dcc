import os
import getpass

from .. import cmds, isConnected
from ..dialogs import qlogindialog
from ...decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Relogin(abstractdecorator.AbstractDecorator):
    """
    Overload of `AbstractDecorator` that prompts the user to login if their session has expired.
    """

    # region Dunderscores
    __slots__ = ()

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Check if server is available
        #
        connected = isConnected()

        if not connected:

            return

        # Evaluate expiration time
        #
        loginExpiration = cmds.loginExpiration()

        if loginExpiration > 0:

            return

        # Try remembered password
        #
        success = self.tryRememberedPassword()

        if success:

            return

        # Get existing password from user
        #
        password = self.getExistingPassword()

        if password is not None:

            # Evaluate login attempt
            #
            success = cmds.login(password)

            if success:

                return

            else:

                return self.__enter__()

        else:

            raise RuntimeError('Unable to renew perforce ticket!')

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        pass
    # endregion

    # region Methods
    def tryRememberedPassword(self):
        """
        Attempts to login using the P4PASSWD environment variable.

        :rtype: bool
        """

        # Check password variable
        #
        password = os.environ.get('P4PASSWD', None)

        if password is not None:

            return cmds.login(password)

        else:

            return False

    def getExistingPassword(self):
        """
        Returns a password from the user.

        :rtype: str
        """

        # Prompt user for password
        #
        username = os.environ.get('P4USER', getpass.getuser())
        port = os.environ.get('P4PORT', 'localhost:1666')

        dialog = qlogindialog.QLoginDialog(username=username, port=port)
        result = dialog.exec_()

        if result:

            # Check if password should be remembered
            #
            if dialog.rememberPassword:

                os.environ['P4PASSWD'] = dialog.password

            # Return decoded password
            #
            log.info('Successfully logged in!')
            return dialog.password

        else:

            log.info('Operation aborted...')
            return None
    # endregion
