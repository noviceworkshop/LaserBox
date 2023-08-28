import adsk.core, adsk.fusion, traceback

def draw_bottom(component:adsk.fusion.Component,w,h,d,t,notch):
    sketches = component.sketches
    sketch = sketches.add(component.xZConstructionPlane)
    sketch.name = 'bottom'
    lines = sketch.sketchCurves.sketchLines
    points = bottom_points(w, h, d, t,notch)
    
    pre_x,pre_y = points[0]
    
    for (x, y) in points[1:]:
        lines.addByTwoPoints(
            adsk.core.Point3D.create(pre_x, pre_y, 0),
            adsk.core.Point3D.create(x, y, 0),)
        lines.addByTwoPoints(
            adsk.core.Point3D.create(pre_x, -pre_y, 0),
            adsk.core.Point3D.create(x, -y, 0),)
        lines.addByTwoPoints(
            adsk.core.Point3D.create(pre_y, pre_x, 0),
            adsk.core.Point3D.create(y, x, 0),)
        lines.addByTwoPoints(
            adsk.core.Point3D.create(-pre_y, pre_x, 0),
            adsk.core.Point3D.create(-y, x, 0),)
        pre_x, pre_y = (x, y)

    
def bottom_points(w, h, d, t,notch):
    n_len = w/(notch*2+1)
    points = []
    start_x = w/2
    start_y = h/2
    count = 0
    for i in range((notch*2+1)*2):
        if count ==0:
            points.append([start_x,start_y])
            count += 1
            continue
        elif count%4 in [0,1]:
            next_x = start_x - n_len*((i+1)//2)
            next_y = start_y
            points.append([next_x,next_y])
            count+=1
        else:
            next_x = start_x - n_len*((i+1)//2)
            next_y = start_y - t
            points.append([next_x,next_y])
            count+=1
    return points
    

# def create_sketch()