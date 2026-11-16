"""Validate results against independent pandas calculations from the snapshot."""
import sqlite3
import unittest
import pandas as pd
from src.analysis import ROOT, run_queries

class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames,cls.quality=run_queries(ROOT/'data'/'schools_analysis.sqlite')
        with sqlite3.connect('file:'+str(ROOT/'data'/'schools_analysis.sqlite')+'?mode=ro',uri=True) as c:
            cls.sat=pd.read_sql_query('SELECT * FROM satscores',c)
            cls.frpm=pd.read_sql_query('SELECT * FROM frpm',c)
            cls.schools=pd.read_sql_query('SELECT * FROM schools',c)

    def test_frpm_bands_and_means(self):
        f=self.frpm
        share=f['Percent (%) Eligible FRPM (K-12)']
        valid=f[(f['Academic Year']=='2014-2015') & share.between(0,1)].copy()
        valid['category']=pd.cut(valid['Percent (%) Eligible FRPM (K-12)'],[-.001,.25,.5,.75,1],labels=['Low','Moderate','High','Very High'])
        groups=valid.groupby('category',observed=True)['Percent (%) Eligible FRPM (K-12)']
        got=self.frames['03_frpm_distribution'].set_index('category')
        self.assertEqual(got.school_records.to_dict(),groups.size().to_dict())
        for key,value in groups.mean().items():
            self.assertAlmostEqual(got.loc[key,'mean_frpm_percent'],100*value,delta=0.005001)

    def test_county_means_and_weights(self):
        t=self.sat
        t=t[(t.rtype=='S') & (t.NumTstTakr>0) & t[['AvgScrRead','AvgScrMath','AvgScrWrite']].apply(lambda s:s.between(200,800)).all(axis=1)].copy()
        t['score']=t[['AvgScrRead','AvgScrMath','AvgScrWrite']].sum(axis=1)
        merged=t.merge(self.schools,left_on='cds',right_on='CDSCode',validate='one_to_one')
        got=self.frames['01_county_sat'].set_index('county')
        for county,g in merged.groupby('County'):
            self.assertEqual(got.loc[county,'schools_with_scores'],len(g))
            self.assertAlmostEqual(got.loc[county,'mean_school_sat'],g.score.mean(),delta=0.005001)
            self.assertAlmostEqual(got.loc[county,'weighted_sat'],(g.score*g.NumTstTakr).sum()/g.NumTstTakr.sum(),delta=0.005001)

    def test_opening_dates(self):
        named=self.schools[self.schools.School.notna()]
        years=pd.to_datetime(named.OpenDate,errors='coerce').dt.year
        expected=years.dropna().astype(int).value_counts().sort_index().to_dict()
        self.assertEqual(self.frames['02_openings_by_year'].set_index('opening_year').recorded_openings.to_dict(),expected)

    def test_join_unique_valid_and_school_only(self):
        joined=self.frames['05_frpm_sat']
        self.assertFalse(joined.cds.duplicated().any())
        self.assertTrue(joined.frpm_percent.between(0,100).all())
        self.assertTrue(joined.total_sat.between(600,2400).all())
        self.assertTrue(set(joined.cds).issubset(set(self.sat.loc[self.sat.rtype=='S','cds'])))
        f=self.frpm[self.frpm['Academic Year']=='2014-2015'].copy()
        f['cds']=(f['County Code'].astype(int).astype(str).str.zfill(2)+f['District Code'].astype(int).astype(str).str.zfill(5)+f['School Code'].astype(int).astype(str).str.zfill(7))
        self.assertFalse(f.cds.duplicated().any())
        check=joined.merge(f,on='cds',validate='one_to_one')
        self.assertTrue(((check.frpm_percent/100-check['Percent (%) Eligible FRPM (K-12)']).abs()<1e-10).all())

    def test_known_results(self):
        top=self.frames['04_top_sat_schools'].iloc[0]
        self.assertEqual(top.school,'Mission San Jose High')
        self.assertEqual(top.total_sat,2023)
        self.assertEqual(self.quality['frpm_missing_share'],189)

if __name__=='__main__':unittest.main()
