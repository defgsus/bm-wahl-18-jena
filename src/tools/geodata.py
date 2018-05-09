from shapely.geometry import Polygon, MultiPolygon


class GeoData:

    def __init__(self, fileid):
        from .data import load_json
        self.data = load_json(fileid)

        self.polygons = {}
        for i, f in enumerate(self.data["features"]):
            #points = self._get_points(i)
            poly = self._get_polygon(i)
            if poly:
                self.polygons[f["n"]] = {
                    "polygon": poly,
                    "area": poly.area,
                }

    def _get_points(self, feature_idx):
        # b, d, e, c
        bb = [float(x) for x in self.data["boundingBox"].split()]
        off_x, off_y = bb[:2]
        width, height = bb[2]-bb[0], bb[3]-bb[1]
        pix_w, pix_h = self.data["pixelWidth"], self.data["pixelHeight"]
        points = self.data["features"][feature_idx]["p"][0]
        xa, ya = 0, 0
        ret = []
        for i in range(0, len(points), 2):
            xa += points[i]
            ya += points[i+1]
            ret.append((
                off_x + xa / pix_w * width,
                off_y + ya / pix_h * height
            ))
        return ret

    def _get_polygon(self, feature_idx):
        points = self._get_points(feature_idx)
        if len(points) < 3:
            return None
        return Polygon(points)

    def _get_polygons(self):
        polygons = []
        for i in range(len(self.data["features"])):
            poly = self._get_polygon(i)
            if poly:
                polygons.append(poly)
        return MultiPolygon(polygons)

    def polygon_list(self):
        polygons = []
        for n in sorted(self.polygons):
            poly = self.polygons[n].copy()
            poly["id"] = n
            polygons.append(poly)
        return polygons

    def to_svg(self, color=None, heatmap=None):
        polygons = self.polygon_list()

        bb = MultiPolygon(p["polygon"] for p in polygons).bounds
        bb = (bb[0], bb[1], bb[2]-bb[0], bb[3]-bb[1])
        svg = """<svg width="400px" height="400px" viewBox="%s" xmlns="http://www.w3.org/2000/svg" version="1.1">""" % (
            " ".join("%s" % x for x in bb),
        )

        if heatmap is not None:
            color = dict()
            for poly in polygons:
                color[poly["id"]] = heatmap.get(poly["id"], 0)
            ma = max(color.values())
            if ma:
                color = {k: color[k] / ma for k in color}
            for k in color:
                v = color[k]
                rgb = (v*255, math.pow(v, .3)*255, math.sin(v*3.14)*255)
                color[k] = "rgb(%s, %s, %s)" % tuple((max(0, min(255, x)) for x in rgb))

        for poly in polygons:
            svgpoints = " ".join("%s,%s" % (round(t[0]), round(bb[1]+bb[3]-(t[1] - bb[1])))
                                 for t in poly["polygon"].exterior.coords)
            if color is None:
                col = '#ddd'
            elif callable(color):
                col = color(poly["id"])
            elif isinstance(color, dict):
                col = color.get(poly["id"], "#ddd")
            else:
                col = color
            svg += '<polygon fill="%s" stroke="black" stroke-width="10" points="%s" />' % (
                col, svgpoints
            )

        svg += '</svg>'
        return svg

    def display(self, **kwargs):
        from IPython.display import display, HTML
        display(HTML(self.to_svg(**kwargs)))
