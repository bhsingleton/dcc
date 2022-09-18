# DCC (Digital Content Creation)
A python package used to provide a suite of DCC-agnostic interfaces for tool developers.

## How does it work?
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
By creating export sets you provide other artists - who aren't privy to the original creator's knowledge - a quick and easy way to export an asset.  
For example, animators can associate their animation sequences with an export set without having to muddle around inside the outliner for exportable nodes.  
![image](https://user-images.githubusercontent.com/11181168/190901928-2e4fb610-5856-4525-b995-135014258358.png)



# FBX Sequencer Editor
