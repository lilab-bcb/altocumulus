import os
import unittest

import pandas as pd
import sccutil


class CommandTests(unittest.TestCase):
    def test_create_sample_sheet_dir(self):
        sccutil.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'path'])
        self.assertTrue(df.shape[1], 2)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_create_sample_sheet_r1_r2(self):
        sccutil.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt', '-f', 'r1_r2'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'r1', 'r2'])
        self.assertTrue(df.shape[1], 3)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_create_sample_sheet_r1_r2_i1(self):
        sccutil.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt', '-f', 'r1_r2_i1'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'r1', 'r2', 'i1'])
        self.assertTrue(df.shape[1], 4)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_upload_sample_sheet(self):
        sccutil.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt'])
        sccutil.commands.fc_upload.main(['--dry-run', '-w', 'scCloud-dev/test', 'test_sample_sheet.txt'])
        os.remove('test_sample_sheet.txt')

    def test_run(self):
        sccutil.commands.fc_run.main(['-m', 'broadgdac/echo', '-i', 'test.json', '-w', 'scCloud-dev/test'])

    def test_inputs(self):
        sccutil.commands.fc_inputs.main(['-m', 'broadgdac/echo', '-o', 'test-inputs.json'])
        os.remove('test.json')

    def test_add_method(self):
        sccutil.commands.fc_add_method.main(['-n', 'scCloud-dev', 'inputs/echo.wdl'])

    def test_remove_methods(self):
        sccutil.commands.fc_remove_method.main(['-m', 'scCloud-dev/'])


if __name__ == '__main__':
    unittest.main()
