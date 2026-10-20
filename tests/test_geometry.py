from geographiclib.geodesic import Geodesic
from osintnet.geometry import within_radius,normalize_places

def test_geodesic_mile_boundary_and_provider_identity():
    lat,lon=40.7,-73.9
    a=Geodesic.WGS84.Direct(lat,lon,90,1609.343)
    b=Geodesic.WGS84.Direct(lat,lon,90,1609.345)
    assert within_radius(lat,lon,a['lat2'],a['lon2'])[0]
    assert not within_radius(lat,lon,b['lat2'],b['lon2'])[0]
    items=[{'type':'node','id':1,'lat':lat,'lon':lon,'tags':{'name':'Example','shop':'books','religion':'unused'}},{'type':'node','id':1,'lat':lat,'lon':lon,'tags':{'name':'Duplicate'}},{'type':'node','id':2,'lat':b['lat2'],'lon':b['lon2']}]
    result=normalize_places(items,lat,lon)
    assert len(result)==1 and result[0]['source_id']=='node/1'and'religion'not in result[0]

def test_osm_categories_are_explicit_bounded_and_default_to_shops():
    import urllib.parse
    import pytest
    from osintnet.adapters import validate
    p={'latitude':40.7,'longitude':-73.9,'radius_m':1609.344}
    url,_,_=validate('overpass',p);query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['data'][0]
    assert '[shop]'in query and '[office]'not in query
    with pytest.raises(ValueError,match='supported_place_categories'):validate('overpass',{**p,'categories':['shop;out;']})
    with pytest.raises(ValueError,match='supported_place_categories'):validate('overpass',{**p,'categories':['shop','shop']})
