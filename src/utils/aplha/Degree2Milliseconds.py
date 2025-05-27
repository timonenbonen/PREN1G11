def drehung_in_ms(grad):
    # Konstante: 180° entsprechen 2951 ms
    ms_pro_grad = 2951 / 180
    ms = grad * ms_pro_grad
    return round(ms, 2)

# Beispielnutzung:
if __name__ == "__main__":

    print(drehung_in_ms(90))
