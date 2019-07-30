from migen import *
from migen.genlib.fsm import *
import math
from litex.soc.interconnect.csr import *
from litex.soc.interconnect.csr_eventmanager import *

""" Modulo para generar cualquier señal de reloj:
    Parametros:
     counter: Señal contadora que debe aumentar su valor hasta un maximo.
     cyc_lvl: Señal que determina el valor del contador en el cual el clk va a cambiar de estado,
              esta debe ser de un valor mas pequeño que el valor maximo del counter. |--cyc_lvl--|
     clk: Pin fisico por el que el clock debe salir.                                              ___________
     phase: Bit que invierte el reloj si se activa, por defecto es 0 ===============>|___________|           |"""
class Clock(Module, AutoCSR):
    def __init__(self, counter, cyc_lvl, clk, phase=0):
        self.comb += clk.eq(phase != (counter >= cyc_lvl))

# Modulo principal en el que se ejecuta la maquina de estados y la logica secuencial de carga y serializacion

class _I2S(Module, AutoCSR):
    def __init__(self, scl, bck, sd, ws):
        self.width_word = width_word = Signal(6)
        self.divisor_bck = divisor_bck = Signal(7)
        self.divisor_scl = divisor_scl = Signal(5)
        self.play = play = Signal()
        self.counter_bck = counter_bck = Signal(7)
        self.counter_scl = counter_scl = Signal(5)
        self.counter_ws = counter_ws = Signal(5)
        self.counter_word = counter_word = Signal(5)
        self.load_buffer = load_buffer = Signal() #Enable
        self.load_bit = load_bit = Signal() #Enable
        self.buffer = buffer = Signal(32)
        #########################################################################################
        self.r_en = r_en = Signal()
        self.begin_save_1 = begin_save_1 = Signal()
        self.begin_save_2 = begin_save_2 = Signal()
        self.din = din = Signal(32)
        self.sel_mem = sel_mem = Signal(reset=1)
        self.start_save = start_save = Signal()

        memoria1 = Memory(32, 44100)
        self.specials += memoria1
        port_1 = memoria1.get_port(write_capable=True)

        memoria2 = Memory(32, 44100)
        self.specials += memoria2
        port_2 = memoria2.get_port(write_capable=True)

        self.specials += [port_1, port_2]


        self.submodules.i2s_mem_fsm = FSM(reset_state="IDLE")
        self.i2s_mem_fsm.act("IDLE",
            If(start_save,
                If(sel_mem,
                    NextValue(port_1.adr,0),
                    NextValue(port_1.we,1),
                    NextState("SAVE_1")
                ).Else(
                    NextValue(port_2.adr,0),
                    NextValue(port_2.we,1),
                    NextState("SAVE_2")
                )
            )
        )
        self.i2s_mem_fsm.act("SAVE_1",
            If(r_en,
                NextValue(port_1.dat_w, din),
                NextValue(port_1.adr, port_1.adr+1)
            ),
            If(port_1.adr == 44100,
                NextValue(port_1.adr,0),
                NextValue(port_1.we,0),
                NextState("IDLE")
            )
        )
        self.i2s_mem_fsm.act("SAVE_2",
            If(r_en,
                NextValue(port_2.dat_w, din),
                NextValue(port_2.adr,port_2.adr+1)
            ),
            If(port_2.adr == 44100,
                NextValue(port_2.adr,0),
                NextValue(port_2.we,0),
                NextState("IDLE")
            )
        )
        #########################################################################################

        self.comb += [
            load_bit.eq(counter_bck == divisor_bck*2-1),
            load_buffer.eq(counter_word == width_word),
        ]
        #########################################################################################
        self.sync += [
            # Contador para Reloj de datos
            counter_bck.eq(counter_bck+1),
            If(counter_bck == divisor_bck*2-1,
                counter_bck.eq(0)
            ),

            # Contador para Reloj de Filtro
            counter_scl.eq(counter_scl+1),
            If(counter_scl == divisor_scl*2-1,
                counter_scl.eq(0)
            ),

            # Intercambio de memoria
            If(~sel_mem,
                begin_save_1.eq(port_1.adr==22050)
            ).Else(
                begin_save_2.eq(port_2.adr==22050)
            )
        ]
        ########################################################################################3
        self.submodules.i2s_repro_fsm = FSM(reset_state="IDLE")
        self.i2s_repro_fsm.act("IDLE",
            If(play,
                NextState("RESET_CLOCKS")
            )
        )
        self.i2s_repro_fsm.act("RESET_CLOCKS",
            NextValue(counter_bck, 0),
            NextValue(counter_scl, 0),
            NextValue(counter_ws, 0),
            NextState("MEMORY")
        )
        self.i2s_repro_fsm.act("SERIALIZAR",
            If(load_bit,
                If(width_word == 16,
                    NextValue(sd, buffer[15]),
                    NextValue(buffer, Cat(0,buffer[0:30]))
                ).Elif(width_word == 32,
                    NextValue(sd, buffer[31]),
                    NextValue(buffer, Cat(0,buffer[0:30]))
                ),
                NextValue(counter_word,counter_word+1),
                NextValue(counter_ws,counter_ws+1)

            ),
            If(load_buffer,
                NextState("LOAD")
            )
        )
        self.i2s_repro_fsm.act("LOAD",
            If(~sel_mem,
                NextValue(buffer,port_1.dat_r),
                NextValue(port_1.adr, port_1.adr+1),
                If(port_1.adr==44100,
                    NextState("MEMORY")
                ).Else(
                    NextValue(counter_word, 0),
                    NextState("SERIALIZAR")
                ),
            ).Else(
                NextValue(buffer,port_2.dat_r),
                NextValue(port_2.adr, port_2.adr+1),
                If(port_2.adr==44100,
                    NextState("MEMORY")
                ).Else(
                    NextValue(counter_word, 0),
                    NextState("SERIALIZAR")
                ),
            )
        )
        self.i2s_repro_fsm.act("MEMORY",
            NextValue(sel_mem, sel_mem+1),
            NextState("LOAD")

        )
        ###########################################################################################3
        self.submodules.bitClock = Clock(counter_bck, divisor_bck, bck)
        self.submodules.filClock = Clock(counter_scl, divisor_scl, scl)
        self.submodules.wordSelect = Clock(counter_ws, width_word, ws)
        ############################################################################################



class I2S(Module, AutoCSR):
    def __init__(self, scl, bck, sd, ws):                                    #flt, dmp, scl, bck, din, lck, fmt, xmt):
        self.Width_word = CSRStorage(32)
        self.Divisor_BCK = CSRStorage(7)
        self.Divisor_SCL = CSRStorage(5)

        self.Start_save = CSRStorage()
        self.r_en = CSR()
        self.to_memory = CSRStorage(32)
        self.begin_save_1 = CSRStatus()
        self.begin_save_2 = CSRStatus()

        self.Play = CSRStorage()

        # # #

        #self.submodules.ev = EventManager()
        #self.ev.zero = EventSourcePulse()
        #self.ev.finalize()
        _i2s = _I2S(scl, bck, sd, ws)                                            #flt, dmp, scl, bck, din, lck, fmt, xmt)
        self.submodules += _i2s

        self.comb += [
           _i2s.width_word.eq(self.Width_word.storage),
           _i2s.divisor_bck.eq(self.Divisor_BCK.storage),
           _i2s.divisor_scl.eq(self.Divisor_SCL.storage),
           _i2s.play.eq(self.Play.storage),


           _i2s.start_save.eq(self.Start_save.storage),
           _i2s.r_en.eq(self.r_en.re),
           _i2s.din.eq(self.to_memory.storage),
           self.begin_save_1.status.eq(_i2s.begin_save_1),
           self.begin_save_2.status.eq(_i2s.begin_save_2),

        ]

if __name__ == '__main__':
    bck = Signal()
    ws = Signal()
    sd = Signal()
    scl = Signal()
    dut = _I2S(scl, bck, sd, ws)

    def dut_tb(dut):
        #yield dut.data_left.eq(10986)
        #yield dut.data_right.eq(30901)
        yield dut.width_word.eq(16)
        yield dut.divisor_bck.eq(35)
        yield dut.divisor_scl.eq(9)
        yield dut.start_save.eq(1)
        #while dut.filled.status != 44100:
        yield dut.din.eq(30901)

        #    yield dut.r_en.storage.eq(1)
        #yield dut.Start_save.storage.eq(0)
        #yield dut.Start.storage.eq(1)
        #
        for i in range(100000):
            yield
            yield dut.r_en.eq(1)
            yield
            yield dut.r_en.eq(0)
    run_simulation(dut, dut_tb(dut), vcd_name="i2s.vcd")
