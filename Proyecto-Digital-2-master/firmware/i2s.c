#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <generated/csr.h>
#include <info.h>


#define CLOCK_AUDIO_BITPS 1411000

static void wait_ms(unsigned int ms){
	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(SYSTEM_CLOCK_FREQUENCY/1000*ms);
	timer0_en_write(1);
	timer0_update_value_write(1);
	while(timer0_value_read()) timer0_update_value_write(1);
}

int frame;

void cargar_Cancion(){
  printf("Inicio %d\n",SYSTEM_CLOCK_FREQUENCY/(2*CLOCK_AUDIO_BITPS));
  i2s_Width_word_write(16);
  i2s_Divisor_BCK_write(SYSTEM_CLOCK_FREQUENCY/(2*CLOCK_AUDIO_BITPS));
  i2s_Divisor_SCL_write(9);
	config_dac_out_write(8);		//b1000 = |XMT|FMT|DMP|FLT|
  printf("Cargo datos\n");
  cargar_datos();
  printf("empieza a reproducir\n");
  i2s_Play_write(1);
}

void cargar_datos(){
  int j=0;
  i2s_Start_save_write(1);
  while(j<44099){
			//i2s_to_memory_write(song[frame%180000]);
      i2s_to_memory_write(sen_1kHz_2c_16b[j%89]);
      i2s_r_en_write(1);
      j++;
			frame++;
  }
  printf("una memoria cargada\n");
  i2s_Start_save_write(0);
}
