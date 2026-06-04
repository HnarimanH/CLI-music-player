def convertToSeconds(length):
    minutes,seconds = length.split(':')
    return int(minutes) * 60 + int(seconds)
def convertMillisecondsToSeconds(ms):
    return ms // 1000