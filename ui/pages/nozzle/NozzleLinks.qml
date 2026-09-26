import QtQuick
import RocketForge 1.0
import "../../data"

/*
 * One way for every Nozzle Lab view to select: the drawing's stations and
 * the axial charts. They all write Nozzle.selection, in engineering
 * coordinates -- a station key and its solved x, or a real sample of a
 * distributed quantity -- never a pixel. Selecting solves nothing.
 */
QtObject {
    id: links

    readonly property string selectedStation: Nozzle.selection.kind === "station"
                                              ? Nozzle.selection.key : ""
    readonly property real selectedX: Nozzle.selection.active && Nozzle.selection.kind !== "tableRange"
                                      ? Nozzle.selection.x : NaN
    // A distribution row that is a station (throat, either shock row, exit)
    // lights that station on the drawing and in 3D.
    readonly property int selectedRow: Nozzle.selection.kind === "tableRow"
                                       ? parseInt(Nozzle.selection.key.slice(4)) : -1
    readonly property string rowStation: links.selectedRow >= 0 ? Nozzle.stationForRow(links.selectedRow) : ""
    readonly property string highlightStation: links.selectedStation !== "" ? links.selectedStation
                                                                            : links.rowStation

    function station(key) {
        var list = Nozzle.viewport.stations || []
        for (var i = 0; i < list.length; ++i)
            if (list[i].key === key)
                return list[i]
        return null
    }

    function selectStation(key, source) {
        var s = links.station(key)
        if (s === null)
            return
        Nozzle.selection.select("station", s.key, s.x, s.title, source)
        ShellContext.inspectorOpen = true
    }

    // A point near a station selects the station; elsewhere, the sample.
    function selectNear(x, y, label, source) {
        var list = Nozzle.viewport.stations || []
        var ext = Nozzle.viewport.extent
        var tol = ext ? 0.012 * (ext.xMax - ext.xMin) : 0
        var best = null, bestD = tol
        for (var i = 0; i < list.length; ++i) {
            var d = Math.abs(list[i].x - x)
            if (d <= bestD) { bestD = d; best = list[i] }
        }
        if (best !== null) {
            links.selectStation(best.key, source)
            return
        }
        Nozzle.selection.selectPoint("plotPoint", "axial", x, y, label, source)
    }

    // An axial position picked on the object: the nearest solved Mach sample.
    function selectAxial(x, source) {
        var parts = Nozzle.distribution["mach"] || []
        var best = null, bd = Infinity
        for (var p = 0; p < parts.length; ++p) {
            var pts = parts[p].points
            for (var k = 0; k < pts.length; ++k) {
                var d = Math.abs(pts[k].x - x)
                if (d < bd) { bd = d; best = pts[k] }
            }
        }
        if (best !== null)
            links.selectNear(best.x, best.y, "M", source)
    }

    function clear() { Nozzle.selection.clear() }

    // A distribution row: the drawing, the 3D view, the charts and the
    // inspector follow it.
    function selectRow(row, source) {
        Nozzle.selectTableRow(row)
        ShellContext.inspectorOpen = true
    }

    // The distribution row a selection is, when it is one: a row itself, a
    // station's row (the pre-shock row for the shock), or a plotted sample's.
    function rowOfSelection() {
        var sel = Nozzle.selection
        if (sel.kind === "tableRow")
            return links.selectedRow
        if (sel.kind === "station")
            return sel.key === "throat" ? Nozzle.throatRow
                 : sel.key === "shock" ? Nozzle.preShockRow
                 : sel.key === "exit" ? Nozzle.exitRow : -1
        if (sel.kind === "plotPoint")
            return Nozzle.rowForX(sel.x)
        return -1
    }
}
