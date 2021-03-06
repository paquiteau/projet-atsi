"""
Online Gradient Operator
"""
import numpy as np
from mri.operators.gradient.gradient import GradAnalysis, GradSynthesis
from modopt.base.types import check_float, check_npndarray


class OnlineGradMixin:
    """ A Mixin Class For Gradient Operator"""
    @property
    def obs_data(self):
        """Observed Data

        Raises
        ------
        TypeError
            For invalid input type
        """
        return self._obs_data

    @obs_data.setter
    def obs_data(self, data):
        if self._grad_data_type in (float, np.floating):
            data = check_float(data)
        check_npndarray(data, dtype=self._grad_data_type, writeable=True)

        self._obs_data = data

    # TODO: define a vector cost, with offline comparison if available.


class OnlineGradSynthesis(OnlineGradMixin, GradSynthesis):
    pass

class OnlineGradAnalysis(OnlineGradMixin, GradAnalysis):
    pass
