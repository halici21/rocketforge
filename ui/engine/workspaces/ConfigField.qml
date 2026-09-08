import QtQuick
import "../../theme"
import "../../components"

/*
 * Renders one configuration entry as the control its kind calls for, so a
 * component workspace declares what it needs and not how to build it.
 *
 * The controls edit their own text. Nothing downstream reads them in this
 * build.
 */
Loader {
    id: root

    property var spec: null

    sourceComponent: spec && spec.kind === "choice" ? choiceField : numberField

    Component {
        id: numberField

        RFNumberField {
            width: root.width
            label: root.spec ? root.spec.label : ""
            unit: root.spec && root.spec.unit ? root.spec.unit : ""
            text: root.spec ? root.spec.value : ""
            step: root.spec && root.spec.step ? root.spec.step : 0.01
            decimals: root.spec && root.spec.value ? decimalsOf(root.spec.value) : 2

            function decimalsOf(value) {
                var dot = value.indexOf(".")
                return dot < 0 ? 0 : value.length - dot - 1
            }
        }
    }

    Component {
        id: choiceField

        RFComboBox {
            width: root.width
            label: root.spec ? root.spec.label : ""
            model: root.spec && root.spec.options ? root.spec.options : []
        }
    }
}
