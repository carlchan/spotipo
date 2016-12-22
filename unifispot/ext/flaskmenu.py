from flask_menu import Menu

menu = Menu()


def configure(app):
    menu.init_app(app)


