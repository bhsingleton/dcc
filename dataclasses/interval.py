from dataclasses import dataclass
from typing import Union
from . import adc
from ..generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Interval(adc.ADC):
    """
    Overload of `ADC` that interfaces with animation intervals.
    """

    # region Fields
    startTime: Union[int, float] = 0
    endTime: Union[int, float] = 1
    step: Union[int, float] = 1
    # endregion

    # region Dunderscores
    def __iter__(self):
        """
        Private method that returns a generator that yields frames from this interval.

        :rtype: Iterator[Union[int, float]]
        """

        return inclusiveRange(self.startTime, self.endTime, self.step)
    # endregion
