import os
import unittest

import alto
import pandas as pd


class CommandTests(unittest.TestCase):
    def test_create_sample_sheet_dir(self):
        alto.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'path'])
        self.assertTrue(df.shape[1], 2)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_create_sample_sheet_r1_r2(self):
        alto.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt', '-f', 'r1_r2'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'r1', 'r2'])
        self.assertTrue(df.shape[1], 3)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_create_sample_sheet_r1_r2_i1(self):
        alto.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt', '-f', 'r1_r2_i1'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'r1', 'r2', 'i1'])
        self.assertTrue(df.shape[1], 4)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_upload_sample_sheet(self):
        alto.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt'])
        alto.commands.upload.main(['--dry-run', '-w', 'regev-development/test', 'test_sample_sheet.txt'])
        os.remove('test_sample_sheet.txt')

    def test_run(self):
        alto.commands.run.main(['-m', 'broadgdac/echo', '-i', 'test.json', '-w', 'regev-development/test'])

    def test_inputs(self):
        alto.commands.create_input_stub.main(['-m', 'broadgdac/echo', '-o', 'test-inputs.json'])

    def test_add_method(self):
        alto.commands.add_method.main(['-n', 'cumulus-dev', 'inputs/echo.wdl'])

    def test_remove_methods(self):
        alto.commands.remove_method.main(['-m', 'cumulus-dev/'])


if __name__ == '__main__':
    unittest.main()
