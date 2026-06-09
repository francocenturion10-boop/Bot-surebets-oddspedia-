import os
import time
import requests

# 1. Cargar la configuración segura desde Railway
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_alerta_telegram(mensaje):
    """Envía la alerta formateada directamente a tu Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")
        return False

def calcular_surebet(cuota_1, cuota_2, inversion_total=100):
    """Calcula el beneficio real aplicando el redondeo anti-limitaciones"""
    p1 = 1 / cuota_1
    p2 = 1 / cuota_2
    margen_total = p1 + p2

    if margen_total < 1:
        pago_esperado = inversion_total / margen_total
        
        # Redondeo estricto a números enteros para camuflar el bot ante las casas
        stake_1 = round(pago_esperado / cuota_1)
        stake_2 = round(pago_esperado / cuota_2)
        
        inversion_real = stake_1 + stake_2
        retorno_minimo = min(stake_1 * cuota_1, stake_2 * cuota_2)
        beneficio_real_pct = ((retorno_minimo - inversion_real) / inversion_real) * 100

        # Filtro: Solo si deja más del 0.5% de ganancia real tras el redondeo
        if beneficio_real_pct > 0.5:
            return {
                "es_surebet": True,
                "beneficio_pct": round(beneficio_real_pct, 2),
                "stake_1": stake_1,
                "stake_2": stake_2,
                "inversion_real": inversion_real
            }
    return {"es_surebet": False}

def procesar_datos(eventos):
    """Filtra los eventos y envía las alertas válidas"""
    # Define aquí las casas donde tienes fondos reales
    mis_casas = ["Bet365", "Codere", "Pinnacle", "Betano"]
    
    for ev in eventos:
        if ev["casa_1"] in mis_casas and ev["casa_2"] in mis_casas:
            resultado = calcular_surebet(ev["cuota_1"], ev["cuota_2"])
            
            if resultado["es_surebet"]:
                mensaje = (
                    f"🚨 *SUREBET DETECTADA* (+{resultado['beneficio_pct']}%)\n"
                    f"🏆 *Deporte:* {ev['deporte']}\n"
                    f"⚔️ *Partido:* {ev['partido']}\n"
                    f"📝 *Mercado:* {ev['mercado']}\n"
                    f"-------------------------------------\n"
                    f"📈 *Apuesta 1 ({ev['casa_1']}):* {ev['opcion_1']} @ *{ev['cuota_1']}*\n"
                    f"💰 Importe: *${resultado['stake_1']}*\n\n"
                    f"📉 *Apuesta 2 ({ev['casa_2']}):* {ev['opcion_2']} @ *{ev['cuota_2']}*\n"
                    f"💰 Importe: *${resultado['stake_2']}*\n"
                    f"-------------------------------------\n"
                    f"📊 Inversión Total Sugerida: ${resultado['inversion_real']}"
                )
                enviar_alerta_telegram(mensaje)

# --- BUCLE CONTINUO PARA RAILWAY ---
if __name__ == "__main__":
    print("🚀 Bot iniciado correctamente en Railway. Esperando datos...")
    
    # Enviar un mensaje de confirmación al iniciar para testear la conexión
    enviar_alerta_telegram("✅ *¡Bot de Arbitraje en Línea!*\nConexión exitosa con Railway. Monitoreando mercados...")

    while True:
        try:
            # TODO: Aquí es donde conectaremos la API de Apify o el scraper de Oddspedia
            # Por ahora, usamos un ejemplo de prueba estático para verificar que todo corra bien
            datos_prueba = [{
                "deporte": "Basketball",
                "partido": "Boston Celtics vs Miami Heat",
                "mercado": "Hándicap Asiático",
                "casa_1": "Bet365",
                "opcion_1": "Celtics -4.5",
                "cuota_1": 2.15,
                "casa_2": "Pinnacle",
                "opcion_2": "Heat +4.5",
                "cuota_2": 2.02
            }]
            
            procesar_datos(datos_prueba)
            
            # Pausa de 60 segundos antes de volver a escanear para no saturar
            time.sleep(60)
            
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            time.sleep(10)
