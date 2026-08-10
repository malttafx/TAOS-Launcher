import nuke

taos_menu = nuke.menu("Nuke").addMenu("TAOS")


def hello_taos():
    nuke.message("TAOS Pipeline loaded successfully!")


taos_menu.addCommand(
    "Pipeline Test",
    hello_taos
)