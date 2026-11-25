class ErroNegocio(Exception):
    pass


class NaoEncontrado(ErroNegocio):
    pass


class Invalido(ErroNegocio):
    pass


class Conflito(ErroNegocio):
    pass