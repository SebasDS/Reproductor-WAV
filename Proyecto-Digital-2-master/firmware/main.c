#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>


#include <irq.h>
#include <uart.h>
#include <console.h>
#include <generated/csr.h>

static void wait_ms(unsigned int ms){
	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(SYSTEM_CLOCK_FREQUENCY/1000*ms);
	timer0_en_write(1);
	timer0_update_value_write(1);
	while(timer0_value_read()) timer0_update_value_write(1);
}



int main(void){

	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nlm32-CONFIG i2s, timer and uart "__DATE__" "__TIME__"\n");


	while(1){
		int init = gpio_play_in_read();
		printf("esperando boton\n");
		if(init){
			cargar_Cancion();
			break;
		}
	}


	while(1){
		int init_1 = i2s_begin_save_1_read();
		int init_2 = i2s_begin_save_2_read();
		if(init_1){
			cargar_datos();
			wait_ms(1);
			printf("cargando memoria 1\n");
		}else if(init_2){
			cargar_datos();
			wait_ms(1);
			printf("cargando memoria 2\n");
		}else{

			//LCD
		}
	}

	return 0;
}
