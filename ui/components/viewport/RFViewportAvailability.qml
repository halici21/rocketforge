import QtQuick
import RocketForge 1.0

/*
 * Whether a 3D view can be shown here, and the reason when it cannot.
 *
 * Two conditions: the Qt Quick 3D module is installed (Viewport3D, from the
 * backend at start-up) and this window renders through a 3D graphics API.
 * Qt Quick's software renderer -- the offscreen platform, or a machine with
 * no usable GPU path -- cannot run Qt Quick 3D, and instantiating a View3D
 * there only produces warnings and a blank item. A page checks `available`
 * before it loads a scene, so the 2D engineering view stays the view and the
 * reason is shown instead.
 */
Item {
    id: root
    width: 0
    height: 0

    readonly property int api: GraphicsInfo.api
    readonly property bool rendererReady: root.api !== GraphicsInfo.Unknown
                                          && root.api !== GraphicsInfo.Software
                                          && root.api !== GraphicsInfo.OpenVG
    readonly property bool available: Viewport3D.moduleAvailable && root.rendererReady
    readonly property string reason: !Viewport3D.moduleAvailable ? Viewport3D.moduleReason
                                   : !root.rendererReady ? Viewport3D.rendererReason : ""
}
