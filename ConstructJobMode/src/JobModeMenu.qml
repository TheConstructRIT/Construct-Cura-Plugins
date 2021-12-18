// Zachary Cook
//
// Menu for enabling or disabling job mode.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM
import Cura 1.0 as Cura

Item
{
    signal clicked()

    Button {
        id: jobModeToggleButton
        width: UM.Theme.getSize("machine_selector_widget").width
        height: parent.height
        text: JobModeStage.jobModeState
        anchors.centerIn: parent
        onClicked: JobModeStage.onClick()

        contentItem: Item
        {
            width: parent.width
            height: parent.height

            Label
            {
                id: buttonText
                anchors
                {
                    left: parent.left
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                }
                text: jobModeToggleButton.text
                color: enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("small_button_text")
                font: UM.Theme.getFont("medium")
                visible: text != ""
                renderType: Text.NativeRendering
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }
        }

        background: Rectangle
        {
            id: backgroundRect
            color:
            {
                return jobModeToggleButton.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
            }
            radius: UM.Theme.getSize("action_button_radius").width
            border.width: UM.Theme.getSize("default_lining").width
            border.color: jobModeToggleButton.selected ? UM.Theme.getColor("primary") : "transparent"
        }
    }
}