# 🦾 Roboter starten – Anleitung

## 1. 📶 Mit dem Hotspot verbinden  
Verbinde deinen Laptop mit dem mobilen Hotspot **„Der Gerät“**.

---

## 2. 🌐 IP-Adresse des Raspberry Pi herausfinden  
Der Raspberry Pi sollte sich automatisch mit dem Hotspot verbunden haben.  
Verwende z. B. die App **Net Analyzer**, um die **IP-Adresse des Raspberry Pi** im Netzwerk zu finden.

---

## 3. 🔐 Verbindung über SSH herstellen  
Stelle eine Verbindung zum Raspberry Pi her (ersetze `IP` mit der gefundenen Adresse):

```bash
ssh -L 8001:localhost:8001 timon@IP
 ```
Dieser Befehl erstellt zusätzlich ein Port-Forwarding von localhost:8001 auf den Raspberry Pi (für Web-Interface oder Logging, falls benötigt).


## 4. ⚙️ Umgebung aktivieren & Code aktualisieren
```bash
# Python-Umgebung aktivieren
source /home/timon/PREN1G11/robot-env/bin/activate

# In das Projektverzeichnis wechseln
cd PREN1G11/

# Letzte Änderungen vom Git-Repository holen
git pull
```

## 5. ▶️ Programm starten
```bash
python -m roboter_final
```
