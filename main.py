# FCS_Wifi
# Created at 2020-02-11 20:33:42.746231

import streams
import timers
import socket
from wireless import wifi
from espressif.esp32net import esp32wifi as wifi_driver

time_psoc=timers.timer()
puerto = streams.serial()


casos_surt = {0: 'error', 6: 'espera', 7: 'listo', 8: 'autorizado', 9: 'surtiendo', 10: 'venta', 11: 'venta'}
casos_id = {1: 'libre', 2: 'leyendo', 3: 'leido'}


class ProtocoloMfc():
    def __init__(self):
        self.manguera_venta = 0
        self.dinero = [0,0,0,0,0,0,0]
        self.volumen = [0,0,0,0,0,0,0]
        self.ppu_venta = [0,0,0,0,0]
        self.tota_din_1 = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.tota_din_2 = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.tota_din_3 = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.tota_vol_1 = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.tota_vol_2 = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.tota_vol_3 = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.mangueras = 6

    def enviar_recibir(self, trama, size_out, size_in):
        size = puerto.available()
        if size > 0:
            total_data = puerto.read(size)
        for i in range(size_out):
            puerto.write(trama[i])
        size = puerto.available()
        time_psoc.start()
        while (size < size_in) and (time_psoc.get() <= 5000):
            size = puerto.available()
        if size >= size_in:
            total_data = puerto.read(size_in)
        else:
            total_data = [0, 0]
        return total_data

    def estado(self, pos):
        trama = [pos, 'A']
        total_data = self.enviar_recibir(trama, 2, 3)
        if len(total_data) == 3:
            comando = chr(int(total_data[1]))
            if (comando == 'A'):
                estado = chr(int(total_data[2]))
                return estado
            else:
                return 'F'
        else:
            return 'E'
            
    def pedir_manguera(self, pos):
        trama = [pos, 'B']
        total_data = self.enviar_recibir(trama, 2, 3)
        if len(total_data) == 3:
            comando = chr(int(total_data[1]))
            if (comando == 'B'):
                manguera = chr(int(total_data[2]))
                return manguera
            else:
                return '0'
        else:
            return '0'
            
    def programar_surt(self, pos, manguera, tipo_preset, preset):
        for i in range(7 - len(preset)):
            preset += '0'
        trama = [pos, 'C', manguera, tipo_preset, chr(int(preset[0])), chr(int(preset[1])), chr(int(preset[2])), chr(int(preset[3])), chr(int(preset[4])), chr(int(preset[5])), chr(int(preset[6]))]
        total_data = self.enviar_recibir(trama, 11, 3)
        if len(total_data) == 3:
            comando = chr(int(total_data[1]))
            if (comando == 'C'):
                ok = chr(int(total_data[2]))
                return ok
            else:
                return '0'
        else:
            return '0' 
            
    def autorizar_surt(self, pos):
        trama = [pos, 'D']
        total_data = self.enviar_recibir(trama, 2, 3)
        if len(total_data) == 3:
            comando = chr(int(total_data[1]))
            if (comando == 'D'):
                ok = chr(int(total_data[2]))
                return ok
            else:
                return '0'
        else:
            return '0'
            
    def reporte_venta(self, pos):
        trama = [pos, 'E']
        total_data = self.enviar_recibir(trama, 2, 22)
        if len(total_data) == 22:
            comando = chr(int(total_data[1]))
            if (comando == 'E'):
                self.manguera_venta = chr(int(total_data[2]))
                for i in range(7):
                    self.volumen[i] = chr(int(total_data[3+i]))
                    self.dinero[i] = chr(int(total_data[10+i]))
                for i in range(5):
                    self.ppu_venta[i] = chr(int(total_data[17+i]))
                return '1'
            else:
                return '0'
        else:
            return '0'
            
    def cambiar_precio_surt(self, pos, manguera, precio):
        for i in range(5 - len(precio)):
            precio += '0'
        trama = [pos, 'F', manguera, chr(int(precio[0])), chr(int(precio[1])), chr(int(precio[2])), chr(int(precio[3])), chr(int(precio[4]))]
        total_data = self.enviar_recibir(trama, 8, 3)
        if len(total_data) == 3:
            comando = chr(int(total_data[1]))
            if (comando == 'F'):
                ok = chr(int(total_data[2]))
                return ok
            else:
                return 'F'
        else:
            return 'E' 
            
    def totales(self, pos, mangueras):
        trama = [pos, 'G', mangueras]
        total_data = self.enviar_recibir(trama, 3, 74)
        if len(total_data) == 74:
            comando = chr(int(total_data[1]))
            if (comando == 'G'):
                for i in range(12):
                    self.tota_din_1[i] = chr(int(total_data[2+i]))
                    self.tota_din_2[i] = chr(int(total_data[14+i]))
                    self.tota_din_3[i] = chr(int(total_data[26+i]))
                    self.tota_vol_1[i] = chr(int(total_data[38+i]))
                    self.tota_vol_2[i] = chr(int(total_data[50+i]))
                    self.tota_vol_3[i] = chr(int(total_data[62+i]))
                return '1'
            else:
                return 'F'
        else:
            return 'E'
            
            
def wifi_init():
    wifi_driver.auto_init()
    print("Creating Access Point...")
    try:
        wifi.softap_init("ESP32",wifi.WIFI_WPA2,"123456789")
        print("Access Point started!")
    except Exception as e:
        print("ooops, something :(", e)
        while True:
            sleep(1000)

wifi_init()
sock = socket.socket()
sock.bind(80)
sock.listen()
mfc = ProtocoloMfc()
while True:
    try:
        clientsock,addr = sock.accept()
        client = streams.SocketStream(clientsock)
        line = client.readline()
        comando = line[0:line.find(";")]
        pos = chr(int(line[line.find(";") + 1]))
        if comando == "estado":
            estado = mfc.estado(pos)   
            client.write("estado;"+pos+";"+estado+"\r\n")
        elif comando == "manguera":
            manguera = mfc.pedir_manguera(pos)  
            client.write("manguera;"+pos+";"+manguera+"\r\n")
        elif comando == "programar":
            manguera = chr(int(line[line.find(";M") + 2]))
            tipo_preset = chr(int(line[line.find(";T") + 2]))
            preset = line[(line.find(";P") + 2):line.find(".")]
            preset = preset[::-1]
            ok = mfc.programar_surt(pos,manguera,tipo_preset,preset)
            client.write("programar;"+pos+";"+ok+"\r\n")
        elif comando == "autorizar":
            ok = mfc.autorizar_surt(pos)  
            client.write("autorizar;"+pos+";"+ok+"\r\n")
        elif comando == "venta":
            ok = mfc.reporte_venta(pos)
            if ok == '1':
                volumen = "".join(mfc.volumen)
                dinero = "".join(mfc.dinero)
                ppu = "".join(mfc.ppu_venta)
                client.write("venta;"+pos+";"+ok+";"+mfc.manguera_venta+";"+volumen[::-1]+";"+dinero[::-1]+";"+ppu[::-1]+"\r\n")
            elif ok == '0':
                client.write("venta;"+pos+";"+ok+"\r\n")
        elif comando == "precio":
            manguera = chr(int(line[line.find(";M") + 2]))
            precio = line[(line.find(";P") + 2):line.find(".")]
            precio = precio[::-1]
            ok = mfc.cambiar_precio_surt(pos,manguera,precio)
            client.write("precio;"+pos+";"+ok+"\r\n")
        elif comando == "totales":
            mangueras = chr(int(line[line.find(";M") + 2]))
            ok = mfc.totales(pos, mangueras)
            if ok == '1':
                dinero1 = "".join(mfc.tota_din_1)
                dinero2 = "".join(mfc.tota_din_2)
                dinero3 = "".join(mfc.tota_din_3)
                volumen1 = "".join(mfc.tota_vol_1)
                volumen2 = "".join(mfc.tota_vol_2)
                volumen3 = "".join(mfc.tota_vol_3)
                client.write("totales;"+pos+";"+ok+";"+dinero1[::-1]+";"+dinero2[::-1]+";"+dinero3[::-1]+";"+volumen1[::-1]+";"+volumen2[::-1]+";"+volumen3[::-1]+"\r\n")
            elif ok == '0':
                client.write("totales;"+pos+";"+ok+"\r\n")
        sleep(1000)
        client.close()
    except Exception as e:
        print("ooops, something wrong:",e)

    