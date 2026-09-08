pragma Singleton
import QtQuick

/*
 * MockData - every number the interface displays in this phase.
 *
 * IMPORTANT: nothing here is computed and nothing here is physically
 * authoritative. These are hand-authored, decorative constants whose only job
 * is to exercise the typography, alignment and plotting of the design system
 * while the engineering modules do not exist yet. Keeping them in one file is
 * what makes them replaceable by a real backend later: pages read from this
 * singleton, never from literals of their own.
 */
QtObject {
    // ======================= isentropic flow page =========================

    readonly property var gasModels: ["Calorically perfect", "Thermally perfect", "Real gas (planned)"]
    readonly property var gases: ["Air", "Nitrogen", "Helium", "Carbon dioxide", "Combustion products"]

    readonly property string gammaInput: "1.220"
    readonly property var givenOptions: ["Mach", "p/p₀", "T/T₀", "A/A*"]

    // The given quantity only changes which field is being asked for. Each
    // entry carries its own placeholder; nothing is converted between them.
    readonly property var givenFields: [
        { label: "Mach number",            value: "2.400",  decimals: 3, step: 0.01 },
        { label: "Pressure ratio p/p₀",    value: "0.0641", decimals: 4, step: 0.001 },
        { label: "Temperature ratio T/T₀", value: "0.4621", decimals: 4, step: 0.001 },
        { label: "Area ratio A/A*",        value: "2.731",  decimals: 3, step: 0.01 }
    ]

    // Curve family for the isentropic chart, sampled every dM = 0.2 from 0 to 4.
    readonly property real curveMachStep: 0.2
    readonly property var isentropicSeries: [
        {
            name: "p/p₀",
            values: [1.000, 0.973, 0.895, 0.784, 0.656, 0.528, 0.412, 0.314,
                     0.235, 0.174, 0.128, 0.094, 0.068, 0.050, 0.036, 0.026,
                     0.019, 0.014, 0.010, 0.008, 0.006]
        },
        {
            name: "T/T₀",
            values: [1.000, 0.992, 0.969, 0.932, 0.886, 0.832, 0.775, 0.717,
                     0.661, 0.607, 0.556, 0.508, 0.462, 0.421, 0.383, 0.349,
                     0.318, 0.290, 0.265, 0.242, 0.222]
        },
        {
            name: "ρ/ρ₀",
            values: [1.000, 0.981, 0.924, 0.841, 0.740, 0.634, 0.531, 0.438,
                     0.356, 0.287, 0.230, 0.184, 0.147, 0.118, 0.094, 0.076,
                     0.061, 0.049, 0.040, 0.033, 0.027]
        }
    ]

    // The inspected operating point drawn on the chart.
    readonly property real markerMach: 2.417
    readonly property int markerSeriesIndex: 0

    // Instrument readout under the chart.
    readonly property var flowState: [
        { label: "Mach", value: "2.417",  unit: "" },
        { label: "p/p₀", value: "0.0641", unit: "" },
        { label: "T/T₀", value: "0.4621", unit: "" },
        { label: "ρ/ρ₀", value: "0.1387", unit: "" },
        { label: "A/A*", value: "2.731",  unit: "" },
        { label: "μ",    value: "24.44",  unit: "deg" },
        { label: "ν",    value: "37.42",  unit: "deg" }
    ]

    readonly property string isentropicEquation:
        "<i>p</i>/<i>p</i><sub>0</sub> = [ 1 + ½ (γ − 1) <i>M</i><sup>2</sup> ] <sup>−γ/(γ−1)</sup>"
    readonly property var isentropicAssumptions: [
        "Steady, one-dimensional flow",
        "Adiabatic and reversible",
        "Calorically perfect gas, constant γ",
        "No body forces, no work exchange"
    ]
    readonly property string isentropicInterpretation:
        "Stagnation properties stay constant along the streamline, so every static ratio " +
        "depends on Mach number alone. The area ratio has two branches about the sonic " +
        "point, one subsonic and one supersonic, which is why the given-quantity selector " +
        "will later need a branch choice."

    // ============================ nozzle lab ==============================

    // Wall contour as (axial fraction, radius fraction) pairs, mirrored about
    // the centreline when drawn. A hand-drawn shape, not a designed contour.
    readonly property var nozzleContour: [
        [0.000, 1.000], [0.150, 1.000], [0.190, 0.980], [0.240, 0.900],
        [0.290, 0.760], [0.340, 0.580], [0.390, 0.420], [0.425, 0.330],
        [0.450, 0.300], [0.478, 0.325], [0.520, 0.395], [0.570, 0.470],
        [0.620, 0.535], [0.680, 0.598], [0.740, 0.650], [0.800, 0.694],
        [0.860, 0.730], [0.920, 0.757], [1.000, 0.780]
    ]
    readonly property real throatX: 0.450

    readonly property real backPressureDefault: 0.420

    // Operating bands along the back-pressure axis. The band widths are a
    // drawing decision; the active band is found by hit-testing the slider
    // position against them. No regime is being determined here.
    readonly property var nozzleRegimes: [
        {
            key: "underexpanded", label: "Underexpanded", short: "Under", tone: "neutral",
            from: 0.000, to: 0.055, shockX: -1, sonic: true, plume: "expand",
            note: "Expansion fans stand off the exit plane.",
            trace: [[0.00,1.000],[0.16,0.996],[0.25,0.958],[0.32,0.885],[0.38,0.752],
                    [0.425,0.628],[0.45,0.528],[0.52,0.352],[0.60,0.232],[0.70,0.152],
                    [0.80,0.106],[0.90,0.079],[1.00,0.064]]
        },
        {
            key: "ideal", label: "Ideal", short: "Ideal", tone: "success",
            from: 0.055, to: 0.105, shockX: -1, sonic: true, plume: "none",
            note: "Exit plane matched to the ambient pressure.",
            trace: [[0.00,1.000],[0.16,0.996],[0.25,0.958],[0.32,0.885],[0.38,0.752],
                    [0.425,0.628],[0.45,0.528],[0.52,0.352],[0.60,0.232],[0.70,0.152],
                    [0.80,0.106],[0.90,0.079],[1.00,0.064]]
        },
        {
            key: "overexpanded", label: "Overexpanded", short: "Over", tone: "neutral",
            from: 0.105, to: 0.340, shockX: -1, sonic: true, plume: "compress",
            note: "Oblique shock train forms outside the exit.",
            trace: [[0.00,1.000],[0.16,0.996],[0.25,0.958],[0.32,0.885],[0.38,0.752],
                    [0.425,0.628],[0.45,0.528],[0.52,0.360],[0.60,0.245],[0.70,0.170],
                    [0.80,0.125],[0.90,0.098],[1.00,0.082]]
        },
        {
            key: "internal", label: "Internal shock", short: "Shock", tone: "warning",
            from: 0.340, to: 0.720, shockX: 0.620, sonic: true, plume: "none",
            note: "Normal shock stands inside the diverging section.",
            trace: [[0.00,1.000],[0.16,0.996],[0.25,0.960],[0.32,0.890],[0.38,0.760],
                    [0.425,0.640],[0.45,0.528],[0.50,0.400],[0.55,0.320],[0.60,0.268],
                    [0.62,0.255],[0.62,0.630],[0.66,0.648],[0.75,0.676],[0.85,0.700],
                    [1.00,0.720]]
        },
        {
            key: "subsonic", label: "Subsonic", short: "Sub", tone: "neutral",
            from: 0.720, to: 1.000, shockX: -1, sonic: false, plume: "none",
            note: "Throat is not choked; the duct behaves as a venturi.",
            trace: [[0.00,1.000],[0.16,0.998],[0.25,0.975],[0.32,0.930],[0.38,0.870],
                    [0.425,0.812],[0.45,0.772],[0.50,0.800],[0.58,0.850],[0.66,0.888],
                    [0.75,0.918],[0.85,0.940],[1.00,0.955]]
        }
    ]

    readonly property var nozzleStations: [
        { label: "Chamber", value: "0.000",  unit: "M" },
        { label: "Throat",  value: "1.000",  unit: "M" },
        { label: "Exit",    value: "3.420",  unit: "M" },
        { label: "Aₑ/A*",   value: "12.40",  unit: "" },
        { label: "pₑ/p₀",   value: "0.0480", unit: "" },
        { label: "Tₑ/T₀",   value: "0.2960", unit: "" }
    ]

    // ========================== reference pages ===========================

    readonly property var equationEntries: [
        { group: "Isentropic", name: "Stagnation pressure ratio",
          body: "<i>p</i><sub>0</sub>/<i>p</i> = [ 1 + ½ (γ−1) <i>M</i><sup>2</sup> ] <sup>γ/(γ−1)</sup>" },
        { group: "Isentropic", name: "Stagnation temperature ratio",
          body: "<i>T</i><sub>0</sub>/<i>T</i> = 1 + ½ (γ−1) <i>M</i><sup>2</sup>" },
        { group: "Isentropic", name: "Area–Mach relation",
          body: "<i>A</i>/<i>A</i>* = (1/<i>M</i>) [ (2/(γ+1)) ( 1 + ½ (γ−1) <i>M</i><sup>2</sup> ) ] <sup>(γ+1)/2(γ−1)</sup>" },
        { group: "Normal shock", name: "Downstream Mach number",
          body: "<i>M</i><sub>2</sub><sup>2</sup> = ( 1 + ½ (γ−1) <i>M</i><sub>1</sub><sup>2</sup> ) / ( γ <i>M</i><sub>1</sub><sup>2</sup> − ½ (γ−1) )" },
        { group: "Normal shock", name: "Static pressure jump",
          body: "<i>p</i><sub>2</sub>/<i>p</i><sub>1</sub> = 1 + (2γ/(γ+1)) ( <i>M</i><sub>1</sub><sup>2</sup> − 1 )" },
        { group: "Oblique shock", name: "θ–β–M relation",
          body: "tan θ = 2 cot β ( <i>M</i><sub>1</sub><sup>2</sup> sin<sup>2</sup>β − 1 ) / ( <i>M</i><sub>1</sub><sup>2</sup> ( γ + cos 2β ) + 2 )" },
        { group: "Expansion", name: "Prandtl–Meyer function",
          body: "ν(<i>M</i>) = √((γ+1)/(γ−1)) arctan √( (γ−1)(<i>M</i><sup>2</sup>−1)/(γ+1) ) − arctan √( <i>M</i><sup>2</sup>−1 )" },
        { group: "Duct flow", name: "Fanno friction length",
          body: "4<i>f</i> <i>L</i>*/<i>D</i> = (1−<i>M</i><sup>2</sup>)/(γ<i>M</i><sup>2</sup>) + ((γ+1)/2γ) ln[ (γ+1)<i>M</i><sup>2</sup> / (2 + (γ−1)<i>M</i><sup>2</sup>) ]" },
        { group: "Duct flow", name: "Rayleigh stagnation temperature ratio",
          body: "<i>T</i><sub>0</sub>/<i>T</i><sub>0</sub>* = ((γ+1)<i>M</i><sup>2</sup> (2 + (γ−1)<i>M</i><sup>2</sup>)) / (1 + γ<i>M</i><sup>2</sup>)<sup>2</sup>" },
        { group: "Mass flow", name: "Choked mass flow",
          body: "ṁ = <i>p</i><sub>0</sub> <i>A</i>* √(γ/<i>R T</i><sub>0</sub>) ( 2/(γ+1) ) <sup>(γ+1)/2(γ−1)</sup>" }
    ]

    // ============================ shell status ============================

    readonly property var statusChips: [
        { label: "SI", tone: "neutral" },
        { label: "Calorically perfect", tone: "neutral" },
        { label: "Supersonic", tone: "accent" },
        { label: "Case 01", tone: "neutral" }
    ]
    readonly property string workspaceName: "Untitled workspace"
    readonly property string solverStatus: "No solver in this build"

    // ---- helpers used by the plots (array lookups only) ------------------

    // Nearest hand-authored sample to an axis position, used by the chart
    // inspector so that hovering feels alive. An array lookup, not an
    // evaluation of anything.
    function nearestSampleIndex(mach, sampleCount) {
        var i = Math.round(mach / curveMachStep)
        return Math.max(0, Math.min(sampleCount - 1, i))
    }
}
