import os

from functools import partial
from dcc.perforce import cmds
from dcc.perforce.dialogs import qlogindialog

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Relogin(object):
    """
    Base class used to evaluate the time before the user's perforce session expires.
    """

    # region Dunderscores
    __slots__ = ('_name', '_instance', '_owner', '_func')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(Relogin, self).__init__()

        # Declare public variables
        #
        self._instance = None
        self._owner = None
        self._func = None

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self._func = args[0]

    def __get__(self, instance, owner):
        """
        Private method called whenever this object is accessed via attribute lookup.

        :type instance: object
        :type owner: type
        :rtype: Undo
        """

        self._instance = instance
        self._owner = owner

        return self

    def __call__(self, *args, **kwargs):
        """
        Private method that is called whenever this instance is evoked.

        :type func: function
        :rtype: function
        """

        # Execute order of operations
        #
        self.__enter__()
        results = self.func(*args, **kwargs)
        self.__exit__(None, None, None)

        return results

    def __enter__(self, *args):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

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

    # region Properties
    @property
    def func(self):
        """
        Getter method used to return the wrapped function.
        If this is a descriptor then the function will be bound.

        :rtype: function
        """

        if self._instance is not None:

            return self._func.__get__(self._instance, self._owner)

        else:

            return self._func
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
        dialog = qlogindialog.QLoginDialog()
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


def relogin(*args, **kwargs):
    """
    Returns a function wrapper that evaluates the login expiration time.
    If the session has expired then a login dialog is displayed.

    :rtype: method
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs == 0:

        return partial(relogin, **kwargs)

    elif numArgs == 1:

        return Relogin(*args, **kwargs)

    else:

        raise TypeError('undo() expects at most 1 argument (%s given)!' % numArgs)

