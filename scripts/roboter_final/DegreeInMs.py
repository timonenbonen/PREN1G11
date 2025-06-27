class Degree2Milliseconds:

    @staticmethod
    def turn_degrees_to_ms(degrees:float) -> int:
        ms = degrees * 2951 / 180
        return int(ms)