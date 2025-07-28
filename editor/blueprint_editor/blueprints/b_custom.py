
import pygame
from editor.blueprint_editor.node import DropdownButton, Node, register_node

# @register_node("Set custom Value", category="Custom")
# class SetExemple(Node):
#     def __init__(self, pos, editor, properties):
#         super().__init__(pos, "Set Custom", editor, properties)
#         self.add_data_pin("value", is_output=False, default=100, label="value_custom")
    
#     def execute(self, context):
#         pin = next(p for p in self.inputs if p.name == "value")
#         value = pin.connection.node.properties[pin.connection.name] if pin.connection else self.properties["value"]
#         self.editor.game_state["custom"] = int(value)
#         return next((p.connection.node for p in self.outputs if p.pin_type == "exec"), None)
  