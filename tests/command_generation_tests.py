import contextlib
import unittest
import os
import pandas as pd
import nordypy

class CommandGenerationTests(unittest.TestCase):
    maxDiff = None

    def test_create_table_statement(self):
        expected = """CREATE TABLE "jimbo"."jones" ("a a" FLOAT8, "b.b" FLOAT8, "c-c" INT2, "d_d" INT2, "e" INT4, "f" INT8, "g" INT2, "h" INT4, "i" INT8, "j" INT8, "k"  VARCHAR(100), "l"  VARCHAR(100), "m" TIMESTAMP, "n" TIMESTAMP, "o" BOOL);"""
        dummy_data = [1]
        df = pd.DataFrame(
            data = {
                'a a': dummy_data,
                'b.b': dummy_data,
                'c-c': dummy_data,
                'd_d': dummy_data,
                'e': dummy_data,
                'f': dummy_data,
                'g': dummy_data,
                'h': dummy_data,
                'i': dummy_data,
                'j': dummy_data,
                'k': 'object',
                'l': 'category',
                'm': pd.to_datetime('1970-01-01', infer_datetime_format=True),
                'n': pd.to_datetime(1490195805, unit='s'),
                'o': True
            },
            index=['row'],
        )
    
        df['a a'] = df['a a'].astype('float32')
        df['b.b'] = df['b.b'].astype('float64')
        df['c-c'] = df['c-c'].astype('int8')
        df['d_d'] = df['d_d'].astype('int16')
        df['e'] = df['e'].astype('int32')
        df['f'] = df['f'].astype('int64')
        df['g'] = df['g'].astype('uint8')
        df['h'] = df['h'].astype('uint16')
        df['i'] = df['i'].astype('uint32')
        df['j'] = df['j'].astype('uint64')
    
        results = nordypy._command_generation._create_table_statement(data=df, table_name='jimbo.jones', conn=conn)

        self.assertEqual(results, expected)


if __name__ == '__main__':
    database_key = 'redshift-dsa'
    yaml_filepath = '~/config.yaml'
    conn = nordypy.database_connect(database_key=database_key, yaml_filepath=yaml_filepath)

    unittest.main()