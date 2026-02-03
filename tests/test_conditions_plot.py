import unittest
from unittest.mock import patch

class TestConditionsPlot(unittest.TestCase):

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_some_condition(self, mock_getObs):
        # Your test implementation
        pass

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_another_condition(self, mock_getObs):
        # Your test implementation
        pass

    # Add more test methods as needed with the updated patch

if __name__ == '__main__':
    unittest.main()