import json
from src.grounded_insights import extract_observations, aggregate


def test_ungrounded_quotes_and_incidental_competitors_rejected():
    segments=[{'start':12,'end':20,'text':'iPhone Duo battery is better than Galaxy Z Fold and lasts all day.'}]
    def completion(prompt):return json.dumps({'observations':[
        {'segment_id':0,'quote':segments[0]['text'],'attribute':'Battery','sentiment':'positive','focal_product':'iPhone Duo','competitor':'Galaxy Z Fold','is_direct':True,'theme':'All-day use'},
        {'segment_id':0,'quote':'Imaginary battery quotation is great','attribute':'Battery','sentiment':'positive'},
        {'segment_id':0,'quote':segments[0]['text'],'attribute':'Camera','sentiment':'neutral','competitor':'Google Pixel','is_direct':True}
    ]})
    rows=extract_observations('iPhone Duo reviews',segments,completion)
    assert len(rows)==2 and rows[0]['is_direct'] is True and rows[1]['is_direct'] is False
    assert rows[0]['start_seconds']==12


def test_distinct_coverage_sentiment_and_evidence():
    row={'attribute':'Battery','quote':'Battery lasts all day','sentiment':'positive','theme':'All-day use','competitor':'Pixel 9 Pro','is_direct':True,'start_seconds':1,'end_seconds':4}
    report=aggregate({'evidence':[]},{'v1':[row,{**row,'start_seconds':5,'end_seconds':8}],'v2':[row]})
    assert report['attributes'][0]['source_ids']==['v1','v2']
    assert report['attributes'][0]['mention_count']==3
    assert report['comparisons'][0]['source_ids']==['v1','v2']
    assert report['attributes'][0]['sentiment_counts']['positive']==3
    assert all(e['spoken']=='Battery lasts all day' for e in report['evidence'])


def test_unrelated_product_comparison_does_not_become_focal_comparison():
    quote='Pixel is better than Galaxy Z Fold at night.'
    rows=extract_observations('iPhone Duo reviews',[{'start':1,'end':5,'text':quote}],lambda _:json.dumps({'observations':[{'segment_id':0,'quote':quote,'attribute':'Camera','sentiment':'positive','competitor':'Galaxy Z Fold','is_direct':True}]}))
    assert not any(row['is_direct'] for row in rows)


def test_nonfinite_timestamps_cannot_enter_json_report():
    quote='The battery lasts throughout the entire day.'
    for value in [float('nan'),float('inf'),True]:
        rows=extract_observations('iPhone Duo reviews',[{'start':value,'end':value,'text':quote}],lambda _:json.dumps({'observations':[{'segment_id':0,'quote':quote,'attribute':'Battery','sentiment':'positive'}]}))
        assert rows==[]


def coded(window,quote,attribute='Battery'):
    return {'segment_id':window,'quote':quote,'attribute':attribute,'sentiment':'positive'}


def test_cross_segment_quote_uses_bounds_of_exact_overlapping_segments():
    segments=[
        {'start':10,'end':12,'text':'  iPhone Duo battery lasts '},
        {'start':12,'end':15,'text':'for the whole day, even'},
        {'start':15,'end':19,'text':'during heavy camera use.  '},
    ]
    crossing='battery lasts for the whole day, even during heavy'
    contained='for the whole day, even'
    def completion(prompt):
        windows=json.loads(prompt.split('TRANSCRIPT SEGMENTS: ',1)[1])
        assert windows==[{'id':0,'text':'iPhone Duo battery lasts for the whole day, even during heavy camera use.'}]
        return json.dumps({'observations':[coded(0,crossing),coded(0,contained,'Endurance')]})
    rows=extract_observations('iPhone Duo reviews',segments,completion)
    assert [(r['quote'],r['start_seconds'],r['end_seconds']) for r in rows]==[(crossing,10,19),(contained,12,15)]
    assert segments[0]['text']=='  iPhone Duo battery lasts ', 'Raw transcript must stay unchanged'


def test_quotes_cannot_join_disconnected_windows_or_rewrite_punctuation():
    segments=[
        {'start':0,'end':2,'text':'The battery is good.'},
        {'start':5,'end':7,'text':'The camera is better.'},
    ]
    def completion(prompt):
        windows=json.loads(prompt.split('TRANSCRIPT SEGMENTS: ',1)[1])
        assert [w['id'] for w in windows]==[0,1]
        return json.dumps({'observations':[
            coded(0,'The battery is good. The camera is better.'),
            coded(0,'The battery is good!'),
            coded(True,'The camera is better.'),
            coded(1,'The camera is better.','Camera'),
        ]})
    rows=extract_observations('iPhone Duo reviews',segments,completion)
    assert len(rows)==1 and rows[0]['quote']=='The camera is better.'
    assert (rows[0]['start_seconds'],rows[0]['end_seconds'])==(5,7)


def test_window_limit_and_invalid_segment_preserve_window_ids_and_bounds():
    segments=[{'start':i,'end':i+1,'text':f'Sentence number {i}.'} for i in range(6)]
    segments.extend([{'start':float('nan'),'end':8,'text':'Invalid boundary'}, {'start':9,'end':10,'text':'Last grounded sentence.'}])
    def completion(prompt):
        windows=json.loads(prompt.split('TRANSCRIPT SEGMENTS: ',1)[1])
        assert [w['id'] for w in windows]==[0,1,2]
        assert windows[1]['text']=='Sentence number 5.'
        return json.dumps({'observations':[coded(1,'Sentence number 5.'),coded(2,'Last grounded sentence.','Camera')]})
    rows=extract_observations('iPhone Duo reviews',segments,completion)
    assert [(r['segment_id'],r['start_seconds'],r['end_seconds']) for r in rows]==[(1,5,6),(2,9,10)]


def observation(competitor='',attribute='Battery'):
    return {'attribute':attribute,'quote':'iPhone Duo is better than Pixel 9 Pro and Galaxy Fold 7 for battery life.','sentiment':'positive','theme':'Battery longevity','competitor':competitor,'is_direct':bool(competitor),'start_seconds':1,'end_seconds':5}


def test_canonicalization_preserves_model_generations_variants_and_brand_only_entities():
    from src.grounded_insights import canonicalize
    raw={'opaque-source':[{**observation(c),'quote':f'iPhone Duo is better than {c} for battery life.','start_seconds':i*10,'end_seconds':i*10+5} for i,c in enumerate(['Pixel 9','Pixel 9 Pro','Pixel 10','Samsung','Galaxy Fold'])]}
    def completion(_):
        return json.dumps({'attributes':[], 'competitors':[
            {'name':'Pixel 9','labels':['Pixel 9','Pixel 9 Pro','Pixel 10']},
            {'name':'Galaxy Fold','labels':['Samsung','Galaxy Fold']},
        ]})
    result=canonicalize(raw,completion)
    assert {r['competitor'] for r in result['opaque-source']}=={'Pixel 9','Pixel 9 Pro','Pixel 10','Samsung','Galaxy Fold'}
    assert raw['opaque-source'][1]['competitor']=='Pixel 9 Pro'


def test_synonym_normalization_counts_one_quote_once_without_changing_raw_evidence():
    from src.grounded_insights import canonicalize
    raw={'source\u2014id':[observation(attribute='Battery life'),observation(attribute='Battery endurance')]}
    result=canonicalize(raw,lambda _:json.dumps({'attributes':[{'name':'Battery','labels':['Battery life','Battery endurance']}],'competitors':[]}))
    assert list(result)==['source\u2014id'] and len(result['source\u2014id'])==1
    row=result['source\u2014id'][0]
    assert (row['quote'],row['start_seconds'],row['end_seconds'])==(raw['source\u2014id'][0]['quote'],1,5)
    report=aggregate({'evidence':[]},result)
    assert report['attributes'][0]['mention_count']==1
    assert report['attributes'][0]['sentiment_counts']['positive']==1


def test_one_quote_can_support_two_competitors_without_inflating_attribute_count():
    from src.grounded_insights import canonicalize
    raw={'source':[observation('Pixel 9 Pro'),observation('Galaxy Fold 7')]}
    result=canonicalize(raw,lambda _:json.dumps({'attributes':[],'competitors':[]}))
    report=aggregate({'evidence':[]},result)
    assert {c['competitor'] for c in report['comparisons']}=={'Pixel 9 Pro','Galaxy Fold 7'}
    assert report['attributes'][0]['mention_count']==1
    assert report['attributes'][0]['sentiment_counts']['positive']==1


def test_review_passes_preserve_richer_direct_evidence_without_exact_duplicate_count(monkeypatch):
    import src.grounded_insights as module
    base=observation()
    direct=observation('Pixel 9 Pro')
    calls=[]
    def extract(query,segments,**options):
        calls.append(options)
        return [direct] if options.get('comparisons_only') else [base]
    monkeypatch.setattr(module,'extract_observations',extract)
    raw_segments=[{'start':1,'end':5,'text':direct['quote']}]
    result=module.extract_review_observations('iPhone Duo reviews',raw_segments)
    assert calls==[{}, {'window_size':20,'comparisons_only':True}]
    assert result==[direct]
    assert raw_segments[0]['text']==direct['quote']


def test_canonical_brand_prefix_variants_merge_without_rewriting_quote():
    from src.grounded_insights import canonicalize
    first={**observation('Samsung Galaxy Z Fold 7'),'quote':'iPhone Duo lasts longer than Samsung Galaxy Z Fold 7.'}
    second={**observation('Galaxy Z Fold 7'),'quote':'iPhone Duo is better than Galaxy Z Fold 7.','start_seconds':6,'end_seconds':10}
    normalized=canonicalize({'raw-source':[first,second]},lambda _:json.dumps({'attributes':[],'competitors':[{'name':'Samsung Galaxy Z Fold 7','labels':['Samsung Galaxy Z Fold 7','Galaxy Z Fold 7']}]}))
    assert {row['competitor'] for row in normalized['raw-source']}=={'Samsung Galaxy Z Fold 7'}
    assert [r['quote'] for r in normalized['raw-source']]==[first['quote'],second['quote']]
    assert [r['competitor'] for r in [first,second]]==['Samsung Galaxy Z Fold 7','Galaxy Z Fold 7']
