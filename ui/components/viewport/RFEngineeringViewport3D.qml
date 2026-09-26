import QtQuick
import QtQuick3D
import QtQuick3D.Particles3D
import RocketForge.Viewport3D 1.0
import "../../theme"
import ".."

/*
 * RFEngineeringViewport3D — a solved axisymmetric object, in three dimensions.
 *
 * It draws a viewport snapshot (rocketforge/application/visualization/
 * viewport.py) and nothing else: the revolved wall the snapshot carries, the
 * stations it names, and -- only as cues -- which way the flow goes and which
 * phases are present. There is no nozzle physics in this file. It never asks
 * a controller for anything; a camera move, a pick, a layer toggle or a
 * paused flow changes view state here and emits a signal, and that is all.
 *
 * Interaction, CAD-style:
 *   left drag     orbit (pitch clamped to +-89 degrees: the view never flips)
 *   middle drag   pan
 *   wheel         zoom towards the target, clamped between a near and a far
 *                 limit, so the camera never enters the geometry
 *   double-click  fit
 *   click         select the station under the pointer
 *   F  fit    Space  pause/resume flow    Esc  clear the selection
 *
 * Standard views ease for Motion.camera so the change of orientation can be
 * followed; direct manipulation is never animated.
 */
Item {
    id: root

    // ---- what to draw ----------------------------------------------------
    property var snapshot: ({})
    property string selectedKey: ""
    property bool stale: false
    property string staleText: "Inputs changed — showing the last solved state"
    // Shown, centred, when the snapshot is not a solved state: nothing
    // solved means nothing drawn -- no outline, no placeholder object.
    property string emptyText: ""

    // ---- view state (never solved for) -----------------------------------
    property bool cutaway: false
    property string projection: "perspective"      // perspective | orthographic
    // Flow cues play by default only in Full motion. Reduced and Off start
    // with them hidden -- static geometry -- and an explicit choice (the Flow
    // button) wins over the default.
    property bool flowVisible: Motion.spatial
    property bool flowPaused: false
    // Whether the flow layer (the particle system) exists. It follows
    // valid && flowVisible one turn of the event loop later, so the layer is
    // created and destroyed on its own, never inside the binding cascade of a
    // snapshot change: destroying the particle system while that same change
    // re-evaluated its emitters' bindings crashed Qt Quick 3D (an access
    // violation on a refused Calculate with the cues playing).
    property bool flowLayer: false
    function syncFlowLayer() { root.flowLayer = root.valid && root.flowVisible }
    onValidChanged: Qt.callLater(root.syncFlowLayer)
    onFlowVisibleChanged: Qt.callLater(root.syncFlowLayer)
    property real flowSpeed: 1.0                    // visualization playback only
    property bool showToolbar: true

    signal stationPicked(string key, real x, string title)
    signal axialPicked(real x)
    signal selectionCleared()

    // ---- derived from the snapshot --------------------------------------
    readonly property bool valid: root.snapshot !== undefined && root.snapshot !== null
                                  && root.snapshot.valid === true
    readonly property var stations: root.valid ? root.snapshot.stations : []
    readonly property var flow: root.valid ? root.snapshot.flow : ({})
    readonly property real xMin: root.valid ? root.snapshot.extent.xMin : 0
    readonly property real xMax: root.valid ? root.snapshot.extent.xMax : 1
    readonly property real rMax: root.valid ? root.snapshot.extent.rMax : 0.5
    readonly property real rThroat: root.valid ? root.snapshot.extent.rThroat : 0.2
    readonly property real span: Math.max(root.xMax - root.xMin, 2 * root.rMax, 1e-9)
    // One scene unit is the object's longest dimension, so camera limits and
    // line weights are the same for a 5 cm nozzle and a 3 m one.
    readonly property real unit: 1.0 / root.span
    readonly property real xMid: 0.5 * (root.xMin + root.xMax)

    function station(key) {
        for (var i = 0; i < root.stations.length; ++i)
            if (root.stations[i].key === key)
                return root.stations[i]
        return null
    }
    readonly property var shock: root.station("shock")
    readonly property var keepStations: {
        var out = []
        for (var i = 0; i < root.stations.length; ++i)
            out.push(root.stations[i].x)
        return out
    }

    // ---- camera -----------------------------------------------------------
    readonly property real fov: 30
    // The fraction of the canvas a fitted object fills, in its tighter axis.
    readonly property real fillFraction: 0.84
    property real yaw: -32
    property real pitch: -16
    property real distance: 2.7
    property vector3d target: Qt.vector3d(0, 0, 0)
    // The iso fit, as the scale for the zoom limits.
    readonly property real fitReference: root.fitDistanceFor(-32, -16, root.width, root.height)
    readonly property real minDistance: 0.35 * root.fitReference
    readonly property real maxDistance: 4.0 * root.fitReference
    // True until the user zooms or pans: a resize or a new solve re-frames.
    property bool framed: true
    property bool easing: false

    // The camera distance at which the object's bounding box, seen from
    // (yaw, pitch), fills the canvas: every corner inside the frustum. The
    // box is symmetric about the target, so the sign conventions of the
    // rotation do not matter.
    function fitDistanceFor(yaw, pitch, w, h) {
        var a = 0.5 * (root.xMax - root.xMin) * root.unit
        var b = root.rMax * root.unit
        var aspect = Math.max(0.25, w / Math.max(1, h))
        var tv = Math.tan(Math.PI * root.fov / 360) * root.fillFraction
        var th = Math.tan(Math.PI * root.fov / 360) * aspect * root.fillFraction
        var cy = Math.cos(yaw * Math.PI / 180), sy = Math.sin(yaw * Math.PI / 180)
        var cp = Math.cos(pitch * Math.PI / 180), sp = Math.sin(pitch * Math.PI / 180)
        var need = 0.2
        for (var i = 0; i < 8; ++i) {
            var x = (i & 1 ? a : -a), y = (i & 2 ? b : -b), z = (i & 4 ? b : -b)
            var x1 = x * cy + z * sy, z1 = -x * sy + z * cy
            var y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp
            need = Math.max(need, z2 + Math.abs(x1) / th, z2 + Math.abs(y2) / tv)
        }
        return need
    }
    function reframe() {
        if (root.framed && root.width > 0 && root.height > 0 && !root.easing)
            root.distance = root.fitDistanceFor(root.yaw, root.pitch, root.width, root.height)
    }
    // Bumped whenever anything that moves a projected point changes, so the
    // screen-space labels re-project exactly when they need to. Deferred one
    // turn of the event loop: a change handler can run before the camera's
    // own bindings have taken the new value, and a label projected then
    // would stay one camera behind.
    property int labelTick: 0
    function advanceLabels() { root.labelTick = root.labelTick + 1 }
    function bumpLabels() { Qt.callLater(root.advanceLabels) }
    onYawChanged: bumpLabels()
    onPitchChanged: bumpLabels()
    onDistanceChanged: bumpLabels()
    onTargetChanged: bumpLabels()
    onProjectionChanged: bumpLabels()
    onWidthChanged: { bumpLabels(); reframe() }
    onHeightChanged: { bumpLabels(); reframe() }
    onSnapshotChanged: { bumpLabels(); reframe() }
    Component.onCompleted: { reframe(); syncFlowLayer() }

    function clampPitch(p) { return Math.max(-89, Math.min(89, p)) }

    function fit() {
        root.easing = Motion.animated
        root.framed = true
        root.target = Qt.vector3d(0, 0, 0)
        root.distance = root.fitDistanceFor(root.yaw, root.pitch, root.width, root.height)
        easeEnd.restart()
    }

    function standardView(name) {
        var yaw = root.yaw, pitch = root.pitch
        if (name === "iso") { yaw = -32; pitch = -16 }
        else if (name === "side") { yaw = 0; pitch = 0 }
        else if (name === "top") { yaw = 0; pitch = -89 }
        else if (name === "front") { yaw = -90; pitch = 0 }
        root.easing = Motion.animated
        root.framed = true
        root.yaw = yaw
        root.pitch = pitch
        root.target = Qt.vector3d(0, 0, 0)
        root.distance = root.fitDistanceFor(yaw, pitch, root.width, root.height)
        easeEnd.restart()
    }

    Timer { id: easeEnd; interval: Motion.camera + 30; onTriggered: root.easing = false }

    Behavior on yaw { enabled: root.easing; NumberAnimation { duration: Motion.camera; easing.type: Motion.standard } }
    Behavior on pitch { enabled: root.easing; NumberAnimation { duration: Motion.camera; easing.type: Motion.standard } }
    Behavior on distance { enabled: root.easing; NumberAnimation { duration: Motion.camera; easing.type: Motion.standard } }

    // Scene position of a point on the object, for labels and picking.
    function scenePoint(x, r) {
        return Qt.vector3d((x - root.xMid) * root.unit, r * root.unit, 0)
    }

    // ---- materials ---------------------------------------------------------
    readonly property color bodyColor: Theme.isDark ? "#A3A9B1" : "#C4C0B7"
    readonly property color gasColor: Theme.isDark ? "#C9D2DB" : "#4B5663"
    readonly property color condensedColor: Theme.isDark ? "#E0CFA8" : "#6E5A38"
    readonly property color feedColor: Theme.series[0]

    View3D {
        id: view
        anchors.fill: parent
        camera: root.projection === "orthographic" ? orthoCamera : perspectiveCamera

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: Theme.plotBackground
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        Node {
            id: rig
            position: root.target
            eulerRotation: Qt.vector3d(root.pitch, root.yaw, 0)

            PerspectiveCamera {
                id: perspectiveCamera
                position: Qt.vector3d(0, 0, root.distance)
                fieldOfView: root.fov
                clipNear: 0.01
                clipFar: 50
            }
            OrthographicCamera {
                id: orthoCamera
                position: Qt.vector3d(0, 0, root.distance)
                clipNear: 0.01
                clipFar: 50
                horizontalMagnification: Math.max(1, view.height) / (root.distance * 0.62)
                verticalMagnification: Math.max(1, view.height) / (root.distance * 0.62)
            }
        }

        // Restrained key, fill and rim: enough to read the cone's form.
        DirectionalLight { eulerRotation: Qt.vector3d(-38, -28, 0); brightness: 1.35 }
        DirectionalLight { eulerRotation: Qt.vector3d(24, 150, 0); brightness: 0.6 }
        DirectionalLight { eulerRotation: Qt.vector3d(80, 0, 0); brightness: 0.35 }

        Node {
            id: object
            visible: root.valid
            scale: Qt.vector3d(root.unit, root.unit, root.unit)
            position: Qt.vector3d(-root.xMid * root.unit, 0, 0)

            Model {
                id: body
                objectName: "body"
                pickable: true
                geometry: RFRevolvedGeometry {
                    profile: root.valid ? root.snapshot.profile : ({})
                    sweep: root.cutaway ? 180 : 360
                    keep: root.keepStations
                    capStart: root.valid && root.snapshot.capStart === true
                }
                materials: PrincipledMaterial {
                    baseColor: root.bodyColor
                    roughness: 0.62
                    metalness: 0.12
                    cullMode: Material.NoCulling
                    opacity: root.stale ? 0.55 : 1.0
                }
            }

            // The axis of revolution.
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(root.xMid, 0, 0)
                eulerRotation: Qt.vector3d(0, 0, 90)
                // #Cylinder is radius 50, height 100: a line of radius 0.12 % of span
                scale: Qt.vector3d(root.span * 0.000024, (root.xMax - root.xMin) / 100, root.span * 0.000024)
                materials: PrincipledMaterial {
                    baseColor: Theme.textMuted
                    lighting: PrincipledMaterial.NoLighting
                    opacity: root.cutaway ? 0.9 : 0.35
                }
            }

            // Station rings: throat and exit always, the shock only when the
            // solution has one. A ring marks where a station is; it has no
            // physical thickness.
            Repeater3D {
                model: root.stations
                delegate: Model {
                    id: ring
                    required property var modelData
                    readonly property bool selected: modelData.key === root.selectedKey
                    readonly property bool isShock: modelData.key === "shock"
                    objectName: "station:" + modelData.key
                    pickable: true
                    position: Qt.vector3d(modelData.x, 0, 0)
                    // Selection is carried by line weight as well as colour.
                    geometry: RFRingGeometry {
                        radius: ring.modelData.r
                        tube: root.span * (ring.selected ? 0.0065 : 0.0038)
                    }
                    materials: PrincipledMaterial {
                        baseColor: ring.selected || ring.isShock ? Theme.accent
                                   : Theme.textSecondary
                        lighting: PrincipledMaterial.NoLighting
                        opacity: root.stale ? 0.55 : 1.0
                    }
                }
            }

            // The quasi-1D normal shock station: a thin plane across the
            // passage at the solved x. It is where the solver puts the
            // discontinuity -- not a shock thickness, not a resolved structure.
            // Between two solves it eases to the new station and fades in or
            // out when a shock appears or disappears: continuity for the eye,
            // not a propagating shock.
            Model {
                id: shockPlane
                objectName: "station:shock-plane"
                pickable: root.shock !== null
                // The last solved shock station; kept while it fades out.
                property real stationX: 0
                property real stationR: 1
                function follow() {
                    if (root.shock !== null) {
                        stationX = root.shock.x
                        stationR = root.shock.r
                    }
                }
                Component.onCompleted: follow()
                Connections { target: root; function onShockChanged() { shockPlane.follow() } }
                position: Qt.vector3d(stationX, 0, 0)
                eulerRotation: Qt.vector3d(0, 0, 90)
                source: "#Cylinder"
                scale: Qt.vector3d(stationR / 50, root.span * 0.00002, stationR / 50)
                opacity: root.shock !== null ? 1 : 0
                visible: opacity > 0
                Behavior on stationX { NumberAnimation { duration: Motion.data; easing.type: Motion.standard } }
                Behavior on stationR { NumberAnimation { duration: Motion.data; easing.type: Motion.standard } }
                Behavior on opacity { NumberAnimation { duration: Motion.data } }
                materials: PrincipledMaterial {
                    baseColor: Theme.accent
                    lighting: PrincipledMaterial.NoLighting
                    opacity: 0.32
                    cullMode: Material.NoCulling
                }
            }
        }

        // ---- qualitative flow cues -------------------------------------
        // Direction and phase presence only. Tracers enter at the inlet
        // plane inside the throat radius and move straight along the axis at
        // one uniform speed, so they stay inside the wall and claim no
        // velocity field. The counts are display budgets, not physical
        // particle counts. flowSpeed scales playback, not physical time.
        // Sprites are static images, not `Texture { sourceItem: ... }`: a live
        // 2D item as a texture provider, destroyed with the flow layer while
        // the scene lives on, left the renderer a dangling provider and the
        // next frame crashed (a refused Calculate with flow cues playing).
        // Qt Quick 3D's particle system runs an update animation for as long
        // as it exists -- whatever `running`, `paused` or `visible` say -- and
        // a running animation keeps the window rendering every frame. So the
        // system exists only while the cues are shown: with flow off (the
        // default in Reduced and Off motion) the 3D view is static and renders
        // nothing until something changes. A paused flow keeps its frozen cues
        // on screen, and with them the per-frame render.
        Loader3D {
            id: flowLoader
            active: root.flowLayer
            sourceComponent: Component {
                ParticleSystem3D {
                    id: flowSystem
                    objectName: "flowSystem"
                    running: true
                    paused: root.flowPaused
                    readonly property real length: (root.xMax - root.xMin) * root.unit
                    readonly property real lifeMs: 2600 / Math.max(0.25, root.flowSpeed)
                    readonly property real speed: length / (lifeMs / 1000)
                    readonly property real inletX: (root.xMin - root.xMid) * root.unit
                    readonly property real core: 0.78 * root.rThroat * root.unit
                    // The radius of the object's first station (the chamber face).
                    readonly property real inletR: root.valid && root.snapshot.profile.r.length > 0
                                                   ? root.snapshot.profile.r[0] * root.unit : core

                    // Gas: short streaks laid along the axis (the direction
                    // of travel), so a gas cue reads as a direction of flow
                    // rather than as a particle. A streak is a flat sprite, so
                    // two fixed emitters lay them in two planes that both
                    // contain the axis (x-y and x-z): seen from any side the
                    // streaks run along the flow, and looking down the axis
                    // they turn edge-on, as a line along the axis does.
                    SpriteParticle3D {
                        id: gasTracer
                        maxAmount: 220
                        color: root.gasColor
                        billboard: false
                        fadeInDuration: 160
                        fadeOutDuration: 260
                        sprite: Texture { source: "tracer_streak.png" }
                    }
                    ParticleEmitter3D {
                        id: gasStreaksXY
                        particle: gasTracer
                        enabled: root.flow.gas === true
                        position: Qt.vector3d(flowSystem.inletX, 0, 0)
                        shape: ParticleShape3D {
                            type: ParticleShape3D.Sphere
                            extents: Qt.vector3d(0.004, flowSystem.core, flowSystem.core)
                        }
                        velocity: VectorDirection3D {
                            direction: Qt.vector3d(flowSystem.speed, 0, 0)
                            directionVariation: Qt.vector3d(flowSystem.speed * 0.04, 0, 0)
                        }
                        particleRotation: Qt.vector3d(0, 0, 90)
                        emitRate: 110 / (flowSystem.lifeMs / 1000)
                        lifeSpan: flowSystem.lifeMs
                        particleScale: 0.0042
                        particleScaleVariation: 0.0008
                    }
                    ParticleEmitter3D {
                        id: gasStreaksXZ
                        particle: gasTracer
                        enabled: root.flow.gas === true
                        position: Qt.vector3d(flowSystem.inletX, 0, 0)
                        shape: ParticleShape3D {
                            type: ParticleShape3D.Sphere
                            extents: Qt.vector3d(0.004, flowSystem.core, flowSystem.core)
                        }
                        velocity: VectorDirection3D {
                            direction: Qt.vector3d(flowSystem.speed, 0, 0)
                            directionVariation: Qt.vector3d(flowSystem.speed * 0.04, 0, 0)
                        }
                        particleRotation: Qt.vector3d(90, 0, 90)
                        emitRate: 110 / (flowSystem.lifeMs / 1000)
                        lifeSpan: flowSystem.lifeMs
                        particleScale: 0.0042
                        particleScaleVariation: 0.0008
                    }

                    // Condensed phase: sparse, heavier square specks mixed with the
                    // gas streaks, shown only when the solved case reports condensed
                    // products. A different shape (a speck, not a streak) as well as a
                    // different tone, so the two phases are told apart without colour.
                    SpriteParticle3D {
                        id: condensedTracer
                        maxAmount: 48
                        color: root.condensedColor
                        billboard: true
                        fadeInDuration: 160
                        fadeOutDuration: 260
                        sprite: Texture { source: "tracer_square.png" }
                    }
                    ParticleEmitter3D {
                        particle: condensedTracer
                        enabled: root.flow.condensed === true
                        position: Qt.vector3d(flowSystem.inletX, 0, 0)
                        shape: ParticleShape3D {
                            type: ParticleShape3D.Sphere
                            extents: Qt.vector3d(0.004, flowSystem.core, flowSystem.core)
                        }
                        velocity: VectorDirection3D {
                            direction: Qt.vector3d(flowSystem.speed, 0, 0)
                            directionVariation: Qt.vector3d(flowSystem.speed * 0.04, 0, 0)
                        }
                        emitRate: 48 / (flowSystem.lifeMs / 1000)
                        lifeSpan: flowSystem.lifeMs
                        particleScale: 0.0034
                    }

                    // Liquid reactants, stylized: two feed streams entering at the
                    // chamber face, inside the wall, fading within the chamber. No
                    // spray, no droplets, no injector pattern -- the chamber is an
                    // equilibrium state, and these say only what enters.
                    SpriteParticle3D {
                        id: feedTracer
                        maxAmount: 60
                        color: root.feedColor
                        billboard: true
                        fadeInDuration: 120
                        fadeOutDuration: 320
                        sprite: Texture { source: "tracer_round.png" }
                    }
                    // Two fixed emitters, switched by `enabled` -- never created or
                    // destroyed with a snapshot. A Repeater3D rebuilt them on every
                    // snapshot change, and the particle system's next tick emitted from
                    // an emitter already detached from its parent: an access violation in
                    // QQuick3DNode::sceneTransform (a refused Calculate with cues playing).
                    ParticleEmitter3D {
                        id: feedUpper
                        particle: feedTracer
                        enabled: root.flow.liquidInlet === true
                        position: Qt.vector3d(flowSystem.inletX + 0.004,
                                              0.55 * flowSystem.inletR, 0)
                        velocity: VectorDirection3D {
                            direction: Qt.vector3d(0.09 * Math.max(0.25, root.flowSpeed), 0, 0)
                        }
                        emitRate: 18 * Math.max(0.25, root.flowSpeed)
                        lifeSpan: 1300 / Math.max(0.25, root.flowSpeed)
                        particleScale: 0.0021
                    }
                    ParticleEmitter3D {
                        id: feedLower
                        particle: feedTracer
                        enabled: root.flow.liquidInlet === true
                        position: Qt.vector3d(flowSystem.inletX + 0.004,
                                              -0.55 * flowSystem.inletR, 0)
                        velocity: VectorDirection3D {
                            direction: Qt.vector3d(0.09 * Math.max(0.25, root.flowSpeed), 0, 0)
                        }
                        emitRate: 18 * Math.max(0.25, root.flowSpeed)
                        lifeSpan: 1300 / Math.max(0.25, root.flowSpeed)
                        particleScale: 0.0021
                    }
                }
            }
        }
    }

    // ---- interaction -----------------------------------------------------
    MouseArea {
        id: drag
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        hoverEnabled: false
        property point last
        property point origin
        property bool moved: false
        onPressed: function (m) {
            root.forceActiveFocus()
            root.easing = false
            last = Qt.point(m.x, m.y)
            origin = last
            moved = false
        }
        onPositionChanged: function (m) {
            var dx = m.x - last.x, dy = m.y - last.y
            last = Qt.point(m.x, m.y)
            if (Math.abs(m.x - origin.x) + Math.abs(m.y - origin.y) > 3)
                moved = true
            if (m.buttons & Qt.LeftButton) {
                root.yaw -= dx * 0.35
                root.pitch = root.clampPitch(root.pitch - dy * 0.35)
            } else if (m.buttons & Qt.MiddleButton) {
                root.framed = false
                var k = root.distance / Math.max(200, view.height) * 0.8
                var right = perspectiveCamera.right, up = perspectiveCamera.up
                root.target = Qt.vector3d(root.target.x - (right.x * dx - up.x * dy) * k,
                                          root.target.y - (right.y * dx - up.y * dy) * k,
                                          root.target.z - (right.z * dx - up.z * dy) * k)
            }
        }
        onReleased: function (m) {
            if (!moved && m.button === Qt.LeftButton)
                root.pickAt(m.x, m.y)
        }
        onDoubleClicked: root.fit()
        onWheel: function (w) {
            root.easing = false
            root.framed = false
            var f = w.angleDelta.y > 0 ? 0.88 : 1.0 / 0.88
            root.distance = Math.max(root.minDistance, Math.min(root.maxDistance, root.distance * f))
        }
    }

    // The station under the pointer, else the axial position on the wall.
    function pickAt(px, py) {
        var hit = view.pick(px, py)
        var node = hit.objectHit
        if (node && node.objectName.indexOf("station:") === 0) {
            var key = node.objectName.substring(8)
            if (key === "shock-plane")
                key = "shock"
            var s = root.station(key)
            if (s !== null) {
                root.stationPicked(s.key, s.x, s.title)
                return s.key
            }
        }
        if (node && node.objectName === "body") {
            var local = object.mapPositionFromScene(hit.scenePosition)
            // near a station: that station; otherwise the axial position
            var best = null, bestD = 0.035 * root.span
            for (var i = 0; i < root.stations.length; ++i) {
                var d = Math.abs(root.stations[i].x - local.x)
                if (d < bestD) { bestD = d; best = root.stations[i] }
            }
            if (best !== null) {
                root.stationPicked(best.key, best.x, best.title)
                return best.key
            }
            root.axialPicked(Math.max(root.xMin, Math.min(root.xMax, local.x)))
            return "axial"
        }
        root.selectionCleared()
        return ""
    }

    Keys.onPressed: function (event) {
        if (event.key === Qt.Key_F) { root.fit(); event.accepted = true }
        else if (event.key === Qt.Key_Space) { root.flowPaused = !root.flowPaused; event.accepted = true }
        else if (event.key === Qt.Key_Escape) { root.selectionCleared(); event.accepted = true }
    }

    // ---- screen-space station labels ---------------------------------------
    Repeater {
        model: root.valid ? root.stations : []
        delegate: Text {
            required property var modelData
            readonly property bool selected: modelData.key === root.selectedKey
            readonly property vector3d at: {
                root.labelTick
                return view.mapFrom3DScene(root.scenePoint(modelData.x, modelData.r * 1.12))
            }
            x: at.x - implicitWidth / 2
            y: at.y - implicitHeight - 4
            visible: at.z > 0 && x > 0 && y > 0 && x < root.width - implicitWidth
            text: modelData.title
            color: selected || modelData.key === "shock" ? Theme.accent : Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.chartAnnotation
            font.weight: selected ? Typography.medium : Typography.regular
        }
    }

    // ---- what this picture is ---------------------------------------------
    Column {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: Metrics.spacing.m
        spacing: 2

        Text {
            text: root.valid ? root.snapshot.label : ""
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.letterSpacing: 0.4
        }
        Text {
            visible: root.shock !== null
            text: "QUASI-1D NORMAL SHOCK STATION, NOT A RESOLVED SHOCK"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.letterSpacing: 0.4
        }
        Text {
            visible: root.valid && root.flowVisible
            text: root.valid ? root.flow.label : ""
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.letterSpacing: 0.4
        }
        Row {
            visible: root.valid && root.flowVisible
            spacing: Metrics.spacing.m
            Row {
                spacing: 4
                // a streak, as the gas cues are drawn
                Rectangle { width: 12; height: 2; radius: 1; color: root.gasColor; anchors.verticalCenter: parent.verticalCenter }
                Text { text: "gas"; color: Theme.textMuted; font.family: Typography.sans; font.pixelSize: Typography.meta }
            }
            Row {
                visible: root.flow.condensed === true
                spacing: 4
                Rectangle { width: 7; height: 7; color: root.condensedColor; anchors.verticalCenter: parent.verticalCenter }
                Text {
                    text: "condensed phase present — " + (root.flow.condensedLabel || "")
                          + (root.flow.condensedFraction ? "  (" + (root.flow.condensedFraction * 100).toFixed(1) + " % of the mass)" : "")
                    color: Theme.textMuted; font.family: Typography.sans; font.pixelSize: Typography.meta
                }
            }
            Row {
                visible: root.flow.liquidInlet === true
                spacing: 4
                Rectangle { width: 6; height: 6; radius: 3; color: root.feedColor; anchors.verticalCenter: parent.verticalCenter }
                Text { text: "liquid feed (stylized)"; color: Theme.textMuted; font.family: Typography.sans; font.pixelSize: Typography.meta }
            }
            Text {
                text: "counts are a display budget"
                color: Theme.textMuted; font.family: Typography.sans; font.pixelSize: Typography.meta; font.italic: true
            }
        }
    }

    // ---- nothing solved, said -------------------------------------------------
    Text {
        objectName: "viewportEmptyText"
        anchors.centerIn: parent
        width: Math.min(parent.width - 2 * Metrics.spacing.xl, 520)
        visible: !root.valid && root.emptyText !== ""
        text: root.emptyText
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.body
    }

    // ---- stale state, stated -------------------------------------------------
    RFStatusChip {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: Metrics.spacing.m
        visible: root.stale && root.valid
        text: root.staleText
        tone: "warning"
    }

    // ---- the context toolbar -------------------------------------------------
    Row {
        id: toolbar
        objectName: "viewportToolbar"
        visible: root.showToolbar && root.valid
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Metrics.spacing.m
        spacing: Metrics.spacing.xs

        RFToolButton { text: "ISO"; tooltip: "Isometric view"; onClicked: root.standardView("iso") }
        RFToolButton { text: "Side"; tooltip: "Side view, along the axis normal"; onClicked: root.standardView("side") }
        RFToolButton { text: "Top"; tooltip: "Top view"; onClicked: root.standardView("top") }
        RFToolButton { text: "Front"; tooltip: "Front view, looking down the axis"; onClicked: root.standardView("front") }
        RFToolButton { text: "Fit"; tooltip: "Fit the object (F, or double-click)"; onClicked: root.fit() }
        Item { width: Metrics.spacing.s; height: 1 }
        RFToolButton {
            text: "Cutaway"; checked: root.cutaway
            tooltip: "Half revolution: shows the axis and the stations on it"
            onClicked: root.cutaway = !root.cutaway
        }
        RFToolButton {
            text: root.projection === "orthographic" ? "Ortho" : "Persp"
            tooltip: "Perspective or orthographic projection"
            onClicked: root.projection = root.projection === "orthographic" ? "perspective" : "orthographic"
        }
        Item { width: Metrics.spacing.s; height: 1 }
        RFToolButton {
            text: "Flow"; checked: root.flowVisible
            tooltip: "Qualitative flow cues: direction and phase presence only"
            onClicked: root.flowVisible = !root.flowVisible
        }
        RFToolButton {
            text: root.flowPaused ? "Play" : "Pause"
            enabled: root.flowVisible
            tooltip: "Pause or resume the flow cues (Space)"
            onClicked: root.flowPaused = !root.flowPaused
        }
        RFToolButton {
            text: root.flowSpeed + "×"
            enabled: root.flowVisible
            tooltip: "Visualization playback speed, not a physical time scale"
            onClicked: root.flowSpeed = root.flowSpeed === 0.5 ? 1 : root.flowSpeed === 1 ? 2 : 0.5
        }
    }
}
