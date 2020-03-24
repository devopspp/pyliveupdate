class Render:
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    cyan = '\033[36m'
    bright_green = '\033[92m'
    white = '\033[37m\033[97m'

    bg_dark_blue_255 = '\033[48;5;24m'
    white_255 = '\033[38;5;15m'

    bold = '\033[1m'
    faint = '\033[2m'

    end = '\033[0m'
    
    @staticmethod
    def rend(str_, color):
        return '{}{}{}'.format(color, str_, Render.end)
    
    @staticmethod
    def rend_correct(str_):
        return Render.rend(str_, Render.green)
    
    @staticmethod
    def rend_wrong(str_):
        return Render.rend(str_, Render.red)