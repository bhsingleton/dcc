from abc import ABCMeta
from six import with_metaclass
from ... import fnscene, fnreference
from ...json import psonobject

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxBase(with_metaclass(ABCMeta, psonobject.PSONObject)):
    """
    Overload of PSONObject that acts as a base class for all fbx data objects.
    The dunderscore function set constructors are exposed for DCCs that require custom bindings.
    Especially, for instance, 3ds Max where XRef hasn't worked for over 20 years.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_name', '__weakref__')
    __scene__ = fnscene.FnScene
    __reference__ = fnreference.FnReference

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._scene = self.__scene__()
        self._name = kwargs.get('name', '')

        # Call parent method
        #
        super(FbxBase, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: fnscene.FnScene
        """

        return self._scene

    @property
    def name(self):
        """
        Getter method that returns the name of this object.

        :rtype: str
        """

        return self._name

    @name.setter
    def name(self, newName):
        """
        Setter method that updates the name of this object

        :type newName: str
        :rtype: None
        """

        self._name = newName
    # endregion

    # region Methods
    def absolutify(self, name, namespace):
        """
        Returns an absolute name using the supplied namespace.

        :type name: str
        :type namespace: str
        :rtype: str
        """

        if self.scene.isNullOrEmpty(namespace):

            return name

        else:

            return '{namespace}:{name}'.format(namespace=namespace, name=name)
    # endregion
