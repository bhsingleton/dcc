import re

from ...python import stringutils
from ...vendor.Qt import QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QSlugValidator(QtGui.QValidator):
    """
    Overload of `QValidator` that removes illegal character from input strings.
    """

    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: Union[QtWidgets.QObject, None]
        :rtype: None
        """

        # Call parent method
        #
        super(QSlugValidator, self).__init__(parent=parent)

        # Declare private variables
        #
        self._illegalRegex = re.compile(r'[^\w\s-]')
        self._whitespaceRegex = re.compile(r'[-\s]+')

    def fixup(self, input):
        """
        This function attempts to change input to be valid according to this validator’s rules.

        :type input: str
        :rtype: str
        """

        return stringutils.slugify(input)

    def validate(self, input, pos):
        """
        This function returns `Invalid` if input is invalid according to this validator’s rules,
        `Intermediate` if it is likely that a little more editing will make the input acceptable,
        and `Acceptable` if the input is valid.

        :type input: str
        :type pos: int
        :rtype: QtGui.QValidator.State
        """

        isIllegal = not stringutils.isNullOrEmpty(self._illegalRegex.findall(input))
        hasWhitespace = not stringutils.isNullOrEmpty(self._whitespaceRegex.findall(input))

        if isIllegal or hasWhitespace:

            return self.State.Invalid

        else:

            return self.State.Acceptable