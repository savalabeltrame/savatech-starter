import qrcode
import io

def generar_string_pix(chave_pix, nome_recebedor, cidade_recebedor, valor_total, txt_id="ST01"):
    """
    Genera el string compatible con el estándar EMV/Pix del Banco Central de Brasil
    """
    # Formatear el valor a dos decimales
    valor_str = f"{valor_total:.2f}"
    
    # Estructura de bloques estáticos obligatorios del estándar Pix
    payload = "000201" # Versión del payload
    
    # Información de la cuenta / Clave Pix
    merchant_account = f"0014br.gov.bcb.pix01{len(chave_pix):02d}{chave_pix}"
    payload += f"26{len(merchant_account):02d}{merchant_account}"
    
    payload += "52040000" # Categoría de comerciante (General)
    payload += "5303986" # Código de moneda (BRL)
    
    # Monto de la transacción
    payload += f"54{len(valor_str):02d}{valor_str}"
    payload += "5802BR" # Código de país
    
    # Nombre y Ciudad del beneficiario
    payload += f"59{len(nome_recebedor):02d}{nome_recebedor}"
    payload += f"60{len(cidade_recebedor):02d}{cidade_recebedor}"
    
    # ID de la transacción (No puede tener espacios)
    additional_data = f"05{len(txt_id):02d}{txt_id}"
    payload += f"62{len(additional_data):02d}{additional_data}"
    
    # Añadir el prefijo del CRC16 obligatorio
    payload += "6304"
    
    # Cálculo del algoritmo CRC16 (Requisito bancario obligatorio)
    crc = 0xFFFF
    for char in payload:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
            
    # Retorna el código Pix completo ("Copia e Cola")
    return payload + f"{crc:04X}"
