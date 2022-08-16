import maya.cmds as cmds
import maya.mel as mel
import re
import random as rand
import math

################################################################################
## Functions
################################################################################

def takeSecond( elem ):
    return elem[1]

def getShells( obj ):

	# convert to vertices
	verts = cmds.polyListComponentConversion( obj, toVertex=True )

	# flatten the list
	verts = cmds.ls( verts, flatten=True )

	# define variables
	remaining_verts = verts
	shells = list()

	while len( remaining_verts ) > 0:
		
		# select the first shell
		cmds.select( remaining_verts[0] )
		
		# convert to shell
		cmds.polySelectConstraint( shell=True, t=0x0001, m=2 )
		
		# define the shell as the next shell
		next_shell = cmds.ls( selection=True, flatten=True )
		
		# clear the selection
		cmds.select( clear=True )
		
		# add it to the list of shells
		shells.append( next_shell )
		
		# remove the shell from the list of remaining verts
		remaining_verts = set( remaining_verts )
		next_shell = set( next_shell )
		remaining_verts = remaining_verts.difference( next_shell )
		remaining_verts = list( remaining_verts )
		
	cmds.polySelectConstraint( shell=False )
	return shells

def getPoleVerts( obj ) :
	# convert to vertices
	verts = cmds.polyListComponentConversion( obj, toVertex=True )
	# flatten the list
	verts = cmds.ls( verts, flatten=True )
	# create an empty list to store the poles
	poles = list()
	# for all vertices
	for v in verts:
		# get the edges connected to the vertex and store it in a list
		edges = cmds.polyListComponentConversion( v, toEdge=True )
		# flatten the list
		edges = cmds.ls( edges, flatten=True )
		# if there are more than 4 edges
		if len( edges ) > 4 :
			# add it to the list of poles
			poles.append( v )
	# return the list of poles
	return poles

def getSeamEdges( obj, poles ):
	# create an empty set to store the edges
	pole_edges = set()
	# for each pole
	for v in poles:
		# convert the pole to edges
		edges = cmds.polyListComponentConversion( v, toEdge=True )
		# flatten the list
		edges = cmds.ls( edges, flatten=True )
		# convert to a set
		edges = set( edges )
		# merge the esges with the set of edges
		pole_edges = pole_edges.union( edges )
	
	# get the first edge
	edge = list( pole_edges )[0]
	
	# get the index of the edge
	temp_string = edge.split( "[" )
	temp_string = temp_string[1].split( "]" )[0]
	edge_index = int( temp_string )
	# convert the edge to an edge loop
	cmds.polySelect( obj, edgeLoop=edge_index )
	# list and flatten the selection
	seam_edges = cmds.ls( selection=True, flatten=True )
	# convert to a set
	seam_edges = set( seam_edges )
	
	# get the union of the seam and pole edges
	result_edges = seam_edges.union( pole_edges )
	# convert to a list
	result_edges = list( result_edges )
	# return
	return result_edges

def normalizePoleTriangles( obj, poles ):

	# get all faces connected to the pole
	pole_faces = cmds.polyListComponentConversion( poles, toFace=True )
	# flatten the list
	pole_faces = cmds.ls( pole_faces, flatten=True )
	# get all the uvs for the pole
	pole_uvs = cmds.polyListComponentConversion( poles, toUV=True )
	# flatten the list
	pole_uvs = cmds.ls( pole_uvs, flatten=True )
	# convert to a set
	pole_uvs = set( pole_uvs )
	# define a threshold
	threshold = 0.01
	
	for face in pole_faces:
		face_uvs = cmds.polyListComponentConversion( face, toUV=True )
		face_uvs = cmds.ls( face_uvs, flatten=True )
		face_uvs = set( face_uvs )
		
		pole_uv = face_uvs.intersection( pole_uvs )
		non_pole_uv = face_uvs.difference( pole_uv )
		
		non_pole_uv = list( non_pole_uv )
		pole_uv = list( pole_uv )
		
		# get the pole coordinates
		pole_coord = cmds.polyEditUV( pole_uv, query=True )
		
		case = 0
		# check case
		if pole_coord[0] > ( 1 - threshold ) and pole_coord[0] < ( 1 + threshold ):
			if pole_coord[1] > ( 1 - threshold ) and pole_coord[1] < ( 1 + threshold ):
			 	case = 1
			else:
			 	case = 2
		else:
			case = 3
		
		# move the pole uv
		cmds.polyEditUV( pole_uv, u=0.5, v=1.0, r=False )
		
		uvc_red = cmds.polyEditUV( non_pole_uv[0], query=True )
		uvc_blue = cmds.polyEditUV( non_pole_uv[1], query=True )
		
		if case == 2:
			if uvc_red[0] > uvc_blue[0]:
				a_uv = non_pole_uv[0]
				b_uv = non_pole_uv[1]
			else:
				a_uv = non_pole_uv[1]
				b_uv = non_pole_uv[0]
			cmds.polyEditUV( a_uv, u=0.0, v=0.0, r=False )
			cmds.polyEditUV( b_uv, u=1.0, v=0.0, r=False )
			
		if case == 3:
			if uvc_red[1] > uvc_blue[1]:
				a_uv = non_pole_uv[1]
				b_uv = non_pole_uv[0]
			else:
				a_uv = non_pole_uv[0]
				b_uv = non_pole_uv[1]
			cmds.polyEditUV( a_uv, u=0.0, v=0.0, r=False )
			cmds.polyEditUV( b_uv, u=1.0, v=0.0, r=False )

def unitizeAndLayout( obj, seams, poles, uv_set ):
	# convert the object to edges
	edges = cmds.polyListComponentConversion( obj, toEdge=True )
	# flatten the list
	edges = cmds.ls( edges, flatten=True )
	# convert to a set
	edges = set( edges )
	# convert to a set
	seams = set( seams )
	# get the difference between the two sets
	sew_edges = edges.difference( seams )
	# convert to a list
	sew_edges = list( sew_edges )
	# set the current uv set
	cmds.polyUVSet( obj, currentUVSet=True, uvSet=uv_set )
	# unitize the object
	cmds.polyForceUV( obj, unitize=True )
	# normalize the pole triangles
	normalizePoleTriangles( obj, poles )
	# move and sew edges
	cmds.polyMapSewMove( sew_edges, nf=10, lps=0, ch=1 )
	# layout
	cmds.polyLayoutUV( obj, lm=1, sc=2, se=2, rbf=0, fr=1, ps=0, l=2, gu=1, gv=1, ch=1 )
	# get the uv shell
	uv_shell = cmds.polyListComponentConversion( obj, toUV=True )
	# select the uv shell
	cmds.select( uv_shell )
	# rotate the uv shell
	cmds.polyEditUVShell( rot=True, angle=180, pu=0.5, pv=0.5 )
	# clear the selection
	cmds.select( clear=True )

def getVertsWithEdgeCount( obj, edge_count ):

	verts = cmds.polyListComponentConversion( obj, toVertex=True )
	verts = cmds.ls( verts, flatten=True )
	
	# make a list to hold the verts with the specified edge count
	edge_verts = list()
	
	# get the verts
	for v in verts:
		edges = cmds.polyListComponentConversion( v, toEdge=True )
		edges = cmds.ls( edges, flatten=True )
		if len( edges ) == edge_count:
			edge_verts.append( v )
	
	return edge_verts

def getEdgeLengthSum( edges ):
	
	total_length = 0
	
	for edge in edges:
		verts = cmds.polyListComponentConversion( edge, toVertex=True )
		p = cmds.xform( verts, q=True, t=True, ws=True )
		length = math.sqrt( math.pow( p[0] - p[3], 2 ) + math.pow( p[1] - p[4], 2 ) + math.pow( p[2] - p[5], 2 ) )
		total_length = total_length + length
	
	return total_length

def multVectorByScalar( scalar, vector ):
	
	b = []
	
	for i in range( len( vector ) ):
		b.append( scalar * vector[i] )

	return b

def customRename( obj, name_base, sep, padding, index, first_index, mode ):
	
	if mode==1:
		suffix = str( index + first_index ).rjust( padding, '0' )
	if mode==2:
		suffix = chr( ord('@') + index + first_index )
	
	new_name = name_base + sep + suffix
	cmds.rename( obj, new_name )

# Sort Outliner

def getParentChildList( objs ):
	parent_child_list = list()
	for obj in objs:
		parent = cmds.listRelatives( obj, parent=True, fullPath=True )
		child = cmds.ls( obj, long=True )[0]
		if parent==None:
			parent = "root"
		else:
			parent = parent[0]
		parent_child_pair = list()
		parent_child_pair.append( parent )
		parent_child_pair.append( child )
		parent_child_list.append( parent_child_pair )
	return parent_child_list

def getUniqueParents( objs ):
	parents_set = set()
	for obj in objs:
		parent = cmds.listRelatives( obj, parent=True, fullPath=True )
		if parent==None:
			parent = "root"
		else:
			parent = parent[0]
		parents_set.add( parent )
	unique_parents = list( parents_set )
	return unique_parents

def groupParentChildren( parent_child_list, unique_parents):
	grouped_children = list()
	for p in unique_parents:
		grouped_children.append( list() )
	for pair in parent_child_list:
		for i in range( len( unique_parents ) ):
			if pair[0] == unique_parents[i]:
				grouped_children[i].append( pair[1] )
	return grouped_children

def getAllChildrenFromParents( parents ):
	all_children = list()
	for p in parents:
		all_children.append( list() )
	for i in range( len( parents ) ):
		if parents[i]=="root":
			children = cmds.ls( assemblies=True, long=True )
		else:
			children = cmds.listRelatives( parents[i], fullPath=True, children=True )
		for c in children:
			all_children[i].append( c )
	return all_children

def getObjsAboveSelected( unique_parents, sel_children, all_children ):
	above_selected = list()
	for p in unique_parents:
		above_selected.append( list() )
	for i in range( len( unique_parents ) ):
		#print( "parent: " + unique_parents[i] )
		for c in all_children[i]:
			#print( "all child: " + c )
			match_found = False
			for s in sel_children[i]:
				#print( "comparing: " + s + " and " + c )
				if c==s:
					match_found = True
					break
			if not match_found:
				#print( "NOT FOUND" )
				above_selected[i].append( c )
			else:
				break				
	return above_selected

def getChildTransforms( objs ):
	child_transforms = list()
	for obj in objs:
		children = cmds.listRelatives( obj, fullPath=True, children=True )
		transforms = cmds.ls( children, long=True, type="transform" )
		for t in transforms:
			child_transforms.append( t )
	return child_transforms

def sortOutliner( objs, recursive ):

	parent_child_list = getParentChildList( objs )	
	unique_parents = getUniqueParents( objs )
	grouped_children = groupParentChildren( parent_child_list, unique_parents )
	all_children = getAllChildrenFromParents( unique_parents )
	above_selected = getObjsAboveSelected( unique_parents, grouped_children, all_children )
	
	for i in range( len( grouped_children ) ):
		grouped_children[i].sort()
		grouped_children[i].reverse()
	
	for i in range( len( above_selected ) ):
		above_selected[i].reverse()

	for ls in grouped_children:
		for child in ls:
			cmds.reorder( child, front=True )

	for ls in above_selected:
		for child in ls:
			cmds.reorder( child, front=True )
	
	if recursive:
		child_transforms = getChildTransforms( objs )
		if child_transforms:
			sortOutliner( child_transforms, True )

################################################################################
## Buttons
################################################################################

def OnBtnSeparate( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		shells = getShells( obj )
		if len( shells ) > 1:
			cmds.polySeparate( obj )
			cmds.delete( constructionHistory=True )
	
	child_objs = cmds.listRelatives( sel, c=True )
	
	for obj in child_objs:
		cmds.xform( obj, cp=True )
	
	cmds.select( sel ) 

def OnBtnCombine( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for grp in sel:
		
		# get the number of objects in the group
		num_children = len( cmds.listRelatives( grp ) )
		
		# combine only if there is more than one object in the group
		if num_children > 1:
			# get the parent group	
			parent_grp = cmds.listRelatives( grp, parent=True, fullPath=True )
			# combine the objects in the group
			cmds.polyUnite( grp )
			# delete construction history
			cmds.delete( constructionHistory=True )
			# get the group short names
			short_name = grp.split('|')[-1]	
			# rename the new object
			cmds.rename( short_name )
			# store the new object
			combined_obj = cmds.ls( selection=True )
			# clear the selection
			cmds.select( clear=True )
			
			if parent_grp:
				# parent the new object to the parent group
				cmds.parent( combined_obj, parent_grp )

def OnBtnFixNormals( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
	
		cmds.polySetToFaceNormal( obj )
		#cmds.polySoftEdge( obj, a=60, ch=0 )
		cmds.polySoftEdge( obj, a=180 )
		cmds.select( clear=True )
		
def OnBtnInitializeUV( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		
		# get the names of all uv sets
		uv_sets = cmds.polyUVSet( obj, auv=True, query=True )
		
		# if there are no uv sets, create one
		if len( uv_sets ) == 0:
			cmds.polyUVSet( obj, create=True, uvSet="map1" )
		
		# otherwise, delete all uv sets except for the first and name it to map1
		else:
			
			# get the first uv set
			first_uv_set = uv_sets[0]
			
			# if there are additional uv sets, delete them
			if len( uv_sets ) > 1:
				uv_sets.pop( 0 )
				for uv_set in uv_sets:
					# delete the uv set
					cmds.polyUVSet( obj, delete=True, uvSet=uv_set )
			
			# check if map1 exists
			if first_uv_set != "map1":
				# rename the first uv set to map1
				cmds.polyUVSet( obj, rename=True, uvSet=first_uv_set, newUVSet="map1" )

	# get the faces of the selected objects
	faces = cmds.polyListComponentConversion( sel, toFace=True )
		
	# planar map the uvs
	cmds.polyProjection( faces, type="Planar", ibd=True, kir=True, md="z", ch=True, uvSetName="map1" )
	
	# create two new uv sets
	for obj in sel:
		
		# create new uv sets
		cmds.polyCopyUV( obj, uvSetNameInput="map1", uvSetName="UnitizeUV", createNewMap=True, ch=True )
		cmds.polyCopyUV( obj, uvSetNameInput="map1", uvSetName="StackedUV", createNewMap=True, ch=True )
		
		# set the current uv set
		cmds.polyUVSet( obj, currentUVSet=True, uvSet="map1" )
	
	cmds.select( clear=True )

def OnBtnDeleteUV( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		
		# get the names of all uv sets
		uv_sets = cmds.polyUVSet( obj, auv=True, query=True )
		
		# if there are no uv sets, create one
		if len( uv_sets ) == 0:
			cmds.polyUVSet( obj, create=True, uvSet="map1" )
		
		# otherwise, delete all uv sets except for the first and name it to map1
		else:
			
			# get the first uv set
			first_uv_set = uv_sets[0]
			
			# if there are additional uv sets, delete them
			if len( uv_sets ) > 1:
				uv_sets.pop( 0 )
				for uv_set in uv_sets:
					# delete the uv set
					cmds.polyUVSet( obj, delete=True, uvSet=uv_set )
			
			# check if map1 exists
			if first_uv_set != "map1":
				# rename the first uv set to map1
				cmds.polyUVSet( obj, rename=True, uvSet=first_uv_set, newUVSet="map1" )
		
		# set the current uv set
		cmds.polyUVSet( obj, currentUVSet=True, uvSet="map1" )
		
		# delete the contents of map1
		cmds.polyMapDel( obj )
		
		# delete construction history
		cmds.delete( constructionHistory=True )

	cmds.select( clear=True )

def OnBtnUnfoldLayout( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
	
		# set the current uv set
		cmds.polyUVSet( obj, currentUVSet=True, uvSet="StackedUV" )
		
		# unfold and layout
		cmds.u3dUnfold( obj, ite=10, p=0, bi=1, tf=1, ms=1024, rs=0 )
		cmds.u3dLayout( obj, res=256, scl=1 )

def OnBtnOrientShell( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	mel.eval("texOrientEdge;")
	obj = cmds.ls( selection=True, o=True )
	cmds.u3dLayout( obj, res=256, scl=1 )
	cmds.select( obj )

def OnBtnTransferUVUnitize( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	source_obj = sel[ len( sel ) - 1 ]
	
	for i in range( len( sel ) - 1 ):
		
		dest_obj = sel[ i ]
		cmds.transferAttributes( source_obj, dest_obj, transferUVs=True, sampleSpace=4, sourceUvSet="UnitizeUV", targetUvSet="UnitizeUV"  )
	
	for obj in sel:
		
		# set the current uv set
		cmds.polyUVSet( obj, currentUVSet=True, uvSet="UnitizeUV" )

def OnBtnTransferUVStacked( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	source_obj = sel[ len( sel ) - 1 ]
	
	for i in range( len( sel ) - 1 ):
		
		dest_obj = sel[ i ]
		cmds.transferAttributes( source_obj, dest_obj, transferUVs=True, sampleSpace=4, sourceUvSet="StackedUV", targetUvSet="StackedUV"  )
	
	for obj in sel:
		
		# set the current uv set
		cmds.polyUVSet( obj, currentUVSet=True, uvSet="StackedUV" )

def OnBtnCopyUVSetToUVmap1( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
	
		cmds.polyCopyUV( obj, uvSetName="map1", ch=1 )
	
	cmds.select( sel )

def OnBtnCopyUVSetToUVUnitize( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
	
		cmds.polyCopyUV( obj, uvSetName="UnitizeUV", ch=1 )
	
	cmds.select( sel )

def OnBtnCopyUVSetToStacked( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
	
		cmds.polyCopyUV( obj, uvSetName="StackedUV", ch=1 )
	
	cmds.select( sel )

def OnBtnDeleteExtruded( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		
		verts = cmds.polyListComponentConversion( obj, toVertex=True )
		verts = cmds.ls( verts, flatten=True )
		
		# make a list to hold the corner verts
		corner_verts = list()
		# make a list to hold two edge verts
		two_edge_verts = list()
		
		# get the corner verts
		for v in verts:
			edges = cmds.polyListComponentConversion( v, toEdge=True )
			edges = cmds.ls( edges, flatten=True )
			if len( edges ) <= 3:
				corner_verts.append( v )
			if len( edges ) == 2:
				two_edge_verts.append( v )
		
		if len( corner_verts ) >= 8 and len( two_edge_verts ) < 1:
		
			# get the corner internal edges
			corner_internal_edges = cmds.polyListComponentConversion( corner_verts, toEdge=True, internal=True )
			corner_internal_edges = cmds.ls( corner_internal_edges, flatten=True )
			corner_internal_edges = set( corner_internal_edges )
			
			# get the corner edges
			corner_edges = cmds.polyListComponentConversion( corner_verts, toEdge=True )
			corner_edges = cmds.ls( corner_edges, flatten=True )
			corner_edges = set( corner_edges )
			
			# get the corner seam edges
			corner_seam_edges = corner_edges.difference( corner_internal_edges )
			corner_seam_edges = list( corner_seam_edges )
			
			# get the seam edges
			cmds.select( corner_seam_edges )
			cmds.polySelectConstraint( pp=4, t=0x8000, m=2 )
			seam_edges = cmds.ls( selection=True, flatten=True )
			
			# get the seam faces
			seam_verts = cmds.polyListComponentConversion( seam_edges, toVertex=True )
			seam_faces = cmds.polyListComponentConversion( seam_verts, toFace=True, internal=True )
			
			cmds.select( seam_faces )
			
			cmds.delete( seam_faces )
			
			cmds.select( verts[0] )
			cmds.polySelectConstraint( shell=True, t=0x0001, m=2 )
			back_faces = cmds.ls( selection=True, flatten=True )
			back_faces = cmds.polyListComponentConversion( back_faces, toFace=True )
			cmds.select( clear=True )
			cmds.polySelectConstraint( shell=False )
			
			cmds.delete( back_faces )
	
	cmds.select( sel )

def OnBtnPolyRetopo( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
	
		cmds.polyRetopo( obj, targetFaceCount=10 )

def OnBtnUnitizeUVPlanar( isChecked, uvset_name ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		
		# set the current uv set
		cmds.polyUVSet( obj, currentUVSet=True, uvSet=uvset_name )
		
		cmds.polyForceUV( obj, unitize=True )
		cmds.polyMapSewMove( obj ) # nf=10, lps=0, ch=1
		cmds.polyMultiLayoutUV( obj, lm=1, sc=2, rbf=0, fr=1, ps=0, l=2, gu=1, gv=1, psc=0, su=1, sv=1, ou=0, ov=0 )
		
		verts = cmds.polyListComponentConversion( obj, toVertex=True )
		verts = cmds.ls( verts, flatten=True )
		
		corner_vert = list()
		
		for v in verts:
			
			edges = cmds.polyListComponentConversion( v, toEdge=True )
			edges = cmds.ls( edges, flatten=True )
			
			if len( edges ) <= 2:
				corner_vert.append( v )
		
		a_uv = cmds.polyListComponentConversion( corner_vert[0], toUV=True )
		b_uv = cmds.polyListComponentConversion( corner_vert[1], toUV=True )
		
		a_coord = cmds.polyEditUV( a_uv, query=True )
		b_coord = cmds.polyEditUV( b_uv, query=True )
		
		#print( a_coord )
		#print( b_coord )
		
		uv_shell = cmds.polyListComponentConversion( obj, toUV=True )
		uv_shell = cmds.ls( uv_shell, flatten=True )
		
		threshold = 0.1
		case = 0
		
		if b_coord[0] > 1 - threshold and b_coord[0] < 1 + threshold:
			if b_coord[1] > 1 - threshold and b_coord[1] < 1 + threshold:
				case = 2 # rotate clockwise 90 deg
			else:
				case = 1 # leave as is
		else:
			if b_coord[1] > 1 - threshold and b_coord[1] < 1 + threshold:
				case = 3 # rotate 180 deg
			else:
				case = 4 # rotate counter clockwise 90 deg
		
		#print( case )
		
		cmds.select( uv_shell )
		
		if case == 2:
			cmds.polyEditUVShell( rot=True, angle=-90, pu=0.5, pv=0.5 )
		if case == 3:
			cmds.polyEditUVShell( rot=True, angle=180, pu=0.5, pv=0.5 )
		if case == 4:
			cmds.polyEditUVShell( rot=True, angle=90, pu=0.5, pv=0.5 )
			
		cmds.select( clear=True )
		
	cmds.select( sel )

def OnBtnUnitizeUVPolar( isChecked, uvset_name ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		# get the poles
		obj_poles = getPoleVerts( obj )
		# get seam edges
		obj_seams = getSeamEdges( obj, obj_poles )
		# do uv layout
		unitizeAndLayout( obj, obj_seams, obj_poles, uvset_name )
	
	cmds.select( sel )

def onBtnPaintFXMergeAndCloseHoles( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1

	for obj in sel:
		# merge vertex
		cmds.polyMergeVertex( obj, d=0.0001, am=1, ch=1 )
		# get the perimeter edges
		faces = cmds.polyListComponentConversion( obj, toFace=True )
		edges_perimeter = cmds.polyListComponentConversion( faces, toEdge=True, bo=True )
		# merge to center
		cmds.polyMergeVertex( edges_perimeter, d=100000, ch=1, am=True )
		
	cmds.select( sel )

def onBtnPaintFXToPoly( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	strokes = list()

	for obj in sel:
		children = cmds.listRelatives( obj, c=True, f=True )
		for child in children:
			if cmds.nodeType( child ) == "stroke":
				print( "is a stroke" )
				strokes.append( child )
				break
			else:
				print( "no" )

	strokes_groups = list()
	strokes_geo = list()

	for st in strokes:
		cmds.select( st )
		mel.eval("doPaintEffectsToPoly( 1,0,1,0,100000);")
		geo = cmds.listRelatives( p=True )
		strokes_geo.append( geo )
		grp = cmds.listRelatives( geo, p=True )
		strokes_groups.append( grp )

	geo_group = cmds.group( n="StrokeMeshes", em=True )

	for geo in strokes_geo:
		cmds.parent( geo, geo_group )

	for grp in strokes_groups:
		cmds.delete( grp )

def OnBtnCenterYMin( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1

	for obj in sel:
		
		# get bounding box
		bbox = cmds.exactWorldBoundingBox( obj, ii=True )
		
		# get center point at Y min
		x_pos = ( bbox[0] + bbox[3] ) / 2
		y_pos = bbox[1]
		z_pos = ( bbox[2] + bbox[5] ) / 2
		new_pivot = [ x_pos, y_pos, z_pos ]
		offset = [ x_pos * -1, y_pos * -1, z_pos * -1 ]
		
		# freeze transformations
		cmds.makeIdentity( obj, apply=True, t=True, r=True, s=True, n=False, pn=True )
		# move object to world origin
		cmds.xform( obj, t=offset, ws=True )
		# move pivot
		cmds.xform( obj, piv=[ 0, 0, 0 ], ws=True )
		# freeze transformations
		cmds.makeIdentity( obj, apply=True, t=True, r=True, s=True, n=False, pn=True )

def OnBtnCenterPole( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1

	for obj in sel:
		
		poles = getPoleVerts( obj )
		
		pole_pos = list()
		
		for p in poles:
			position = cmds.xform( p, query=True, translation=True, worldSpace=True )
			pole_pos.append( position )
		
		pole_pos.sort( key=takeSecond )
		
		x_pos = pole_pos[0][0]
		y_pos = pole_pos[0][1]
		z_pos = pole_pos[0][2]
		
		# get center point at Y min
		new_pivot = [ x_pos, y_pos, z_pos ]
		offset = [ x_pos * -1, y_pos * -1, z_pos * -1 ]
		
		# freeze transformations
		cmds.makeIdentity( obj, apply=True, t=True, r=True, s=True, n=False, pn=True )
		# move object to world origin
		cmds.xform( obj, t=offset, ws=True )
		# move pivot
		cmds.xform( obj, piv=[ 0, 0, 0 ], ws=True )
		# freeze transformations
		cmds.makeIdentity( obj, apply=True, t=True, r=True, s=True, n=False, pn=True )
		
def OnBtnSetPivot( isChecked, mode ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		
		# get bounding box
		bbox = cmds.exactWorldBoundingBox( obj, ii=True )
		
		if mode == "ymax":
			# get center point at Y max
			x_pos = ( bbox[0] + bbox[3] ) / 2
			y_pos = bbox[4]
			z_pos = ( bbox[2] + bbox[5] ) / 2
			new_pivot = [ x_pos, y_pos, z_pos ]
		elif mode == "ymin":
			# get center point at Y min
			x_pos = ( bbox[0] + bbox[3] ) / 2
			y_pos = bbox[1]
			z_pos = ( bbox[2] + bbox[5] ) / 2
			new_pivot = [ x_pos, y_pos, z_pos ]
		
		# move pivot
		cmds.xform( obj, piv=new_pivot, ws=True )

def OnBtnPivotToWorldOrigin( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		# move pivot to world origin
		cmds.xform( obj, piv=[ 0, 0, 0 ], ws=True )
		# freeze transformations
		cmds.makeIdentity( obj, apply=True, t=True, r=True, s=True, n=False, pn=True )

def OnBtnRandRot( isChecked, mode ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	rot_min = 0
	rot_max = 360
	
	for obj in sel:
	
		rand_float = rand.random()
		rand_deg = ( rot_max - rot_min ) * rand_float
		current_rot = cmds.xform( obj, ro=True, query=True )
		new_rot = current_rot
		
		if( mode == "x" ):
			new_rot = [ rand_deg, current_rot[1], current_rot[2] ]
		elif( mode == "y" ):
			new_rot = [ current_rot[0], rand_deg, current_rot[2] ]
		elif( mode == "z" ):
			new_rot = [ current_rot[0], current_rot[1], rand_deg ]
		
		
		cmds.xform( obj, ro=new_rot )
	
def OnBtnDistribute( isChecked, mode, value ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1

	running_total = 0
	sign = value / abs( value )
	spacing = value
	
	all_children = set()

	for obj in sel:
		children = cmds.listRelatives( obj, c=True, ad=True, f=True )
		children = set( children )
		all_children = all_children.union( children )

	all_children = list( all_children )

	geo_nodes = list()

	for child in all_children:
		if cmds.nodeType( child ) == "mesh":
			geo = cmds.listRelatives( child, p=True, f=True )
			geo_nodes.append( geo )

	geo_nodes.sort()

	for i in range( len( geo_nodes ) ):
		
		# get bounding box
		bbox = cmds.exactWorldBoundingBox( geo_nodes[i], ii=True )
		
		if( mode == "x" ):
			width = abs( bbox[3] - bbox[0] )
			if i==0:
				pos = 0
				running_total = sign * width / 2 + spacing
			else:
				pos = running_total + ( sign * width / 2 )
				running_total = running_total + sign * width + spacing
			new_trans = [ pos, 0, 0 ]
			
		elif( mode == "y" ):
			width = abs( bbox[4] - bbox[1] )
			if i==0:
				pos = 0
				running_total = sign * width / 2 + spacing
			else:
				pos = running_total + ( sign * width / 2 )
				running_total = running_total + sign * width + spacing
			new_trans = [ 0, pos, 0 ]
			
		elif( mode == "z" ):
			width = abs( bbox[5] - bbox[2] )
			if i==0:
				pos = 0
				running_total = sign * width / 2 + spacing
			else:
				pos = running_total + ( sign * width / 2 )
				running_total = running_total + sign * width + spacing
			new_trans = [ 0, 0, pos ]
		
		# move the object to the new position
		cmds.xform( geo_nodes[i], t=new_trans, ws=True )

def OnBtnZeroTranslation( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	sel_and_children = set()

	for obj in sel:
		children = cmds.listRelatives( obj, c=True, ad=True, f=True )
		children = set( children )
		sel_and_children = sel_and_children.union( children )
		sel_and_children = sel_and_children.union( set( [obj] ) )

	sel_and_children = list( sel_and_children )

	for obj in sel_and_children:
		
		if cmds.nodeType( obj ) == "transform":
			cmds.xform( obj, t=[ 0, 0, 0 ], ws=True )

def OnBtnSortOutliner( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	int_list = list()

	for obj in sel:
		match = re.split(r"([0-9]+)", obj )
		for i in range( len( match ) ):
			j = len( match ) - i - 1
			try:
				integer = int( match[ j ] )
				int_list.append( integer )
				break
			except ValueError:
				integer = None

	obj_name_int = list()

	for i in range( len( sel ) ):
		new_entry = [ sel[i], int_list[i] ]
		obj_name_int.append( new_entry )
		
	# sort list with key
	obj_name_int.sort( key=takeSecond )

	for i in range( len( obj_name_int ) ):
		length = len( obj_name_int )
		obj = obj_name_int[ length - 1 - i ][0]
		cmds.reorder( obj, f=True )

def OnBtnAssignRampMat( isChecked ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	# create shader nodes
	lambert = cmds.shadingNode( "lambert", asShader=True, n="Gradient_mat" )
	lambert_sg = cmds.sets( name=( lambert + "SG" ), renderable=True, noSurfaceShader=True, empty=True )
	cmds.connectAttr( lambert + ".outColor", lambert_sg + ".surfaceShader" )
	ramp = cmds.shadingNode( "ramp", asTexture=True )
	place_2d = cmds.shadingNode( "place2dTexture", asUtility=True )
	cmds.connectAttr( place_2d + ".outUV", ramp + ".uv" )
	cmds.connectAttr( place_2d + ".outUvFilterSize", ramp + ".uvFilterSize" )
	cmds.connectAttr( ramp + ".outColor", lambert + ".color" )
	cmds.setAttr( ramp + ".colorEntryList[0].color", 1, 0, 0, type="double3" )
	cmds.setAttr( ramp + ".colorEntryList[1].color", 1, 1, 0, type="double3" )
	cmds.setAttr( ramp + ".colorEntryList[1].position", 1 )
	cmds.setAttr( lambert + ".diffuse", 0 )
	cmds.setAttr( lambert + ".ambientColor", 1, 1, 1, type="double3" )
	
	for obj in sel:
	
		# assign the material
		cmds.sets( obj, forceElement=lambert_sg )
		# link the uv set
		cmds.uvLink( make=True, uvSet=( obj + ".uvSet[1].uvSetName" ), texture=ramp )

def OnBtnDeleteHistory( isChecked ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
		
	for obj in sel:
	
		cmds.delete( obj, constructionHistory=True )

def onBtnScaleUvQuad( isChecked, uv_set ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		corner_verts = getVertsWithEdgeCount( obj, 2 )
		corner_edges = cmds.polyListComponentConversion( corner_verts[0], toEdge=True )
		dimension_edges = list()
		
		for e in corner_edges:
			cmds.select( e )
			cmds.polySelectConstraint( m2a=45, m3a=180, m=2, t=0x8000, pp=4 )
			edges = cmds.ls( selection=True, flatten=True )
			cmds.select( clear=True )
			dimension_edges.append( edges )
		
		edge_lengths = list()
		
		for e_list in dimension_edges:
			edge_lengths.append( getEdgeLengthSum( e_list ) )
		
		a = edge_lengths[0] / edge_lengths[1]
		b = edge_lengths[1] / edge_lengths[0]
		
		length_ratio = 1
		
		'''
		if a < b:
			length_ratio = a
		else:
			length_ratio = b
		
		print( length_ratio )
		'''
		
		length_ratio = a
		
		cmds.polyUVSet( obj, uvs=uv_set, cuv=True )
		uvs = cmds.polyListComponentConversion( obj, toUV=True )
		cmds.polyEditUV( uvs, pu=0, pv=0, su=length_ratio )
	
	cmds.select( sel )

def OnBtnApplyVertColor( isChecked, mode, channel ):
	
	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
		
		verts = cmds.polyListComponentConversion( obj, toVertex=True )
		verts = cmds.ls( verts, flatten=True )
		
		uvs = list()
		
		for v in verts:
			uv = cmds.polyListComponentConversion( v, toUV=True )
			uv = cmds.ls( uv, flatten=True )[0]
			uvs.append( uv )
		
		additive = True
		vertex_color = (0.0, 0.0, 0.0)
		values = list()
		
		# define colors
		if channel == "r":
			vertex_color = (1.0, 0.0, 0.0)
		elif channel == "g":
			vertex_color = (0.0, 1.0, 0.0)
		elif channel == "b":
			vertex_color = (0.0, 0.0, 1.0)
		
		# define modes
		if mode == "uv_v":
			for uv in uvs:
				val = cmds.polyEditUV( uv, query=True )[1]
				values.append( val )
		
		elif mode == "clear":
			additive = False
			vertex_color = (0.0, 0.0, 0.0)
			for uv in uvs:
				values.append( 0.0 )
		
		# apply vertex colors
		for i in range( len( verts ) ):
			result_color = multVectorByScalar( values[i], vertex_color )
			#print( result_color )
			cmds.polyColorPerVertex( verts[i], rgb=result_color, rel=additive, cdo=True )

def OnBtnRenameFromSel( isChecked, name_mode, selection_mode, num_mode, new_name ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1

	'''
	name_mode = 1		# 1=selection, 2=string
	selection_mode = 1	# 1=parent, 2=object
	num_mode = 1		# 1=numerically, 2=alphabetically
	'''
	
	sep = "_"
	name_base = new_name
	padding = 2
	first_index = 1
	
	if selection_mode==1:
		children_list = list()
		for grp in sel:
			name_base = grp.split("|")[-1]
			children = cmds.listRelatives( grp, ad=True, f=True, type="transform" )		
			children.sort()
			for i in range( len( children ) ):
				customRename( children[i], name_base, sep, padding, i, first_index, num_mode )
	
	if selection_mode==2:
		 
		if name_mode==2:
			sel.sort()
			for i in range( len( sel ) ):
				customRename( sel[i], name_base, sep, padding, i, first_index, num_mode )
		 
		if name_mode==1:
			name_base = sel[-1].split("|")[-1]
			sel.pop()
			sel.sort()
			for i in range( len( sel ) ):
				customRename( sel[i], name_base, sep, padding, i, first_index, num_mode )

def OnBtnSortOutliner( isChecked, recursive ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	sortOutliner( sel, recursive )

def OnBtnCustomRename( isChecked, input_str, mode ):

	# get the selected objects
	sel = cmds.ls( selection=True, long=True )
	
	# throw an error if nothing is selected
	if (not sel):
		cmds.confirmDialog( title='ERROR', message=('ERROR: Nothing selected.'), button=['OK'], defaultButton='OK' )
		return -1
	
	for obj in sel:
	
		obj_name = cmds.ls( obj, long=False )[0]
	
		if mode=="Add Suffix":
			cmds.rename( obj, obj_name + input_str )
		if mode=="Add Prefix":
			cmds.rename( obj, input_str + obj_name )
		if mode=="Remove String":
			name_split = obj_name.split( input_str )
			new_name = ""
			for s in name_split:
				new_name = new_name + s
			cmds.rename( obj, new_name )
		if mode=="Remove Last 'n' Chars":
			try:
				index = int( input_str )
			except:
				cmds.confirmDialog( title='ERROR', message=('ERROR: Please enter an integer.'), button=['OK'], defaultButton='OK' )
				return -1
			cmds.rename( obj, obj_name[:-index] )
		if mode=="Remove First 'n' Chars":
			try:
				index = int( input_str )
			except:
				cmds.confirmDialog( title='ERROR', message=('ERROR: Please enter an integer.'), button=['OK'], defaultButton='OK' )
				return -1
			cmds.rename( obj, obj_name[index:] )
		# number alphabetically
		if mode=='Numbering (A)':
			index = sel.index( obj ) + 1
			letter = chr( ord( '@' ) + index )
			new_name = input_str + letter
			cmds.rename( obj, new_name )
		if mode=='Numbering (01)' or mode=='Numbering (001)' or mode=='Numbering (0001)':
			if mode=='Numbering (01)':
				padding = 2
			if mode=='Numbering (001)':
				padding = 3
			if mode=='Numbering (0001)':
				padding = 4
			index = sel.index( obj ) + 1
			new_name = input_str + str( index ).zfill( padding )
			cmds.rename( obj, new_name )	

################################################################################
## User Interface
################################################################################

def makeColWidth( buttons, mode ):
	
	column_width = list()
	custom_val = 0
		
	first_entry = ( 1, win_first_column_width )
	column_width.append( first_entry )
	
	# buttons only
	if mode==1:
		
		if buttons==1:
			custom_val = 6
		elif buttons==2:
			custom_val = 2
		elif buttons==3:
			custom_val = 1
			
		for i in range( buttons ):
			new_entry = ( i+2, ( ( win_width - win_first_column_width ) / buttons ) + custom_val  )
			column_width.append( new_entry )
	
	# slider and buttons
	if mode==2:
		
		if buttons==1:
			custom_val = 2
		elif buttons==2:
			custom_val = 0
		elif buttons==3:
			custom_val = 0
		elif buttons==4:
			custom_val = -1
		
		second_entry = (2, ( ( win_width - win_first_column_width ) / 2 ) + 2 )
		column_width.append( second_entry )
		
		for i in range( buttons ):
			new_entry = ( i+3, ( ( ( win_width - win_first_column_width ) / 2 ) / buttons ) + custom_val )
			column_width.append( new_entry )

	# text field, option menu and button
	if mode==3:
		
		text_field = (2, ( ( win_width - win_first_column_width ) / 2 ) + 2 )
		option_menu = (3, ( ( win_width - win_first_column_width ) / 3 ) + 16 )
		button = (4, ( ( win_width - win_first_column_width ) / 6 ) + 0 )
		
		column_width.append( text_field )
		column_width.append( option_menu )
		column_width.append( button )
	
	return column_width

def makeColAttach( buttons, mode ):
	
	column_attach = list()
	index_val = 0
	
	# buttons only
	if mode==1:
		index_val = 1
	
	# slider and buttons
	if mode==2:
		index_val = 2
	
	for i in range( buttons+index_val ):
		new_entry = ( i+1, 'both', win_row_offset )
		column_attach.append( new_entry )
	
	return column_attach

def makeUI():

	col_align = (1, 'left')
	window_name = 'window_ui'

	# Delete the window ui if it already exists
	if cmds.window( window_name, exists = True ):
		cmds.deleteUI( window_name )

	# Window
	main_window = cmds.window( window_name, title="Game Asset Helper Scripts", iconName='GAHS', width=win_width, rtf=True, ret=False )
	main_layout = cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	cmds.text( label='', height=win_padding )
	
	
	# Frame Begin
	cmds.frameLayout( label='Topology', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )	
	# Delete Back Face Extruded
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Delete Back Face Extruded', command=OnBtnDeleteExtruded, annotation="Creates a new lambert with a color ramp and assigns it to the selected objects."  )
	cmds.setParent( '..' )
	# Poly Retopo
	btns_mode = [ 1, 2 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+2, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, adj=1, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.floatSliderGrp( field=True, value=10, minValue=0.0, maxValue=100.0, fieldMinValue=-1.0e+06, fieldMaxValue=1.0e+06 )
	cmds.button( label='Poly Retopo', command=OnBtnPolyRetopo, annotation="Retopologizes the selected objects."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )


	# Frame Begin
	cmds.frameLayout( label='Normals', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Set Normals
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Set Normals to Face and Soften', command=OnBtnFixNormals, annotation="Sets the normals to their face normals and automatically soften/harden edges based on their face angle."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )


	# Frame Begin
	cmds.frameLayout( label='PaintFX', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='PaintFX -> Polygons', command=onBtnPaintFXToPoly, annotation="Converts PaintFX strokes to polygons."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Merge Vertices and Close Holes', command=onBtnPaintFXMergeAndCloseHoles, annotation="Merges vertices and closes holes on PaintFX strokes."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )

	
	# Frame Begin
	cmds.frameLayout( label='UV', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Buttons
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Unitize UV' )
	cmds.button( label='Quad Mesh ( map1 )', command='OnBtnUnitizeUVPlanar( "True", "map1" )', annotation="Unitizes the UVs of the selected planar quad meshes and stores them in the map1 set."  )
	cmds.button( label='Polar Mesh ( map1 )', command='OnBtnUnitizeUVPolar( "True", "map1" )', annotation="Unitizes the UVs of the selected tube mesh with polar end caps and stores them in the map1 set."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Scale UVs Proportionately Quad Mesh ( map1 )', command='onBtnScaleUvQuad( "True", "map1" )', annotation="Scales the UVs of the selected planar quad meshes in the U direction based on edge length ratio in the map1 set."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Delete UVs', command=OnBtnDeleteUV, annotation="Deletes all UVs and UV sets."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )
	
	
	# Frame Begin
	cmds.frameLayout( label='Multi UV Set Workflow', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Initialize UVs', command=OnBtnInitializeUV, annotation="Deletes all existing UV sets and creates new ones."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Unfold and Layout ( StackedUV )', command=OnBtnUnfoldLayout, annotation="Unfold and layout the selected objects in the StackedUV set."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Orient Shell to Edges', command=OnBtnOrientShell, annotation="Orient the UV shell to the nearest 90 degrees."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Unitize UV' )
	cmds.button( label='Quad Mesh ( UnitizeUV )', command='OnBtnUnitizeUVPlanar( "True", "UnitizeUV" )', annotation="Unitizes the UVs of the selected planar quad meshes and stores them in the UnitizeUV set."  )
	cmds.button( label='Polar Mesh ( UnitizeUV )', command='OnBtnUnitizeUVPolar( "True", "UnitizeUV" )', annotation="Unitizes the UVs of the selected tube mesh with polar end caps and stores them in the UnitizeUV set."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Transfer UVs' )
	cmds.button( label='UnitizeUV -> UnitizeUV', command=OnBtnTransferUVUnitize, annotation="First select the destination objects, last select the source object. The script will transfer the UVs from source to destination in the UnitizeUV set."  )
	cmds.button( label='StackedUV -> StackedUV', command=OnBtnTransferUVStacked, annotation="First select the destination objects, last select the source object. The script will transfer the UVs from source to destination in the StackedUV set."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 3, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Copy UV Set' )
	cmds.button( label='Current -> map1', command=OnBtnCopyUVSetToUVmap1, annotation="Copy the UV set from current to the map1 set."  )
	cmds.button( label='Current -> UnitizeUV', command=OnBtnCopyUVSetToUVUnitize, annotation="Copy the UV set from current to the UnitizeUV set."  )
	cmds.button( label='Current -> StackedUV', command=OnBtnCopyUVSetToStacked, annotation="Copy the UV set from current to the StackedUV set."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )
	
	
	# Frame Begin
	cmds.frameLayout( label='Transforms', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Silder
	btns_mode = [ 3, 2 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+2, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, adj=1, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Distribute' )
	cmds.floatSliderGrp( 'dist_val', field=True, value=50, minValue=0.0, maxValue=100.0, fieldMinValue=-1.0e+06, fieldMaxValue=1.0e+06 )
	cmds.button( label='X', command='OnBtnDistribute( "True", "x", cmds.floatSliderGrp( "dist_val", q=True, v=True) )', annotation="Distribute the selected objects along the X axis."  )
	cmds.button( label='Y', command='OnBtnDistribute( "True", "y", cmds.floatSliderGrp( "dist_val", q=True, v=True) )', annotation="Distribute the selected objects along the Y axis."  )
	cmds.button( label='Z', command='OnBtnDistribute( "True", "z", cmds.floatSliderGrp( "dist_val", q=True, v=True) )', annotation="Distribute the selected objects along the Z axis."  )
	cmds.setParent( '..' )
	# Button
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+2, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, adj=1, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Randomize Rotation' )
	cmds.button( label='Y', command='OnBtnRandRot( "True", "y" )', annotation="Randomize the rotation of the selected objects."  )
	cmds.setParent( '..' )
	# Button
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+2, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, adj=1, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Zero' )
	cmds.button( label='Translation', command=OnBtnZeroTranslation, annotation="Sets translation to zero on the selected transforms."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Set Pivot' )
	cmds.button( label='Y Min', command='OnBtnSetPivot( "True", "ymin" )', annotation="Sets the pivot point of the selected objects to the minimum y position of the object."  )
	cmds.button( label='Y Max', command='OnBtnSetPivot( "True", "ymax" )', annotation="Sets the pivot point of the selected objects to the maximum y position of the object."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Set Pivot & Freeze' )
	cmds.button( label='World Origin', command=OnBtnPivotToWorldOrigin, annotation="Sets the pivot point on the selected objects to the world origin and freezes transformations."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Set Pivot, Move & Freeze' )
	cmds.button( label='Y Min', command=OnBtnCenterYMin, annotation="Moves the object to the world origin centered at the minimum y position."  )
	cmds.button( label='Pole Y Min', command=OnBtnCenterPole, annotation="Moves the object to the world origin centered at the minimum y pole."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )
	
	
	# Frame Begin
	cmds.frameLayout( label='Rename', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Text Field, Option Menu and Button
	btns_mode = [ 3, 3 ]
	cmds.rowLayout( numberOfColumns=4, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Rename Selected' )
	name = cmds.textField( 'rename_field' )
	cmds.optionMenu( 'rename_options' )
	cmds.menuItem( label='Add Prefix' )
	cmds.menuItem( label='Add Suffix' )
	cmds.menuItem( label='Remove String' )
	cmds.menuItem( label="Remove Last 'n' Chars" )
	cmds.menuItem( label="Remove First 'n' Chars" )
	cmds.menuItem( label='Numbering (01)' )
	cmds.menuItem( label='Numbering (001)' )
	cmds.menuItem( label='Numbering (0001)' )
	cmds.menuItem( label='Numbering (A)' )
	cmds.button( label='Rename', command='OnBtnCustomRename( True, cmds.textField( "rename_field", query=True, text=True ), cmds.optionMenu( "rename_options", query=True, value=True ) )', annotation="Rename the selected objects using the selected mode."  )
	cmds.setParent( '..' )
	# Button
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+2, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, adj=1, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'From Group' )
	cmds.button( label='ABC', command='OnBtnRenameFromSel( True, 1, 1, 2, "" )', annotation="Rename the selected objects alphabetically based on the group name."  )
	cmds.button( label='123', command='OnBtnRenameFromSel( True, 1, 1, 1, "" )', annotation="Rename the selected objects numerically with a padding of '2' based on the group name."  )
	cmds.setParent( '..' )
	# Button
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+2, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, adj=1, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'From Last Selected' )
	cmds.button( label='ABC', command='OnBtnRenameFromSel( True, 1, 2, 2, "" )', annotation="Rename the selected objects alphabetically based on the last selected object."  )
	cmds.button( label='123', command='OnBtnRenameFromSel( True, 1, 2, 1, "" )', annotation="Rename the selected objects numerically with a padding of '2' based on the last selected object."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )
	
	
	# Frame Begin
	cmds.frameLayout( label='Outliner', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Buttons
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Sort Outliner' )
	cmds.button( label='Selection', command='OnBtnSortOutliner( True, False )', annotation="Sorts the selected objects in the outliner by name."  )
	cmds.button( label='Selection and Children', command='OnBtnSortOutliner( True, True )', annotation="Sorts the selected objects, and all children of the selected objects, in the outliner by name."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )
	
	
	# Frame Begin
	cmds.frameLayout( label='Combine, Separate & History', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Separate Meshes and Delete History', command=OnBtnSeparate, annotation="Separates the polygon shells in the selected objects into distinct objects."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Combine Groups and Delete History', command=OnBtnCombine, annotation="Combines the objects within the selected groups into one object per group."  )
	cmds.setParent( '..' )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Delete History', command=OnBtnDeleteHistory, annotation="Deletes construction history on selected objects."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )

	
	# Frame Begin
	cmds.frameLayout( label='Vertex Color', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Buttons
	btns_mode = [ 2, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( 'Apply Color' )
	cmds.button( label='Set to Black', command='OnBtnApplyVertColor( "True", "clear", "r" )', annotation="Sets the vertex colors to black."  )
	cmds.button( label='V Coord -> R', command='OnBtnApplyVertColor( "True", "uv_v", "r" )', annotation="Sets vertex colors based on V coordinates. Uses additive color blending in the R channel."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )
	
	# Frame Begin
	cmds.frameLayout( label='Materials', collapsable=True, collapse=win_frame_is_collapsed, bv=win_border_vis, mh=win_margin, mw=win_margin )
	cmds.text( '', height=( win_padding/2 ) )
	cmds.columnLayout( adjustableColumn=True, columnAttach=('both', win_padding), columnOffset=('both', 0), rowSpacing=0 )
	# Buttons
	btns_mode = [ 1, 1 ]
	cmds.rowLayout( numberOfColumns=btns_mode[0]+1, adj=1, columnWidth=makeColWidth( btns_mode[0], btns_mode[1] ), columnAlign=col_align, columnAttach=makeColAttach( btns_mode[0], btns_mode[1] ) )
	cmds.text( '' )
	cmds.button( label='Create and Assign Ramp Material', command=OnBtnAssignRampMat, annotation="Creates and assigns a lambert material with color ramp to the selected objects and uv links the ramp to uvSet[1]."  )
	cmds.setParent( '..' )
	# Frame End
	cmds.text( label='', height=win_padding )
	cmds.setParent( main_layout )
	
	# Close Button
	cmds.separator( height=( win_padding * 4 ), style='in' )
	cmds.button( label='Close', command=('cmds.deleteUI(\"' + main_window + '\", window=True)'), h=50 )
	cmds.text( label='', height=win_padding )

	# Show Window
	cmds.showWindow( main_window )

# UI global settings
win_width = 540
win_padding = 5
win_row_offset = 0
win_row_height = 0
win_margin = 0
win_frame_is_collapsed = True
win_border_vis = False
win_first_column_width = 140

# Make the window UI
makeUI()
