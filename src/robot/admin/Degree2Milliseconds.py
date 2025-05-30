class Degree2Milliseconds:
    def __init__(self):
        # Konstante: 180° entsprechen 2951 ms
        self.ms_pro_grad = 2951 / 180

    def drehung_in_ms(self, grad):
        ms = grad * self.ms_pro_grad
        return round(ms, 2)

# Beispielnutzung:
if __name__ == "__main__":
    drehung = Degree2Milliseconds()
    print(drehung.drehung_in_ms(90))