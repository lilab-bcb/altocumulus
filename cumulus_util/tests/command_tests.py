import os
import unittest

import pandas as pd

import cumulus_util


class CommandTests(unittest.TestCase):
    def test_create_sample_sheet_dir(self):
        cumulus_util.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'path'])
        self.assertTrue(df.shape[1], 2)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_create_sample_sheet_r1_r2(self):
        cumulus_util.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt', '-f', 'r1_r2'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'r1', 'r2'])
        self.assertTrue(df.shape[1], 3)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_create_sample_sheet_r1_r2_i1(self):
        cumulus_util.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt', '-f', 'r1_r2_i1'])
        df = pd.read_table('test_sample_sheet.txt', header=None, names=['sample', 'r1', 'r2', 'i1'])
        self.assertTrue(df.shape[1], 4)
        self.assertTrue(df.shape[0], 5)
        self.assertTrue(len(df['sample'].unique()) == 3)
        os.remove('test_sample_sheet.txt')

    def test_upload_sample_sheet(self):
        cumulus_util.commands.sample_sheet.main(['-d', 'inputs', '-o', 'test_sample_sheet.txt'])
        cumulus_util.commands.fc_upload.main(['--dry-run', '-w', 'cumulus-dev/test', 'test_sample_sheet.txt'])
        os.remove('test_sample_sheet.txt')

    def test_run(self):
        cumulus_util.commands.fc_run.main(['-m', 'broadgdac/echo', '-i', 'test.json', '-w', 'cumulus-dev/test'])

    def test_inputs(self):
        cumulus_util.commands.fc_inputs.main(['-m', 'broadgdac/echo', '-o', 'test-inputs.json'])
        os.remove('test.json')

    def test_add_method(self):
        cumulus_util.commands.fc_add_method.main(['-n', 'cumulus-dev', 'inputs/echo.wdl'])

    def test_remove_methods(self):
        cumulus_util.commands.fc_remove_method.main(['-m', 'cumulus-dev/'])


if __name__ == '__main__':
    unittest.main()
