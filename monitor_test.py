import unittest
from monitor_object import EnergyMonitor, FuelType
import tkinter as tk
import datetime

class TestBasicLoading(unittest.TestCase):

    def test_initial(self):
        print('Testing the loading methods')

        self.assertIsNotNone(self.gui)
        self.assertIsInstance(self.gui, EnergyMonitor)
        self.assertDictEqual(self.gui.data_container, {})
        self.assertDictEqual(self.gui.monthly_data, {})
        self.assertListEqual(self.gui.loaded_fuels, [])
        self.assertListEqual(self.gui.loaded_ids, [])


    def test_badfiles(self):
        print("Testing for bad file types")

        # test that calling the load method with a wrongly formatted name
        with self.assertRaises(ValueError):
            self.gui.load_file('C:\\Users\\jpower\\Documents\\Work Experience\\test1.csv')

        with self.assertRaises(ValueError):
            self.gui.load_file('C:\\Nonexistent\\file\\path.csv')

        with self.assertRaises(ValueError):
            self.gui.load_file('C:\\Users\\jpower\\Documents\\Work Experience\\testcase_invalid_format_both_daily.csv')

        with self.assertRaises(ValueError):
            self.gui.load_file('C:\\Users\\jpower\\Documents\\Work Experience\\testcase_invalid_csv_both_daily.csv')


    def test_correctload(self):
        print("Testing that when a correct file is used the data is populated correctly")

        self.gui.load_file('C:\\Users\\jpower\\Documents\\Work Experience\\test1_both_daily.csv')

        self.assertEqual(self.gui.house_combo.get(), 'test1')
        self.assertEqual(len(self.gui.house_combo["values"]), 1)

        self.assertEqual(len(self.gui.loaded_ids), 1)
        self.assertEqual(self.gui.loaded_ids[0], 'test1')

        self.assertEqual(len(self.gui.loaded_fuels), 2)
        self.assertEqual(self.gui.loaded_fuels, [FuelType.electricity, FuelType.gas])

        self.assertEqual(len(list(self.gui.data_container.keys())), 4)
        first_date = datetime.date(2016, 1, 1)
        self.assertEqual(list(self.gui.data_container.keys())[0], first_date)
        self.assertEqual(self.gui.data_container[first_date], {'test1': {FuelType.gas: 4.063200168,
                                                                         FuelType.electricity: 20.93194302}})


    def setUp(self):
        self.root = tk.Tk()
        self.gui = EnergyMonitor(self.root)


if __name__ == '__main__':
    unittest.main()
