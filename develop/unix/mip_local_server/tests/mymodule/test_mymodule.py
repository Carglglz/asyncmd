import unittest
import mymodule


class TestSum(unittest.TestCase):
    def test_sum(self):
        self.assertEqual(sum([1, 2, 3]), 6, "Should be 6")

    def test_sum_tuple(self):
        self.assertEqual(sum((mymodule.ret(), 2, 1)), 6, "Should be 6")

    def test_diff_tuple(self):
        self.assertEqual(mymodule.ret() - 2, 1, "Should be 1")


if __name__ == "__main__":
    unittest.main()
