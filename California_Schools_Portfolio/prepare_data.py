"""Create the analysis-only database from the original user-supplied snapshot."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLUMNS = {
    'schools': ['CDSCode', 'County', 'School', 'StatusType', 'OpenDate'],
    'satscores': ['cds', 'rtype', 'sname', 'cname', 'enroll12', 'NumTstTakr', 'AvgScrRead', 'AvgScrMath', 'AvgScrWrite'],
    'frpm': ['Academic Year', 'County Code', 'District Code', 'School Code', 'Percent (%) Eligible FRPM (K-12)'],
}

def prepare(source):
    source = Path(source).resolve()
    target = ROOT / 'data' / 'schools_analysis.sqlite'
    if source == target:
        raise ValueError('Source must be the original database, not the analysis copy.')
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as src:
        # Read all required fields successfully before replacing the derived file.
        records = {}
        schemas = {}
        for table, columns in COLUMNS.items():
            fields = ', '.join('"' + col + '"' for col in columns)
            records[table] = src.execute(f'SELECT {fields} FROM {table}').fetchall()
            info = {row[1]: row[2] for row in src.execute(f'PRAGMA table_info({table})')}
            schemas[table] = ', '.join(f'"{col}" {info[col]}' for col in columns)
    target.parent.mkdir(exist_ok=True)
    target.unlink(missing_ok=True)
    with sqlite3.connect(target) as dst:
        for table, columns in COLUMNS.items():
            dst.execute(f'CREATE TABLE {table} ({schemas[table]})')
            dst.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in columns)})', records[table])
    provenance = {
        'source_filename': source.name,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'description': 'Column subset of the supplied historical SQLite snapshot; no rows changed or removed.',
        'retained_columns': COLUMNS,
        'rows': {table: len(rows) for table, rows in records.items()},
        'frpm_year': '2014-2015 (two source records have no year)',
        'sat_year': 'Not encoded in the supplied table; not independently verified.',
        'license': 'Original redistribution terms not verified. Verify before public redistribution of the database.',
    }
    (ROOT / 'data' / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    prepare(parser.parse_args().source)
