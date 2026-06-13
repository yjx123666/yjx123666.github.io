# -*- coding: utf-8 -*-
"""
GIS格式批量互转工具箱
支持SHP/DWG/MDB/GDB/KML全部互转
兼容ArcGIS Pro和ArcMap 10.x
"""

import os
import sys
import traceback

import arcpy

# ---------------------------------------------------------------------------
# 全局常量
# ---------------------------------------------------------------------------
FORMAT_LIST = [u"SHP", u"DWG", u"MDB", u"GDB", u"KML"]
DWG_MODE_LIST = [u"ArcGIS", u"ezdxf"]

# ---------------------------------------------------------------------------
# 版本检测
# ---------------------------------------------------------------------------
def _is_arcgis_pro():
    try:
        info = arcpy.GetInstallInfo()
        if info.get("ProductName", "") == "ArcGISPro":
            return True
        return False
    except:
        return False

IS_PRO = _is_arcgis_pro()

# ---------------------------------------------------------------------------
# 兼容层：Pro用arcpy.conversion.xxx，ArcMap用arcpy.xxx_conversion
# ---------------------------------------------------------------------------
def _call_conversion(tool_name, *args, **kwargs):
    if IS_PRO:
        func = getattr(arcpy.conversion, tool_name, None)
    else:
        func = getattr(arcpy, tool_name + "_conversion", None)
    if func is None:
        raise RuntimeError(u"找不到转换工具: " + tool_name)
    return func(*args, **kwargs)

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

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
    if fmt == u"SHP":
        return _scan_files(folder, [".shp"])
    elif fmt == u"DWG":
        return _scan_files(folder, [".dwg", ".dxf"])
    elif fmt == u"MDB":
        return _scan_files(folder, [".mdb"])
    elif fmt == u"GDB":
        results = []
        for item in os.listdir(folder):
            full = os.path.join(folder, item)
            if os.path.isdir(full) and item.lower().endswith(".gdb"):
                results.append(full)
        return results
    elif fmt == u"KML":
        return _scan_files(folder, [".kml", ".kmz"])
    return []


def _get_fc_list(workspace):
    arcpy.env.workspace = workspace
    fcs = arcpy.ListFeatureClasses()
    if fcs is None:
        return []
    return [os.path.join(workspace, fc) for fc in fcs]


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
        return None, u"未安装ezdxf库，请执行: pip install ezdxf"

# =========================================================================
# 转换函数
# =========================================================================

# ------ SHP -> xxx -------------------------------------------------------

def shp_to_dwg(shp_path, out_folder, mode="ArcGIS"):
    name = _base_name(shp_path)
    if mode == "ezdxf":
        ezdxf_mod, err = _try_import_ezdxf()
        if err:
            raise RuntimeError(err)
        _shp_to_dwg_ezdxf(shp_path, out_folder, name)
    else:
        out_dwg = os.path.join(out_folder, name + ".dwg")
        _call_conversion("FeaturesToCAD", shp_path, out_dwg)
    return os.path.join(out_folder, name + ".dwg")


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
                msp.add_lwpolyline([(p[0], p[1]) for p in pts], close=True)
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


# ------ DWG -> xxx -------------------------------------------------------

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
        raise RuntimeError(u"未安装pyshp库，请执行: pip install pyshp")

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
    return [os.path.join(gdb_path, fc) for fc in fcs]


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


# ------ MDB -> xxx -------------------------------------------------------

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
            out_dwg = os.path.join(out_folder, name + ".dwg")
            _call_conversion("FeaturesToCAD", fc, out_dwg)
            results.append(out_dwg)
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


# ------ GDB -> xxx -------------------------------------------------------

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
            out_dwg = os.path.join(out_folder, name + ".dwg")
            _call_conversion("FeaturesToCAD", fc, out_dwg)
            results.append(out_dwg)
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


# ------ KML -> xxx -------------------------------------------------------

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
            arcpy.FeatureClassToFeatureClass_conversion(
                os.path.join(tmp_gdb, fc), mdb_path, fc
            )
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
            arcpy.FeatureClassToFeatureClass_conversion(
                os.path.join(tmp_gdb, fc), gdb_path, fc
            )
            results.append(os.path.join(gdb_path, fc))
    arcpy.Delete_management(tmp_gdb)
    return results


# =========================================================================
# 调度器
# =========================================================================

def convert_one(src_format, tgt_format, src_path, out_folder, extra_params=None):
    if extra_params is None:
        extra = {}
    else:
        extra = extra_params
    mode = extra.get("mode", "ArcGIS")
    sf = src_format.upper()
    tf = tgt_format.upper()

    if sf == u"SHP":
        if tf == u"DWG":
            return shp_to_dwg(src_path, out_folder, mode)
        elif tf == u"MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return shp_to_mdb(src_path, mdb)
        elif tf == u"GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return shp_to_gdb(src_path, gdb)
        elif tf == u"KML":
            return shp_to_kml(src_path, out_folder)

    elif sf == u"DWG":
        if tf == u"SHP":
            return dwg_to_shp(src_path, out_folder, mode)
        elif tf == u"MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return dwg_to_mdb(src_path, out_folder, mdb, mode)
        elif tf == u"GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return dwg_to_gdb(src_path, gdb, mode)
        elif tf == u"KML":
            return dwg_to_kml(src_path, out_folder, mode)

    elif sf == u"MDB":
        if tf == u"SHP":
            return mdb_to_shp(src_path, out_folder)
        elif tf == u"DWG":
            return mdb_to_dwg(src_path, out_folder, mode)
        elif tf == u"GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return mdb_to_gdb(src_path, gdb)
        elif tf == u"KML":
            return mdb_to_kml(src_path, out_folder)

    elif sf == u"GDB":
        if tf == u"SHP":
            return gdb_to_shp(src_path, out_folder)
        elif tf == u"DWG":
            return gdb_to_dwg(src_path, out_folder, mode)
        elif tf == u"MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return gdb_to_mdb(src_path, mdb)
        elif tf == u"KML":
            return gdb_to_kml(src_path, out_folder)

    elif sf == u"KML":
        if tf == u"SHP":
            return kml_to_shp(src_path, out_folder)
        elif tf == u"DWG":
            return kml_to_dwg(src_path, out_folder, mode)
        elif tf == u"MDB":
            mdb = extra.get("mdb_path")
            if not mdb:
                mdb = _make_output_mdb(out_folder)
            return kml_to_mdb(src_path, out_folder, mdb)
        elif tf == u"GDB":
            gdb = extra.get("gdb_path")
            if not gdb:
                gdb = _make_output_gdb(out_folder)
            return kml_to_gdb(src_path, gdb)

    raise ValueError(u"不支持的转换: " + sf + u" -> " + tf)


# =========================================================================
# ArcGIS Python Toolbox
# =========================================================================

class Toolbox(object):
    def __init__(self):
        self.label = u"GIS格式批量互转工具"
        self.alias = u"GISConverter"
        self.tools = [ToSHP, ToDWG, ToMDB, ToGDB, ToKML]


# ------ 参数辅助 ------

def _add_common_params(tool, include_mode=False):
    tool.parameters = []

    p0 = arcpy.Parameter(
        displayName=u"输入文件夹",
        name="input_folder",
        datatype="DEWorkspace",
        parameterType="Required",
        direction="Input"
    )
    tool.parameters.append(p0)

    p1 = arcpy.Parameter(
        displayName=u"源数据格式",
        name="src_format",
        datatype="GPString",
        parameterType="Required",
        direction="Input"
    )
    p1.filter.type = "ValueList"
    p1.filter.list = FORMAT_LIST
    tool.parameters.append(p1)

    p2 = arcpy.Parameter(
        displayName=u"输出文件夹",
        name="output_folder",
        datatype="DEWorkspace",
        parameterType="Required",
        direction="Input"
    )
    tool.parameters.append(p2)

    p3 = arcpy.Parameter(
        displayName=u"输出坐标系(可选)",
        name="coord_sys",
        datatype="GPCoordinateSystem",
        parameterType="Optional",
        direction="Input"
    )
    p3.value = u""
    tool.parameters.append(p3)

    if include_mode:
        p4 = arcpy.Parameter(
            displayName=u"DWG处理方式",
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

    coord_sys = None
    if parameters[3].value:
        coord_sys = parameters[3].valueAsText

    mode = "ArcGIS"
    if len(parameters) > 4 and parameters[4].value:
        mode = parameters[4].valueAsText

    if src_format.upper() == tgt_format.upper():
        arcpy.AddError(u"源格式和目标格式相同，无需转换！")
        return

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    arcpy.AddMessage(u"=" * 50)
    arcpy.AddMessage(u"GIS格式批量互转: " + src_format + u" -> " + tgt_format)
    arcpy.AddMessage(u"输入: " + input_folder)
    arcpy.AddMessage(u"输出: " + output_folder)
    arcpy.AddMessage(u"=" * 50)

    files = _get_input_files(input_folder, src_format)
    if len(files) == 0:
        arcpy.AddWarning(u"在输入文件夹中未找到 " + src_format + u" 格式的文件！")
        return

    arcpy.AddMessage(u"找到 " + str(len(files)) + u" 个待转换文件")

    sr = None
    if coord_sys:
        sr = arcpy.SpatialReference(coord_sys)

    extra = {"mode": mode}
    if tgt_format.upper() == u"MDB":
        extra["mdb_path"] = _make_output_mdb(output_folder)
    elif tgt_format.upper() == u"GDB":
        extra["gdb_path"] = _make_output_gdb(output_folder)

    success = 0
    fail = 0
    total = len(files)
    for i in range(total):
        fpath = files[i]
        fname = os.path.basename(fpath)
        idx = str(i + 1)
        arcpy.AddMessage(u"[" + idx + u"/" + str(total) + u"] " + fname)
        try:
            result = convert_one(src_format, tgt_format, fpath, output_folder, extra)
            if sr and result:
                if isinstance(result, list):
                    for r in result:
                        if r.endswith(".shp"):
                            arcpy.DefineProjection_management(r, sr)
                elif isinstance(result, str) or isinstance(result, unicode):
                    if result.endswith(".shp"):
                        arcpy.DefineProjection_management(result, sr)
            success = success + 1
            arcpy.AddMessage(u"  -> 成功")
        except Exception as e:
            fail = fail + 1
            arcpy.AddWarning(u"  -> 失败: " + str(e))
            arcpy.AddWarning(traceback.format_exc())

    arcpy.AddMessage(u"=" * 50)
    arcpy.AddMessage(u"完成! 成功:" + str(success) + u" 失败:" + str(fail) + u" 共:" + str(total))
    arcpy.AddMessage(u"=" * 50)


# ------ 5个工具类 ------

class ToSHP(object):
    def __init__(self):
        self.label = u"批量转为SHP"
        self.description = u"将DWG/MDB/GDB/KML批量转为Shapefile"
        self.canRunInBackground = True

    def getParameterInfo(self):
        _add_common_params(self, False)
        self.parameters[1].filter.list = [u"DWG", u"MDB", u"GDB", u"KML"]
        return self.parameters

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        _batch_convert(self, parameters, u"SHP")


class ToDWG(object):
    def __init__(self):
        self.label = u"批量转为DWG"
        self.description = u"将SHP/MDB/GDB/KML批量转为DWG/DXF"
        self.canRunInBackground = True

    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = [u"SHP", u"MDB", u"GDB", u"KML"]
        return self.parameters

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        _batch_convert(self, parameters, u"DWG")


class ToMDB(object):
    def __init__(self):
        self.label = u"批量转为MDB"
        self.description = u"将SHP/DWG/GDB/KML批量转为Personal Geodatabase"
        self.canRunInBackground = True

    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = [u"SHP", u"DWG", u"GDB", u"KML"]
        return self.parameters

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        _batch_convert(self, parameters, u"MDB")


class ToGDB(object):
    def __init__(self):
        self.label = u"批量转为GDB"
        self.description = u"将SHP/DWG/MDB/KML批量转为File Geodatabase"
        self.canRunInBackground = True

    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = [u"SHP", u"DWG", u"MDB", u"KML"]
        return self.parameters

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        _batch_convert(self, parameters, u"GDB")


class ToKML(object):
    def __init__(self):
        self.label = u"批量转为KML"
        self.description = u"将SHP/DWG/MDB/GDB批量转为KML/KMZ"
        self.canRunInBackground = True

    def getParameterInfo(self):
        _add_common_params(self, True)
        self.parameters[1].filter.list = [u"SHP", u"DWG", u"MDB", u"GDB"]
        return self.parameters

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        _batch_convert(self, parameters, u"KML")
