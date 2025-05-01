# Modellen in LeggerWidget

Op deze pagina worden de modellen beschreven die worden gebruikt in de widget voor het aanwijzen van de legger, dus
in de widget `LeggerWidget`.

Er worden 3 soorten modellen onderscheiden:

- Tree models - pyQt modellen voor tree structuren (gebruikt in mappen), dit zijn:
    - area_model (AreaTreeModel) -
    - leggermodel (LeggerTreeModel) - pyQt model van de hydrovakken vanaf het startpunt van het peilgebied
- List models - pyQt modellen voor lijst structuren (gebruikt in tabellen):
    - measured_model (ProfileModel): lijst van gemeten profielen in hydrovak
    - variant_model (VariantModel): lijst van leggervarianten in hydrovak
- QGISlayers - QGIS lagen (gebruikt in de kaart):
    - line_layer
    - vl_tree_layer
    - vl_endpoint_layer
    - vl_track_layer
    - vl_hover_layer
    - vl_selected_layer
    - vl_startpoint_hover_layer

De data wordt ingelezen vanuit het maken van het Netwerk (Network).

functie hydrovak_class_tree_with_data
--> functie graph

- query Line: vanuit graph_lines (gemaakt bij redirecten), hydroobject, kenmerken, geselecteerd, varianten:
  gl.hydro_id, gl.startnode_id, gl.endnode_id, hocategory(categorieoppwaterlichaam), length (lengte ho.geometry),
  ho.debiet_3di, ho.debiet,
  ho.target_level(streefpeil), kn.soort_vak, ho.duiker_count, v.verhang, ho.has_startnode(eindpunt_geselecteerd)

  line_feature from full_line_layer

## hydro_tree_item

| field                 | in                           | used                              | source                                       | description           |
|-----------------------|------------------------------|-----------------------------------|----------------------------------------------|-----------------------|
| feat_id (objectid)    | netw_dict                    | sideview                          | feature                                      |                       |
| code ??               | model, h_obj_ken, netw_dict  | table_col                         | h_obj_ken                                    |                       |
| hydro_id (=id )       | model, netw_dict             | table_col, sideview, cross        | h_obj_ken                                    |                       |
| arc_nr                | netw_dict                    |                                   | tree                                         |                       |
| sp (= user input)     | model                        | table_col, sel_path, cross, sidev | interaction                                  | startpoint of traject |
| ep (= user input)     | model                        | table_col, sel_path, cross, sidev | interaction                                  | endpoint of traject   |
| selected (=use input) | model                        | table_col, cross                  | interaction                                  |                       |
| hover (=use input)    | model                        | table_col, cross, sideview        | interaction                                  |                       |
| distance              | model, netw_dict             | sideview,                         | tree calc                                    |                       |
| depth                 | model, h_obj_ken, netw_dict  | table_col, sideview               | h_obj_ken                                    |                       |
| width                 | model, h_obj_ken, netw_dict  | table_col                         | h_obj_ken                                    |                       |
| variant_min_depth     | model, h_obj_ken, netw_dict  | table_col, sideview               | h_obj_ken                                    |                       |
| variant_max_depth     | model, h_obj_ken, netw_dict  | table_col, sideview               | h_obj_ken                                    |                       |
| target_level          | hmodel, h_obj_ken, netw_dict | sideview, cross                   | h_obj_ken                                    |                       |
| category              | hmodel, h_obj_ken, netw_dict | table_col                         | h_obj_ken                                    |                       |
| flow                  | model, h_obj_ken, netw_dict  | table_col                         | h_obj_ken                                    |                       |
| selected_depth        | model, h_obj_ken, netw_dict  | table_col, sideview, cross        | h_obj_ken                                    |                       |
| selected_depth_tmp    | model                        | table_col, sideview               | interaction                                  |                       |
| selected_width        | model, h_obj_ken, netw_dict  | table_col                         | h_obj_ken, set in function initial_loop_tree |                       |
| over_depth            | model                        | table_col                         | calc, set in function initial_loop_tree      |                       |
| over_width            | model                        | table_col                         | calc, set in function initial_loop_tree      |                       |
| score                 | model, h_obj_ken, netw_dict  | table_col                         | h_obj_ken, set in function initial_loop_tree |                       |
| end_arc_type          | netw_dict                    | table icon                        | tree calc                                    |                       |

model:

- parent()/ younger()/ older() / child()
- upstream/ downstream

get op:
feature --> worden items uitgehaald, als niet aanwezig uit data_dict
startpoint
endpoint
icon

    hydrovak class
        - endpoint
        - feature
        - from dict
        - special for icon

- parent (always None)
- feature/ line_feature (virtual_tree_layer)

waarde overnemen voorgaande...

- new_depth
- new_variant_min_depth
- new_variant_max_depth
- in_vertex_id
- out_vertex_id
- start_distance
- end_distance


- feature
- startpoint_feature
- endpoint_feature
  --> endpoint op x afstand van eind?

split hydrovak heeft:

- hydro_id
- line_feature
- distance

endpoints:

- vertex_id
- arc_nr
- type: end/ target/ ...
- feat_id
- start_tree_item

start_tree_item:

- target_level
- distance
- category
- start_vertex_id
- point
- arc_nr
- line_feature
- parent (always None)
- children

virtual_tree_layer
line:

- weight (length)
- line_id (feat_id)
- hydro_id
- min_depth (depth)
- var_min_depth (variant_min_depth)
- var_max_depth (variant_max_depth)
- target_level
- category

end_point_layer
point:

- id (feat_id hydro)
- hydro_id (feat_id hydro)
- typ (end, target)
- vertex_id
- arc_nr toevoegen ??

ideeen:

- LeggerMapVisualisation uitbreiden. Deel code vanuit netwerk verwijderen. Kan anders weg.


