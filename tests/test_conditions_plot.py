import unittest
from unittest.mock import patch
from murgtools.plotting.conditions_plot import getObs

class TestBinData(unittest.TestCase):

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_bin_data_case1(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_bin_data_case2(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_bin_data_case3(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_bin_data_case4(self, mock_getObs):
        # Your test code here
        pass

class TestConditionsPlot(unittest.TestCase):

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_basic(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_with_date_string(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_with_groups(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_tp_computation(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_missing_variable(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_custom_limits(self, mock_getObs):
        # Your test code here
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_save_file(self, mock_getObs):
        # Your test code here
        pass

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def some_other_patch(self, mock_close, mock_savefig):
        # Your test code here
        pass

if __name__ == '__main__':
    unittest.main()