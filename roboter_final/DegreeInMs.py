class Degree2Milliseconds:

    @staticmethod
    def turn_degrees_to_ms(degrees:float) -> int:
        ms = degrees * 2750 / 180
        return int(ms)