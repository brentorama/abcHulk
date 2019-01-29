import maya.cmds as cmd
import os

gA = cmd.getAttr
sA = cmd.setAttr
cA = cmd.connectAttr
lC = cmd.listConnections
dA = cmd.disconnectAttr
cN = cmd.createNode
aA = cmd.addAttr

def unFuckTheReferenceNodes():
    log = []
    referenceNodes = cmd.ls(type = 'reference')
    for one in referenceNodes:
        if 'RN' in one:
            node = cmd.referenceQuery(one, nodes=True)[0]
            check =  node.split(':')[0]
            if check != node:
                log.append('Bad namespace %s : %s' % (check, node))
            split = one.split('RN')
            if len(split[1]) > 0:
                log.append('Bad reference node %s, fixed.' % one)
                cmd.lockNode(one, lock = False)
                fix = cmd.rename(one, '%sRN' % split[0])
                cmd.lockNode(fix, lock = True)        
    return log

def replaceRiggingWithShading(one):
    report = ''
    filePath = cmd.referenceQuery('%sRN' % one, filename = True)
    if 'rigging' in filePath:
        report = 'Updated %s reference to shader version' % one
        newPath = filePath.replace('rigging', 'shading')
        cmd.file(newPath, loadReference = '%sRN' % one)
        if one == 'Phone01':
            cmd.sA('Phone01:deformHead_root.translateX', 180.001)
            cmd.sA('Phone01:deformHead_root.translateX', 180.0)
        print 'updating reference to %s ' %newPath
    return report
	    
def makeRenderSet(name = 'render'):
    geo = []
    lister = cmd.listRelatives('render_GP', ad = True, ni = True, s = False, typ = 'transform')
    for object in lister:
        shape = cmd.listRelatives(object, s= True, ni = True)
        if shape != None:
            shapeType = cmd.objectType(shape)
            if shapeType == 'mesh':
                geo.append(object)
    geo.sort()
    if cmd.objExists('render'):
        cmd.sets(geo, include = name)
    else:
        cmd.sets(geo, name = name)

def saveShaderAssignments(renderSet = 'render'):
    shaders = []
    renderObs = cmd.sets(renderSet, q = True)
    for one in renderObs:
        shape = cmd.listRelatives(one, type = 'mesh', ni = True)[0]
        shader = cmd.lC(shape, type='shadingEngine')[0]
        shaders.append(shape+ ' : ' + shader)
    return shaders

def addShaderAttribute(shaders):
    for one in shaders:
        shape, shader = one.split(' : ')
        if not cmd.attributeQuery('shaderGp', node = shape, ex = True):
            cmd.aA(shape, ln = 'shaderGp', dt = 'string', k = True)
        cmd.sA('%s.shaderGp' % shape, shader, type = 'string')

def saveShaderMap(shaders):
    curFile = cmd.file(q = True, sn = True)
    curName = cmd.file(q= True, sn = True, shn = True)
    name = curName.split('.')[0]
    dirc = curFile.split(curName)[0]
    shaderMap = '%s%s.txt' % (dirc, name)
    f = open(shaderMap, 'w+')
    for one in shaders:
        f.write(one+'\n')
    f.close()
    return shaderMap

def loadShaderMap(asset = 'Boy'):
    map = []
    shaderMap = 'X:/production/assets/ch/%s/shading/master/%s.txt' % (asset, asset)
    if not os.path.isfile(shaderMap):
        shaderMap = 'X:/production/assets/pr/%s/shading/master/%s.txt' % (asset, asset)
    f=open(shaderMap, "r")    
    if f.mode == 'r':
        map = f.read().splitlines()
    f.close()
    return map       
    
def getNameSpace(ob = ''):
	ns = ob.split(':')[0]
	return ns
		
def exportAbc(asset, start, end, export):
     '''This function exports the mesh and returns the abc filename and the save path
    only exports transforms with visibility == True, so make sure visibility 
    animation is done on the ROOT node'''
    
    panel = 'modelPanel4'
    cmd.modelEditor(panel, e=1, allObjects=0)
    objects = ''
    obs = [x for x in cmd.listRelatives('%s:render_GP' % asset, ad = True, typ = 'mesh')] 
    for one in obs:
        pNode = cmd.listRelatives(one, p = True)[0]
        if gA('%s.v' % pNode) == 1: 
            objects+= '-root %s ' % pNode 
             
    baseName = cmd.file(q = True, sn = True, shn=True)
    filePath = cmd.file(q=True, sn=True)
    outPath = os.path.join(filePath.split(baseName)[0], '%s.ma' % asset)
    renderPath = outPath.replace('animation', 'rendering')
    fileName = baseName.split('.')[0] + '_' + asset + '.abc'
    dirPath = 'X:/cache/alembic/'
    command = '-frameRange %s %s -attr shaderGp -uvWrite -worldSpace -dataFormat ogawa %s-file %s%s'  % (start-3, end+3, objects, dirPath, fileName)
    if export:
        cmd.AbcExport(j = '%s' % command)
    abcPath = '%s%s' % (dirPath, fileName)
    cmd.modelEditor(panel, e=1, allObjects=1)
    print renderPath
    return abcPath, renderPath

def importShaders(shader = 'Boy'):
    log = []
    shaderFile = 'X:/production/assets/ch/%s/shading/master/%s.shaders.ma' % (shader, shader)
    propFile = 'X:/production/assets/pr/%s/shading/master/%s.shaders.ma' % (shader, shader)
    try:
        cmd.file(shaderFile, i = True)
    except:
        log.append('Failed importing shader from %s' % shaderFile)
        try:
            cmd.file(propFile, i = True)
        except:
            log.append('Failed importing shader from %s' % propFile)
    return log
    
def deleteAllShaders():
    '''read shaders from file'''
    mat = cmd.ls(mat = True)
    shadingEngine = cmd.ls(type = 'shadingEngine')
    history = cmd.listHistory(mat)
    cmd.select(history, noExpand = True)
    cmd.delete()
    cmd.delete(shadingEngine)

def updateShaders(asset = 'Boy'):
    deleteAllShaders()
    importShaders(asset)
    map = loadShaderMap(asset)
    assignShadersToObjects(map)

def assignShadersToObjects(map = []):
    log = []
    for one in map:
        ob, SG = one.split(' : ')
        try:
            cmd.sets(ob, e=True, forceElement=SG)
            cmd.refresh()
        except:
            log.append('Failed connecting shader to %s Requires manual assignment' % ob)
    return log
	
def createFile(asset, abcIn, savePath, start, end): 
    log = []
    cmd.file(new=True, force = True)  
    cmd.playbackOptions(e = True, minTime = start, ast = start)
    cmd.playbackOptions(e = True, maxTime= end, aet = end)
    cmd.currentUnit(time='film')
    cmd.currentTime(start)
    root = cmd.group(em=True, name = asset)
    node = cmd.AbcImport(abcIn, mode = 'import', reparent = root)
    objs = cmd.listRelatives(root)
    result = ''.join([i for i in asset if not i.isdigit()])
    message = importShaders(shader = result)
    if message:
        for one in message:
            log.append(one)
    map = loadShaderMap(result)
    message = assignShadersToObjects(map)
    if message:
        for one in message:
            log.append(one)  
    cmd.file(rename = savePath)
    cmd.file(save = True, f = True, type = "mayaAscii")
    return log
	
def smash(export = True, buildFiles = True, preview = True):
    sel = cmd.ls(sl=True)
    if len(sel) == 0:
        print 'You need to select something you want to export'
    else:
        reportLog = ['\n']
        ns = []
        output = {}
        obs = []
        newFiles = []
        start = int(cmd.playbackOptions(q = True, ast= True))
        end = int(cmd.playbackOptions(q = True, aet= True))
        report = unFuckTheReferenceNodes()
        if report:
            for one in report:
                reportLog.append(one)
        for one in sel:
            name = getNameSpace(one)
            ns.append(name)
        obs = list(set(ns))
        for asset in obs: 
            report = replaceRiggingWithShading(asset) 
            if report:
                reportLog.append(report)
        print 'all rigs updated to shader version'
        if export:
            for asset in obs:
                print 'exporting %s' % asset
                abcOut, savePath = exportAbc(asset, start, end, export = True)     
                output[asset] = [abcOut, savePath] 
        if buildFiles:
            for asset in output:
                abcIn = output[asset][0]
                savePath = output[asset][1]
                log = createFile(asset, abcIn, savePath, start, end)
                newFiles.append(savePath)
                if len(log):
                    for line in log:
                        reportLog.append(line)
        if preview:
            cmd.file(new=True, force = True)
            cmd.currentUnit(time='film')
            cmd.playbackOptions(e = True, minTime = start, ast = start)
            cmd.playbackOptions(e = True, maxTime= end, aet = end)
            cmd.currentTime(start)
            for importFile in newFiles:
                cmd.file(importFile, i = True) 
        for name in output:
            print name
            print output[name]
        for new in newFiles:
            print new
        for line in reportLog:
            print line
        print ('asset = \'%s\' \nabcIn = \'%s\'\nsavePath = \'%s\'\nstart = \'%s\'\nend = \'%s\''%(asset, abcIn, savePath, start, end))
            
def updateShadingMap():
    makeRenderSet()	
    shaders = saveShaderAssignments()  
    map = saveShaderMap(shaders)
    addShaderAttribute(shaders)
    for one in shaders:
        print one
    print map




