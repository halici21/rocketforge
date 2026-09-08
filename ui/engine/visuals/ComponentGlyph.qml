import QtQuick
import "../../theme"

/*
 * ComponentGlyph - the schematic symbol for a component type.
 *
 * Drawn as strokes on a 24x24 grid, in the same manner as the application icon
 * set, so glyphs recolour with the theme and stay legible from 15 px in the
 * project tree to 23 px on a node.
 *
 * The vocabulary is a propulsion schematic, not an icon set. That distinction
 * is most of what separates this canvas from a generic node editor: a rounded
 * square with a letter in it would identify a component just as reliably and
 * would say nothing, whereas a bell contour, an impeller and a pintle tip are
 * read as the parts they are before the label is read at all. So a tank is a
 * vessel with dished ends and an outlet, a pump is a volute with vanes and a
 * radial discharge, a nozzle has a throat and a bell, and a turbine has a hub
 * on a shaft inside an expanding annulus.
 *
 * Two rules hold the set together. Every symbol is line work of one weight on
 * the same grid, with no fills and no detail that dies below 16 px; and every
 * symbol is drawn in the orientation the canvas flows, left to right, so a
 * glyph on a node and the architecture around it agree.
 */
Canvas {
    id: root

    property string glyph: ""
    property color color: Theme.textSecondary
    property real strokeWidth: 1.5

    implicitWidth: 24
    implicitHeight: 24
    antialiasing: true

    onGlyphChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.save()
        ctx.scale(width / 24, height / 24)
        ctx.strokeStyle = root.color
        ctx.fillStyle = root.color

        /* The grid scale would take the stroke down with it, and a 15 px glyph
         * drawn at 0.9 px reads as grey mush. The line is therefore specified
         * in device pixels and bounded, so the whole set keeps one weight from
         * the tree to the canvas. */
        var device = Math.max(1.2, Math.min(1.7, root.strokeWidth * width / 22))
        ctx.lineWidth = device * 24 / Math.max(1, width)
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.beginPath()

        switch (root.glyph) {
        case "tank":
            // Vessel with dished ends, a level line and an outlet.
            ctx.moveTo(6, 7.5); ctx.lineTo(6, 16)
            ctx.quadraticCurveTo(6, 19.2, 12, 19.2)
            ctx.quadraticCurveTo(18, 19.2, 18, 16)
            ctx.lineTo(18, 7.5)
            ctx.quadraticCurveTo(18, 4.3, 12, 4.3)
            ctx.quadraticCurveTo(6, 4.3, 6, 7.5)
            ctx.closePath()
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(6.6, 12.2); ctx.lineTo(17.4, 12.2)
            ctx.moveTo(12, 19.2); ctx.lineTo(12, 21.6)
            break

        case "pump":
            // Centrifugal stage: axial inlet, volute, radial discharge.
            ctx.arc(11.5, 13.5, 6, 0, Math.PI * 2)
            ctx.stroke()
            ctx.beginPath()
            // Impeller vanes, swept the way the rotor turns.
            ctx.moveTo(11.5, 13.5); ctx.quadraticCurveTo(15, 12, 16.6, 15.2)
            ctx.moveTo(11.5, 13.5); ctx.quadraticCurveTo(9.5, 16.8, 12.2, 19.2)
            ctx.moveTo(11.5, 13.5); ctx.quadraticCurveTo(9.5, 10.3, 6.4, 11.6)
            ctx.stroke()
            ctx.beginPath()
            // Suction in, discharge up.
            ctx.moveTo(2.5, 13.5); ctx.lineTo(5.5, 13.5)
            ctx.moveTo(11.5, 7.5); ctx.lineTo(11.5, 3.5)
            break

        case "valve":
            // Bow tie with a stem and a handwheel.
            ctx.moveTo(4, 8); ctx.lineTo(4, 17); ctx.lineTo(12, 12.5); ctx.closePath()
            ctx.moveTo(20, 8); ctx.lineTo(20, 17); ctx.lineTo(12, 12.5); ctx.closePath()
            ctx.moveTo(12, 12.5); ctx.lineTo(12, 6)
            ctx.moveTo(8.5, 5); ctx.lineTo(15.5, 5)
            break

        case "regulator":
            // Bow tie under a sensing dome, with the sensing line to the outlet.
            ctx.moveTo(5, 13); ctx.lineTo(5, 20); ctx.lineTo(12, 16.5); ctx.closePath()
            ctx.moveTo(19, 13); ctx.lineTo(19, 20); ctx.lineTo(12, 16.5); ctx.closePath()
            ctx.moveTo(12, 16.5); ctx.lineTo(12, 11.5)
            ctx.stroke()
            ctx.beginPath()
            ctx.arc(12, 8.5, 4.5, Math.PI, 0)
            ctx.lineTo(7.5, 11.5)
            break

        case "orifice":
            // Restriction plate between two pipe walls.
            ctx.moveTo(3, 8); ctx.lineTo(21, 8)
            ctx.moveTo(3, 16); ctx.lineTo(21, 16)
            ctx.moveTo(12, 8); ctx.lineTo(12, 10.6)
            ctx.moveTo(12, 13.4); ctx.lineTo(12, 16)
            break

        case "injector":
            // Pintle: manifold, face plate, central post and a converging sheet.
            ctx.moveTo(4.5, 5); ctx.lineTo(19.5, 5)
            ctx.moveTo(4.5, 5); ctx.lineTo(4.5, 11)
            ctx.moveTo(19.5, 5); ctx.lineTo(19.5, 11)
            // Face plate, broken where the post passes through it.
            ctx.moveTo(4.5, 11); ctx.lineTo(9.6, 11)
            ctx.moveTo(14.4, 11); ctx.lineTo(19.5, 11)
            // Post and tip.
            ctx.moveTo(9.6, 6); ctx.lineTo(9.6, 15)
            ctx.moveTo(14.4, 6); ctx.lineTo(14.4, 15)
            ctx.moveTo(9.6, 15); ctx.lineTo(12, 17.6); ctx.lineTo(14.4, 15)
            // Spray.
            ctx.moveTo(12, 17.6); ctx.lineTo(7.6, 21.5)
            ctx.moveTo(12, 17.6); ctx.lineTo(16.4, 21.5)
            break

        case "chamber":
            // Injector face, barrel, throat. Open at the throat so it reads as a
            // chamber feeding something rather than a sealed pot, and closed at
            // the head by a doubled face line - without it the outline is a
            // vessel, which is the tank.
            ctx.moveTo(4, 5); ctx.lineTo(4, 19)
            ctx.moveTo(6.2, 6); ctx.lineTo(6.2, 18)
            ctx.moveTo(4, 5); ctx.lineTo(13, 5)
            ctx.quadraticCurveTo(18.5, 5, 20, 10.6)
            ctx.moveTo(4, 19); ctx.lineTo(13, 19)
            ctx.quadraticCurveTo(18.5, 19, 20, 13.4)
            break

        case "igniter":
            // Torch lead with a spark at the tip.
            ctx.moveTo(3, 20.5); ctx.lineTo(11, 12.5)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(15, 4); ctx.lineTo(15, 8)
            ctx.moveTo(19.5, 6); ctx.lineTo(15.8, 8.6)
            ctx.moveTo(19.5, 12.5); ctx.lineTo(15.8, 10.8)
            ctx.moveTo(11.5, 6.5); ctx.lineTo(14.2, 9.2)
            break

        case "nozzle":
            // Chamber, throat, bell. The proportions carry the meaning: the exit
            // is the widest station and the throat the narrowest, and the
            // divergent wall flattens towards the lip instead of running
            // straight. Drawn with the inlet as wide as the exit it reads as an
            // hourglass, which is a different part entirely.
            // The throat is left open. A tick drawn across it joins the two
            // walls and the silhouette collapses into an X at node size, which
            // is the one reading this glyph must not have.
            ctx.moveTo(3.5, 6.6); ctx.lineTo(8.4, 9.9)
            ctx.quadraticCurveTo(15, 5.4, 20.5, 2.8)
            ctx.moveTo(3.5, 17.4); ctx.lineTo(8.4, 14.1)
            ctx.quadraticCurveTo(15, 18.6, 20.5, 21.2)
            break

        case "turbine":
            // Hub on a shaft inside an expanding blade annulus.
            ctx.moveTo(2.5, 12); ctx.lineTo(6.5, 12)
            ctx.stroke()
            ctx.beginPath()
            ctx.arc(8.6, 12, 2.1, 0, Math.PI * 2)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(11.5, 7.5); ctx.lineTo(19.5, 4)
            ctx.lineTo(19.5, 20); ctx.lineTo(11.5, 16.5)
            ctx.closePath()
            ctx.moveTo(15.5, 5.7); ctx.lineTo(15.5, 18.3)
            break

        case "shaft":
            // Shaft between two bearings.
            ctx.moveTo(3, 12); ctx.lineTo(21, 12)
            ctx.stroke()
            ctx.beginPath()
            ctx.arc(8, 12, 2.6, 0, Math.PI * 2)
            ctx.stroke()
            ctx.beginPath()
            ctx.arc(16, 12, 2.6, 0, Math.PI * 2)
            break

        case "gasgenerator":
            // Small combustor, two feeds, one hot-gas outlet.
            ctx.moveTo(7, 7); ctx.lineTo(15, 7)
            ctx.quadraticCurveTo(19, 7, 19, 12)
            ctx.quadraticCurveTo(19, 17, 15, 17)
            ctx.lineTo(7, 17)
            ctx.closePath()
            ctx.moveTo(3, 9); ctx.lineTo(7, 9)
            ctx.moveTo(3, 15); ctx.lineTo(7, 15)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(19, 12); ctx.lineTo(22, 12)
            break

        case "preburner":
            // Same family as the gas generator, distinguished by the split
            // outlet: a preburner feeds turbines rather than dumping overboard.
            ctx.moveTo(6, 6); ctx.lineTo(14, 6)
            ctx.quadraticCurveTo(18, 6, 18, 12)
            ctx.quadraticCurveTo(18, 18, 14, 18)
            ctx.lineTo(6, 18)
            ctx.closePath()
            ctx.moveTo(2, 8.5); ctx.lineTo(6, 8.5)
            ctx.moveTo(2, 15.5); ctx.lineTo(6, 15.5)
            ctx.moveTo(18, 9.5); ctx.lineTo(22, 9.5)
            ctx.moveTo(18, 14.5); ctx.lineTo(22, 14.5)
            break

        case "coolingjacket":
            // Cooled wall in section: coolant channels between two skins, with
            // the heat load arriving from the gas side beneath.
            ctx.moveTo(3.5, 5); ctx.lineTo(20.5, 5)
            ctx.moveTo(3.5, 11); ctx.lineTo(20.5, 11)
            ctx.moveTo(7, 5); ctx.lineTo(7, 11)
            ctx.moveTo(10.5, 5); ctx.lineTo(10.5, 11)
            ctx.moveTo(14, 5); ctx.lineTo(14, 11)
            ctx.moveTo(17.5, 5); ctx.lineTo(17.5, 11)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(3.5, 15); ctx.lineTo(20.5, 15)
            ctx.moveTo(8, 20.5); ctx.lineTo(8, 16.5)
            ctx.moveTo(12, 20.5); ctx.lineTo(12, 16.5)
            ctx.moveTo(16, 20.5); ctx.lineTo(16, 16.5)
            break

        case "heatexchanger":
            // Shell with a counter-flow path through it.
            ctx.moveTo(4.5, 5.5); ctx.lineTo(19.5, 5.5); ctx.lineTo(19.5, 18.5)
            ctx.lineTo(4.5, 18.5); ctx.closePath()
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(4.5, 9); ctx.lineTo(12, 9); ctx.lineTo(12, 15); ctx.lineTo(19.5, 15)
            break

        case "filmcooling":
            // Chamber wall with film injected along it.
            ctx.moveTo(6, 3); ctx.lineTo(6, 21)
            ctx.moveTo(6, 7); ctx.lineTo(13, 9)
            ctx.moveTo(6, 12); ctx.lineTo(14, 14)
            ctx.moveTo(6, 17); ctx.lineTo(13, 19)
            break

        default:
            // Unknown type: a neutral placeholder box.
            ctx.moveTo(5.5, 5.5); ctx.lineTo(18.5, 5.5); ctx.lineTo(18.5, 18.5)
            ctx.lineTo(5.5, 18.5); ctx.closePath()
            break
        }

        ctx.stroke()
        ctx.restore()
    }
}
