# -*- coding: utf-8 -*-
import os
import sys
import traceback
import arcpy

FORMAT_LIST = ["SHP", "DWG", "MDB", "GDB", "KML"]
DWG_MODE_LIST = ["ArcGIS", "ezdxf"]

def _is_arcgis_pro():
    try:
        info = arcpy.GetInstallInfo()
        if info.get("ProductName", "") == "ArcGISPro":
            return True
    except:
        pass
    return False

def _call_conversion(tool_name, *args, **kwargs):
    if _is_arcgis_pro():
        func = getattr(arcpy.conversion, tool_name, None)
    else:
        func = getattr(arcpy, tool_name + "_conversion", None)
    if func is None:
        raise RuntimeError("Tool not found: " + tool_name)
    return func(*args, **kwargs)

def _scan_files(folder, ext_list):
    results = []
    folder = folder.strip()
    if not os.path.isdir(folder):
        return results
    for root, dirs, files in os.walk(folder):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ext_list:
                results.append(os.path.join(root, f))
    return results

def _get_input_files(folder, src_format):
    fmt = src_format.upper()
    if fmt == "SHP":
        return _scan_files(folder, [".shp"])
    elif fmt == "DWG":
        return _scan_files(folder, [".dwg", ".dxf"])
    elif fmt == "MDB":
        # If user selected an .mdb file directly, use it
        if folder.lower().endswith(".mdb") and os.path.isfile(folder):
            return [folder]
        return _scan_files(folder, [".mdb"])
    elif fmt == "GDB":
        # If user selected a .gdb folder directly, use it
        if folder.lower().endswith(".gdb") and os.path.isdir(folder):
            return [folder]
        # Otherwise scan for .gdb folders inside
        results = []
        for item in os.listdir(folder):
            full = os.path.join(folder, item)
            if os.path.isdir(full) and item.lower().endswith(".gdb"):
                results.append(full)
        return results
    elif fmt == "KML":
        return _scan_files(folder, [".kml", ".kmz"])
    return []

def _get_fc_list(workspace):
    arcpy.env.workspace = workspace
    fcs = arcpy.ListFeatureClasses()
    if fcs is None:
        return []
    result = []
    for fc in fcs:
        result.append(os.path.join(workspace, fc))
    return result

def _base_name(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]

def _make_output_gdb(folder, name="Converted.gdb"):
    gdb_path = os.path.join(folder, name)
    if not arcpy.Exists(gdb_path):
        arcpy.CreateFileGDB_management(folder, name)
    return gdb_path

def _make_output_mdb(folder, name="Converted.mdb"):
    mdb_path = os.path.join(folder, name)
    if not arcpy.Exists(mdb_path):
        arcpy.CreatePersonalGDB_management(folder, name)
    return mdb_path

def _try_import_ezdxf():
    try:
        import ezdxf
        return ezdxf, None
    except ImportError:
        return None, "ezdxf not installed. Please run: {} -m pip install ezdxf".format(sys.executable)

# ------ SHP -> xxx ------

def shp_to_dwg(shp_path, out_folder, mode="ArcGIS"):
    name = _base_name(shp_path)
    if mode == "ezdxf":
        ezdxf_mod, err = _try_import_ezdxf()
        if err:
            raise RuntimeError(err)
        _shp_to_dwg_ezdxf(shp_path, out_folder, name)
        return os.path.join(out_folder, name + ".dxf")
    else:
        # Try ArcGIS native conversion
        try:
            out_dwg = os.path.join(out_folder, name + ".dwg")
            _call_conversion("FeaturesToCAD", shp_path, out_dwg)
            return out_dwg
        except Exception as e:
            # ArcGIS license insufficient or tool unavailable, fallback to ezdxf
            arcpy.AddWarning("FeaturesToCAD unavailable: " + str(e))
            arcpy.AddWarning("Switching to ezdxf mode...")
            ezdxf_mod, err = _try_import_ezdxf()
            if err:
                raise RuntimeError("FeaturesToCAD unavailable and ezdxf not installed. \n" + err)
            _shp_to_dwg_ezdxf(shp_path, out_folder, name)
            return os.path.join(out_folder, name + ".dxf")

def _shp_to_dwg_ezdxf(shp_path, out_folder, name):
    ezdxf_mod, _ = _try_import_ezdxf()
    doc = ezdxf_mod.new("R2010")
    msp = doc.modelspace()
    fields = []
    for f in arcpy.ListFields(shp_path):
        if f.type not in ("OID", "Geometry"):
            fields.append(f.name)
    cursor = arcpy.da.SearchCursor(shp_path, ["SHAPE@"] + fields)
    for row in cursor:
        geom = row[0]
        if geom is None:
            continue
        if geom.type == "point":
            msp.add_point((geom.firstPoint.X, geom.firstPoint.Y, 0))
        elif geom.type == "polyline":
            pts = []
            part = geom.getPart(0)
            for p in part:
                pts.append((p.X, p.Y, 0))
            if len(pts) >= 2:
                msp.add_lwpolyline([(p[0], p[1]) for p in pts])
        elif geom.type == "polygon":
            pts = []
            part = geom.getPart(0)
            for p in part:
                if p:
                    pts.append((p.X, p.Y, 0))
            if len(pts) >= 3:
                poly = msp.add_lwpolyline([(p[0], p[1]) for p in pts])
                poly.set_flag_state(poly.CLOSED, state=True)
    del cursor
    out_dxf = os.path.join(out_folder, name + ".dxf")
    doc.saveas(out_dxf)

def shp_to_mdb(shp_path, mdb_path):
    name = _base_name(shp_path)
    arcpy.FeatureClassToFeatureClass_conversion(shp_path, mdb_path, name)
    return os.path.join(mdb_path, name)

def shp_to_gdb(shp_path, gdb_path):
    name = _base_name(shp_path)
    arcpy.FeatureClassToFeatureClass_conversion(shp_path, gdb_path, name)
    return os.path.join(gdb_path, name)

def shp_to_kml(shp_path, out_folder):
    name = _base_name(shp_path)
    out_kmz = os.path.join(out_folder, name + ".kmz")
    tmp_layer = "tmp_kml_layer"
    arcpy.MakeFeatureLayer_management(shp_path, tmp_layer)
    _call_conversion("LayerToKML", tmp_layer, out_kmz)
    arcpy.Delete_management(tmp_layer)
    return out_kmz

# ------ DWG -> xxx ------

def dwg_to_shp(dwg_path, out_folder, mode="ArcGIS"):
    name = _base_name(dwg_path)
    if mode == "ezdxf":
        ezdxf_mod, err = _try_import_ezdxf()
        if err:
            raise RuntimeError(err)
        return _dwg_to_shp_ezdxf(dwg_path, out_folder, name)
    else:
        return _dwg_to_shp_arcpy(dwg_path, out_folder, name)

def _dwg_to_shp_arcpy(dwg_path, out_folder, name):
    tmp_gdb = _make_output_gdb(out_folder, "_tmp_cad.gdb")
    _call_conversion("CADToGeodatabase", dwg_path, tmp_gdb, name + "_CAD", "1000", "POLYGON")
    arcpy.env.workspace = tmp_gdb
    fcs = arcpy.ListFeatureClasses(name + "_CAD*")
    results = []
    if fcs:
        for fc in fcs:
            fc_full = os.path.join(tmp_gdb, fc)
            arcpy.FeatureClassToShapefile_conversion([fc_full], out_folder)
            results.append(os.path.join(out_folder, fc + ".shp"))
    arcpy.Delete_management(tmp_gdb)
    return results

def _dwg_to_shp_ezdxf(dwg_path, out_folder, name):
    ezdxf_mod, _ = _try_import_ezdxf()
    try:
        import shapefile
    except ImportError:
        raise RuntimeError("pyshp not installed. Run: pip install pyshp")
    doc = ezdxf_mod.readfile(dwg_path)
    msp = doc.modelspace()
    points = []
    lines = []
    polys = []
    for entity in msp:
        dtype = entity.dxftype()
        if dtype == "POINT":
            points.append((entity.dxf.location.x, entity.dxf.location.y))
        elif dtype == "LINE":
            lines.append([
                (entity.dxf.start.x, entity.dxf.start.y),
                (entity.dxf.end.x, entity.dxf.end.y)
            ])
        elif dtype == "LWPOLYLINE":
            pts = [p for p in entity.get_points(format="xy")]
            if entity.closed:
                polys.append(pts)
            else:
                lines.append(pts)
    results = []
    if points:
        w = shapefile.Writer(os.path.join(out_folder, name + "_points"))
        w.field("ID", "N")
        for i in range(len(points)):
            w.point(points[i][0], points[i][1])
            w.record(i)
        w.close()
        results.append(os.path.join(out_folder, name + "_points.shp"))
    if lines:
        w = shapefile.Writer(os.path.join(out_folder, name + "_lines"))
        w.field("ID", "N")
        for i in range(len(lines)):
            w.line([lines[i]])
            w.record(i)
        w.close()
        results.append(os.path.join(out_folder, name + "_lines.shp"))
    if polys:
        w = shapefile.Writer(os.path.join(out_folder, name + "_polys"))
        w.field("ID", "N")
        for i in range(len(polys)):
            w.poly([polys[i]])
            w.record(i)
        w.close()
        results.append(os.path.join(out_folder, name + "_polys.shp"))
    return results

def dwg_to_mdb(dwg_path, out_folder, mdb_path, mode="ArcGIS"):
    tmp_gdb = _make_output_gdb(out_folder, "_tmp_cad.gdb")
    name = _base_name(dwg_path)
    _call_conversion("CADToGeodatabase", dwg_path, tmp_gdb, name + "_CAD", "1000", "POLYGON")
    arcpy.env.workspace = tmp_gdb
    fcs = arcpy.ListFeatureClasses(name + "_CAD*")
    results = []
    if fcs:
        for fc in fcs:
            fc_full = os.path.join(tmp_gdb, fc)
            arcpy.FeatureClassToFeatureClass_conversion(fc_full, mdb_path, fc)
            results.append(os.path.join(mdb_path, fc))
    arcpy.Delete_management(tmp_gdb)
    return results

def dwg_to_gdb(dwg_path, gdb_path, mode="ArcGIS"):
    name = _base_name(dwg_path)
    _call_conversion("CADToGeodatabase", dwg_path, gdb_path, name + "_CAD", "1000", "POLYGON")
    arcpy.env.workspace = gdb_path
    fcs = arcpy.ListFeatureClasses(name + "_CAD*")
    if fcs is None:
        return []
    result = []
    for fc in fcs:
        result.append(os.path.join(gdb_path, fc))
    return result

def dwg_to_kml(dwg_path, out_folder, mode="ArcGIS"):
    name = _base_name(dwg_path)
    tmp_gdb = _make_output_gdb(out_folder, "_tmp_cad.gdb")
    _call_conversion("CADToGeodatabase", dwg_path, tmp_gdb, name + "_CAD", "1000", "POLYGON")
    arcpy.env.workspace = tmp_gdb
    fcs = arcpy.ListFeatureClasses(name + "_CAD*")
    results = []
    if fcs:
        for fc in fcs:
            fc_full = os.path.join(tmp_gdb, fc)
            out_kmz = os.path.join(out_folder, fc + ".kmz")
            arcpy.MakeFeatureLayer_management(fc_full, "tmp_kml")
            _call_conversion("LayerToKML", "tmp_kml", out_kmz)
            arcpy.Delete_management("tmp_kml")
            results.append(out_kmz)
    arcpy.Delete_management(tmp_gdb)
    return results

# ------ MDB -> xxx ------

def mdb_to_shp(mdb_path, out_folder):
    fcs = _get_fc_list(mdb_path)
    results = []
    for fc in fcs:
        name = _base_name(fc)
        arcpy.FeatureClassToShapefile_conversion([fc], out_folder)
        results.append(os.path.join(out_folder, name + ".shp"))
    return results

def mdb_to_dwg(mdb_path, out_folder, mode="ArcGIS"):
    fcs = _get_fc_list(mdb_path)
    results = []
    if mode == "ezdxf":
        for fc in fcs:
            name = _base_name(fc)
            _shp_to_dwg_ezdxf(fc, out_folder, name)
            results.append(os.path.join(out_folder, name + ".dxf"))
    else:
        for fc in fcs:
            name = _base_name(fc)
            try:
                out_dwg = os.path.join(out_folder, name + ".dwg")
                _call_conversion("FeaturesToCAD", fc, out_dwg)
                results.append(out_dwg)
            except (RuntimeError, AttributeError):
                arcpy.AddWarning("FeaturesToCAD unavailable, switching to ezdxf mode")
                ezdxf_mod, err = _try_import_ezdxf()
                if err:
                    raise RuntimeError("FeaturesToCAD unavailable and ezdxf not installed")
                _shp_to_dwg_ezdxf(fc, out_folder, name)
                results.append(os.path.join(out_folder, name + ".dxf"))
    return results

def mdb_to_gdb(mdb_path, gdb_path):
    fcs = _get_fc_list(mdb_path)
    results = []
    for fc in fcs:
        name = _base_name(fc)
        arcpy.FeatureClassToFeatureClass_conversion(fc, gdb_path, name)
        results.append(os.path.join(gdb_path, name))
    return results

def mdb_to_kml(mdb_path, out_folder):
    fcs = _get_fc_list(mdb_path)
    results = []
    for fc in fcs:
        name = _base_name(fc)
        out_kmz = os.path.join(out_folder, name + ".kmz")
        arcpy.MakeFeatureLayer_management(fc, "tmp_kml")
        _call_conversion("LayerToKML", "tmp_kml", out_kmz)
        arcpy.Delete_management("tmp_kml")
        results.append(out_kmz)
    return results

# ------ GDB -> xxx ------

def gdb_to_shp(gdb_path, out_folder):
    fcs = _get_fc_list(gdb_path)
    results = []
    for fc in fcs:
        arcpy.FeatureClassToShapefile_conversion([fc], out_folder)
        results.append(os.path.join(out_folder, _base_name(fc) + ".shp"))
    return results

def gdb_to_dwg(gdb_path, out_folder, mode="ArcGIS"):
    fcs = _get_fc_list(gdb_path)
    results = []
    if mode == "ezdxf":
        for fc in fcs:
            name = _base_name(fc)
            _shp_to_dwg_ezdxf(fc, out_folder, name)
            results.append(os.path.join(out_folder, name + ".dxf"))
    else:
        for fc in fcs:
            name = _base_name(fc)
            try:
                out_dwg = os.path.join(out_folder, name + ".dwg")
                _call_conversion("FeaturesToCAD", fc, out_dwg)
                results.append(out_dwg)
            except (RuntimeError, AttributeError):
                arcpy.AddWarning("FeaturesToCAD unavailable, switching to ezdxf mode")
                ezdxf_mod, err = _try_import_ezdxf()
                if err:
                    raise RuntimeError("FeaturesToCAD unavailable and ezdxf not installed")
                _shp_to_dwg_ezdxf(fc, out_folder, name)
                results.append(os.path.join(out_folder, name + ".dxf"))
    return results

def gdb_to_mdb(gdb_path, mdb_path):
    fcs = _get_fc_list(gdb_path)
    results = []
    for fc in fcs:
        name = _base_name(fc)
        arcpy.FeatureClassToFeatureClass_conversion(fc, mdb_path, name)
        results.append(os.path.join(mdb_path, name))
    return results

def gdb_to_kml(gdb_path, out_folder):
    fcs = _get_fc_list(gdb_path)
    results = []
    for fc in fcs:
        name = _base_name(fc)
        out_kmz = os.path.join(out_folder, name + ".kmz")
        arcpy.MakeFeatureLayer_management(fc, "tmp_kml")
        _call_conversion("LayerToKML", "tmp_kml", out_kmz)
        arcpy.Delete_management("tmp_kml")
        results.append(out_kmz)
    return results

# ------ KML -> xxx ------

def kml_to_shp(kml_path, out_folder):
    name = _base_name(kml_path)
    tmp_gdb = _make_output_gdb(out_folder, "_tmp_kml.gdb")
    _call_conversion("KMLToLayer", kml_path, tmp_gdb, name)
    arcpy.env.workspace = tmp_gdb
    fcs = arcpy.ListFeatureClasses(name + "*")
    results = []
    if fcs:
        for fc in fcs:
            arcpy.FeatureClassToShapefile_conversion([os.path.join(tmp_gdb, fc)], out_folder)
            results.append(os.path.join(out_folder, fc + ".shp"))
    arcpy.Delete_management(tmp_gdb)
    return results

def kml_to_dwg(kml_path, out_folder, mode="ArcGIS"):
    shps = kml_to_shp(kml_path, out_folder)
    results = []
    for shp in shps:
        r = shp_to_dwg(shp, out_folder, mode)
        results.append(r)
    return results

def kml_to_mdb(kml_path, out_folder, mdb_path):
    name = _base_name(kml_path)
    tmp_gdb = _make_output_gdb(out_folder, "_tmp_kml.gdb")
    _call_conversion("KMLToLayer", kml_path, tmp_gdb, name)
    arcpy.env.workspace = tmp_gdb
    fcs = arcpy.ListFeatureClasses(name + "*")
    results = []
    if fcs:
        for fc in fcs:
            arcpy.FeatureClassToFeatureClass_conversion(os.path.join(tmp_gdb, fc), mdb_path, fc)
            results.append(os.path.join(mdb_path, fc))
    arcpy.Delete_management(tmp_gdb)
    return results

def kml_to_gdb(kml_path, gdb_path):
    name = _base_name(kml_path)
    out_folder = os.path.dirname(gdb_path)
    tmp_gdb = _make_output_gdb(out_folder, "_tmp_kml.gdb")
    _call_conversion("KMLToLayer", kml_path, tmp_gdb, name)
    arcpy.env.workspace = tmp_gdb
    fcs = arcpy.ListFeatureClasses(name + "*")
    results = []
    if fcs:
        for fc in fcs:
            arcpy.FeatureClassToFeatureClass_conversion(os.path.join(tmp_gdb, fc), gdb_path, fc)
            results.append(os.path.join(gdb_path, fc))
    arcpy.Delete_management(tmp_gdb)
    return results

# ------ Scheduler ------

def convert_one(src_format, tgt_format, src_path, out_folder, extra_params=None):
    if extra_params is None:
        extra = {}
    else:
        extra = extra_params
    mode = extra.get("mode", "ArcGIS")
    sf = src_format.upper()
    tf = tgt_format.upper()

    if sf == "SHP":
        if tf == "DWG":
            return shp_to_dwg(src_path, out_folder, mode)
        elif tf == "MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return shp_to_mdb(src_path, mdb)
        elif tf == "GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return shp_to_gdb(src_path, gdb)
        elif tf == "KML":
            return shp_to_kml(src_path, out_folder)

    elif sf == "DWG":
        if tf == "SHP":
            return dwg_to_shp(src_path, out_folder, mode)
        elif tf == "MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return dwg_to_mdb(src_path, out_folder, mdb, mode)
        elif tf == "GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return dwg_to_gdb(src_path, gdb, mode)
        elif tf == "KML":
            return dwg_to_kml(src_path, out_folder, mode)

    elif sf == "MDB":
        if tf == "SHP":
            return mdb_to_shp(src_path, out_folder)
        elif tf == "DWG":
            return mdb_to_dwg(src_path, out_folder, mode)
        elif tf == "GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return mdb_to_gdb(src_path, gdb)
        elif tf == "KML":
            return mdb_to_kml(src_path, out_folder)

    elif sf == "GDB":
        if tf == "SHP":
            return gdb_to_shp(src_path, out_folder)
        elif tf == "DWG":
            return gdb_to_dwg(src_path, out_folder, mode)
        elif tf == "MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return gdb_to_mdb(src_path, mdb)
        elif tf == "KML":
            return gdb_to_kml(src_path, out_folder)

    elif sf == "KML":
        if tf == "SHP":
            return kml_to_shp(src_path, out_folder)
        elif tf == "DWG":
            return kml_to_dwg(src_path, out_folder, mode)
        elif tf == "MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return kml_to_mdb(src_path, out_folder, mdb)
        elif tf == "GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return kml_to_gdb(src_path, gdb)

    raise ValueError("Unsupported: " + sf + " -> " + tf)

def _add_common_params(tool, include_mode=False):
    tool.parameters = []

    p0 = arcpy.Parameter(
        displayName="Input Folder",
        name="input_folder",
        datatype="DEWorkspace",
        parameterType="Required",
        direction="Input"
    )
    tool.parameters.append(p0)

    p1 = arcpy.Parameter(
        displayName="Source Format",
        name="src_format",
        datatype="GPString",
        parameterType="Required",
        direction="Input"
    )
    p1.filter.type = "ValueList"
    p1.filter.list = FORMAT_LIST
    tool.parameters.append(p1)

    p2 = arcpy.Parameter(
        displayName="Output Folder",
        name="output_folder",
        datatype="DEWorkspace",
        parameterType="Required",
        direction="Input"
    )
    tool.parameters.append(p2)

    p3 = arcpy.Parameter(
        displayName="Output Coordinate System (Optional)",
        name="coord_sys",
        datatype="GPCoordinateSystem",
        parameterType="Optional",
        direction="Input"
    )
    p3.value = ""
    tool.parameters.append(p3)

    if include_mode:
        p4 = arcpy.Parameter(
            displayName="DWG Mode",
            name="dwg_mode",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        p4.filter.type = "ValueList"
        p4.filter.list = DWG_MODE_LIST
        p4.value = DWG_MODE_LIST[0]
        tool.parameters.append(p4)

def _batch_convert(tool, parameters, tgt_format):
    input_folder = parameters[0].valueAsText
    src_format = parameters[1].valueAsText
    output_folder = parameters[2].valueAsText

    arcpy.env.overwriteOutput = True

    coord_sys = None
    if parameters[3].value:
        coord_sys = parameters[3].valueAsText

    mode = "ArcGIS"
    if len(parameters) > 4 and parameters[4].value:
        mode = parameters[4].valueAsText

    if src_format.upper() == tgt_format.upper():
        arcpy.AddError("Source and target format are the same!")
        return

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    arcpy.AddMessage("=" * 50)
    arcpy.AddMessage("Converting: " + src_format + " -> " + tgt_format)
    arcpy.AddMessage("Input: " + input_folder)
    arcpy.AddMessage("Output: " + output_folder)
    arcpy.AddMessage("=" * 50)

    files = _get_input_files(input_folder, src_format)
    if len(files) == 0:
        arcpy.AddWarning("No " + src_format + " files found in input folder!")
        return

    arcpy.AddMessage("Found " + str(len(files)) + " files")

    sr = None
    if coord_sys:
        sr = arcpy.SpatialReference(coord_sys)

    extra = {"mode": mode}
    if tgt_format.upper() == "MDB":
        extra["mdb_path"] = _make_output_mdb(output_folder)
    elif tgt_format.upper() == "GDB":
        extra["gdb_path"] = _make_output_gdb(output_folder)

    success = 0
    fail = 0
    total = len(files)
    for i in range(total):
        fpath = files[i]
        fname = os.path.basename(fpath)
        arcpy.AddMessage("[" + str(i + 1) + "/" + str(total) + "] " + fname)
        try:
            result = convert_one(src_format, tgt_format, fpath, output_folder, extra)
            if sr and result:
                if isinstance(result, list):
                    for r in result:
                        if r.endswith(".shp"):
                            arcpy.DefineProjection_management(r, sr)
            success = success + 1
            arcpy.AddMessage("  -> OK")
        except Exception as e:
            fail = fail + 1
            arcpy.AddError("  -> FAILED: " + str(e))
            arcpy.AddError(traceback.format_exc())

    arcpy.AddMessage("=" * 50)
    arcpy.AddMessage("Done! Success:" + str(success) + " Fail:" + str(fail) + " Total:" + str(total))
    arcpy.AddMessage("=" * 50)

# ------ 5 Tools ------

class ToSHP(object):
    def __init__(self):
        self.label = "Batch to SHP"
        self.description = "Convert DWG/MDB/GDB/KML to Shapefile"
        self.canRunInBackground = False
    def getParameterInfo(self):
        _add_common_params(self, False)
        self.parameters[1].filter.list = ["DWG", "MDB", "GDB", "KML"]
        return self.parameters
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
        try:
            _batch_convert(self, parameters, "SHP")
        except Exception as e:
            import traceback
            arcpy.AddError(str(e))
            arcpy.AddError(traceback.format_exc())
            raise

class ToDWG(object):
    def __init__(self):
        self.label = "Batch to DWG"
        self.description = "Convert SHP/MDB/GDB/KML to DWG/DXF"
        self.canRunInBackground = False
    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = ["SHP", "MDB", "GDB", "KML"]
        return self.parameters
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
        try:
            _batch_convert(self, parameters, "DWG")
        except Exception as e:
            import traceback
            arcpy.AddError(str(e))
            arcpy.AddError(traceback.format_exc())
            raise

class ToMDB(object):
    def __init__(self):
        self.label = "Batch to MDB"
        self.description = "Convert SHP/DWG/GDB/KML to Personal Geodatabase"
        self.canRunInBackground = False
    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = ["SHP", "DWG", "GDB", "KML"]
        return self.parameters
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
        try:
            _batch_convert(self, parameters, "MDB")
        except Exception as e:
            import traceback
            arcpy.AddError(str(e))
            arcpy.AddError(traceback.format_exc())
            raise

class ToGDB(object):
    def __init__(self):
        self.label = "Batch to GDB"
        self.description = "Convert SHP/DWG/MDB/KML to File Geodatabase"
        self.canRunInBackground = False
    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = ["SHP", "DWG", "MDB", "KML"]
        return self.parameters
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
        try:
            _batch_convert(self, parameters, "GDB")
        except Exception as e:
            import traceback
            arcpy.AddError(str(e))
            arcpy.AddError(traceback.format_exc())
            raise

class ToKML(object):
    def __init__(self):
        self.label = "Batch to KML"
        self.description = "Convert SHP/DWG/MDB/GDB to KML/KMZ"
        self.canRunInBackground = False
    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = ["SHP", "DWG", "MDB", "GDB"]
        return self.parameters
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
        try:
            _batch_convert(self, parameters, "KML")
        except Exception as e:
            import traceback
            arcpy.AddError(str(e))
            arcpy.AddError(traceback.format_exc())
            raise

# =========================================================================
# ArcGIS Python Toolbox
# =========================================================================

class Toolbox(object):
    def __init__(self):
        self.label = "GIS Format Converter"
        self.alias = "GISConv"
        self.tools = [ToSHP, ToDWG, ToMDB, ToGDB, ToKML]
