import copy,json,pathlib,sqlite3,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import app

class IntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=pathlib.Path(self.tmp.name)/'test.sqlite'; app.initialize(self.db); self.c=app.connect(self.db)
    def tearDown(self): self.c.close();self.tmp.cleanup()
    def product(self,pid): return next(p for p in app.all_products(self.c) if p['id']==pid)
    def test_seed_is_idempotent_and_relational(self):
        app.initialize(self.db)
        self.assertEqual(self.c.execute('SELECT count(*) FROM products').fetchone()[0],9)
        self.assertEqual(self.c.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_platform_variants_not_collapsed(self):
        self.assertEqual(self.product('lenovo-t14g6-a')['max_ram_gb'],64)
        self.assertEqual(self.product('lenovo-t14g6-v')['max_ram_gb'],32)
    def test_unknown_weight_not_a_candidate(self):
        self.assertEqual(app.evaluate(self.product('dell-l5450'),64,1.5,True)['status'],'unknown')
    def test_known_failure_takes_precedence_over_unknown(self):
        self.assertEqual(app.evaluate(self.product('asus-p5405'),64,1.5,True)['status'],'fail')
    def test_boundary_is_inclusive(self):
        self.assertEqual(app.evaluate(self.product('apple-air13m4'),32,1.24)['status'],'pass')
    def test_fleet_candidates(self):
        passed=[p['id'] for p in app.all_products(self.c) if app.evaluate(p,64,1.5,True)['status']=='pass']
        self.assertEqual(set(passed),{'lenovo-t14g6-a','hp-e840g11'})
    def test_retrieval_uses_evidence(self):
        docs=app.retrieve(self.c,'MacBook Air M4 memory')
        self.assertIn('S8',[d['id'] for d in docs])
    def test_unsupported_question_abstains(self):
        result=app.answer(self.c,'quantum entanglement medicine')
        self.assertEqual(result['citations'],[])
    def test_historical_price_not_current_quote(self):
        result=app.answer(self.c,'What is the laptop price?')
        self.assertIn('not a current quote',result['answer'])
        self.assertEqual(self.c.execute("SELECT count(*) FROM prices WHERE kind!='launch'").fetchone()[0],0)
    def test_analytical_answers_do_not_let_model_override_rules(self):
        with patch.object(app,'llm_settings',side_effect=AssertionError('Model should not decide portfolio rules')):
            result=app.answer(self.c,'Where are the portfolio gaps?',True)
        self.assertIn('Dell: 0 candidate(s), 1 unresolved',result['answer'])
        self.assertIn('deterministic business rules',result['mode'])
    def test_reviewed_change_is_audited(self):
        p=self.product('dell-l5450');p['weight_kg']=1.5
        app.import_research(self.c,{'products':[p]})
        change=dict(self.c.execute('SELECT * FROM changes').fetchone())
        self.assertEqual(change['field'],'weight_kg');self.assertEqual(change['old_value'],'null');self.assertEqual(change['new_value'],'1.5')
    def test_invalid_import_rolls_back(self):
        self.c.close()
        with self.assertRaises(ValueError):
            with app.connect(self.db) as c:
                p=app.all_products(c)[0];p['weight_kg']=2
                bad=copy.deepcopy(p);bad['id']='INVALID'
                app.import_research(c,{'products':[p,bad]})
        self.c=app.connect(self.db)
        self.assertEqual(self.c.execute('SELECT count(*) FROM changes').fetchone()[0],0)
    def test_source_overwrite_rejected(self):
        seed=json.loads((app.ROOT/'data/seed.json').read_text())
        with self.assertRaises(ValueError):app.import_research(self.c,{'products':[self.product('dell-l5450')],'sources':[seed['sources'][0]]})
    def test_unrelated_price_source_rejected(self):
        p=json.loads((app.ROOT/'data/seed.json').read_text())['prices'][0];p['source_id']='S1'
        with self.assertRaises(ValueError):app.add_price(self.c,p)
    def test_exports_allowlisted(self):
        with self.assertRaises(ValueError):app.export_csv(self.c,'products; DROP TABLE sources')
        self.assertIn('max_ram_gb',app.export_csv(self.c,'products').splitlines()[0])
    def test_database_constraints_reject_negative_weight(self):
        with self.assertRaises(sqlite3.IntegrityError):self.c.execute('UPDATE products SET weight_kg=-1')
    def test_windows_csv_exports_have_no_blank_records(self):
        import csv
        with patch.object(app,'ROOT',pathlib.Path(self.tmp.name)):
            app.export_all(self.c)
        with (pathlib.Path(self.tmp.name)/'powerbi/exports/products.csv').open(encoding='utf-8-sig',newline='') as f:
            records=list(csv.DictReader(f))
        self.assertEqual(len(records),9)
        self.assertTrue(all(r['id'] for r in records))
        raw=(pathlib.Path(self.tmp.name)/'powerbi/exports/products.csv').read_bytes()
        self.assertNotIn(b'\r\r\n',raw)

if __name__=='__main__': unittest.main(verbosity=2)
