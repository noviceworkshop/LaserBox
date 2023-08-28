#Author-Autodesk Inc.
#Description-Demo command input examples
import adsk.core, adsk.fusion, traceback
import os
import sys
sys.path.append(os.path.dirname(__file__))
# from CreateLines import *

_app = None
_ui  = None

# Global set of event handlers to keep them referenced for the duration of the command
_handlers = []

#DEFAULT_VALUE
DEFAULT_WIDTH = '100 mm'
DEFAULT_HEIGHT = '100 mm'
DEFAULT_DEPTH = '100 mm'
DEFAULT_THICKNESS = '3 mm'



    


class buildbox():
    def __init__(self,component):
        self.component = component
        self.sketches = component.sketches
        pass

    def buildAll(self,w, h, d, t,notch,mode):
        #make bottom,right,front
        if mode=='normal':
            self.make_normal_extrusion(w,d,t,notch,self.component.xZConstructionPlane,x_cavity=True,y_cavity=True,name='bottom')
        if mode=='brim':
            pass
        self.make_normal_extrusion(w,h,t,notch,self.component.xYConstructionPlane,x_cavity=False,y_cavity=False,name='front')
        self.make_normal_extrusion(d,h,t,notch,self.component.yZConstructionPlane,x_cavity=False,y_cavity=True,name='right')
        
        #make the other three sides
        self.makeCopy('bottom','top')
        self.makeCopy('front','back')
        self.makeCopy('right','left')
        #move so the 6 sides match together
        self.moveBody('front',y=h/2,z=d/2-t)
        self.moveBody('back',y=h/2,z=-d/2)
        self.moveBody('right',y=h/2,x=w/2-t)
        self.moveBody('left',y=h/2,x=-w/2)
        self.moveBody('top',y=h-t)

    def corner_points(self,x, y, t, notch,x_cavity,y_cavity): #x_cavity and y_cavity is defined by whether there the notch should be an protrusion or a cavity
        x_len = (x)/(notch*2+1)
        if x_cavity:
            y_len = (y)/(notch*2+1)
        else:
            y_len = (y-t*2)/(notch*2+1)
        points = []    
        # Plot the first two points horizontal side 
        # XOR base on whether there's a notch at the centerline and whether there is a notch or an protrusion or a cavity
        start_x = 0
        start_y = y/2
        if notch%2==1 ^ x_cavity:
            points.append([start_x,start_y])    
            points.append([start_x+x_len*.5,start_y])
            count = 2
        else:
            points.append([start_x,start_y-t])    
            points.append([start_x+x_len*.5,start_y-t])
            count = 0
        start_x = start_x+x_len*.5

        #draw the rest of the lines on the horizontal side
        for i in range((notch*2)):
            next_x = start_x + x_len*((i+1)//2)
            if count%4 in [0,1]:
                next_y = start_y
            else:
                next_y = start_y - t
            points.append([next_x,next_y])
            count+=1
        #count correction if only one of axis is set as cavity = True
        if y_cavity ^ x_cavity:
            count+=2
        #correction on the last point on the horizontal line if the y_cavity is True
        if not y_cavity:
            points[-1] = [points[-1][0]-t,points[-1][1]]
        
        #draw the beginning part of the perpendicular side
        start_x = next_x
        start_y = next_y
        for i in range(1,(notch*2)):
            if (count%4 in [0,3]):
                next_x = start_x - t
            else:
                next_x = start_x 
            next_y = start_y - y_len*((i+1)//2)
            points.append([next_x,next_y])
            count+=1
        
        # Plot the last two points perpendicular side 
        # XOR base on whether there's a notch at the centerline and whether there is a notch or an protrusion or a cavity
        if notch%2==1 ^ y_cavity:
            points.append([start_x,next_y])    
            points.append([start_x,next_y-y_len*.5])
        else:
            points.append([start_x-t,next_y])    
            points.append([start_x-t,next_y-y_len*.5])
        
        return points

    def draw_line(self,sketch:adsk.fusion.Sketch,points):
        lines = sketch.sketchCurves.sketchLines
        pre_x,pre_y = points[0]
        
        for (x, y) in points[1:]:
            lines.addByTwoPoints(
                adsk.core.Point3D.create(pre_x, pre_y, 0),
                adsk.core.Point3D.create(x, y, 0),)
            pre_x, pre_y = (x, y)
        return lines

    def make_normal_extrusion(self,x,y,t,notch,plane:adsk.fusion.ConstructionPlane,x_cavity,y_cavity,name):
        
        sketch = self.sketches.add(plane)
        sketch.name = name
        points = self.corner_points(x, y, t,notch,x_cavity=x_cavity,y_cavity=y_cavity)
        self.draw_line(sketch,points)
        self.draw_line(sketch,[[x,-y] for [x,y]in points])
        self.draw_line(sketch,[[-x,-y] for [x,y]in points])
        self.draw_line(sketch,[[-x,y] for [x,y]in points])
        
        extrudes = self.component.features.extrudeFeatures
        prof = sketch.profiles.item(0)
        distance = adsk.core.ValueInput.createByReal(t)
        extrude1 = extrudes.addSimple(prof,distance,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        body1 = extrude1.bodies.item(0)
        body1.name = name

    def moveBody(self,bodyname,x=0,y=0,z=0):
        body = self.component.bRepBodies.itemByName(bodyname)
        vector = adsk.core.Vector3D.create(x, y, z)
        transform = adsk.core.Matrix3D.create()
        transform.translation = vector
        features = self.component.features
        moveFeats = features.moveFeatures
        move_bodies = adsk.core.ObjectCollection.create()
        move_bodies.add(body)
        moveFeatureInput = moveFeats.createInput2(move_bodies)
        moveFeatureInput.defineAsFreeMove(transform)
        moveFeats.add(moveFeatureInput)

    def makeCopy(self,org_body_name,new_body_name):
        org_body = self.component.bRepBodies.itemByName(org_body_name)
        holder = self.component.features.copyPasteBodies.add(org_body)
        new_body = holder.bodies.item(0)
        new_body.name = new_body_name
    

class myCommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            unitsMgr = _app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = {}
            for input in command.commandInputs:
                inputs[input.id] = input

            # Get current design
            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design:
                
                return

            component = design.rootComponent
            inputs['width'] = unitsMgr.evaluateExpression(inputs['width'].expression, "mm")
            inputs['height'] = unitsMgr.evaluateExpression(inputs['height'].expression, "mm")
            inputs['depth'] = unitsMgr.evaluateExpression(inputs['depth'].expression, "mm")
            inputs['thickness'] = unitsMgr.evaluateExpression(inputs['thickness'].expression, "mm")
            inputs['notchNum'] = inputs['notchNum'].valueOne
            inputs['mode'] = inputs['mode'].selectedItem.name
            _ui.messageBox(f"{inputs['mode']}")
            # Built it!
            box = buildbox(component)
            box.buildAll(inputs['width'],inputs['height'],inputs['depth'],inputs['thickness'],inputs['notchNum'],inputs['mode'])

            args.isValidResult = True

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler that reacts to when the command is destroyed. This terminates the script.            
class MyCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # When the command is done, terminate the script
            # This will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)

            # Connect to the command destroyed event.
            onDestroy = MyCommandDestroyHandler()
            onExecute = myCommandExecuteHandler()
            cmd.execute.add(onExecute)
            cmd.destroy.add(onDestroy)
            _handlers.append(onExecute)
            _handlers.append(onDestroy)
            

            # Get the CommandInputs collection associated with the command.
            inputs = cmd.commandInputs

            # Create value input.
            inputs.addValueInput('width', 'Width', 'mm', adsk.core.ValueInput.createByString(DEFAULT_WIDTH))
            inputs.addValueInput('height', 'Height', 'mm', adsk.core.ValueInput.createByString(DEFAULT_HEIGHT))
            inputs.addValueInput('depth', 'Depth', 'mm', adsk.core.ValueInput.createByString(DEFAULT_DEPTH))
            inputs.addValueInput('thickness', 'Thickness', 'mm', adsk.core.ValueInput.createByString(DEFAULT_THICKNESS))

            # Create integer slider input with one slider.
            inputs.addIntegerSliderCommandInput('notchNum', 'Number of notch per side', 2, 10)

            # Create a message that spans the entire width of the dialog by leaving out the "name" argument.
            # message = '<div align="center">Normal: regular 6 sided box</div><div>Offset: Top and bottom with 3mm brim</div>'
            # inputs.addTextBoxCommandInput('fullWidth_textBox', '', message, 2, True)    

            # Create dropdown input with radio style.
            dropdownInput3 = inputs.addDropDownCommandInput('mode', 'Box type', adsk.core.DropDownStyles.LabeledIconDropDownStyle);
            dropdown3Items = dropdownInput3.listItems
            dropdown3Items.add('Normal', True, '')
            dropdown3Items.add('Brim', False, '')

            
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        # Get the existing command definition or create it if it doesn't already exist.
        cmdDef = _ui.commandDefinitions.itemById('cmdInputsSample')
        if not cmdDef:
            cmdDef = _ui.commandDefinitions.addButtonDefinition('cmdInputsSample', 'Command Inputs Sample', 'Sample to demonstrate various command inputs.')

        # Connect to the command created event.
        onCommandCreated = MyCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Execute the command definition.
        cmdDef.execute()

        # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))