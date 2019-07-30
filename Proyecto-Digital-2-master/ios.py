from migen import *

from litex.soc.interconnect.csr import *
from litex.soc.cores import gpio


class Play(gpio.GPIOIn):
    pass

class Config(gpio.GPIOOut):
    pass
