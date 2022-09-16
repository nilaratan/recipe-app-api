"""
Sample tests
"""
from django.test import SimpleTestCase
from app.calc import add, substract


class TestCalc(SimpleTestCase):
    """
    Test the calc module
    """

    def test_add_number(self):
        a = 5
        b = 6
        self.assertEqual(add(a, b), 11)

    def test_substract_number(self):
        a = 10
        b = 5
        self.assertEqual(substract(a, b), 5)
