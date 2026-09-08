import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Isentropic charts.
 *
 * Plotted from the same computed block the table renders, so the two can never
 * disagree about what the physics said. The canvas draws points it is given;
 * it evaluates nothing.
 *
 * One quantity at a time by default: p0/p spans four decades over this Mach
 * range while T0/T spans one, and overlaying them on a shared linear axis
 * would flatten the smaller curve into the baseline.
 */
Item {
    id: page

    readonly property var quantities: Isentropic.tableColumns.filter(function (c) {
        return c.key !== "mach"
    })
    property int quantityIndex: 0
    readonly property var active: quantities.length > 0 ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var points: active ? Isentropic.chartSeries(active.key) : []
    property bool logScale: true

    onPointsChanged: plot.requestPaint()
    onLogScaleChanged: plot.requestPaint()

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 78

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                ColumnLayout {
                    Layout.preferredWidth: 420
                    spacing: 3
                    RFSectionLabel { text: "Quantity" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: page.quantities.map(function (q) { return q.label })
                        currentIndex: page.quantityIndex
                        useMonoFont: true
                        onSelected: function (index) { page.quantityIndex = index }
                    }
                }

                RFToggle {
                    text: "Logarithmic vertical axis"
                    checked: page.logScale
                    onToggled: page.logScale = checked
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: page.points.length + " points · γ = " + Isentropic.tableGamma.toFixed(3)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: page.active ? page.active.label + "  versus  M" : "Chart"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                Text {
                    text: "computed by RocketForge"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            Canvas {
                id: plot
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240

                readonly property real padLeft: 74
                readonly property real padRight: 18
                readonly property real padTop: 14
                readonly property real padBottom: 34

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.clearRect(0, 0, width, height)

                    var pts = page.points
                    if (!pts || pts.length < 2)
                        return

                    var x0 = padLeft, x1 = width - padRight
                    var y0 = padTop, y1 = height - padBottom

                    // Extents of the supplied points. No physics: this is the
                    // range of numbers handed to the canvas, nothing more.
                    var xmin = pts[0].x, xmax = pts[0].x
                    var ymin = pts[0].y, ymax = pts[0].y
                    for (var i = 1; i < pts.length; ++i) {
                        if (pts[i].x < xmin) xmin = pts[i].x
                        if (pts[i].x > xmax) xmax = pts[i].x
                        if (pts[i].y < ymin) ymin = pts[i].y
                        if (pts[i].y > ymax) ymax = pts[i].y
                    }

                    var useLog = page.logScale && ymin > 0 && (ymax / ymin) > 20
                    function ty(v) {
                        if (useLog) {
                            var lo = Math.log(ymin), hi = Math.log(ymax)
                            return y1 - (Math.log(v) - lo) / (hi - lo) * (y1 - y0)
                        }
                        return y1 - (v - ymin) / (ymax - ymin || 1) * (y1 - y0)
                    }
                    function tx(v) {
                        return x0 + (v - xmin) / (xmax - xmin || 1) * (x1 - x0)
                    }

                    // grid
                    ctx.strokeStyle = Theme.gridLine
                    ctx.lineWidth = 1
                    // The family must be quoted: an unquoted "Segoe UI" is
                    // parsed as two tokens and the whole font string is rejected.
                    ctx.font = '10px "' + Typography.sans + '"'
                    ctx.fillStyle = Theme.textMuted
                    for (var g = 0; g <= 4; ++g) {
                        var gy = y0 + (y1 - y0) * g / 4
                        ctx.beginPath(); ctx.moveTo(x0, gy); ctx.lineTo(x1, gy); ctx.stroke()
                        var val = useLog
                            ? Math.exp(Math.log(ymax) - (Math.log(ymax) - Math.log(ymin)) * g / 4)
                            : ymax - (ymax - ymin) * g / 4
                        ctx.textAlign = "right"
                        ctx.fillText(val >= 1000 || val < 0.01 ? val.toExponential(1) : val.toFixed(2),
                                     x0 - 8, gy + 3)
                    }
                    for (var h = 0; h <= 5; ++h) {
                        var gx = x0 + (x1 - x0) * h / 5
                        ctx.beginPath(); ctx.moveTo(gx, y0); ctx.lineTo(gx, y1); ctx.stroke()
                        ctx.textAlign = "center"
                        ctx.fillText((xmin + (xmax - xmin) * h / 5).toFixed(2), gx, y1 + 16)
                    }

                    // axes
                    ctx.strokeStyle = Theme.axisLine
                    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0, y1); ctx.lineTo(x1, y1); ctx.stroke()

                    // sonic marker: the one Mach number every reader looks for
                    if (xmin < 1 && xmax > 1) {
                        ctx.strokeStyle = Theme.accent
                        ctx.globalAlpha = 0.45
                        ctx.setLineDash([3, 3])
                        ctx.beginPath(); ctx.moveTo(tx(1), y0); ctx.lineTo(tx(1), y1); ctx.stroke()
                        ctx.setLineDash([])
                        ctx.globalAlpha = 1
                        ctx.fillStyle = Theme.accent
                        ctx.textAlign = "left"
                        ctx.fillText("M = 1", tx(1) + 4, y0 + 11)
                    }

                    // curve
                    ctx.strokeStyle = Theme.accent
                    ctx.lineWidth = 1.6
                    ctx.beginPath()
                    ctx.moveTo(tx(pts[0].x), ty(pts[0].y))
                    for (var k = 1; k < pts.length; ++k)
                        ctx.lineTo(tx(pts[k].x), ty(pts[k].y))
                    ctx.stroke()

                    ctx.fillStyle = Theme.textMuted
                    ctx.textAlign = "center"
                    ctx.fillText("Mach number", (x0 + x1) / 2, height - 6)
                }

                Connections {
                    target: Isentropic
                    function onTableChanged() { plot.requestPaint() }
                }
            }
        }
    }
}
