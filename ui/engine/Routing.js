.pragma library

/*
 * Orthogonal connection routing, shared by the drawn connections and by the
 * line that follows the cursor while one is being made.
 *
 * Pure geometry: it takes two points and the sides they leave from, and
 * returns a polyline with rounded corners. It knows nothing about components.
 */

function isHorizontal(side) {
    return side === "left" || side === "right"
}

function stubPoint(p, side, stub) {
    if (side === "left")  return { x: p.x - stub, y: p.y }
    if (side === "right") return { x: p.x + stub, y: p.y }
    if (side === "top")   return { x: p.x, y: p.y - stub }
    return { x: p.x, y: p.y + stub }
}

/* Leave each port along its own side, then join the two stubs with at most
 * two turns. Runs that share a corridor stay parallel, which is what keeps a
 * feed system readable once it has more than a handful of components. */
function route(p1, side1, p2, side2, stub) {
    var a = stubPoint(p1, side1, stub)
    var b = stubPoint(p2, side2, stub)
    var pts = [{ x: p1.x, y: p1.y }, a]

    if (isHorizontal(side1) && isHorizontal(side2)) {
        var forward = (side1 === "right" && b.x >= a.x) || (side1 === "left" && b.x <= a.x)
        if (forward) {
            var midX = (a.x + b.x) / 2
            pts.push({ x: midX, y: a.y })
            pts.push({ x: midX, y: b.y })
        } else {
            // Doubling back: step out vertically between the two components.
            var midY = (a.y + b.y) / 2
            pts.push({ x: a.x, y: midY })
            pts.push({ x: b.x, y: midY })
        }
    } else if (!isHorizontal(side1) && isHorizontal(side2)) {
        pts.push({ x: a.x, y: b.y })
    } else if (isHorizontal(side1) && !isHorizontal(side2)) {
        pts.push({ x: b.x, y: a.y })
    } else {
        var mid = (a.y + b.y) / 2
        pts.push({ x: a.x, y: mid })
        pts.push({ x: b.x, y: mid })
    }

    pts.push(b)
    pts.push({ x: p2.x, y: p2.y })
    return simplify(pts)
}

/* A free end (the cursor while dragging) has no side of its own. */
function routeToPoint(p1, side1, cursor, stub) {
    var a = stubPoint(p1, side1, stub)
    var pts = [{ x: p1.x, y: p1.y }, a]
    if (isHorizontal(side1)) {
        var midX = (a.x + cursor.x) / 2
        pts.push({ x: midX, y: a.y })
        pts.push({ x: midX, y: cursor.y })
    } else {
        var midY = (a.y + cursor.y) / 2
        pts.push({ x: a.x, y: midY })
        pts.push({ x: cursor.x, y: midY })
    }
    pts.push({ x: cursor.x, y: cursor.y })
    return simplify(pts)
}

// Drop duplicated and collinear points so that every corner is a real corner.
function simplify(pts) {
    var packed = []
    var i
    for (i = 0; i < pts.length; ++i) {
        var p = pts[i]
        if (packed.length > 0) {
            var q = packed[packed.length - 1]
            if (Math.abs(p.x - q.x) < 0.5 && Math.abs(p.y - q.y) < 0.5)
                continue
        }
        packed.push(p)
    }

    var out = []
    for (i = 0; i < packed.length; ++i) {
        if (i === 0 || i === packed.length - 1) {
            out.push(packed[i])
            continue
        }
        var prev = packed[i - 1], cur = packed[i], next = packed[i + 1]
        var flatX = Math.abs(prev.x - cur.x) < 0.5 && Math.abs(cur.x - next.x) < 0.5
        var flatY = Math.abs(prev.y - cur.y) < 0.5 && Math.abs(cur.y - next.y) < 0.5
        if (!flatX && !flatY)
            out.push(cur)
    }
    return out
}

function distance(a, b) {
    return Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y))
}

/* Where to put the direction mark, and which way it points.
 *
 * The longest leg is chosen rather than the true mid-length point: a long
 * straight run is where an arrowhead is readable, and it is also the piece of
 * the line the eye follows. Corners are avoided for the same reason.
 * Returns null when there is no leg long enough to carry a mark. */
function flowMarker(pts, clearance) {
    if (!pts || pts.length < 2)
        return null
    var bestIndex = -1
    var bestLength = clearance
    for (var i = 0; i < pts.length - 1; ++i) {
        var len = distance(pts[i], pts[i + 1])
        if (len > bestLength) {
            bestLength = len
            bestIndex = i
        }
    }
    if (bestIndex < 0)
        return null
    var a = pts[bestIndex], b = pts[bestIndex + 1]
    return {
        x: (a.x + b.x) / 2,
        y: (a.y + b.y) / 2,
        angle: Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI
    }
}

function towards(from, to, r) {
    var d = distance(from, to)
    if (d < 0.001)
        return from
    return { x: from.x + (to.x - from.x) * r / d, y: from.y + (to.y - from.y) * r / d }
}

/* An SVG path string is the most direct way to build a rounded polyline whose
 * geometry changes on every frame of a drag. */
function roundedPath(pts, radius) {
    if (!pts || pts.length < 2)
        return ""
    var d = "M " + pts[0].x + " " + pts[0].y
    for (var i = 1; i < pts.length - 1; ++i) {
        var prev = pts[i - 1], cur = pts[i], next = pts[i + 1]
        var r = Math.min(radius, distance(prev, cur) / 2, distance(cur, next) / 2)
        var t1 = towards(cur, prev, r)
        var t2 = towards(cur, next, r)
        d += " L " + t1.x + " " + t1.y
        d += " Q " + cur.x + " " + cur.y + " " + t2.x + " " + t2.y
    }
    var last = pts[pts.length - 1]
    return d + " L " + last.x + " " + last.y
}
