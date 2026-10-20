from geographiclib.geodesic import Geodesic

def within_radius(latitude,longitude,point_latitude,point_longitude,radius_m=1609.344):
    distance=Geodesic.WGS84.Inverse(latitude,longitude,point_latitude,point_longitude)['s12']
    return distance<=radius_m,distance

def normalize_places(elements,latitude,longitude,radius_m=1609.344):
    seen=set();out=[]
    for item in elements:
        key=str(item.get('type'))+'/'+str(item.get('id'));tags=item.get('tags',{});center=item.get('center',item)
        if key in seen or not all(k in center for k in('lat','lon')):continue
        inside,distance=within_radius(latitude,longitude,center['lat'],center['lon'],radius_m)
        if not inside:continue
        seen.add(key)
        out.append({'provider':'OpenStreetMap','source_id':key,'name':tags.get('name')or tags.get('brand')or'Unnamed listing','category':tags.get('shop')or tags.get('office')or tags.get('amenity')or'other','latitude':center['lat'],'longitude':center['lon'],'distance_m':round(distance,3)})
    return out
