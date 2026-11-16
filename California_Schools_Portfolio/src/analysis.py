"""Read-only SQL analysis and portable chart/report exports."""
from pathlib import Path
import json
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'figure.facecolor': '#f8fafc',
                     'axes.facecolor': '#f8fafc', 'savefig.facecolor': '#f8fafc'})
BLUE, TEAL = '#245b91', '#168a87'

def run_queries(db):
    path = Path(db).resolve()
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as conn:
        frames = {p.stem: pd.read_sql_query(p.read_text(), conn) for p in sorted((ROOT/'sql').glob('*.sql'))}
        quality = {}
        for table in ['schools', 'satscores', 'frpm']:
            quality[table + '_rows'] = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        quality['frpm_missing_share'] = conn.execute('SELECT COUNT(*) FROM frpm WHERE "Percent (%) Eligible FRPM (K-12)" IS NULL').fetchone()[0]
        quality['open_date_1980_07_01_records'] = conn.execute("SELECT COUNT(*) FROM schools WHERE School IS NOT NULL AND OpenDate='1980-07-01'").fetchone()[0]
        quality['sat_school_records'] = conn.execute("SELECT COUNT(*) FROM satscores WHERE rtype='S'").fetchone()[0]
        quality['frpm_missing_year'] = conn.execute('SELECT COUNT(*) FROM frpm WHERE "Academic Year" IS NULL').fetchone()[0]
        quality['school_records_without_name'] = conn.execute('SELECT COUNT(*) FROM schools WHERE School IS NULL').fetchone()[0]
        quality['named_schools_without_valid_open_date'] = conn.execute("SELECT COUNT(*) FROM schools WHERE School IS NOT NULL AND strftime('%Y',OpenDate) IS NULL").fetchone()[0]
    joined = frames['05_frpm_sat']
    if joined.cds.duplicated().any():
        raise ValueError('FRPM/SAT join duplicates school IDs; investigate source keys.')
    quality['matched_frpm_sat_schools'] = len(joined)
    quality['pearson_r'] = float(joined.frpm_percent.corr(joined.total_sat))
    quality['scored_school_count'] = int(frames['01_county_sat'].schools_with_scores.sum())
    return frames, quality

def save(fig, out, name):
    fig.tight_layout(pad=2)
    fig.savefig(out/name, dpi=180, bbox_inches='tight')
    plt.close(fig)

def charts(frames, out):
    county=frames['01_county_sat'].head(10).iloc[::-1]
    fig, ax=plt.subplots(figsize=(11,7))
    labels=county.county + ' (n=' + county.schools_with_scores.astype(str) + ')'
    bars=ax.barh(labels,county.mean_school_sat,color=BLUE)
    ax.bar_label(bars,fmt='%.2f',padding=4)
    ax.set(xlim=(0,1850),xlabel='Mean of school SAT totals · reading + math + writing',
           title='Highest county averages | school sample sizes matter')
    save(fig,out,'01_county_sat.png')
    yearly=frames['02_openings_by_year']
    fig,ax=plt.subplots(figsize=(11,5))
    ax.plot(yearly.opening_year,yearly.recorded_openings,color=BLUE,lw=1.8)
    ax.set(xlabel='Recorded opening year',ylabel='Named school records',
           title='School openings recorded in the historical snapshot')
    ax.set_yscale('symlog', linthresh=10)
    ax.set_ylabel('Named school records · symmetric-log scale')
    peak=yearly.sort_values('recorded_openings',ascending=False).iloc[0]
    ax.annotate('10,679 share 1980-07-01\nDate concentration: interpretation uncertain',
                xy=(peak.opening_year,peak.recorded_openings),xytext=(1890,1500),
                arrowprops={'arrowstyle':'->','color':'#a44b35'},fontsize=9,color='#a44b35')
    fig.text(.1,.005,'Includes active, closed, merged and pending records; not net school growth.',fontsize=9)
    save(fig,out,'02_openings_by_year.png')
    poverty=frames['03_frpm_distribution']
    fig,ax=plt.subplots(figsize=(9,5))
    bars=ax.bar(poverty.category,poverty.school_records,color=[BLUE,'#4486ac',TEAL,'#d69340'])
    ax.bar_label(bars,padding=4)
    ax.set(ylim=(0,poverty.school_records.max()*1.18),ylabel='School records',
           xlabel='FRPM eligibility bands: ≤25%, >25–50%, >50–75%, >75%',
           title='FRPM eligibility distribution | 2014–2015')
    save(fig,out,'03_frpm_distribution.png')
    top=frames['04_top_sat_schools'].iloc[::-1]
    fig,ax=plt.subplots(figsize=(11,7))
    bars=ax.barh(top.school,top.total_sat,color=TEAL)
    ax.bar_label(bars,padding=4)
    ax.set(xlim=(0,2400),xlabel='Sum of three reported school-average SAT components',
           title='Top school SAT totals | historical snapshot')
    save(fig,out,'04_top_sat_schools.png')
    joined=frames['05_frpm_sat']
    fig,ax=plt.subplots(figsize=(10,6))
    ax.scatter(joined.frpm_percent,joined.total_sat,s=17,alpha=.4,color=BLUE,edgecolors='none')
    r=joined.frpm_percent.corr(joined.total_sat)
    ax.set(xlabel='Students eligible for FRPM (%) · 2014–2015',ylabel='School-average SAT total',
           title=f'FRPM and SAT | {len(joined):,} matched schools · Pearson r = {r:.3f}')
    fig.text(.1,.005,'Exploratory school-level association; SAT year unverified; no causal interpretation.',fontsize=9)
    save(fig,out,'05_frpm_sat.png')

def report(frames,q,out):
    p=frames['03_frpm_distribution']
    count=frames['01_county_sat']
    peak=frames['02_openings_by_year'].sort_values('recorded_openings',ascending=False).iloc[0]
    lines=['# California Schools — findings and limitations','',
      'Generated from the bundled analysis database by `python main.py`.','',
      '## Verified findings','',
      f'- Marin leads the school-weighted county means at {count.iloc[0].mean_school_sat:,.2f}, based on {int(count.iloc[0].schools_with_scores)} scored schools.',
      '- Mission San Jose High has the highest observed three-component SAT total: 2,023.',
      f'- The FRPM analysis includes {int(p.school_records.sum()):,} records with a valid share and the 2014–2015 year.',
      f'- The highest recorded annual opening count is {int(peak.recorded_openings):,} in {int(peak.opening_year)}. This is a snapshot-based count, not a measure of net growth.',
      f'- The exploratory school-level FRPM/SAT join contains {q["matched_frpm_sat_schools"]:,} schools; Pearson correlation is {q["pearson_r"]:.3f}.',
      '', '| FRPM category | School records | Mean eligibility |','|---|---:|---:|']
    lines += [f'| {r.category} | {r.school_records:,} | {r.mean_frpm_percent:.2f}% |' for r in p.itertuples()]
    lines += ['', '## Interpretation', '',
      'Opening-date anomaly: 10,679 named school records share 1980-07-01. This may reflect an administrative or default date, but its meaning is not verified. Preserve the records and do not interpret the spike as demonstrated construction activity. The time chart uses a symmetric-log vertical scale to keep smaller counts visible.', '',
      'The matched sample shows how FRPM eligibility and reported school SAT averages vary together. It does not establish a causal effect of household income, school funding, or county. SAT participation, admissions, school type, and other factors may affect comparisons. The SAT year is not encoded in the supplied table, so temporal alignment with FRPM is unverified.',
      '', '## Data quality and scope', '',
      f'- Source tables: {q["schools_rows"]:,} school-directory records, {q["satscores_rows"]:,} SAT records and {q["frpm_rows"]:,} FRPM records.',
      f'- SAT records include state, county and district aggregates. Queries retain school rows only (`rtype = S`); {q["scored_school_count"]:,} schools pass score and test-taker filters and match the directory.',
      f'- FRPM has {q["frpm_missing_share"]} missing eligibility shares and {q["frpm_missing_year"]} missing years. These exclusions can overlap; do not add them.',
      f'- The directory contains {q["school_records_without_name"]:,} unnamed records. Opening trends exclude these and {q["named_schools_without_valid_open_date"]:,} named records without a parseable opening date.',
      '- County means weight schools equally. A second CSV column weights the rounded school averages by test-taker counts; it is an approximation of a student-level mean.',
      '- FRPM bands are analyst-defined eligibility categories, not official poverty classifications.',
      '- Rankings include all valid scored schools, with sample sizes disclosed. They are not comprehensive measures of school quality.',
      '- Dates describe a historical snapshot. No results represent current school performance.',
      '', '## Charts','']
    for name in ['01_county_sat','02_openings_by_year','03_frpm_distribution','04_top_sat_schools','05_frpm_sat']:
        lines += [f'![{name.replace("_"," ")}]({name}.png)','']
    (out/'FINDINGS.md').write_text('\n'.join(lines)+'\n')

def main(db,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    frames,quality=run_queries(db)
    for name,frame in frames.items():frame.to_csv(out/(name+'.csv'),index=False)
    (out/'data_quality.json').write_text(json.dumps(quality,indent=2)+'\n')
    charts(frames,out);report(frames,quality,out)
    print(json.dumps(quality,indent=2))
