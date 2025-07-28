from editor.blueprint_editor.node import Node, register_node


# Events
@register_node("On Enter", category="Events")
class OnEnter(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'on_enter', editor,is_event=True,properties=properties)

    def draw(self, surf, selected=False):
        super().draw(surf, selected)

@register_node("On Exit", category="Events")
class OnExit(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'on_exit', editor,is_event=True,properties=properties)

    def draw(self, surf, selected=False):
        super().draw(surf, selected)

@register_node("On Overlap", category="Events")
class OnOverlap(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'on_overlap', editor,is_event=True,properties=properties)

    def draw(self, surf, selected=False):
        super().draw(surf, selected)


@register_node("On Start", category="Events")
class OnStart(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'on_start', editor,is_event=True,properties=properties)

    def draw(self, surf, selected=False):
        super().draw(surf, selected)


@register_node("On Tick", category="Events")
class OnStart(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'on_tick', editor,is_event=True,properties=properties)

    def draw(self, surf, selected=False):
        super().draw(surf, selected)

@register_node("On End", category="Events")
class OnStart(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'on_end', editor,is_event=True,properties=properties)

    def draw(self, surf, selected=False):
        super().draw(surf, selected)