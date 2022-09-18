# DCC (Digital Content Creation)
A python package used to provide a suite of DCC-agnostic interfaces for tool developers.

### How does it work?
The dcc package uses function sets to encapsulate logic for specific DCC components.  
For example, all required logic for nodes is outlined in the abstract class: ```dcc.abstract.afnnode.AFnNode```.  
Next, each DCC defines the logic from its own package: ```dcc.maya.fnnode.FnNode``` and ```dcc.max.fnnode.FnNode```.  
Finally, the top-level module ```dcc.fnnode``` resolves the import statement by detecting the DCC the user is using and importing accordingly.  

All together, an example of DCC-agnostic can be:  
```
from dcc import fnnode

node = fnnode.FnNode('locator1')
print(node.handle())
```

Function sets also provide multiple mechanisms to attach objects to them.  
Please note that not all function sets require objects, such as FnScene, to operate!  

The following illustrates how you can attach a queue to a function set in order to process multiple objects.   
```
from dcc import fnnode, fnscene

scene = fnscene.FnScene()
node = fnnode.FnNode()
node.setQueue(scene.getActiveSelection())

while not node.isDone():
  node.next()
  print(node.name())
```

# FBX
Exporting game assets can be a pain, especially across multiple DCCs.  
To remedy this the dcc package comes with an fbx sub-package to assist in day-to-day exporting tasks.  

## FBX Export Set Editor
The export set editor provides artists and riggers the means to define which objects get exported and where.  
But why do this?  
By creating export sets, you provide other artists - who aren't privy to the original creator's knowledge - a quick and easy way to export an asset.  
For example, animators can associate their animation sequences with an export set without having to muddle around inside the outliner for exportable nodes. 

### How to open:

```
from dcc.fbx.ui import qfbxexportseteditor

window = qfbxexportseteditor.QFbxExportSetEditor()
window.show()
```

### How to use:

![image](https://user-images.githubusercontent.com/11181168/190901928-2e4fb610-5856-4525-b995-135014258358.png)  

### Asset:
* **Name**: The name of the asset.
* **Directory**: The current working directory for the asset (Also accepts environment variables).
* **File Type**: Specifies if the fbx should be exported either as binary or ascii.
* **File Version**: Specifies which version of fbx to use (Please see your game engine's documentation for the version).

### Export Sets:
* **Name**: The name of the export set and associated file name.
* **Directory**: The directory, relative to the asset, that the set will be exported to.
* **Scale**: A value to scale up/down the exported nodes.
* **Move to Origin**: Instructs the exporter whether all nodes inside the fbx should be shifted back to origin.
* **Remove Display Layers**: Instructs the exporter whether all display layers inside the fbx should be removed.
* **Remove Containers**: Instructs the exporter whether all containers inside the fbx should be removed.
* **Camera**: Specifies the name of the camera to export.
* **Skeleton**: Specifies the joints that should be selected for export.
* **Mesh**: Specifies the nodes that should be selected for export and which mesh data components should be included.
* **Custom Scripts**: Provides developer hooks to inject their own pre/post export code on export.

### Where is my data?
All data gets serialized to the file properties.  
This allows your data to be accessed externally by other tools for referencing.
