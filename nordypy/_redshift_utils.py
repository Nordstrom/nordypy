analyze_table = """SELECT schema, "table", encoded, diststyle,
                sortkey1, sortkey_num, unsorted, stats_off, size,
                skew_sortkey1, skew_rows
                FROM svv_table_info
                WHERE schema = '{}'
                AND "table" = '{}'
                ORDER BY 1;"""

table_columns = """SELECT column_name {}
                FROM information_schema.columns
                WHERE table_schema = '{}'
                    AND table_name = '{}'
                ORDER BY ordinal_position;"""
