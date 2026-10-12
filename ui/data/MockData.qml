pragma Singleton
import QtQuick

/*
 * MockData - the hand-authored constants a few views still draw.
 *
 * Nothing here is computed and nothing here is physically authoritative:
 * the Engine Design nozzle schematic draws a hand-drawn outline, and the
 * Equation Library lists the relations the compressible-flow modules
 * implement as text. Every computed page reads its numbers from a controller,
 * never from here.
 */
QtObject {
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
}
