"""Apply readable default formatting to the generated report visuals."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def value(v):return {'expr':{'Literal':{'Value':str(v).lower() if not isinstance(v,str) else "'"+v+"'"}}}
def color(v):return {'solid':{'color':value(v)}}
for path in (ROOT/'PortfolioLens.Report/definition/pages').rglob('visual.json'):
    obj=json.loads(path.read_text(encoding='utf-8'));v=obj['visual'];props=v['visualContainerObjects']['title'][0]['properties']
    props.update(fontSize=value(14),fontColor=color('#172B3A'),bold=value(True))
    kind=v['visualType']; objects=v.setdefault('objects',{})
    if kind=='tableEx':
        objects.update(grid=[{'properties':{'textSize':value(12),'rowPadding':value(5)}}],columnHeaders=[{'properties':{'fontSize':value(12),'bold':value(True),'wordWrap':value(True),'columnAdjustment':value('growToFit')}}],values=[{'properties':{'fontSize':value(12),'wordWrap':value(True)}}])
    elif kind=='clusteredBarChart':
        objects.update(categoryAxis=[{'properties':{'fontSize':value(11),'maxMarginFactor':value(45)}}],valueAxis=[{'properties':{'fontSize':value(11)}}],dataPoint=[{'properties':{'defaultColor':color('#176754')}}])
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
print('Report readability formatting applied.')
