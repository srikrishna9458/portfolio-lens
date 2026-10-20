"""Generate the editable PBIP report and semantic model from SQL CSV exports."""
import csv,json,pathlib,uuid
ROOT=pathlib.Path(__file__).resolve().parent
REPORT=ROOT/'PortfolioLens.Report'; MODEL=ROOT/'PortfolioLens.SemanticModel'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def schema(kind): return BASE+kind+'/1.0.0/schema.json'
write(ROOT/'Portfolio Lens.pbip',{'version':'1.0','artifacts':[{'report':{'path':'PortfolioLens.Report'}}],'settings':{'enableAutoRecovery':True}})
write(REPORT/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../PortfolioLens.SemanticModel'}}})
write(MODEL/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{'qnaEnabled':False}})
tables=[]
numbers={'screen_in','max_ram_gb','ram_upgradeable','weight_kg','max_storage_gb','ethernet','battery_wh','evidence_coverage_pct','amount','platform_variants','families'}
names={'products':'Products','sources':'Sources','prices':'Prices','launches':'Launches','changes':'Changes','source_checks':'SourceChecks','brands':'Brands'}
for filename,name in names.items():
    with (ROOT/'exports'/f'{filename}.csv').open(encoding='utf-8-sig',newline='') as f: fields=next(csv.reader(f))
    numeric=[f for f in fields if f in numbers or (f=='id' and filename in ('prices','launches','changes','source_checks'))]
    types=', '.join('{"'+f+'", '+('type number' if f in numeric else 'type text')+'}' for f in fields)
    expr=['let',f'    Source = Csv.Document(File.Contents(DataFolder & "{filename}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',f'    Typed = Table.TransformColumnTypes(Nulls, {{{types}}}, "en-US")','in','    Typed']
    cols=[{'name':f,'dataType':'double' if f in numeric else 'string','sourceColumn':f,'summarizeBy':'none'} for f in fields]
    for col in cols:
        if col['name']=='url': col['dataCategory']='WebUrl'
        if col['name']=='weight_kg': col['formatString']='0.000'
    table={'name':name,'columns':cols,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}
    if name=='Products':
        table['columns'] += [
            {'type':'calculated','name':'Platform','dataType':'string','expression':'Products[brand] & " " & Products[family] & " / " & Products[variant]','summarizeBy':'none'},
            {'type':'calculated','name':'FleetFit','dataType':'string','expression':'SWITCH(TRUE(), NOT ISBLANK(Products[max_ram_gb]) && Products[max_ram_gb] < 64, "No match", NOT ISBLANK(Products[weight_kg]) && Products[weight_kg] > 1.5, "No match", NOT ISBLANK(Products[ram_upgradeable]) && Products[ram_upgradeable] = 0, "No match", ISBLANK(Products[max_ram_gb]) || ISBLANK(Products[weight_kg]) || ISBLANK(Products[ram_upgradeable]), "Unresolved", "Candidate - verify SKU")','summarizeBy':'none'},
            {'type':'calculated','name':'TravelFit','dataType':'string','expression':'SWITCH(TRUE(), NOT ISBLANK(Products[max_ram_gb]) && Products[max_ram_gb] < 32, "No match", NOT ISBLANK(Products[weight_kg]) && Products[weight_kg] > 1.3, "No match", ISBLANK(Products[max_ram_gb]) || ISBLANK(Products[weight_kg]), "Unresolved", "Candidate - verify SKU")','summarizeBy':'none'}]
        measures={'Platform variants':'COUNTROWS(Products)','Product families':'COUNTROWS(SUMMARIZE(Products, Products[brand], Products[family]))','Brands tracked':'DISTINCTCOUNT(Products[brand])','Evidence coverage %':'AVERAGE(Products[evidence_coverage_pct])','Starting weight kg':'MIN(Products[weight_kg])','Max memory GB':'MAX(Products[max_ram_gb])','Fleet candidates':'CALCULATE(COUNTROWS(Products), Products[FleetFit] = "Candidate - verify SKU")'}
        table['measures']=[{'name':k,'expression':v,'formatString':'0.000' if k=='Starting weight kg' else '0'} for k,v in measures.items()]
    tables.append(table)
relations=[]
for name in ['Prices','Launches','Changes']:
    relations.append({'name':str(uuid.uuid4()),'fromTable':name,'fromColumn':'product_id','toTable':'Products','toColumn':'id','crossFilteringBehavior':'oneDirection'})
    relations.append({'name':str(uuid.uuid4()),'fromTable':name,'fromColumn':'source_id','toTable':'Sources','toColumn':'id','crossFilteringBehavior':'oneDirection'})
relations.append({'name':str(uuid.uuid4()),'fromTable':'SourceChecks','fromColumn':'source_id','toTable':'Sources','toColumn':'id','crossFilteringBehavior':'oneDirection'})
model={'name':'PortfolioLens','compatibilityLevel':1606,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':True},'expressions':[{'name':'DataFolder','kind':'m','expression':'"'+str(ROOT/'exports').replace('\\','/')+'/" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],'tables':tables,'relationships':relations,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(list(names.values()))},{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}}
write(MODEL/'model.bim',model)
write(REPORT/'definition/version.json',{'$schema':schema('versionMetadata'),'version':'2.0.0'})
write(REPORT/'definition/report.json',{'$schema':schema('report'),'themeCollection':{},'layoutOptimization':'None','annotations':[{'name':'Research scope','value':'Curated sample; starting weights and maximum RAM may not coexist. Historical prices are not current offers.'}]})
pages=[('Overview','01 · Market overview'),('PortfolioFit','02 · Portfolio fit'),('Pricing','03 · Pricing evidence'),('Sources','04 · Sources and changes')]
write(REPORT/'definition/pages/pages.json',{'$schema':schema('pagesMetadata'),'pageOrder':[p[0] for p in pages],'activePageName':'Overview'})
def literal(value): return {'expr':{'Literal':{'Value':"'"+value.replace("'","''")+"'"}}}
def projection(table,col,measure=False): return {'field':{'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':col}},'queryRef':table+'.'+col,'nativeQueryRef':col,'displayName':col.replace('_',' ')}
def visual(page,name,kind,title,query,x,y,w,h):
    obj={'$schema':schema('visualContainer'),'name':name,'position':{'x':x,'y':y,'z':0,'width':w,'height':h,'tabOrder':y+x},'visual':{'visualType':kind,'query':{'queryState':{role:{'projections':projs} for role,projs in query.items()}},'visualContainerObjects':{'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'true'}}},'text':literal(title)}}]}}}
    write(REPORT/f'definition/pages/{page}/visuals/{name}/visual.json',obj)
def table(page,name,title,entity,cols,x,y,w,h):visual(page,name,'tableEx',title,{'Values':[projection(entity,c) for c in cols]},x,y,w,h)
def card(page,name,measure,x):visual(page,name,'card',measure,{'Values':[projection('Products',measure,True)]},x,20,285,120)
for name,title in pages:write(REPORT/f'definition/pages/{name}/page.json',{'$schema':schema('page'),'name':name,'displayName':title,'displayOption':'FitToPage','height':900,'width':1280})
for i,m in enumerate(['Product families','Platform variants','Brands tracked','Evidence coverage %']):card('Overview','Card'+str(i),m,20+i*315)
visual('Overview','BrandCoverage','clusteredBarChart','Platform variants in the research sample',{'Category':[projection('Products','brand')],'Y':[projection('Products','Platform variants',True)]},20,160,500,320)
visual('Overview','Weight','clusteredBarChart','Starting weights (kg) · configuration dependent',{'Category':[projection('Products','Platform')],'Y':[projection('Products','Starting weight kg',True)]},540,160,720,320)
table('Overview','Catalog','Product capabilities · maxima are not installed specifications','Products',['brand','family','variant','max_ram_gb','weight_kg','ram_upgradeable','evidence_coverage_pct'],20,500,1240,370)
visual('PortfolioFit','BrandFilter','slicer','Filter brand',{'Values':[projection('Products','brand')]},20,20,300,140)
table('PortfolioFit','Fit','Fleet: ≥64GB, ≤1.5kg, upgradable RAM | Travel: ≥32GB, ≤1.3kg','Products',['brand','family','variant','FleetFit','TravelFit','weight_kg','max_ram_gb'],20,180,1240,400)
table('PortfolioFit','Caveats','Read configuration notes before interpreting a candidate','Products',['Platform','notes'],20,600,1240,270)
table('Pricing','Prices','Dated observations · launch prices are NOT current offers','Prices',['product_id','amount','currency','market','kind','observed_on','configuration','tax_basis','source_id'],20,20,1240,380)
table('Pricing','Launches','Recorded historical launches · not exhaustive market news','Launches',['announced_on','title','summary','source_id'],20,420,1240,450)
table('Sources','Evidence','Manufacturer evidence · curated summaries','Sources',['id','title','publisher','verified_on','summary','url'],20,20,1240,430)
table('Sources','Changes','Reviewed specification changes (empty until research updates)','Changes',['product_id','changed_at','field','old_value','new_value','source_id'],20,470,600,400)
table('Sources','Checks','Source checks · fingerprint differences require review','SourceChecks',['source_id','checked_at','status','detail'],640,470,620,400)
write(ROOT/'Portfolio Lens Theme.json',{'name':'Portfolio Lens','dataColors':['#176754','#3D83A0','#C19B45','#765C9E','#D87D56'],'background':'#F5F6F8','foreground':'#172B3A','tableAccent':'#176754'})
print('Power BI project created: 4 pages, 7 data tables, 7 measures.')
import runpy
runpy.run_path(str(ROOT/'style_report.py'))

